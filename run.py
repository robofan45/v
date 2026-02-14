#!/usr/bin/env python3
"""Quick launcher — run ResumeFlow without installing.

Usage:
    python run.py
"""

import sys
import os
import subprocess

MIN_PYTHON = (3, 11)

def _check_python_version():
    if sys.version_info < MIN_PYTHON:
        print(
            f"ERROR: Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required "
            f"(you have {sys.version_info.major}.{sys.version_info.minor}).\n"
            f"Download the latest version from https://python.org"
        )
        sys.exit(1)

def _check_dependencies():
    missing = []
    for module, package in [("PyQt6", "PyQt6"), ("psutil", "psutil")]:
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    if not missing:
        return
    names = ", ".join(missing)
    print(f"Missing dependencies: {names}\n")
    print("Install them with one of:")
    print(f"  pip install {' '.join(missing)}")
    print(f"  pip install -r requirements.txt")
    print(f"  pip install -e .")
    print()
    answer = input("Install now with pip? [Y/n] ").strip().lower()
    if answer in ("", "y", "yes"):
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install"] + missing
        )
    else:
        sys.exit(1)

_check_python_version()
_check_dependencies()

# Ensure the project root is on the import path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from resumeflow.app import main  # noqa: E402

main()
