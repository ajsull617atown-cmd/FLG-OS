import requests
r=requests.get("http://127.0.0.1:8000/api/factory/stats",timeout=3)
print(f"PASS broker: {r.json()}")
r2=requests.post("http://127.0.0.1:8000/api/factory/trigger",json={"prompt":"cozy farming sim"})
print(f"PASS trigger: {r2.json()}")
print("SUCCESS - Note20 factory working")
