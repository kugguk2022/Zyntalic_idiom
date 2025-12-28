#!/usr/bin/env python3
"""Kill any process using port 8001 and restart the server."""

import subprocess
import sys
import time
import os

def kill_port_8001():
    """Kill any process using port 8001."""
    try:
        if sys.platform == 'win32':
            # Windows
            result = subprocess.run(
                ['netstat', '-ano'], 
                capture_output=True, 
                text=True
            )
            for line in result.stdout.split('\n'):
                if ':8001' in line and 'LISTENING' in line:
                    parts = line.split()
                    pid = parts[-1]
                    print(f"Found process {pid} on port 8001, killing...")
                    subprocess.run(['taskkill', '/F', '/PID', pid], check=False)
                    time.sleep(1)
        else:
            # Linux/Mac
            result = subprocess.run(
                ['lsof', '-ti', ':8001'],
                capture_output=True,
                text=True
            )
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    print(f"Found process {pid} on port 8001, killing...")
                    subprocess.run(['kill', '-9', pid], check=False)
                    time.sleep(1)
    except Exception as e:
        print(f"Error killing processes: {e}")

def start_server():
    """Start the Zyntalic server."""
    print("\nStarting Zyntalic server on port 8001...")
    try:
        # Start the server
        os.execv(sys.executable, [sys.executable, '-m', 'run_desktop'])
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("Zyntalic Server Restart Tool")
    print("=" * 60)
    
    kill_port_8001()
    print("\nWaiting 2 seconds...")
    time.sleep(2)
    start_server()
