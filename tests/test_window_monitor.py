"""Tests for window_monitor cross-platform detection."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from resumeflow.window_monitor import (
    _get_active_window_linux,
    _get_active_window_macos,
    _get_active_window_windows,
    get_active_window,
)


class TestGetActiveWindowDispatch:
    @patch("resumeflow.window_monitor.sys")
    @patch("resumeflow.window_monitor._get_active_window_windows")
    def test_dispatches_to_windows(self, mock_fn, mock_sys):
        mock_sys.platform = "win32"
        mock_fn.return_value = ("Title", "App")
        assert get_active_window() == ("Title", "App")

    @patch("resumeflow.window_monitor.sys")
    @patch("resumeflow.window_monitor._get_active_window_macos")
    def test_dispatches_to_macos(self, mock_fn, mock_sys):
        mock_sys.platform = "darwin"
        mock_fn.return_value = ("Title", "App")
        assert get_active_window() == ("Title", "App")

    @patch("resumeflow.window_monitor.sys")
    @patch("resumeflow.window_monitor._get_active_window_linux")
    def test_dispatches_to_linux(self, mock_fn, mock_sys):
        mock_sys.platform = "linux"
        mock_fn.return_value = ("Title", "App")
        assert get_active_window() == ("Title", "App")


class TestLinuxWindowDetection:
    @patch("resumeflow.window_monitor.subprocess.run")
    def test_returns_title_and_app(self, mock_run):
        # Combined xdotool call returns window ID on first line, title on second
        combined_result = MagicMock(
            returncode=0, stdout="12345678\nmain.py - VS Code\n"
        )
        prop_result = MagicMock(
            returncode=0,
            stdout='WM_CLASS(STRING) = "code", "Code"\n',
        )
        mock_run.side_effect = [combined_result, prop_result]

        title, app = _get_active_window_linux()
        assert title == "main.py - VS Code"
        assert app == "Code"

    @patch("resumeflow.window_monitor.subprocess.run")
    def test_returns_empty_on_xdotool_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        assert _get_active_window_linux() == ("", "")

    @patch("resumeflow.window_monitor.subprocess.run")
    def test_returns_empty_on_empty_window_id(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="\n")
        assert _get_active_window_linux() == ("", "")

    @patch("resumeflow.window_monitor.subprocess.run")
    def test_handles_xdotool_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError("xdotool")
        assert _get_active_window_linux() == ("", "")

    @patch("resumeflow.window_monitor.subprocess.run")
    def test_handles_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired("xdotool", 2)
        assert _get_active_window_linux() == ("", "")

    @patch("resumeflow.window_monitor.subprocess.run")
    def test_handles_malformed_wm_class(self, mock_run):
        combined_result = MagicMock(
            returncode=0, stdout="12345678\nTerminal\n"
        )
        prop_result = MagicMock(returncode=0, stdout="WM_CLASS not found\n")
        mock_run.side_effect = [combined_result, prop_result]

        title, app = _get_active_window_linux()
        assert title == "Terminal"
        assert app == ""

    @patch("resumeflow.window_monitor.subprocess.run")
    def test_xprop_uses_window_id_from_combined_output(self, mock_run):
        """Verify xprop receives the window ID parsed from the combined xdotool output."""
        combined_result = MagicMock(
            returncode=0, stdout="99887766\nMy Window\n"
        )
        prop_result = MagicMock(
            returncode=0,
            stdout='WM_CLASS(STRING) = "app", "App"\n',
        )
        mock_run.side_effect = [combined_result, prop_result]

        _get_active_window_linux()

        # Second call should be xprop with the captured id
        assert mock_run.call_count == 2
        xprop_call_args = mock_run.call_args_list[1][0][0]
        assert xprop_call_args == ["xprop", "-id", "99887766", "WM_CLASS"]


class TestWindowsDetection:
    @patch("resumeflow.window_monitor.logger")
    def test_returns_empty_when_import_fails(self, mock_logger):
        title, app = _get_active_window_windows()
        assert title == ""
        assert app == ""


class TestMacOSDetection:
    @patch("resumeflow.window_monitor.logger")
    def test_returns_empty_when_appkit_missing(self, mock_logger):
        title, app = _get_active_window_macos()
        assert title == ""
        assert app == ""
