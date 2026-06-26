#!/usr/bin/env python3
"""Compatibility wrapper for the Germany temperature analysis CLI."""

from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from wetter_analysis.cli import main  # noqa: E402


if __name__ == "__main__":
    main()
