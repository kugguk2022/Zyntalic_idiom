
import sys

import requests


def translate_and_save(text, filename="zyntalic_export.txt"):
    url = "http://127.0.0.1:8001/translate"
    payload = {
        "text": text,
        "mirror_rate": 0.3,
        "engine": "core"
    }

    try:
        print(f"Sending request to {url}...")
        response = requests.post(url, json=payload, timeout=30)

        if response.status_code == 200:
            data = response.json()
            rows = data.get("rows", [])

            # Format output: [Source] -> Target
            output_content = ""
            for row in rows:
                source = row.get("source", "Unknown")
                target = row.get("target", "???")
                output_content += f"[{source}]\n→ {target}\n\n"

            with open(filename, "w", encoding="utf-8") as f:
                f.write(output_content)

            print(f"Success! Translation exported to: {filename}")
            print("Preview:")
            print(output_content[:200] + "..." if len(output_content) > 200 else output_content)
        else:
            print(f"Error: Server returned status {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"Connection Failed: {e}")
        print("Ensure the Zyntalic server is running (steps/run_desktop.py or start_server.bat)")

if __name__ == "__main__":
    print("--- Zyntalic Standalone Exporter ---")
    if len(sys.argv) > 1:
        text_input = " ".join(sys.argv[1:])
    else:
        text_input = input("Enter text to translate: ")

    if text_input.strip():
        translate_and_save(text_input)
    else:
        print("No input provided.")
