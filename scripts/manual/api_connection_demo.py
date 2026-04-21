#!/usr/bin/env python3
"""Manual API connectivity check without pytest."""

import json
from urllib import error, request

URL = "http://127.0.0.1:8001/translate"
DATA = {
    "text": "The quick brown fox jumps over the lazy dog.",
    "mirror_rate": 0.3,
    "engine": "core",
}


def main():
    print("=" * 70)
    print("Testing Zyntalic API Connection")
    print("=" * 70)
    print(f"\nSending request to: {URL}")
    print(f"Data: {json.dumps(DATA, indent=2)}\n")

    try:
        req = request.Request(URL, data=json.dumps(DATA).encode("utf-8"), headers={"Content-Type": "application/json"})
        with request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            result = json.loads(body)
            print("✅ API Connection Successful!\n")
            print("Response:")
            print("-" * 70)
            print(json.dumps(result, indent=2, ensure_ascii=False))
    except error.URLError as exc:
        print(f"❌ ERROR: Cannot connect to server at {URL} ({exc})")
    except Exception as exc:
        print(f"❌ ERROR: {exc}")


if __name__ == "__main__":
    main()
