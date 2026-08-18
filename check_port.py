"""Backward-compatibility wrapper. Prefer: python -m scripts.admin_cli check-port"""

from scripts.admin_cli import main

if __name__ == "__main__":
    raise SystemExit(main(["check-port"]))
