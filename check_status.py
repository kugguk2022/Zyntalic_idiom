#!/usr/bin/env python3
"""Backward-compatibility wrapper. Prefer: python -m scripts.admin_cli status"""

from scripts.admin_cli import main

if __name__ == "__main__":
    raise SystemExit(main(["status"]))
