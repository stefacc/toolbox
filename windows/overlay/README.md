# overlay - visual trigger on a screen zone

Puts a semi-transparent green overlay on a zone of the screen, watches it and,
when the zone changes from **state X** to **state Y**, performs an action (click).

Windows only. Single dependency: Pillow.

```
pip install -r requirements.txt
python overlay.py
```

## Usage

1. **Select zone** - drag a rectangle on the screen (Esc cancels).
2. **Capture state X** - saves how the zone looks now (starting state).
3. **Capture state Y** - bring the zone to the state that should trigger the action and capture.
4. **Click point (3s)** - within 3 seconds move the mouse where it should click.
   If not set, it clicks the center of the zone.
5. **Start** or **F8** - starts monitoring. F8 stops it from any window.

## How it works

- The overlay is **click-through**: clicks go through it.
- The overlay is **excluded from screen captures** (`SetWindowDisplayAffinity`),
  so the green tint doesn't skew the comparison.
- Each reading is scaled down to 32x32 and compared with the reference images:
  the "distance" (0-255) is shown live. Below the **threshold** the state is
  recognized, otherwise it is `?` and nothing happens.
- A state must stay the same for 2 consecutive readings before it counts; after an
  action there is a **cooldown** (default 1 s).
- Actions: left click, double click, right click; option to move the mouse back
  where it was.

Zone, click point, settings and reference images are saved next to the script
(`config.json`, `state_X.png`, `state_Y.png`) and reloaded at startup.
