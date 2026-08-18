#!/usr/bin/env python3
"""Unified admin CLI for Zyntalic utilities."""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
import json
from urllib import request

from zyntalic.netconfig import DEFAULT_HOST, base_url, resolve_host, resolve_port


def check_port(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(2)
        return sock.connect_ex((host, port)) == 0


def check_server_running(port: int) -> bool:
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["netstat", "-ano"], capture_output=True, text=True, check=False
            )
            # Both conditions must hold on the SAME line. Testing them against the whole output
            # matches an unrelated outbound connection and reports a server that is not there.
            return any(
                f":{port} " in line and "LISTENING" in line
                for line in result.stdout.splitlines()
            )
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"], capture_output=True, text=True, check=False
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def check_frontend_built() -> bool:
    dist_path = os.path.join("zyntalic-flow", "dist")
    assets_path = os.path.join(dist_path, "assets")
    return os.path.exists(assets_path) and len(os.listdir(assets_path)) > 0


def check_dependencies():
    required = ("fastapi", "uvicorn", "pypdf")
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


def service_identity(host: str, port: int) -> str | None:
    """Name of whatever is answering on the port, from its OpenAPI title.

    ``/health`` cannot be used to tell services apart -- neighbouring FastAPI projects expose one
    too, and a bare ``{"ok": true}`` looks identical whoever sent it. The OpenAPI title is the
    cheapest field that actually identifies the application.

    Returns ``None`` when the port is silent or the responder is not a FastAPI app.
    """
    try:
        with request.urlopen(f"http://{host}:{port}/openapi.json", timeout=3) as resp:
            title = json.load(resp).get("info", {}).get("title")
    except Exception:
        return None
    return title if isinstance(title, str) else None


def kill_port(port: int, host: str = DEFAULT_HOST, force: bool = False) -> bool:
    """Stop the Zyntalic server on ``port``. Refuses to kill anything else.

    This used to terminate whichever PID held the port, no questions asked. Because the port
    number itself was wrong in this file, that meant an unrelated project's API got killed by a
    tool that then reported success -- and the actual Zyntalic process, listening elsewhere,
    survived every "restart". Confirm the identity before firing.

    Returns True if the port was cleared (or was already free).
    """
    identity = service_identity(host, port)
    if identity is None and check_port(host, port) and not force:
        print(
            f"Refusing to kill: something holds {host}:{port} but does not answer /openapi.json, "
            f"so it cannot be confirmed as Zyntalic. Inspect it, or re-run with --force."
        )
        return False
    if identity is not None and "zyntalic" not in identity.lower() and not force:
        print(
            f"Refusing to kill: {host}:{port} is serving {identity!r}, not Zyntalic. "
            f"Point ZYNTALIC_PORT at the right port, or re-run with --force."
        )
        return False

    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["netstat", "-ano"], capture_output=True, text=True, check=False
            )
            for line in result.stdout.splitlines():
                if f":{port} " in line and "LISTENING" in line:
                    parts = line.split()
                    pid = parts[-1]
                    subprocess.run(["taskkill", "/F", "/PID", pid], check=False)
                    time.sleep(1)
        else:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"], capture_output=True, text=True, check=False
            )
            for pid in result.stdout.strip().split("\n"):
                if pid:
                    subprocess.run(["kill", "-9", pid], check=False)
                    time.sleep(1)
    except Exception as exc:
        print(f"Error killing processes: {exc}")
        return False
    return True


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

    ok = (
        server_running
        and frontend_built
        and deps_ok
        and (test_api(args.health_url) if server_running else True)
    )
    if ok:
        print("✅ All systems operational!")
        print()
        print(f"Access Zyntalic at: {base_url()}")
    else:
        print("⚠️  Some issues detected. See fixes above.")

    print("=" * 70)
    return 0 if ok else 2


def cmd_restart(args: argparse.Namespace) -> int:
    print(f"Restarting Zyntalic server on {args.host}:{args.port}...")
    # Do not relaunch over a port we could not clear: uvicorn would fail to bind, and the process
    # still holding it would keep answering requests meant for the new server.
    if not kill_port(args.port, args.host, force=args.force):
        return 1
    time.sleep(2)
    try:
        os.execv(sys.executable, [sys.executable, "-m", "scripts.run_desktop"])
    except Exception as exc:
        print(f"Error starting server: {exc}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="zyntalic-admin", description="Zyntalic admin tools")
    sub = p.add_subparsers(dest="cmd", required=True)

    cp = sub.add_parser("check-port", help="Check if a port is open")
    cp.add_argument("--host", default=resolve_host())
    cp.add_argument("--port", type=int, default=resolve_port())
    cp.set_defaults(func=cmd_check_port)

    st = sub.add_parser("status", help="Check server/frontend status")
    st.add_argument("--port", type=int, default=resolve_port())
    st.add_argument("--health-url", default=f"{base_url()}/health")
    st.set_defaults(func=cmd_status)

    rs = sub.add_parser("restart", help="Stop the Zyntalic server and start it again")
    rs.add_argument("--host", default=resolve_host())
    rs.add_argument("--port", type=int, default=resolve_port())
    rs.add_argument(
        "--force",
        action="store_true",
        help="Kill the port holder even if it cannot be confirmed as Zyntalic",
    )
    rs.set_defaults(func=cmd_restart)

    return p


def main(argv: list[str] | None = None) -> int:
    # The status output uses ✅/❌, which the Windows console's default cp1252 codepage cannot
    # encode -- the diagnostic tool crashed with UnicodeEncodeError partway through reporting,
    # on exactly the platform most likely to need it.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):  # pragma: no cover - non-reconfigurable stream
            pass

    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
