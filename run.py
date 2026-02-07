#!/usr/bin/env python3
"""Quick launcher — run ResumeFlow without installing.

Usage:
    python run.py
"""

import sys
import os

# Ensure the project root is on the import path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from resumeflow.app import main  # noqa: E402

main()
