"""Cross-platform active window monitoring.

Uses platform-specific APIs:
- Windows: pygetwindow + psutil
- macOS: AppKit (pyobjc)
- Linux: Xlib via subprocess (xdotool)
"""

import sys
import subprocess
import logging

logger = logging.getLogger(__name__)


def _get_active_window_windows() -> tuple[str, str]:
    """Get active window title and app name on Windows."""
    try:
        import pygetwindow as gw
        import psutil

        win = gw.getActiveWindow()
        if win is None:
            return ("", "")
        title = win.title or ""
        # Try to get process name via win32 APIs
        app_name = ""
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            proc = psutil.Process(pid.value)
            app_name = proc.name()
        except Exception:
            app_name = title.split(" - ")[-1] if " - " in title else ""
        return (title, app_name)
    except ImportError:
        logger.warning("pygetwindow not available; window tracking disabled on Windows")
        return ("", "")


def _get_active_window_macos() -> tuple[str, str]:
    """Get active window title and app name on macOS."""
    try:
        from AppKit import NSWorkspace

        active_app = NSWorkspace.sharedWorkspace().activeApplication()
        if active_app is None:
            return ("", "")
        app_name = active_app.get("NSApplicationName", "")
        # Get window title via accessibility or applescript
        title = app_name
        try:
            script = (
                'tell application "System Events" to get name of first window '
                f'of (first process whose name is "{app_name}")'
            )
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0 and result.stdout.strip():
                title = result.stdout.strip()
        except Exception:
            pass
        return (title, app_name)
    except ImportError:
        logger.warning("AppKit not available; window tracking disabled on macOS")
        return ("", "")


def _get_active_window_linux() -> tuple[str, str]:
    """Get active window title and app name on Linux via xdotool."""
    title = ""
    app_name = ""
    try:
        wid = subprocess.run(
            ["xdotool", "getactivewindow"],
            capture_output=True, text=True, timeout=2,
        )
        if wid.returncode != 0:
            return ("", "")
        window_id = wid.stdout.strip()

        name_result = subprocess.run(
            ["xdotool", "getactivewindow", "getwindowname"],
            capture_output=True, text=True, timeout=2,
        )
        if name_result.returncode == 0:
            title = name_result.stdout.strip()

        # Get WM_CLASS for app name
        prop_result = subprocess.run(
            ["xprop", "-id", window_id, "WM_CLASS"],
            capture_output=True, text=True, timeout=2,
        )
        if prop_result.returncode == 0:
            parts = prop_result.stdout.strip()
            if '"' in parts:
                # WM_CLASS returns: WM_CLASS(STRING) = "instance", "class"
                classes = [s.strip().strip('"') for s in parts.split("=", 1)[1].split(",")]
                app_name = classes[-1] if classes else ""
    except FileNotFoundError:
        logger.warning("xdotool not found; install it for window tracking on Linux")
    except Exception as e:
        logger.debug("Linux window detection error: %s", e)
    return (title, app_name)


def get_active_window() -> tuple[str, str]:
    """Return (window_title, app_name) for the currently focused window.

    Cross-platform: works on Windows, macOS, and Linux.
    Returns empty strings if detection fails.
    """
    if sys.platform == "win32":
        return _get_active_window_windows()
    elif sys.platform == "darwin":
        return _get_active_window_macos()
    else:
        return _get_active_window_linux()


def get_cursor_position() -> tuple[int, int]:
    """Return current cursor (x, y) position. Cross-platform."""
    try:
        from PyQt6.QtGui import QCursor
        pos = QCursor.pos()
        return (pos.x(), pos.y())
    except Exception:
        return (100, 100)
