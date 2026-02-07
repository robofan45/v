# ResumeFlow

**A lightweight desktop app that helps you stay focused by tracking context switches and helping you resume work faster.**

When you return to a window after being away, ResumeFlow shows a small popup reminding you what you were last doing and lets you jot down a quick micro-task before diving back in.

Everything runs locally. No cloud, no telemetry, no accounts. Your data never leaves your machine.

---

## Features

- **Window Monitoring** -- Detects active window changes on Windows, macOS, and Linux
- **Resume Popup** -- Non-intrusive floating widget with fade-in animation appears when you return to a window after being away
- **Micro-task Capture** -- One-line text field to write your next action, saved as context for next time
- **Focus Score** -- Real-time 0-100 score displayed in system tray (green/yellow/red colour coding)
- **Weekly Reports** -- Visual dashboard with stat cards, progress bar, and colour-coded daily breakdown table
- **SQLite Logging** -- All switches logged locally at `~/.resumeflow/resumeflow.db`
- **Quiet Hours** -- Suppress popups during configurable time windows (supports midnight wrapping)
- **Dark Theme** -- Polished Catppuccin Mocha dark theme across all UI components
- **Configurable** -- Away threshold, popup position, opacity, auto-dismiss, poll interval

---

## Quick Start

### Option 1: One-Command Install (Recommended)

**macOS / Linux:**

```bash
git clone https://github.com/robofan45/v.git
cd v
chmod +x install.sh
./install.sh
```

Then run:

```bash
.venv/bin/resumeflow
```

**Windows:**

```powershell
git clone https://github.com/robofan45/v.git
cd v
install.bat
```

Then run:

```powershell
.venv\Scripts\resumeflow.exe
```

### Option 2: Make (macOS / Linux)

```bash
git clone https://github.com/robofan45/v.git
cd v
make run
```

That's it. `make run` creates a virtual environment, installs everything, and starts the app.

Other make targets:

| Command      | What it does                          |
|-------------|---------------------------------------|
| `make install` | Create venv and install dependencies |
| `make run`     | Install + start ResumeFlow           |
| `make test`    | Run the full test suite              |
| `make clean`   | Remove venv and build artifacts      |

### Option 3: Manual Install with pip

```bash
# 1. Clone the repo
git clone https://github.com/robofan45/v.git
cd v

# 2. Create a virtual environment
python3 -m venv .venv

# 3. Activate it
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate.bat     # Windows

# 4. Install ResumeFlow
pip install -e .

# 5. Run it
resumeflow
```

### Option 4: Run Without Installing

If you just want to try it quickly:

```bash
pip install PyQt6 psutil
python run.py
```

---

## Requirements

- **Python 3.11** or newer
- **PyQt6** (installed automatically)
- **psutil** (installed automatically)

### Platform-specific dependencies

| Platform | Extra dependency | How to install |
|----------|-----------------|----------------|
| **Windows** | pygetwindow | Installed automatically by pip |
| **macOS** | pyobjc-framework-Cocoa | Installed automatically by pip |
| **Linux** | xdotool | `sudo apt install xdotool` (Debian/Ubuntu) |
|           |         | `sudo dnf install xdotool` (Fedora) |
|           |         | `sudo pacman -S xdotool` (Arch) |

---

## How to Use

ResumeFlow starts minimised to the **system tray**. Look for the circular icon with a number in it.

### System Tray

- The **number** on the icon shows your switches per hour
- The **ring colour** shows your focus score:
  - Green = great focus (score >= 70)
  - Yellow = moderate switching (score 40-69)
  - Red = high switching (score < 40)
- **Right-click** the tray icon to access the menu:
  - **Weekly Report** -- View your stats dashboard
  - **Settings** -- Configure thresholds and popup behaviour
  - **Quit** -- Clean shutdown

### Resume Popup

When you switch back to a window after being away longer than the threshold (default 30 seconds):

1. A floating popup fades in near your cursor
2. It shows how long you were away and what you were last working on
3. Type your next micro-task and press **Enter** or click **Go**
4. The popup closes and your task is saved as context for next time

### Weekly Report

The report dialog shows:

- Three stat cards: **Focus Score**, **Switches Today**, **Last Hour**
- A colour-coded progress bar for your score
- A table with daily breakdown: date, switch count, average away time, max away time
- Switch counts are colour-coded (green < 15, yellow 15-30, red > 30)

---

## Settings

| Setting | Default | Range | Description |
|---------|---------|-------|-------------|
| Away threshold | 30s | 30-300s | Time away before showing resume popup |
| Poll interval | 1.0s | 0.5-5.0s | How often to check the active window |
| Popup position | cursor | cursor / top-right / bottom-right | Where the popup appears |
| Popup opacity | 0.95 | 0.5-1.0 | Popup transparency |
| Auto-dismiss | 0 (manual) | 0-60s | Auto-hide popup after N seconds |
| Quiet hours | disabled | HH:MM - HH:MM | Suppress popups during this window |

Settings are saved to the SQLite database and persist across restarts.

---

## Project Structure

```
resumeflow/
    __init__.py          # Package metadata
    __main__.py          # python -m resumeflow entry point
    app.py               # Main controller, signal handlers, shutdown
    theme.py             # Catppuccin Mocha theme and global stylesheet
    context_tracker.py   # Switch detection, away timing, LRU history
    database.py          # SQLite layer (WAL mode, error-safe)
    window_monitor.py    # Cross-platform active window detection
    popup.py             # Floating resume popup with drop shadow + animation
    tray.py              # System tray icon with score-coloured ring
    settings_manager.py  # Persistent settings via SQLite
    settings_dialog.py   # Settings UI with themed form controls
    report_dialog.py     # Weekly report with stat cards + styled table
tests/                   # 78 tests across all modules
run.py                   # Quick launcher (no install needed)
install.sh               # One-command installer (macOS/Linux)
install.bat              # One-command installer (Windows)
Makefile                 # make install / run / test / clean
pyproject.toml           # Package configuration
```

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Run tests headless (CI / no display)
QT_QPA_PLATFORM=offscreen pytest -v
```

78 tests covering: database CRUD, context tracking logic, window monitor dispatch, popup widget behaviour, tray icon rendering, settings persistence, dialog construction, and report generation.

---

## Troubleshooting

**"No module named PyQt6"**
Make sure you're running inside the virtual environment. Run `source .venv/bin/activate` (macOS/Linux) or `.venv\Scripts\activate.bat` (Windows) first.

**"Could not load the Qt platform plugin"**
On Linux, you may need: `sudo apt install libegl1 libgl1`

**"xdotool: command not found" (Linux)**
Install xdotool: `sudo apt install xdotool`

**The tray icon doesn't appear**
Some Linux desktop environments need a system tray extension (e.g., GNOME needs the AppIndicator extension).

**"Python 3.11+ required"**
Check your version with `python3 --version`. If you need to upgrade, visit [python.org](https://www.python.org/downloads/).

---

## Design Decisions

- **Single-threaded** -- All work on the Qt main thread via `QTimer`. No locks, no race conditions.
- **Bounded memory** -- Window history is an LRU `OrderedDict` capped at 500 entries.
- **Error-safe DB** -- Every database method catches `sqlite3.Error` and returns safe defaults.
- **Graceful shutdown** -- SIGINT and SIGTERM handled; all resources cleaned up on exit.
- **No network** -- Zero outbound connections. Data stays on disk at `~/.resumeflow/`.
- **Catppuccin Mocha** -- Consistent dark theme across all UI components.

## License

MIT
