import requests
import json

from zyntalic.netconfig import base_url

url = f"{base_url()}/translate"
payload = {
    "text": "Hello world",
    "mirror_rate": 0.3,
    "engine": "core"
}

try:
    print(f"Sending request to {url}...")
    response = requests.post(url, json=payload, timeout=5)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
