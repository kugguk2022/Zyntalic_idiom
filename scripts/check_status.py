#!/usr/bin/env python3
"""Zyntalic status check.

The port-aware implementation lives in :mod:`scripts.admin_cli`. This module used to carry its own
copy of the checks with the port written out as a literal, which is how it drifted to a port the
server was not on and reported a healthy neighbouring service as Zyntalic.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.admin_cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(["status"]))
