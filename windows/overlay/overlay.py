"""
Overlay Trigger - green overlay on a screen zone that watches the zone's state and,
when it changes from state X to state Y, performs an action (click).

Usage:
  1. "Select zone"      -> drag a rectangle on the screen (Esc cancels)
  2. "Capture state X"  -> snapshots the zone as it is now (starting state)
  3. "Capture state Y"  -> snapshots the zone in the state that triggers the action
  4. "Click point"      -> within 3 seconds move the mouse where you want to click
                           (if not set: center of the zone)
  5. "Start" (or F8)    -> monitoring on; F8 stops everything at any time

The overlay is click-through (clicks go through it) and is excluded from screen
captures, so the green tint doesn't skew the image comparison.
"""

import ctypes
import json
import os
import time
import tkinter as tk
from ctypes import wintypes
from tkinter import ttk

import numpy as np
try:
    import cv2
except ImportError:      # search mode needs OpenCV (pip install opencv-python)
    cv2 = None

from PIL import Image, ImageChops, ImageGrab, ImageStat, ImageTk

# Physical pixel coordinates even with Windows scaling at 125%/150%
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()

user32 = ctypes.windll.user32

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WDA_EXCLUDEFROMCAPTURE = 0x11
VK_F8 = 0x77

MOUSE = {
    "left click": (0x0002, 0x0004, 1),
    "double click": (0x0002, 0x0004, 2),
    "right click": (0x0008, 0x0010, 1),
}
# action names used by older (Italian) versions of config.json
LEGACY_ACTIONS = {"click sinistro": "left click", "doppio click": "double click", "click destro": "right click"}

BASE = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(BASE, "config.json")
DEFAULTS = {
    "region": None,          # [left, top, right, bottom]
    "click_point": None,     # [x, y]
    "threshold": 12.0,       # max distance (0-255) to recognize a state
    "interval_ms": 200,
    "stable_frames": 2,      # consecutive readings needed to confirm a state
    "cooldown_s": 1.0,
    "action": "left click",
    "restore_cursor": True,
    "overlay_alpha": 0.30,
    "follow_window": False,  # move zone/click point together with a chosen window
    "win_title": "",         # title of the window to follow
    "search_mode": False,    # look for the captured figure inside a larger area
    "search_region": None,   # [left, top, right, bottom] of that area
    "win_anchor": None,      # [left, top] of that window when zone/point were set
}


def virtual_screen():
    return (user32.GetSystemMetrics(76), user32.GetSystemMetrics(77),
            user32.GetSystemMetrics(78), user32.GetSystemMetrics(79))


def hwnd_of(win):
    win.update_idletasks()
    return user32.GetParent(win.winfo_id()) or win.winfo_id()


def make_clickthrough(win):
    hwnd = hwnd_of(win)
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT
                          | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)
    user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)


def window_title(hwnd):
    buf = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(hwnd, buf, 512)
    return buf.value


def find_window(title):
    """First visible top-level window whose title contains `title`."""
    found = []
    proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(
        lambda h, _l: (found.append(h) if user32.IsWindowVisible(h) and title.lower()
                       in window_title(h).lower() else None) or True)
    user32.EnumWindows(proc, 0)
    return found[0] if found else None


def window_origin(hwnd):
    r = wintypes.RECT()
    if not hwnd or not user32.IsWindow(hwnd) or user32.IsIconic(hwnd)             or not user32.GetWindowRect(hwnd, ctypes.byref(r)):
        return None
    return r.left, r.top


def signature(img):
    return img.convert("RGB").resize((32, 32), Image.BILINEAR)


def distance(a, b):
    return sum(ImageStat.Stat(ImageChops.difference(a, b)).mean) / 3.0


def mouse_click(x, y, action, restore):
    down, up, times = MOUSE[action]
    old = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(old))
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.03)
    for _ in range(times):
        user32.mouse_event(down, 0, 0, 0, 0)
        user32.mouse_event(up, 0, 0, 0, 0)
        time.sleep(0.05)
    if restore:
        user32.SetCursorPos(old.x, old.y)


