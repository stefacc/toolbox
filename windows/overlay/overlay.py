"""
Overlay Trigger - overlay verde su una zona dello schermo che osserva lo stato
della zona e, quando passa dallo stato X allo stato Y, esegue un'azione (click).

Uso:
  1. "Seleziona zona"      -> trascina un rettangolo sullo schermo (Esc annulla)
  2. "Cattura stato X"     -> fotografa la zona com'e' adesso (stato di partenza)
  3. "Cattura stato Y"     -> fotografa la zona nello stato che fa scattare l'azione
  4. "Punto click"         -> entro 3 secondi porta il mouse dove vuoi cliccare
                              (se non impostato: centro della zona)
  5. "Avvia" (o F8)        -> monitoraggio attivo; F8 in qualsiasi momento ferma tutto

L'overlay e' "click-through" (i click lo attraversano) ed e' escluso dalle catture
dello schermo, quindi il verde non falsa il confronto delle immagini.
"""

import ctypes
import json
import os
import time
import tkinter as tk
from ctypes import wintypes
from tkinter import ttk

from PIL import Image, ImageChops, ImageGrab, ImageStat, ImageTk

# Coordinate in pixel fisici anche con scaling di Windows al 125%/150%
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
    "click sinistro": (0x0002, 0x0004, 1),
    "doppio click": (0x0002, 0x0004, 2),
    "click destro": (0x0008, 0x0010, 1),
}

