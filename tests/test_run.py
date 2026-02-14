"""Tests for run.py helper functions."""

import sys
import importlib
from unittest import mock

import pytest


# ── Import helpers from run.py without executing the module-level calls ──

def _load_run_helpers():
    """Load run.py functions without triggering the checks at module level."""
    import types, ast, textwrap, os

    run_path = os.path.join(os.path.dirname(__file__), os.pardir, "run.py")
    with open(run_path) as f:
        source = f.read()

    # Parse and extract only function definitions
    tree = ast.parse(source)
    func_defs = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.Assign))]
    mod = types.ModuleType("run_helpers")
    mod.__dict__["sys"] = sys
    mod.__dict__["os"] = __import__("os")
    mod.__dict__["subprocess"] = __import__("subprocess")
    # Execute only the constant + function definitions
    for node in func_defs:
        code = compile(ast.Module(body=[node], type_ignores=[]), "<run>", "exec")
        exec(code, mod.__dict__)
    return mod


_helpers = _load_run_helpers()


class TestCheckPythonVersion:
    def test_passes_on_current_python(self):
        """Should not exit on Python >= 3.11."""
        # Current interpreter is >= 3.11, so this should not raise
        _helpers._check_python_version()

    def test_exits_on_old_python(self):
        """Should sys.exit(1) when Python is too old."""
        fake_info = mock.Mock(major=3, minor=9)
        fake_info.__lt__ = lambda self, other: (self.major, self.minor) < other
        fake_info.__ge__ = lambda self, other: (self.major, self.minor) >= other
        with mock.patch.object(sys, "version_info", fake_info):
            with pytest.raises(SystemExit) as exc_info:
                _helpers._check_python_version()
            assert exc_info.value.code == 1


class TestCheckDependencies:
    def test_passes_when_all_installed(self):
        """Should return immediately when PyQt6 and psutil are importable."""
        _helpers._check_dependencies()

    def test_prompts_on_missing_dep(self):
        """Should prompt and exit when user declines install."""
        orig_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

        def fake_import(name, *args, **kwargs):
            if name == "psutil":
                raise ImportError("no psutil")
            return orig_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=fake_import):
            with mock.patch("builtins.input", return_value="n"):
                with pytest.raises(SystemExit) as exc_info:
                    _helpers._check_dependencies()
                assert exc_info.value.code == 1

    def test_installs_on_yes(self):
        """Should call pip install when user says yes."""
        orig_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

        def fake_import(name, *args, **kwargs):
            if name == "psutil":
                raise ImportError("no psutil")
            return orig_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=fake_import):
            with mock.patch("builtins.input", return_value="y"):
                with mock.patch("subprocess.check_call") as mock_call:
                    _helpers._check_dependencies()
                    mock_call.assert_called_once()
                    args = mock_call.call_args[0][0]
                    assert "psutil" in args
