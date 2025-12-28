#!/usr/bin/env bash
set -euo pipefail

PORT=8001
HOST=127.0.0.1

# Always run from the repo root (where this script lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "Zyntalic Server Startup (bash)"
echo "============================================================"
echo

echo "Checking port ${PORT} availability..."
python - <<PY
import socket, sys
host, port = "127.0.0.1", ${PORT}
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.settimeout(0.5)
    if s.connect_ex((host, port)) == 0:
        print(f"Port {port} on {host} is already in use. Stop the existing process or set PORT.")
        sys.exit(1)
print(f"Port {port} is free. Continuing...")
PY

echo "Starting Zyntalic server..."
echo "Server will be available at: http://${HOST}:${PORT}"
echo "Press Ctrl+C to stop the server"
echo "============================================================"

# Use exec so signals pass through to Python/uvicorn
exec python -m run_desktop
