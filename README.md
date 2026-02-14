# ResumeFlow

![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776ab?logo=python&logoColor=white)
![License MIT](https://img.shields.io/badge/License-MIT-a6e3a1)
![Tests 150 passing](https://img.shields.io/badge/Tests-150_passing-a6e3a1)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-89b4fa)

**A lightweight desktop app that helps you stay focused by tracking context switches and helping you resume work faster.**

When you return to a window after being away, ResumeFlow shows a small popup reminding you what you were last doing and lets you jot down a quick micro-task before diving back in.

Everything runs locally. No cloud, no telemetry, no accounts. Your data never leaves your machine.

---

## Quick Start

**macOS / Linux:**

```bash
git clone https://github.com/robofan45/v.git && cd v && pip install -e . && resumeflow
```

**Windows:**

```cmd
git clone https://github.com/robofan45/v.git %USERPROFILE%\ResumeFlow && cd %USERPROFILE%\ResumeFlow && install.bat
```

Then run: `.venv\Scripts\resumeflow.exe`

---

## How It Works

```
                    +-----------------+
                    |  Poll active    |
                    |  window (1s)    |
                    +--------+--------+
                             |
                     Window changed?
                        /        \
                      No          Yes
                      |            |
                    (wait)    Log switch to DB
                               |
                        Away > threshold?
                           /        \
                         No          Yes
                         |            |
                       (done)   +------------------+
                                | Show popup:      |
                                |  - Away time     |
                                |  - Last context  |
                                |  - Micro-task    |
                                +------------------+
                                         |
                                 Save task as context
                                 for next time
```

ResumeFlow watches which window you're using. When you return to a window after being away longer than the threshold (default: 30 seconds), it shows a small popup to help you pick up where you left off.

---

## Features

- **Window Monitoring** -- Detects active window changes on Windows, macOS, and Linux
- **Dashboard** -- Live dashboard window with focus score, switch count, per-hour rate, progress bar, and recent context switches table (auto-refreshes every 5 seconds)
- **Resume Popup** -- Non-intrusive floating widget with fade-in animation appears when you return to a window after being away
- **Micro-task Capture** -- One-line text field to write your next action, saved as context for next time
- **Focus Score** -- Real-time 0-100 score displayed in system tray with colour-coded ring (green/yellow/red)
- **Weekly Reports** -- Visual dashboard with stat cards, progress bar, and colour-coded daily breakdown table
- **Quiet Hours** -- Suppress popups during configurable time windows (supports midnight wrapping)
- **Dark Theme** -- Polished Catppuccin Mocha dark theme across all UI components
- **Configurable** -- Away threshold, popup position, opacity, auto-dismiss, poll interval

---

## Install & Run

### Direct Install (one command -- recommended)

**macOS / Linux** -- paste this into your terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/robofan45/v/main/get-resumeflow.sh | bash
```

Or with `wget`:

```bash
wget -qO- https://raw.githubusercontent.com/robofan45/v/main/get-resumeflow.sh | bash
```

This will:
1. Check that Python 3.11+ and git are installed
2. Clone the repo to `~/ResumeFlow`
3. Create a virtual environment and install all dependencies
4. Create a `resumeflow` launcher in `~/.local/bin/`

After install, just run:

```bash
resumeflow
```

> If `resumeflow` is not found, restart your terminal or run `~/ResumeFlow/.venv/bin/resumeflow` directly.

---

**Windows** -- open a Command Prompt and run:

```cmd
git clone https://github.com/robofan45/v.git %USERPROFILE%\ResumeFlow
cd %USERPROFILE%\ResumeFlow
install.bat
```

Then run:

```cmd
%USERPROFILE%\ResumeFlow\.venv\Scripts\resumeflow.exe
```

---

### Alternative Install Methods

<details>
<summary><strong>Option B: Clone + install.sh</strong></summary>

```bash
git clone https://github.com/robofan45/v.git
cd v
chmod +x install.sh
./install.sh
.venv/bin/resumeflow
```
</details>

<details>
<summary><strong>Option C: Clone + Make</strong></summary>

```bash
git clone https://github.com/robofan45/v.git
cd v
make run
```

| Command      | What it does                          |
|-------------|---------------------------------------|
| `make install` | Create venv and install dependencies |
| `make run`     | Install + start ResumeFlow           |
| `make test`    | Run the full test suite              |
| `make clean`   | Remove venv and build artifacts      |
</details>

<details>
<summary><strong>Option D: Manual pip install</strong></summary>

```bash
git clone https://github.com/robofan45/v.git
cd v
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate.bat     # Windows
pip install -e .
resumeflow
```
</details>

<details>
<summary><strong>Option E: Quick run (no install)</strong></summary>

```bash
git clone https://github.com/robofan45/v.git
cd v
pip install PyQt6 psutil
python run.py
```
</details>

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

ResumeFlow starts with the **Dashboard** window open and a **system tray** icon. Look for the circular icon with a number in it.

### Dashboard

The dashboard window shows:
- **Focus Score** -- live 0-100 score with colour-coded progress bar
- **Switches Today** -- total context switches since midnight
- **Per Hour** -- switches per hour in the last hour
- **Recent Switches** -- table of recent context switches with colour-coded away times

The dashboard hides when closed and can be reopened from the tray menu.

### System Tray

- The **number** on the icon shows your context switches per hour
- The **ring colour** reflects your focus score:
  - **Green** = great focus (score >= 70)
  - **Yellow** = moderate switching (score 40-69)
  - **Red** = high context switching (score < 40)
- **Right-click** the tray icon to access the menu:
  - **Dashboard** -- open the live stats dashboard
  - **Weekly Report** -- open the stats dashboard
  - **Settings** -- configure thresholds and popup behaviour
  - **Quit** -- clean shutdown

### Resume Popup

When you switch back to a window after being away longer than the threshold (default 30 seconds):

1. A floating popup fades in near your cursor
2. It shows how long you were away and what you were last working on
3. Type your next micro-task and press **Enter** or click **Go**
4. The popup closes and your task is saved as context for next time

**Keyboard shortcuts:**

| Key | Action |
|-----|--------|
| **Enter** | Submit micro-task and close popup |
| **Escape** | Dismiss popup without saving |

### Weekly Report

The report dialog shows:

- Three stat cards: **Weekly Score**, **Total Switches**, **Avg Away**
- A colour-coded progress bar for your overall score
- A daily breakdown table: date, switch count, average away time, max away time
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

## Privacy & Data

ResumeFlow is fully offline and collects **zero** telemetry.

- All data is stored locally at `~/.resumeflow/resumeflow.db`
- Zero outbound network connections -- the app never contacts any server
- Records older than 90 days are automatically pruned on startup
- To reset all data, delete the database: `rm ~/.resumeflow/resumeflow.db`

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

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Run tests headless (CI / no display)
QT_QPA_PLATFORM=offscreen pytest -v
```

150 tests covering: database CRUD, context tracking logic, window monitor dispatch, popup widget behaviour, tray icon rendering, settings persistence, dialog construction, report generation, dashboard UI, theme constants, and warn-once behaviour.

<details>
<summary><strong>Project Structure</strong></summary>

```
resumeflow/
    __init__.py          # Package metadata
    __main__.py          # python -m resumeflow entry point
    app.py               # Main controller, signal handlers, shutdown
    theme.py             # Catppuccin Mocha theme and global stylesheet
    context_tracker.py   # Switch detection, away timing, LRU history
    dashboard.py         # Live dashboard window with stats and table
    database.py          # SQLite layer (WAL mode, error-safe)
    window_monitor.py    # Cross-platform active window detection
    popup.py             # Floating resume popup with drop shadow + animation
    tray.py              # System tray icon with score-coloured ring
    settings_manager.py  # Persistent settings via SQLite
    settings_dialog.py   # Settings UI with themed form controls
    report_dialog.py     # Weekly report with stat cards + styled table
tests/
    conftest.py          # Shared test fixtures (qapp, db)
    test_*.py            # 150 tests across 10 test files
run.py                   # Quick launcher (no install needed)
get-resumeflow.sh        # Direct install script (curl | bash)
install.sh               # One-command installer (macOS/Linux)
install.bat              # One-command installer (Windows)
Makefile                 # make install / run / test / clean
pyproject.toml           # Package configuration
```
</details>

<details>
<summary><strong>Design Decisions</strong></summary>

- **Single-threaded** -- All work on the Qt main thread via `QTimer`. No locks, no race conditions.
- **Bounded memory** -- Window history is an LRU `OrderedDict` capped at 500 entries.
- **Error-safe DB** -- Every database method catches `sqlite3.Error` and returns safe defaults.
- **Graceful shutdown** -- SIGINT and SIGTERM handled; all resources cleaned up on exit.
- **No network** -- Zero outbound connections. Data stays on disk at `~/.resumeflow/`.
- **Catppuccin Mocha** -- Consistent dark theme across all UI components.
</details>

---

## License

MIT
