# overlay - visual trigger on a screen zone

Puts a semi-transparent green overlay on a zone of the screen, watches it and,
when the zone changes from **state X** to **state Y**, performs an action (click).

Typical use: click a button automatically as soon as it appears or changes look
(e.g. a "Next" / "Continue" button that becomes enabled).

Windows only. Python 3.10+.

```
pip install -r requirements.txt
python overlay.py
```

`opencv-python` is optional: it is only needed for **search mode** (see below).

## Usage

1. **Select zone** - drag a rectangle on the screen (Esc cancels).
2. **Capture state X** - saves how the zone looks now (starting state).
3. **Capture state Y** - bring the zone to the state that should trigger the action and capture.
4. **Click point (3s)** - within 3 seconds move the mouse where it should click.
   If not set, it clicks the center of the zone.
5. **Start** or **F8** - starts monitoring. F8 stops it from any window.

### Optional: search mode

Use it when the figure (e.g. a button) does not always appear in exactly the same place.

1. Capture state X and Y as above, on a small zone around the figure.
2. Tick **Search figure in larger area** and use **5. Select search area** to draw
   a bigger rectangle where the figure can appear.

The figure is then located inside the search area at every reading (OpenCV template
matching) and the click happens relative to where it was found, keeping the same
offset that the click point had inside the original zone.

### Optional: follow window

Use it when the target window may be moved.

1. Click **Pick window (3s)** and hover the target window within 3 seconds.
2. **Follow window** gets ticked: zone, search area and click point now move
   together with that window.

The window is found again by its title if it is closed and reopened. If it is
minimized, the last known position is kept.

## How it works

- The overlay is **click-through**: clicks go through it.
- The overlay is **excluded from screen captures** (`SetWindowDisplayAffinity`),
  so the green tint doesn't skew the comparison.
- Each reading is scaled down to 32x32 and compared with the reference images
  (in search mode: RMS difference at the best match position). The "distance"
  (0-255) is shown live. Below the **threshold** the state is recognized,
  otherwise it is `?` and nothing happens.
- A state must stay the same for 2 consecutive readings before it counts; after an
  action there is a **cooldown** (default 1 s).
- Actions: left click, double click, right click; option to move the mouse back
  where it was.
- DPI aware: coordinates are physical pixels, also with Windows scaling at 125%/150%
  and on multi-monitor setups.

## Saved files

Zone, click point, settings and reference images are saved next to the script
(`config.json`, `state_X.png`, `state_Y.png`) and reloaded at startup.
They depend on your screen layout, so they are git-ignored.