def ref_path(key):
    path = os.path.join(BASE, f"state_{key}.png")
    legacy = os.path.join(BASE, f"stato_{key}.png")
    return legacy if not os.path.exists(path) and os.path.exists(legacy) else path


class App:
    def __init__(self):
        self.cfg = dict(DEFAULTS)
        if os.path.exists(CFG_PATH):
            try:
                with open(CFG_PATH, encoding="utf-8") as f:
                    self.cfg.update(json.load(f))
            except Exception:
                pass
        self.cfg["action"] = LEGACY_ACTIONS.get(self.cfg["action"], self.cfg["action"])
        if self.cfg["action"] not in MOUSE:
            self.cfg["action"] = DEFAULTS["action"]

        self.refs = {"X": None, "Y": None}      # 32x32 signatures
        self.thumbs = {}
        self.full = {}                          # full-resolution templates (RGB arrays)
        self.found = {}                         # last match position per state (screen coords)
        self.match_rect = None
        self.ov_last = None
        self.running = False
        self.stable = None
        self.candidate = None
        self.cand_count = 0
        self.last_action = 0.0
        self.f8_was_down = False
        self.follow_hwnd = None
        self.last_delta = (0, 0)

        self.root = tk.Tk()
        self.root.title("Overlay Trigger")
        self.root.attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.build_ui()

        self.overlay = tk.Toplevel(self.root)
        self.overlay.overrideredirect(True)
        self.overlay.attributes("-topmost", True)
        self.overlay.attributes("-alpha", self.cfg["overlay_alpha"])
        self.overlay.configure(bg="#00c853")
        self.overlay.withdraw()

        for key in ("X", "Y"):
            path = ref_path(key)
            if os.path.exists(path) and self.cfg["region"]:
                self.set_ref(key, Image.open(path).convert("RGB"), save=False)

        self.refresh_info()
        self.show_overlay()
        self.root.after(200, self.tick)

    # ---------------------------------------------------------------- UI
    def build_ui(self):
        r = self.root
        pad = {"padx": 6, "pady": 3}
        top = ttk.Frame(r)
        top.pack(fill="x", **pad)
        ttk.Button(top, text="1. Select zone", command=self.select_region).pack(side="left", padx=2)
        ttk.Button(top, text="2. Capture state X", command=lambda: self.capture_ref("X")).pack(side="left", padx=2)
        ttk.Button(top, text="3. Capture state Y", command=lambda: self.capture_ref("Y")).pack(side="left", padx=2)
        ttk.Button(top, text="4. Click point (3s)", command=self.pick_point).pack(side="left", padx=2)

        self.info = ttk.Label(r, text="")
        self.info.pack(anchor="w", **pad)

        refs = ttk.Frame(r)
        refs.pack(fill="x", **pad)
        self.ref_labels = {}
        for key in ("X", "Y"):
            box = ttk.LabelFrame(refs, text=f"State {key}")
            box.pack(side="left", padx=4)
            lbl = ttk.Label(box, text="(not captured)", width=22, anchor="center")
            lbl.pack(padx=4, pady=4)
            self.ref_labels[key] = lbl

        live = ttk.Frame(r)
        live.pack(fill="x", **pad)
        self.state_lbl = ttk.Label(live, text="State: -", font=("Segoe UI", 12, "bold"))
        self.state_lbl.pack(side="left")
        self.dist_lbl = ttk.Label(live, text="")
        self.dist_lbl.pack(side="left", padx=12)

        opts = ttk.Frame(r)
        opts.pack(fill="x", **pad)
        self.v_thr = tk.DoubleVar(value=self.cfg["threshold"])
        self.v_int = tk.IntVar(value=self.cfg["interval_ms"])
        self.v_cool = tk.DoubleVar(value=self.cfg["cooldown_s"])
        self.v_act = tk.StringVar(value=self.cfg["action"])
        self.v_restore = tk.BooleanVar(value=self.cfg["restore_cursor"])
        self.v_show = tk.BooleanVar(value=True)
        self.v_follow = tk.BooleanVar(value=self.cfg["follow_window"])
        self.v_search = tk.BooleanVar(value=self.cfg["search_mode"])
        ttk.Label(opts, text="Threshold").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(opts, from_=1, to=100, increment=1, width=6, textvariable=self.v_thr).grid(row=0, column=1)
        ttk.Label(opts, text="Interval ms").grid(row=0, column=2, sticky="w", padx=(10, 0))
        ttk.Spinbox(opts, from_=50, to=5000, increment=50, width=6, textvariable=self.v_int).grid(row=0, column=3)
        ttk.Label(opts, text="Cooldown s").grid(row=0, column=4, sticky="w", padx=(10, 0))
        ttk.Spinbox(opts, from_=0, to=60, increment=0.5, width=6, textvariable=self.v_cool).grid(row=0, column=5)
        ttk.Label(opts, text="Action").grid(row=1, column=0, sticky="w")
        ttk.Combobox(opts, values=list(MOUSE), textvariable=self.v_act, state="readonly",
                     width=14).grid(row=1, column=1, columnspan=2, sticky="w")
        ttk.Checkbutton(opts, text="Move mouse back afterwards", variable=self.v_restore).grid(
            row=1, column=3, columnspan=2, sticky="w", padx=(10, 0))
        ttk.Checkbutton(opts, text="Show overlay", variable=self.v_show,
                        command=self.show_overlay).grid(row=1, column=5, sticky="w")

        srch = ttk.Frame(r)
        srch.pack(fill="x", **pad)
        ttk.Checkbutton(srch, text="Search figure in larger area", variable=self.v_search,
                        command=self.toggle_search).pack(side="left")
        ttk.Button(srch, text="5. Select search area", command=lambda: self.select_region("search")
                   ).pack(side="left", padx=6)

        win = ttk.Frame(r)
        win.pack(fill="x", **pad)
        ttk.Checkbutton(win, text="Follow window", variable=self.v_follow,
                        command=self.toggle_follow).pack(side="left")
        ttk.Button(win, text="Pick window (3s)", command=self.pick_window).pack(side="left", padx=6)
        self.win_lbl = ttk.Label(win, text="")
        self.win_lbl.pack(side="left")

        self.run_btn = ttk.Button(r, text="▶ Start (F8)", command=self.toggle_run)
        self.run_btn.pack(fill="x", **pad)

        self.log_box = tk.Text(r, height=8, width=70, state="disabled", font=("Consolas", 9))
        self.log_box.pack(fill="both", expand=True, **pad)

    def log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", time.strftime("%H:%M:%S ") + msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def refresh_info(self):
        reg = self.cfg["region"]
        pt = self.cfg["click_point"]
        txt = f"Zone: {reg if reg else 'not set'}    Click point: "
        txt += f"{pt}" if pt else ("zone center" if reg else "-")
        self.info.configure(text=txt)
        if hasattr(self, "win_lbl"):
            t = self.cfg["win_title"]
            self.win_lbl.configure(text=(t[:40] + "…" if len(t) > 40 else t) if t else "(no window picked)")

    # ---------------------------------------------------------------- follow window
    def delta(self):
        """Offset of the followed window from where it was when zone/point were set."""
        if not (self.cfg["follow_window"] and self.cfg["win_anchor"] and self.cfg["win_title"]):
            return 0, 0
        org = window_origin(self.follow_hwnd)
        if org is None:
            self.follow_hwnd = find_window(self.cfg["win_title"])
            org = window_origin(self.follow_hwnd)
        if org is None:
            return self.last_delta      # window not found/minimized: keep last position
        ax, ay = self.cfg["win_anchor"]
        self.last_delta = (org[0] - ax, org[1] - ay)
        return self.last_delta

    def eff_region(self):
        reg = self.cfg["region"]
        if not reg:
            return None
        dx, dy = self.delta()
        return [reg[0] + dx, reg[1] + dy, reg[2] + dx, reg[3] + dy]

    def eff_point(self):
        pt = self.cfg["click_point"]
        if self.search_on() and self.found.get("Y"):
            # click relative to where the figure was found (offset taken from the captured zone)
            fx, fy = self.found["Y"]
            reg = self.cfg["region"]
            if pt:
                return fx + pt[0] - reg[0], fy + pt[1] - reg[1]
            h, w = self.full["Y"].shape[:2]
            return fx + w // 2, fy + h // 2
        if pt:
            dx, dy = self.delta()
            return pt[0] + dx, pt[1] + dy
        reg = self.eff_region()
        return ((reg[0] + reg[2]) // 2, (reg[1] + reg[3]) // 2)

    def toggle_follow(self):
        self.cfg["follow_window"] = bool(self.v_follow.get())
        if self.cfg["follow_window"] and not self.cfg["win_title"]:
            self.log("Follow window: now use 'Pick window (3s)'.")
        self.last_delta = (0, 0)
        self.save()
        self.refresh_info()
        self.show_overlay()

    def pick_window(self, remaining=3):
        if remaining > 0:
            self.win_lbl.configure(text=f"Hover the target window... {remaining}")
            self.root.after(1000, lambda: self.pick_window(remaining - 1))
            return
        pt = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        hwnd = user32.GetAncestor(user32.WindowFromPoint(pt), 2)   # GA_ROOT
        if not hwnd or hwnd == hwnd_of(self.root) or not window_title(hwnd):
            self.log("No valid window under the cursor.")
            self.refresh_info()
            return
        # re-express zone/point in the new window's frame (they stay where they are on screen)
        self.follow_hwnd = hwnd
        self.cfg["win_title"] = window_title(hwnd)
        self.cfg["win_anchor"] = list(window_origin(hwnd))
        self.last_delta = (0, 0)
        self.v_follow.set(True)
        self.cfg["follow_window"] = True
        self.log(f"Following window: {self.cfg['win_title']!r}")
        self.save()
        self.refresh_info()

    # ---------------------------------------------------------------- overlay
    def search_on(self):
        return bool(cv2 and self.cfg["search_mode"] and self.cfg["search_region"])

    def eff_search(self):
        sr = self.cfg["search_region"]
        if not sr:
            return None
        dx, dy = self.delta()
        return [sr[0] + dx, sr[1] + dy, sr[2] + dx, sr[3] + dy]

    def overlay_rect(self):
        if self.search_on():
            return self.match_rect or self.eff_search()
        return self.eff_region()

    def toggle_search(self):
        if self.v_search.get() and not cv2:
            self.v_search.set(False)
            self.log("OpenCV missing: pip install opencv-python")
        self.cfg["search_mode"] = bool(self.v_search.get())
        if self.cfg["search_mode"] and not self.cfg["search_region"]:
            self.log("Search mode: now use '5. Select search area'.")
        self.match_rect = None
        self.stable = None
        self.save()
        self.show_overlay()

    def show_overlay(self, color="#00c853"):
        reg = self.overlay_rect()
        self.ov_last = reg
        if not reg or not self.v_show.get():
            self.overlay.withdraw()
            return
        l, t, rgt, b = reg
        self.overlay.configure(bg=color)
        self.overlay.geometry(f"{rgt - l}x{b - t}+{l}+{t}")
        self.overlay.deiconify()
        self.overlay.attributes("-topmost", True)
        make_clickthrough(self.overlay)

    def flash(self):
        if self.v_show.get() and self.overlay_rect():
            self.overlay.configure(bg="#ff1744")
            self.root.after(300, lambda: self.overlay.configure(bg="#00c853"))

    # ---------------------------------------------------------------- setup
    def select_region(self, kind="region"):
        self.overlay.withdraw()
        vx, vy, vw, vh = virtual_screen()
        sel = tk.Toplevel(self.root)
        sel.overrideredirect(True)
        sel.attributes("-topmost", True)
        sel.attributes("-alpha", 0.25)
        sel.geometry(f"{vw}x{vh}+{vx}+{vy}")
        cv = tk.Canvas(sel, bg="black", highlightthickness=0, cursor="crosshair")
        cv.pack(fill="both", expand=True)
        state = {"start": None, "rect": None}

        def press(e):
            state["start"] = (e.x_root, e.y_root)
            state["rect"] = cv.create_rectangle(e.x, e.y, e.x, e.y, outline="#00ff00", width=3, fill="#00ff00")

        def drag(e):
            if state["start"]:
                sx, sy = state["start"]
                cv.coords(state["rect"], sx - vx, sy - vy, e.x, e.y)

        def release(e):
            if not state["start"]:
                return
            sx, sy = state["start"]
            l, rgt = sorted((sx, e.x_root))
            t, b = sorted((sy, e.y_root))
            sel.destroy()
            if rgt - l < 4 or b - t < 4:
                self.log("Zone too small, cancelled.")
            elif kind == "search":
                dx, dy = self.delta()
                self.cfg["search_region"] = [l - dx, t - dy, rgt - dx, b - dy]
                self.match_rect = None
                self.log(f"Search area set: {self.cfg['search_region']}")
                self.save()
            else:
                dx, dy = self.delta()
                self.cfg["region"] = [l - dx, t - dy, rgt - dx, b - dy]
                self.refs = {"X": None, "Y": None}
                for k in ("X", "Y"):
                    self.ref_labels[k].configure(image="", text="(not captured)")
                self.stable = None
                self.log(f"Zone set: {self.cfg['region']} (states reset, capture them again)")
                self.save()
            self.refresh_info()
            self.show_overlay()

        def cancel(_e=None):
            sel.destroy()
            self.show_overlay()

        cv.bind("<ButtonPress-1>", press)
        cv.bind("<B1-Motion>", drag)
        cv.bind("<ButtonRelease-1>", release)
        sel.bind("<Escape>", cancel)
        sel.focus_force()

    def grab(self):
        return ImageGrab.grab(bbox=tuple(self.eff_region()), all_screens=True).convert("RGB")

    def capture_ref(self, key):
        if not self.cfg["region"]:
            self.log("Select a zone first.")
            return
        self.set_ref(key, self.grab(), save=True)
        self.log(f"State {key} captured.")

    def set_ref(self, key, img, save):
        self.refs[key] = signature(img)
        self.full[key] = np.ascontiguousarray(np.asarray(img.convert("RGB")))
        thumb = img.copy()
        thumb.thumbnail((160, 90))
        self.thumbs[key] = ImageTk.PhotoImage(thumb)
        self.ref_labels[key].configure(image=self.thumbs[key], text="")
        if save:
            img.save(os.path.join(BASE, f"state_{key}.png"))

    def pick_point(self, remaining=3):
        if remaining > 0:
            self.info.configure(text=f"Move the mouse to the point to click... {remaining}")
            self.root.after(1000, lambda: self.pick_point(remaining - 1))
            return
        pt = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        dx, dy = self.delta()
        self.cfg["click_point"] = [pt.x - dx, pt.y - dy]
        self.log(f"Click point: {self.cfg['click_point']}")
        self.save()
        self.refresh_info()

    # ---------------------------------------------------------------- loop
    def toggle_run(self):
        if not self.running and not (self.cfg["region"] and self.refs["X"] and self.refs["Y"]):
            self.log("Zone, state X and state Y are required before starting.")
            return
        self.running = not self.running
        self.stable, self.candidate, self.cand_count = None, None, 0
        self.run_btn.configure(text="■ Stop (F8)" if self.running else "▶ Start (F8)")
        self.log("Monitoring STARTED." if self.running else "Monitoring stopped.")
        self.save()

    def read_settings(self):
        try:
            self.cfg["threshold"] = float(self.v_thr.get())
            self.cfg["interval_ms"] = max(50, int(self.v_int.get()))
            self.cfg["cooldown_s"] = float(self.v_cool.get())
        except (tk.TclError, ValueError):
            pass
        self.cfg["action"] = self.v_act.get()
        self.cfg["restore_cursor"] = bool(self.v_restore.get())

    def classify(self, sig):
        dists = {k: distance(sig, ref) for k, ref in self.refs.items() if ref is not None}
        best = min(dists, key=dists.get) if dists else None
        if best is not None and dists[best] > self.cfg["threshold"]:
            best = None
        return best, dists

    def match(self):
        """Find each captured figure inside the search area. Distance = RMS pixel difference (0-255)."""
        sr = self.eff_search()
        img = np.ascontiguousarray(np.asarray(
            ImageGrab.grab(bbox=tuple(sr), all_screens=True).convert("RGB")))
        dists, self.found = {}, {}
        for k, tpl in self.full.items():
            if img.shape[0] < tpl.shape[0] or img.shape[1] < tpl.shape[1]:
                continue
            res = cv2.matchTemplate(img, tpl, cv2.TM_SQDIFF)
            mn, _, loc, _ = cv2.minMaxLoc(res)
            dists[k] = (max(mn, 0.0) / tpl.size) ** 0.5
            self.found[k] = (sr[0] + loc[0], sr[1] + loc[1])
        best = min(dists, key=dists.get) if dists else None
        if best is not None and dists[best] > self.cfg["threshold"]:
            best = None
        if best:
            h, w = self.full[best].shape[:2]
            x, y = self.found[best]
            self.match_rect = [x, y, x + w, y + h]
        else:
            self.match_rect = None
        return best, dists

    def tick(self):
        try:
            self.read_settings()
            f8 = bool(user32.GetAsyncKeyState(VK_F8) & 0x8000)
            if f8 and not self.f8_was_down:
                self.toggle_run()
            self.f8_was_down = f8

            if self.cfg["follow_window"]:
                self.delta()
            if self.search_on() and self.full:
                state, dists = self.match()
            elif self.cfg["region"] and (self.refs["X"] or self.refs["Y"]):
                state, dists = self.classify(signature(self.grab()))
            else:
                state, dists = None, None
            if self.overlay_rect() != self.ov_last:
                self.show_overlay()
            if dists is not None:
                self.state_lbl.configure(text=f"State: {state or '?'}")
                self.dist_lbl.configure(text="   ".join(f"dist {k}: {v:.1f}" for k, v in dists.items())
                                        + f"   (threshold {self.cfg['threshold']:g})")
                if self.running:
                    self.handle(state)
        except Exception as e:
            self.log(f"Error: {e}")
        self.root.after(self.cfg["interval_ms"], self.tick)

    def handle(self, state):
        if state is None:          # zone not recognized: the confirmed state doesn't change
            self.candidate, self.cand_count = None, 0
            return
        if state == self.candidate:
            self.cand_count += 1
        else:
            self.candidate, self.cand_count = state, 1
        if self.cand_count < self.cfg["stable_frames"] or state == self.stable:
            return
        old, self.stable = self.stable, state
        self.log(f"State {old or '-'} -> {state}")
        if old == "X" and state == "Y":
            if time.time() - self.last_action >= self.cfg["cooldown_s"]:
                self.do_action()
            else:
                self.log("Transition ignored (cooldown).")

    def do_action(self):
        self.last_action = time.time()
        x, y = self.eff_point()
        self.flash()
        mouse_click(x, y, self.cfg["action"], self.cfg["restore_cursor"])
        self.log(f"ACTION: {self.cfg['action']} at ({x}, {y})")

    # ---------------------------------------------------------------- misc
    def save(self):
        with open(CFG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.cfg, f, indent=2)

    def quit(self):
        self.read_settings()
        self.save()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