BASE = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(BASE, "config.json")
DEFAULTS = {
    "region": None,          # [left, top, right, bottom]
    "click_point": None,     # [x, y]
    "threshold": 12.0,       # distanza massima (0-255) per riconoscere uno stato
    "interval_ms": 200,
    "stable_frames": 2,      # quante letture consecutive servono per confermare uno stato
    "cooldown_s": 1.0,
    "action": "click sinistro",
    "restore_cursor": True,
    "overlay_alpha": 0.30,
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


class App:
    def __init__(self):
        self.cfg = dict(DEFAULTS)
        if os.path.exists(CFG_PATH):
            try:
                with open(CFG_PATH, encoding="utf-8") as f:
                    self.cfg.update(json.load(f))
            except Exception:
                pass

        self.refs = {"X": None, "Y": None}      # firme 32x32
        self.thumbs = {}
        self.running = False
        self.stable = None
        self.candidate = None
        self.cand_count = 0
        self.last_action = 0.0
        self.f8_was_down = False

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
            path = os.path.join(BASE, f"stato_{key}.png")
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
        ttk.Button(top, text="1. Seleziona zona", command=self.select_region).pack(side="left", padx=2)
        ttk.Button(top, text="2. Cattura stato X", command=lambda: self.capture_ref("X")).pack(side="left", padx=2)
        ttk.Button(top, text="3. Cattura stato Y", command=lambda: self.capture_ref("Y")).pack(side="left", padx=2)
        ttk.Button(top, text="4. Punto click (3s)", command=self.pick_point).pack(side="left", padx=2)

        self.info = ttk.Label(r, text="")
        self.info.pack(anchor="w", **pad)

        refs = ttk.Frame(r)
        refs.pack(fill="x", **pad)
        self.ref_labels = {}
        for key in ("X", "Y"):
            box = ttk.LabelFrame(refs, text=f"Stato {key}")
            box.pack(side="left", padx=4)
            lbl = ttk.Label(box, text="(non catturato)", width=22, anchor="center")
            lbl.pack(padx=4, pady=4)
            self.ref_labels[key] = lbl

        live = ttk.Frame(r)
        live.pack(fill="x", **pad)
        self.state_lbl = ttk.Label(live, text="Stato: -", font=("Segoe UI", 12, "bold"))
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
        ttk.Label(opts, text="Soglia").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(opts, from_=1, to=100, increment=1, width=6, textvariable=self.v_thr).grid(row=0, column=1)
        ttk.Label(opts, text="Intervallo ms").grid(row=0, column=2, sticky="w", padx=(10, 0))
        ttk.Spinbox(opts, from_=50, to=5000, increment=50, width=6, textvariable=self.v_int).grid(row=0, column=3)
        ttk.Label(opts, text="Cooldown s").grid(row=0, column=4, sticky="w", padx=(10, 0))
        ttk.Spinbox(opts, from_=0, to=60, increment=0.5, width=6, textvariable=self.v_cool).grid(row=0, column=5)
        ttk.Label(opts, text="Azione").grid(row=1, column=0, sticky="w")
        ttk.Combobox(opts, values=list(MOUSE), textvariable=self.v_act, state="readonly",
                     width=14).grid(row=1, column=1, columnspan=2, sticky="w")
        ttk.Checkbutton(opts, text="Riporta il mouse dov'era", variable=self.v_restore).grid(
            row=1, column=3, columnspan=2, sticky="w", padx=(10, 0))
        ttk.Checkbutton(opts, text="Mostra overlay", variable=self.v_show,
                        command=self.show_overlay).grid(row=1, column=5, sticky="w")

        self.run_btn = ttk.Button(r, text="▶ Avvia (F8)", command=self.toggle_run)
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
        txt = f"Zona: {reg if reg else 'non impostata'}    Punto click: "
        txt += f"{pt}" if pt else ("centro zona" if reg else "-")
        self.info.configure(text=txt)

    # ---------------------------------------------------------------- overlay
    def show_overlay(self, color="#00c853"):
        reg = self.cfg["region"]
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
        if self.v_show.get() and self.cfg["region"]:
            self.overlay.configure(bg="#ff1744")
            self.root.after(300, lambda: self.overlay.configure(bg="#00c853"))

    # ---------------------------------------------------------------- setup
    def select_region(self):
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
                self.log("Zona troppo piccola, annullato.")
            else:
                self.cfg["region"] = [l, t, rgt, b]
                self.refs = {"X": None, "Y": None}
                for k in ("X", "Y"):
                    self.ref_labels[k].configure(image="", text="(non catturato)")
                self.stable = None
                self.log(f"Zona impostata: {self.cfg['region']} (stati azzerati, ricatturali)")
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
        return ImageGrab.grab(bbox=tuple(self.cfg["region"]), all_screens=True).convert("RGB")

    def capture_ref(self, key):
        if not self.cfg["region"]:
            self.log("Prima seleziona una zona.")
            return
        self.set_ref(key, self.grab(), save=True)
        self.log(f"Stato {key} catturato.")

    def set_ref(self, key, img, save):
        self.refs[key] = signature(img)
        thumb = img.copy()
        thumb.thumbnail((160, 90))
        self.thumbs[key] = ImageTk.PhotoImage(thumb)
        self.ref_labels[key].configure(image=self.thumbs[key], text="")
        if save:
            img.save(os.path.join(BASE, f"stato_{key}.png"))

    def pick_point(self, remaining=3):
        if remaining > 0:
            self.info.configure(text=f"Porta il mouse sul punto da cliccare... {remaining}")
            self.root.after(1000, lambda: self.pick_point(remaining - 1))
            return
        pt = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        self.cfg["click_point"] = [pt.x, pt.y]
        self.log(f"Punto click: {self.cfg['click_point']}")
        self.save()
        self.refresh_info()

    # ---------------------------------------------------------------- loop
    def toggle_run(self):
        if not self.running and not (self.cfg["region"] and self.refs["X"] and self.refs["Y"]):
            self.log("Servono zona, stato X e stato Y prima di avviare.")
            return
        self.running = not self.running
        self.stable, self.candidate, self.cand_count = None, None, 0
        self.run_btn.configure(text="■ Ferma (F8)" if self.running else "▶ Avvia (F8)")
        self.log("Monitoraggio AVVIATO." if self.running else "Monitoraggio fermato.")
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

    def tick(self):
        try:
            self.read_settings()
            f8 = bool(user32.GetAsyncKeyState(VK_F8) & 0x8000)
            if f8 and not self.f8_was_down:
                self.toggle_run()
            self.f8_was_down = f8

            if self.cfg["region"] and (self.refs["X"] or self.refs["Y"]):
                state, dists = self.classify(signature(self.grab()))
                self.state_lbl.configure(text=f"Stato: {state or '?'}")
                self.dist_lbl.configure(text="   ".join(f"dist {k}: {v:.1f}" for k, v in dists.items())
                                        + f"   (soglia {self.cfg['threshold']:g})")
                if self.running:
                    self.handle(state)
        except Exception as e:
            self.log(f"Errore: {e}")
        self.root.after(self.cfg["interval_ms"], self.tick)

    def handle(self, state):
        if state is None:          # zona non riconosciuta: non cambia lo stato confermato
            self.candidate, self.cand_count = None, 0
            return
        if state == self.candidate:
            self.cand_count += 1
        else:
            self.candidate, self.cand_count = state, 1
        if self.cand_count < self.cfg["stable_frames"] or state == self.stable:
            return
        old, self.stable = self.stable, state
        self.log(f"Stato {old or '-'} -> {state}")
        if old == "X" and state == "Y":
            if time.time() - self.last_action >= self.cfg["cooldown_s"]:
                self.do_action()
            else:
                self.log("Transizione ignorata (cooldown).")

    def do_action(self):
        self.last_action = time.time()
        if self.cfg["click_point"]:
            x, y = self.cfg["click_point"]
        else:
            l, t, r, b = self.cfg["region"]
            x, y = (l + r) // 2, (t + b) // 2
        self.flash()
        mouse_click(x, y, self.cfg["action"], self.cfg["restore_cursor"])
        self.log(f"AZIONE: {self.cfg['action']} su ({x}, {y})")

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
