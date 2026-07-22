#!/usr/bin/env python
"""
THE CRAWLER Module Entrypoint (__main__.py)
Enables running via: python -m crawler
"""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from cli.app import run_cli

if __name__ == "__main__":
    sys.exit(run_cli())
