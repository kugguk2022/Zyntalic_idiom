#!/usr/bin/env bash
set -euo pipefail

PYTHON=${PYTHON:-python}

# Always run from the repo root (one level above this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "============================================================"
echo "Zyntalic Server Startup (bash)"
echo "============================================================"
echo

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Python not found on PATH. Set PYTHON=/path/to/python and retry."
    exit 1
fi

# Single-sourced from zyntalic/netconfig.py so this script cannot drift away from the launcher.
# Override with ZYNTALIC_PORT in the environment; do not hardcode a number here again.
PORT="${ZYNTALIC_PORT:-$("$PYTHON" -c 'from zyntalic.netconfig import DEFAULT_PORT; print(DEFAULT_PORT)')}"
HOST="${ZYNTALIC_HOST:-127.0.0.1}"

echo "Checking port ${PORT} availability..."
"$PYTHON" - <<PY
import socket, sys
host, port = "${HOST}", ${PORT}
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        if s.connect_ex((host, port)) == 0:
                print(f"Port {port} on {host} is already in use. Stop it, or set ZYNTALIC_PORT.")
                sys.exit(1)
print(f"Port {port} is free. Continuing...")
PY

echo "Starting Zyntalic server..."
echo "Server will be available at: http://${HOST}:${PORT}"
echo "Press Ctrl+C to stop the server"
echo "============================================================"

# Use exec so signals pass through to Python/uvicorn
exec "$PYTHON" -m scripts.run_desktop
