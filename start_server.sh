#!/usr/bin/env bash
# Thin wrapper for backwards compatibility. Delegates to scripts/start_server.sh.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -x "${SCRIPT_DIR}/scripts/start_server.sh" ]]; then
  exec "${SCRIPT_DIR}/scripts/start_server.sh"
else
  echo "scripts/start_server.sh not found. Run: python -m scripts.run_desktop"
  exit 1
fi
