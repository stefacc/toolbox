# quiz_snap - screenshot to Claude in one click

A small floating bar with one button: it takes a screenshot (full monitor or a fixed
zone), sends it to Claude together with your instructions, and streams the answer
into a small always-on-top window.

Useful whenever you want a quick opinion on what is on screen: a question, an error
dialog, a chart, a piece of text in a language you don't read, a form to check...
What Claude does with the image is entirely up to the instructions (⚙).

Windows only. Python 3.10+.

```
pip install -r requirements.txt
python quiz_snap.py
```

## Engine: subscription or API key

The engine is picked at startup:

| `ANTHROPIC_API_KEY` | Engine | Cost |
|---|---|---|
| not set (and `claude` is on PATH) | [Claude Code](https://claude.com/claude-code) CLI, `claude -p` | your logged-in Claude subscription |
| set | Anthropic API (`claude-opus-5-5`, streaming) | pay per use |

To use the API, set the key before starting the program, e.g. in PowerShell:

```
$env:ANTHROPIC_API_KEY = "sk-ant-..."
python quiz_snap.py
```

No key or account data is ever written by the program: it only reads the
environment variable (API) or relies on the existing Claude Code login (CLI).

With the CLI engine a Claude Code process is started in advance and kept waiting,
so a click costs only the answer time (~1-2 s) instead of the CLI startup (~8 s).
Every screenshot uses a fresh process (clean context, no session saved, no tools).

## Usage

- **📸 Analyze** or **F9** (global hotkey) - capture and send.
  Without a fixed zone it captures the monitor where the mouse is.
- **Zone** - drag a rectangle to always capture that area (Esc cancels).
  **Right-click on Zone** goes back to full monitor. `Zone ✓` means a zone is set.
- **⚙** - edit the instructions sent with every screenshot, the **effort**
  (`low` ... `max`: higher = slower but more careful) and whether to keep the screenshots.
  **Restore default** puts back the built-in instructions.
- **⋮⋮** - drag handle to move the bar. **✕** quits.
- The answer window has a **Copy** button; closing it just hides it until the next capture.

The program's own windows are excluded from screen captures
(`SetWindowDisplayAffinity`), so they never end up in the screenshot.

## Saved files

Next to the script (both git-ignored):

- `quiz_snap_config.json` - zone, instructions, effort, "save screenshots" option;
- `screenshots/` - one PNG per capture (`YYYYMMDD_HHMMSS.png`) when "Save screenshots" is on
  (default). Turn it off in ⚙ if you capture sensitive content.

Keep in mind that every screenshot is sent to Anthropic: don't capture what you
wouldn't paste in a chat.
