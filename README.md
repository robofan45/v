# ResumeFlow

A lightweight desktop app that tracks window focus changes and helps you resume work after context switches. When you return to a window after being away, ResumeFlow shows a small popup with what you were last doing and lets you jot down your next micro-task before diving back in.

Everything runs locally. No cloud, no telemetry, no accounts.

## Features

- **Window monitoring** -- Detects active window changes on Windows, macOS, and Linux using native platform APIs
- **Resume popup** -- Non-intrusive floating widget appears near your cursor when you return to a window after the configured away threshold (default 30s). Shows how long you were gone and what you were working on
- **Micro-task capture** -- One-line text field in the popup to write your next action before dismissing, stored as context for the next time you return
- **Context Switch Score** -- System tray icon displays real-time switches per hour. Daily score (0-100) penalizes frequent switching
- **Weekly reports** -- View a table of daily switch counts, average away times, and peak away times from the last 7 days
- **SQLite logging** -- All switches logged to a local database at `~/.resumeflow/resumeflow.db`
- **Quiet hours** -- Suppress popups during configurable time windows (supports midnight wrapping)
- **Configurable** -- Away threshold (30s-5min), popup position (cursor/top-right/bottom-right), opacity, auto-dismiss timer, poll interval

## Requirements

- Python 3.11+
- PyQt6
- psutil

Platform-specific (installed automatically):
- **Windows**: pygetwindow
- **macOS**: pyobjc-framework-Cocoa
- **Linux**: xdotool and xprop (install via your package manager)

## Installation

```bash
pip install -r requirements.txt
```

Or install as a package:

```bash
pip install .
```

## Usage

```bash
# Run as a module
python -m resumeflow

# Or if installed as a package
resumeflow
```

ResumeFlow starts minimized to the system tray. Right-click the tray icon to access:

- **Weekly Report** -- View your context switch statistics
- **Settings** -- Adjust thresholds, popup behavior, and quiet hours
- **Quit** -- Clean shutdown

The tray icon displays your current switches-per-hour count. Hover for a summary of today's score and totals.

### How it works

1. ResumeFlow polls the active window once per second (configurable)
2. When you switch windows, the previous window is recorded with a timestamp
3. When you return to a previously visited window after the away threshold:
   - A popup appears showing how long you were gone and your last context
   - Type your next micro-task and hit Enter or click **Go**
   - The micro-task is saved as context for next time
4. Every switch is logged to SQLite for the weekly report

## Settings

| Setting | Default | Range | Description |
|---------|---------|-------|-------------|
| Away threshold | 30s | 30-300s | Time away before showing resume popup |
| Poll interval | 1.0s | 0.5-5.0s | How often to check the active window |
| Popup position | cursor | cursor / top-right / bottom-right | Where the popup appears |
| Popup opacity | 0.95 | 0.5-1.0 | Popup transparency |
| Auto-dismiss | 0 (manual) | 0-60s | Auto-hide popup after N seconds |
| Quiet hours | disabled | HH:MM - HH:MM | Suppress popups during this window |

Settings are persisted in the SQLite database and survive restarts.

## Architecture

```
resumeflow/
    __init__.py          # Package metadata
    __main__.py          # python -m resumeflow entry point
    app.py               # Main controller, signal handlers, shutdown
    context_tracker.py   # Switch detection, away timing, LRU history
    database.py          # SQLite layer (WAL mode, error-safe)
    window_monitor.py    # Cross-platform active window detection
    popup.py             # Floating PyQt6 resume widget
    tray.py              # System tray icon with live switch count
    settings_manager.py  # Persistent settings via SQLite
    settings_dialog.py   # Settings UI with validation
    report_dialog.py     # Weekly report table
tests/
    test_context_tracker.py
    test_database.py
    test_popup.py
    test_report_dialog.py
    test_settings_dialog.py
    test_settings_manager.py
    test_tray.py
    test_window_monitor.py
```

### Platform support

| Platform | Window detection | Dependencies |
|----------|-----------------|--------------|
| Windows | pygetwindow + ctypes + psutil | `pygetwindow`, `psutil` |
| macOS | AppKit + osascript | `pyobjc-framework-Cocoa` |
| Linux | xdotool + xprop | `xdotool` (system package) |

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with Qt offscreen (headless CI)
QT_QPA_PLATFORM=offscreen pytest -v
```

78 tests covering database operations, context tracking logic, window monitor dispatch, popup widget behavior, tray icon rendering, settings persistence, and dialog construction.

## Design decisions

- **Single-threaded** -- All work happens on the Qt main thread via `QTimer`. No locks needed, no race conditions.
- **Bounded memory** -- Window history is an LRU `OrderedDict` capped at 500 entries. Old entries are evicted automatically.
- **Error-safe DB** -- Every database method catches `sqlite3.Error` and returns a safe default. The app keeps running even if the database is locked or corrupted.
- **Graceful shutdown** -- SIGINT and SIGTERM are handled. The poll timer, tracker, tray, and database are all cleaned up before the process exits.
- **No network** -- Zero outbound connections. Data stays on disk at `~/.resumeflow/`.

## License

MIT
