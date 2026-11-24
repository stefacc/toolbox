"""
Quiz Snap - a floating bar with one button: takes a screenshot and sends it to
Claude together with your instructions; the answer streams into a window.

  📸 / F9   -> capture and analyze
  Zone      -> pick a fixed area to capture (right-click on Zone = back to full screen)
  ⚙         -> edit the instructions sent to Claude

Without a fixed zone it captures the monitor the mouse is on.
The program's own windows are excluded from the screenshot, no need to move them.

Engine:
  - ANTHROPIC_API_KEY NOT set -> uses the Claude Code CLI (`claude -p`),
    i.e. your already logged-in subscription: no key needed;
  - ANTHROPIC_API_KEY set     -> uses the API (streaming answer, pay per use).
"""

import base64
import ctypes
import io
import json
import os
import queue
import shutil
import subprocess
import threading
import time
import tkinter as tk
from ctypes import wintypes
from tkinter import ttk

import anthropic
from PIL import ImageGrab

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()

user32 = ctypes.windll.user32
WDA_EXCLUDEFROMCAPTURE = 0x11
VK_F9 = 0x78

MODEL = "claude-opus-5-5"
BASE = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(BASE, "quiz_snap_config.json")
SHOTS_DIR = os.path.join(BASE, "screenshots")

DEFAULT_PROMPT = ("Look at the screenshot and answer concisely.\n"
                  "If it contains one or more questions, answer each one in ONE line; add a short "
                  "reason (max 1 line) only when the answer is not obvious. If something is ambiguous "
                  "or wrong, point it out in one line.\n"
                  "No introductions, no summary of the content.")
DEFAULTS = {"region": None, "prompt": DEFAULT_PROMPT, "effort": "medium", "save_shots": True}


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]


def monitor_under_cursor():
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    user32.MonitorFromPoint.restype = wintypes.HANDLE
    hmon = user32.MonitorFromPoint(pt, 2)  # MONITOR_DEFAULTTONEAREST
    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(MONITORINFO)
    user32.GetMonitorInfoW(hmon, ctypes.byref(mi))
    r = mi.rcMonitor
    return (r.left, r.top, r.right, r.bottom)


def exclude_from_capture(win):
    win.update_idletasks()
    hwnd = user32.GetParent(win.winfo_id()) or win.winfo_id()
    user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)


def encode_image(img):
    """PNG (best for text); downscale to max 2000px and switch to JPEG if too heavy."""
    img = img.convert("RGB")
    if max(img.size) > 2000:
        img.thumbnail((2000, 2000))
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    media = "image/png"
    if buf.tell() > 3_500_000:
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=90)
        media = "image/jpeg"
    return base64.standard_b64encode(buf.getvalue()).decode(), media


