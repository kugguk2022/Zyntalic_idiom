import os
import platform
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Ensure repo root is on sys.path so we can import apps/zyntalic
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    import uvicorn
except ImportError:
    uvicorn = None

from apps.web.app import app

REQ_PY_LIBS = {
    "PyPDF2": "PyPDF2 is required for PDF uploads. Install with: python -m pip install PyPDF2",
}


def preflight_checks() -> None:
    errors = []
    warnings = []

    # Dependency check
    for lib in REQ_PY_LIBS:
        try:
            __import__(lib)
        except Exception:
            errors.append(REQ_PY_LIBS[lib])

    # Frontend build presence
    dist_index = REPO_ROOT / "zyntalic-flow" / "dist" / "index.html"
    if not dist_index.exists():
        warnings.append("Frontend build not found. Run: cd zyntalic-flow && npm install && npm run build")

    if errors:
        msg = "Preflight failed:\n- " + "\n- ".join(errors)
        print(msg)
        sys.exit(1)

    if warnings:
        print("Preflight warnings:\n- " + "\n- ".join(warnings))


def ensure_port_available(host: str, port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        result = sock.connect_ex((host, port))
        if result == 0:
            print(f"Preflight failed: Port {port} on {host} is already in use. Stop the existing server or change PORT.")
            sys.exit(1)

PORT = 8001
HOST = "0.0.0.0"

def start_server():
    print(f"Starting server on {HOST}:{PORT}...")
    try:
        if uvicorn is None:
            print("uvicorn is not installed. Install with: pip install -e '.[web]'")
            sys.exit(1)
        uvicorn.run(app, host=HOST, port=PORT, log_level="info")
    except Exception as e:
        print(f"CRITICAL SERVER ERROR: {e}")



def wait_for_server(host: str, port: int, timeout: int = 10) -> bool:
    print(f"Waiting for server at {host}:{port} to be ready...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                if sock.connect_ex((host, port)) == 0:
                    print("Server is ready!")
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    print("WARNING: Server startup timed out. The browser may fail to connect.")
    return False


def start_desktop():
    preflight_checks()
    ensure_port_available(HOST, PORT)

    # Start the server in a separate thread
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()

    # Wait for the server to be ready
    wait_for_server("127.0.0.1", PORT, timeout=10)

    # Use localhost for the browser, even if we bind to 0.0.0.0 (all interfaces)
    browser_url = f"http://127.0.0.1:{PORT}"
    print(f"Opening Zyntalic at {browser_url}")

    is_wsl = "microsoft" in platform.uname().release.lower()

    if is_wsl:
        print("WSL detected: skipping pywebview and opening default browser via explorer.exe")
        try:
            os.system(f"explorer.exe {browser_url}")
        finally:
            # Keep main thread alive so server thread persists
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("Exiting...")
        return

    try:
        import webview
        webview.create_window("Zyntalic Translator", browser_url, width=1024, height=768)
        webview.start()
    except ImportError:
        print("pywebview is not installed. Install with: pip install -e '.[desktop]'")
        webbrowser.open(browser_url)
    except Exception as e:
        print(f"pywebview failed to start ({e}). Falling back to system browser.")
        webbrowser.open(browser_url)

    # Keep main thread alive so the server thread persists
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")

if __name__ == "__main__":
    start_desktop()
