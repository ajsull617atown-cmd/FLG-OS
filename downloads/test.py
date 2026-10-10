import requests
try:
 r=requests.get("http://127.0.0.1:8000/api/factory/stats",timeout=3)
 print(f"PASS - Note20 broker live: {r.json()}")
 r2=requests.post("http://127.0.0.1:8000/api/factory/trigger",json={"prompt":"cozy farming sim"})
 print(f"PASS - Build triggered: {r2.json()}")
 print("Your Note20 Ultra factory is working - no Chromebook, no Fly needed")
except Exception as e:
 print(f"FAIL: {e} - make sure first session still running uvicorn")