class App:
    def __init__(self):
        self.cfg = dict(DEFAULTS)
        if os.path.exists(CFG_PATH):
            try:
                with open(CFG_PATH, encoding="utf-8") as f:
                    self.cfg.update(json.load(f))
            except Exception:
                pass
        self.q = queue.Queue()
        self.busy = False
        self.f9_down = False
        self.client = None
        self.warm = None
        self.use_cli = not os.environ.get("ANTHROPIC_API_KEY") and bool(shutil.which("claude"))
        if self.use_cli:
            self._spawn_warm()  # start early: the first click is already fast

        # ---- floating bar
        self.root = tk.Tk()
        self.root.title("Quiz Snap")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.geometry("+40+40")
        bar = tk.Frame(self.root, bg="#1e1e1e", padx=4, pady=4)
        bar.pack()
        grip = tk.Label(bar, text="⋮⋮", bg="#1e1e1e", fg="#888", cursor="fleur")
        grip.pack(side="left", padx=(0, 4))
        grip.bind("<ButtonPress-1>", self._drag_start)
        grip.bind("<B1-Motion>", self._drag_move)
        self.snap_btn = tk.Button(bar, text="📸 Analyze (F9)", command=self.snap, bg="#00c853",
                                  fg="white", relief="flat", font=("Segoe UI", 10, "bold"), padx=8)
        self.snap_btn.pack(side="left")
        self.zone_btn = tk.Button(bar, text="Zone", command=self.select_region, relief="flat", padx=6)
        self.zone_btn.pack(side="left", padx=(4, 0))
        self.zone_btn.bind("<Button-3>", self.clear_region)
        tk.Button(bar, text="⚙", command=self.edit_prompt, relief="flat", padx=6).pack(side="left", padx=(4, 0))
        tk.Button(bar, text="✕", command=self.quit, relief="flat", padx=6).pack(side="left", padx=(4, 0))

        # ---- answer window
        self.out = tk.Toplevel(self.root)
        self.out.title("Quiz Snap - answer")
        self.out.geometry("560x520+40+110")
        self.out.attributes("-topmost", True)
        self.out.protocol("WM_DELETE_WINDOW", self.out.withdraw)
        top = ttk.Frame(self.out)
        top.pack(fill="x", padx=6, pady=4)
        self.status = ttk.Label(top, text="Ready.")
        self.status.pack(side="left")
        ttk.Button(top, text="Copy", command=self.copy_answer).pack(side="right")
        self.text = tk.Text(self.out, wrap="word", font=("Segoe UI", 10), padx=8, pady=8)
        self.text.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self.out.withdraw()

        for w in (self.root, self.out):
            exclude_from_capture(w)
        self.update_zone_label()
        self.root.after(50, self.tick)

    # ------------------------------------------------------------- bar
    def _drag_start(self, e):
        self._dx, self._dy = e.x_root - self.root.winfo_x(), e.y_root - self.root.winfo_y()

    def _drag_move(self, e):
        self.root.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")

    def update_zone_label(self):
        self.zone_btn.configure(text="Zone ✓" if self.cfg["region"] else "Zone")

    def save(self):
        with open(CFG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.cfg, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------- zone
    def select_region(self):
        vx, vy = user32.GetSystemMetrics(76), user32.GetSystemMetrics(77)
        vw, vh = user32.GetSystemMetrics(78), user32.GetSystemMetrics(79)
        sel = tk.Toplevel(self.root)
        sel.overrideredirect(True)
        sel.attributes("-topmost", True)
        sel.attributes("-alpha", 0.25)
        sel.geometry(f"{vw}x{vh}+{vx}+{vy}")
        cv = tk.Canvas(sel, bg="black", highlightthickness=0, cursor="crosshair")
        cv.pack(fill="both", expand=True)
        st = {}

        def press(e):
            st["start"] = (e.x_root, e.y_root)
            st["rect"] = cv.create_rectangle(e.x, e.y, e.x, e.y, outline="#00ff00", width=3, fill="#00ff00")

        def drag(e):
            if "start" in st:
                cv.coords(st["rect"], st["start"][0] - vx, st["start"][1] - vy, e.x, e.y)

        def release(e):
            if "start" not in st:
                return
            (sx, sy) = st["start"]
            l, r = sorted((sx, e.x_root))
            t, b = sorted((sy, e.y_root))
            sel.destroy()
            if r - l > 10 and b - t > 10:
                self.cfg["region"] = [l, t, r, b]
                self.save()
                self.update_zone_label()

        cv.bind("<ButtonPress-1>", press)
        cv.bind("<B1-Motion>", drag)
        cv.bind("<ButtonRelease-1>", release)
        sel.bind("<Escape>", lambda _e: sel.destroy())
        sel.focus_force()

    def clear_region(self, _e=None):
        self.cfg["region"] = None
        self.save()
        self.update_zone_label()

    # ------------------------------------------------------------- instructions
    def edit_prompt(self):
        win = tk.Toplevel(self.root)
        win.title("Instructions for Claude")
        win.attributes("-topmost", True)
        txt = tk.Text(win, wrap="word", width=70, height=14, font=("Segoe UI", 10))
        txt.pack(fill="both", expand=True, padx=6, pady=6)
        txt.insert("1.0", self.cfg["prompt"])
        row = ttk.Frame(win)
        row.pack(fill="x", padx=6, pady=(0, 6))
        ttk.Label(row, text="Effort").pack(side="left")
        eff = ttk.Combobox(row, values=["low", "medium", "high", "xhigh", "max"], width=8, state="readonly")
        eff.set(self.cfg["effort"])
        eff.pack(side="left", padx=4)
        keep = tk.BooleanVar(value=self.cfg["save_shots"])
        ttk.Checkbutton(row, text="Save screenshots", variable=keep).pack(side="left", padx=8)

        def ok():
            self.cfg["prompt"] = txt.get("1.0", "end").strip() or DEFAULT_PROMPT
            self.cfg["effort"] = eff.get()
            self.cfg["save_shots"] = keep.get()
            self.save()
            win.destroy()

        ttk.Button(row, text="Restore default", command=lambda: (txt.delete("1.0", "end"),
                                                                    txt.insert("1.0", DEFAULT_PROMPT))).pack(side="right")
        ttk.Button(row, text="Save", command=ok).pack(side="right", padx=4)

    # ------------------------------------------------------------- capture + send
    def snap(self):
        if self.busy:
            return
        bbox = tuple(self.cfg["region"]) if self.cfg["region"] else monitor_under_cursor()
        img = ImageGrab.grab(bbox=bbox, all_screens=True)
        if self.cfg["save_shots"]:
            os.makedirs(SHOTS_DIR, exist_ok=True)
            img.save(os.path.join(SHOTS_DIR, time.strftime("%Y%m%d_%H%M%S.png")))
        self.busy = True
        self.snap_btn.configure(text="⏳ Analyzing...", bg="#ff9800")
        self.text.delete("1.0", "end")
        self.out.deiconify()
        if self.use_cli:
            self.status.configure(text="Sending to Claude Code (subscription)...")
            threading.Thread(target=self.ask_claude_cli, args=(img,), daemon=True).start()
        else:
            self.status.configure(text=f"Sending to {MODEL} (API)...")
            threading.Thread(target=self.ask_claude, args=(img,), daemon=True).start()

    # --- Claude Code CLI with a "warm" process ----------------------------------
    # Starting Claude Code takes ~8s: we always keep one process already started and
    # waiting on stdin, so a click only costs the answer time (~1-2s).
    # Each process serves ONE screenshot (clean context), then a new one is started.
    def _spawn_warm(self):
        os.makedirs(SHOTS_DIR, exist_ok=True)
        self.warm = subprocess.Popen(
            ["claude", "-p", "--input-format", "stream-json", "--output-format", "stream-json",
             "--verbose", "--include-partial-messages", "--tools", "", "--strict-mcp-config",
             "--model", "opus", "--effort", self.cfg["effort"], "--no-session-persistence"],
            cwd=SHOTS_DIR, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self.warm_effort = self.cfg["effort"]

    def _take_warm(self):
        p = self.warm
        if p is None or p.poll() is not None or self.warm_effort != self.cfg["effort"]:
            if p is not None and p.poll() is None:
                p.kill()
            self._spawn_warm()
            p = self.warm
        self._spawn_warm()  # get the next one ready
        return p

    def ask_claude_cli(self, img):
        t0 = time.time()
        try:
            p = self._take_warm()
            data, media = encode_image(img)
            msg = {"type": "user", "message": {"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media, "data": data}},
                {"type": "text", "text": self.cfg["prompt"]},
            ]}}
            p.stdin.write(json.dumps(msg) + "\n")
            p.stdin.close()
            result = None
            for line in p.stdout:
                try:
                    ev = json.loads(line)
                except ValueError:
                    continue
                if ev.get("type") == "stream_event":
                    e = ev.get("event", {})
                    if e.get("type") == "content_block_delta" and e["delta"].get("type") == "text_delta":
                        self.q.put(("text", e["delta"]["text"]))
                elif ev.get("type") == "result":
                    result = ev
            p.wait(timeout=30)
            if result is None or result.get("is_error"):
                err = (result or {}).get("result") or p.stderr.read().strip() or "unknown error"
                self.q.put(("error", str(err)))
            else:
                self.q.put(("done", f"Done in {time.time() - t0:.1f}s  ·  via Claude Code"))
        except Exception as e:
            self.q.put(("error", str(e)))

    def ask_claude(self, img):
        t0 = time.time()
        try:
            if self.client is None:
                self.client = anthropic.Anthropic()
            data, media = encode_image(img)
            with self.client.beta.messages.stream(
                model=MODEL,
                max_tokens=16000,
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                output_config={"effort": self.cfg["effort"]},
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": media, "data": data}},
                        {"type": "text", "text": self.cfg["prompt"]},
                    ],
                }],
            ) as stream:
                for chunk in stream.text_stream:
                    self.q.put(("text", chunk))
                msg = stream.get_final_message()
            if msg.stop_reason == "refusal":
                self.q.put(("text", "\n\n[Request refused by the model]"))
            elif msg.stop_reason == "max_tokens":
                self.q.put(("text", "\n\n[Answer truncated: token limit]"))
            self.q.put(("done", f"Done in {time.time() - t0:.1f}s  ·  "
                                f"{msg.usage.input_tokens} in / {msg.usage.output_tokens} out token"))
        except anthropic.AuthenticationError:
            self.q.put(("error", "Invalid API key. Check ANTHROPIC_API_KEY."))
        except anthropic.RateLimitError:
            self.q.put(("error", "Rate limit reached, try again shortly."))
        except anthropic.APIStatusError as e:
            self.q.put(("error", f"API error {e.status_code}: {e.message}"))
        except anthropic.APIConnectionError:
            self.q.put(("error", "Network error: check your connection."))
        except Exception as e:
            msg = str(e)
            if "api_key" in msg.lower() or "auth" in msg.lower():
                msg = ("Missing credentials. Set the ANTHROPIC_API_KEY environment variable "
                       "(console.anthropic.com -> API Keys) and restart the program.")
            self.q.put(("error", msg))

    # ------------------------------------------------------------- UI loop
    def tick(self):
        f9 = bool(user32.GetAsyncKeyState(VK_F9) & 0x8000)
        if f9 and not self.f9_down:
            self.snap()
        self.f9_down = f9
        try:
            while True:
                kind, val = self.q.get_nowait()
                if kind == "text":
                    self.text.insert("end", val)
                    self.text.see("end")
                else:
                    if kind == "error":
                        self.text.insert("end", "\n⚠ " + val)
                    self.status.configure(text=val if kind == "done" else "Error.")
                    self.busy = False
                    self.snap_btn.configure(text="📸 Analyze (F9)", bg="#00c853")
        except queue.Empty:
            pass
        self.root.after(50, self.tick)

    def copy_answer(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.text.get("1.0", "end").strip())

    def quit(self):
        self.save()
        if self.warm is not None and self.warm.poll() is None:
            self.warm.kill()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
