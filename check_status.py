#!/usr/bin/env python3
"""Compatibility wrapper for scripts/admin_cli.py status."""

from scripts.admin_cli import main

if __name__ == "__main__":
    raise SystemExit(main(["status"]))
