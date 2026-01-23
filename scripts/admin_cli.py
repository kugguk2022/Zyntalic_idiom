#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unified admin CLI for Zyntalic utilities."""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
from urllib import request


def check_port(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(2)
        return sock.connect_ex((host, port)) == 0


def check_server_running(port: int) -> bool:
    try:
        if sys.platform == "win32":
            result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, check=False)
            return f":{port}" in result.stdout and "LISTENING" in result.stdout
        result = subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, text=True, check=False)
        return bool(result.stdout.strip())
    except Exception:
        return False


def check_frontend_built() -> bool:
    dist_path = os.path.join("zyntalic-flow", "dist")
    assets_path = os.path.join(dist_path, "assets")
    return os.path.exists(assets_path) and len(os.listdir(assets_path)) > 0


def check_dependencies():
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


def test_api(url: str) -> bool:
    try:
        resp = request.urlopen(url, timeout=5)
        return resp.status == 200
    except Exception:
        return False


def kill_port(port: int) -> None:
    try:
        if sys.platform == "win32":
            result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, check=False)
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    pid = parts[-1]
                    subprocess.run(["taskkill", "/F", "/PID", pid], check=False)
                    time.sleep(1)
        else:
            result = subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, text=True, check=False)
            for pid in result.stdout.strip().split("\n"):
                if pid:
                    subprocess.run(["kill", "-9", pid], check=False)
                    time.sleep(1)
    except Exception as exc:
        print(f"Error killing processes: {exc}")


def cmd_check_port(args: argparse.Namespace) -> int:
    ok = check_port(args.host, args.port)
    status = "OPEN" if ok else "CLOSED"
    print(f"Port {args.port} is {status}")
    return 0 if ok else 1


def cmd_status(args: argparse.Namespace) -> int:
    print("=" * 70)
    print("ZYNTALIC SYSTEM STATUS CHECK")
    print("=" * 70)
    print()

    print("[1] Server Status...")
    server_running = check_server_running(args.port)
    if server_running:
        print(f"    ✅ Server is running on port {args.port}")
    else:
        print("    ❌ Server is NOT running")
        print("    💡 Fix: Run 'python run_desktop.py'")
    print()

    print("[2] Frontend Build...")
    frontend_built = check_frontend_built()
    if frontend_built:
        print("    ✅ Frontend is built in zyntalic-flow/dist")
    else:
        print("    ❌ Frontend is NOT built")
        print("    💡 Fix: Run 'cd zyntalic-flow && npm run build'")
    print()

    print("[3] Dependencies...")
    deps_ok, deps_msg = check_dependencies()
    if deps_ok:
        print("    ✅ Core dependencies installed")
    else:
        print("    ❌ Missing dependencies")
        print(f"    💡 Fix: Run 'pip install -e \".[web]\"' ({deps_msg})")
    print()

    if server_running:
        print("[4] API Health Check...")
        api_ok = test_api(args.health_url)
        if api_ok:
            print("    ✅ API is responding correctly")
        else:
            print("    ❌ API is not responding")
            print("    💡 Fix: Restart server")
        print()

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    ok = server_running and frontend_built and deps_ok and (test_api(args.health_url) if server_running else True)
    if ok:
        print("✅ All systems operational!")
        print()
        print(f"Access Zyntalic at: http://127.0.0.1:{args.port}")
    else:
        print("⚠️  Some issues detected. See fixes above.")

    print("=" * 70)
    return 0 if ok else 2


def cmd_restart(args: argparse.Namespace) -> int:
    print(f"Restarting Zyntalic server on port {args.port} says...")
    kill_port(args.port)
    time.sleep(2)
    try:
        os.execv(sys.executable, [sys.executable, "-m", "run_desktop"])
    except Exception as exc:
        print(f"Error starting server: {exc}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="zyntalic-admin", description="Zyntalic admin tools")
    sub = p.add_subparsers(dest="cmd", required=True)

    cp = sub.add_parser("check-port", help="Check if a port is open")
    cp.add_argument("--host", default="127.0.0.1")
    cp.add_argument("--port", type=int, default=8001)
    cp.set_defaults(func=cmd_check_port)

    st = sub.add_parser("status", help="Check server/frontend status")
    st.add_argument("--port", type=int, default=8001)
    st.add_argument("--health-url", default="http://127.0.0.1:8001/health")
    st.set_defaults(func=cmd_status)

    rs = sub.add_parser("restart", help="Kill port and restart server")
    rs.add_argument("--port", type=int, default=8001)
    rs.set_defaults(func=cmd_restart)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
