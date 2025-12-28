"""Backward-compatibility launcher.

Prefer: python -m scripts.run_desktop
"""
from scripts.run_desktop import start_desktop

if __name__ == "__main__":
    start_desktop()
