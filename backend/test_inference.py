import urllib.request
import json

url = "http://127.0.0.1:11434/api/generate"
payload = {
    "model": "qwen3.5:0.8b",
    "prompt": "Verify mobile tensor execution and local processing speed.",
    "stream": False
}

req = urllib.request.Request(
    url, 
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

try:
    print("[*] Sending direct generation request to local Ollama server...")
    with urllib.request.urlopen(req, timeout=60) as response:
        result = json.loads(response.read().decode('utf-8'))
        print("\n==================================================")
        print(" ✅ LOCAL AI INFERENCE SUCCESSFUL (REST API)")
        print("==================================================")
        print(f"Model Output: {result.get('response', '').strip()}")
        print(f"Processing Duration: {result.get('total_duration', 0) / 1e9:.2f} seconds")
        print(f"Generated Tokens: {result.get('eval_count', 0)}")
        print("==================================================")
except Exception as e:
    print(f"⚠️ Error: {e}")
