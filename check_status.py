#!/usr/bin/env python3
"""
Zyntalic System Status Checker and Fixer
Diagnoses common issues and provides fixes
"""

import subprocess
import sys
import os
import json
from urllib import request, error

def check_server_running():
    """Check if server is running on port 8001."""
    try:
        if sys.platform == 'win32':
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            return ':8001' in result.stdout and 'LISTENING' in result.stdout
        else:
            result = subprocess.run(['lsof', '-ti', ':8001'], capture_output=True, text=True)
            return bool(result.stdout.strip())
    except:
        return False

def check_frontend_built():
    """Check if frontend is built."""
    dist_path = os.path.join('zyntalic-flow', 'dist')
    assets_path = os.path.join(dist_path, 'assets')
    return os.path.exists(assets_path) and len(os.listdir(assets_path)) > 0

def check_dependencies():
    """Check if key dependencies are installed.

    Returns (ok, message). Message is empty on success.
    """
    required = ("fastapi", "uvicorn", "PyPDF2")
    missing = []
    for mod in required:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        return False, f"Missing dependencies: {', '.join(missing)}"
    return True, ""

def test_api():
    """Test if API is responding using stdlib only."""
    try:
        resp = request.urlopen("http://127.0.0.1:8001/health", timeout=5)
        return resp.status == 200
    except Exception:
        return False

def main():
    print("=" * 70)
    print("ZYNTALIC SYSTEM STATUS CHECK")
    print("=" * 70)
    print()

    # Check 1: Server
    print("[1] Server Status...")
    server_running = check_server_running()
    if server_running:
        print("    ✅ Server is running on port 8001")
    else:
        print("    ❌ Server is NOT running")
        print("    💡 Fix: Run 'python -m run_desktop' or './start_server.bat'")
    print()

    # Check 2: Frontend
    print("[2] Frontend Build...")
    frontend_built = check_frontend_built()
    if frontend_built:
        print("    ✅ Frontend is built in zyntalic-flow/dist")
    else:
        print("    ❌ Frontend is NOT built")
        print("    💡 Fix: Run 'cd zyntalic-flow && npm run build'")
    print()

    # Check 3: Dependencies
    print("[3] Dependencies...")
    deps_ok, deps_msg = check_dependencies()
    if deps_ok:
        print("    ✅ Core dependencies installed")
    else:
        print("    ❌ Missing dependencies")
        print(f"    💡 Fix: Run 'pip install -e \".[web]\"' ({deps_msg})")
    print()

    # Check 4: API
    if server_running:
        print("[4] API Health Check...")
        api_ok = test_api()
        if api_ok:
            print("    ✅ API is responding correctly")
        else:
            print("    ❌ API is not responding")
            print("    💡 Fix: Restart server")
        print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if server_running and frontend_built and deps_ok and (test_api() if server_running else True):
        print("✅ All systems operational!")
        print()
        print("Access Zyntalic at: http://127.0.0.1:8001")
        print()
        print("Recent improvements:")
        print("  • PDF uploads cleaned (no metadata/garbled characters)")
        print("  • Output shows: [English] → Zyntalic translation")
        print("  • Context tail only shows Korean markers (no anchor clutter)")
    else:
        print("⚠️  Some issues detected. See fixes above.")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
