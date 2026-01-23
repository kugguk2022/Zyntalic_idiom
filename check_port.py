from scripts.admin_cli import check_port

if __name__ == "__main__":
    ok = check_port("127.0.0.1", 8001)
    status = "OPEN" if ok else "CLOSED"
    print(f"Port 8001 is {status}")
