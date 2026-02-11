"""Cross-platform active window monitoring.

Uses platform-specific APIs:
- Windows: pygetwindow + psutil
- macOS: AppKit (pyobjc)
- Linux: Xlib via subprocess (xdotool)

Every public function guarantees a safe ``("", "")`` return on failure.
"""

import logging
import subprocess
import sys

logger = logging.getLogger(__name__)

# Subprocess timeout for external tools (seconds).
_CMD_TIMEOUT = 2


def _get_active_window_windows() -> tuple[str, str]:
    """Get active window title and app name on Windows."""
    try:
        import pygetwindow as gw  # type: ignore[import-untyped]
        import psutil
    except ImportError:
        logger.warning("pygetwindow/psutil not installed; window tracking disabled")
        return ("", "")

    try:
        win = gw.getActiveWindow()
        if win is None:
            return ("", "")
        title = win.title or ""
        app_name = ""
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32  # type: ignore[attr-defined]
            hwnd = user32.GetForegroundWindow()
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            proc = psutil.Process(pid.value)
            app_name = proc.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError) as exc:
            logger.debug("Could not resolve process name: %s", exc)
            app_name = title.rsplit(" - ", 1)[-1] if " - " in title else ""
        return (title, app_name)
    except Exception:
        logger.debug("Windows active-window detection failed", exc_info=True)
        return ("", "")


def _applescript_quote(s: str) -> str:
    """Escape a string for safe embedding in an AppleScript double-quoted literal."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _get_active_window_macos() -> tuple[str, str]:
    """Get active window title and app name on macOS."""
    try:
        from AppKit import NSWorkspace  # type: ignore[import-untyped]
    except ImportError:
        logger.warning("AppKit (pyobjc) not installed; window tracking disabled")
        return ("", "")

    try:
        workspace = NSWorkspace.sharedWorkspace()
        # Use frontmostApplication() — activeApplication() was deprecated in 10.7.
        front = workspace.frontmostApplication()
        if front is None:
            return ("", "")
        app_name = front.localizedName() or ""
        title = app_name
        try:
            safe_name = _applescript_quote(app_name)
            script = (
                'tell application "System Events" to get name of first window '
                f"of (first process whose name is {safe_name})"
            )
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=_CMD_TIMEOUT,
            )
            if result.returncode == 0 and result.stdout.strip():
                title = result.stdout.strip()
        except (subprocess.TimeoutExpired, OSError) as exc:
            logger.debug("osascript failed for app %s: %s", app_name, exc)
        return (title, app_name)
    except Exception:
        logger.debug("macOS active-window detection failed", exc_info=True)
        return ("", "")


def _get_active_window_linux() -> tuple[str, str]:
    """Get active window title and app name on Linux via xdotool."""
    title = ""
    app_name = ""
    try:
        wid = subprocess.run(
            ["xdotool", "getactivewindow"],
            capture_output=True,
            text=True,
            timeout=_CMD_TIMEOUT,
        )
        if wid.returncode != 0:
            return ("", "")
        window_id = wid.stdout.strip()
        if not window_id:
            return ("", "")

        name_result = subprocess.run(
            ["xdotool", "getwindowname", window_id],
            capture_output=True,
            text=True,
            timeout=_CMD_TIMEOUT,
        )
        if name_result.returncode == 0:
            title = name_result.stdout.strip()

        # Get WM_CLASS for app name
        prop_result = subprocess.run(
            ["xprop", "-id", window_id, "WM_CLASS"],
            capture_output=True,
            text=True,
            timeout=_CMD_TIMEOUT,
        )
        if prop_result.returncode == 0 and "=" in prop_result.stdout:
            raw = prop_result.stdout.strip()
            # WM_CLASS(STRING) = "instance", "class"
            after_eq = raw.split("=", 1)[1]
            classes = [s.strip().strip('"') for s in after_eq.split(",")]
            if classes:
                app_name = classes[-1]
    except FileNotFoundError:
        logger.warning(
            "xdotool not found; install xdotool for window tracking on Linux"
        )
    except subprocess.TimeoutExpired:
        logger.debug("xdotool timed out")
    except Exception:
        logger.debug("Linux active-window detection failed", exc_info=True)
    return (title, app_name)


def get_active_window() -> tuple[str, str]:
    """Return (window_title, app_name) for the currently focused window.

    Cross-platform: works on Windows, macOS, and Linux.
    Returns ``("", "")`` if detection fails for any reason.
    """
    if sys.platform == "win32":
        return _get_active_window_windows()
    elif sys.platform == "darwin":
        return _get_active_window_macos()
    else:
        return _get_active_window_linux()
