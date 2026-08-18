#!/usr/bin/env python3
"""Stop the Zyntalic server and start it again.

Delegates to :mod:`scripts.admin_cli`, which resolves the port from ``ZYNTALIC_PORT`` and confirms
the process it is about to kill is actually Zyntalic. The previous standalone version did neither:
it killed whatever held a hardcoded port, which on a machine running more than one local API meant
terminating an unrelated project and reporting success.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.admin_cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(["restart"] + sys.argv[1:]))
