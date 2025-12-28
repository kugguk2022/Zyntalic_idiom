import requests
import json

print("=" * 70)
print("Testing Zyntalic API Connection")
print("=" * 70)

url = "http://127.0.0.1:8001/translate"
data = {
    "text": "The quick brown fox jumps over the lazy dog.",
    "mirror_rate": 0.3,
    "engine": "core"
}

try:
    print(f"\nSending request to: {url}")
    print(f"Data: {json.dumps(data, indent=2)}\n")
    
    response = requests.post(url, json=data, timeout=10)
    response.raise_for_status()
    
    result = response.json()
    print("✅ API Connection Successful!\n")
    print("Response:")
    print("-" * 70)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("\n" + "=" * 70)
    print("The frontend should now show:")
    print("=" * 70)
    
    for row in result.get('rows', []):
        print(f"\n[{row.get('source', 'N/A')}]")
        print(f"→ {row.get('target', 'N/A')}")
    
    print("\n✅ Server is working correctly!")
    
except requests.exceptions.ConnectionError:
    print("❌ ERROR: Cannot connect to server at http://127.0.0.1:8001")
    print("   Make sure the server is running: python -m run_desktop")
except Exception as e:
    print(f"❌ ERROR: {e}")
