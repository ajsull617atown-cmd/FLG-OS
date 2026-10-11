#!/data/data/com.termux/files/usr/bin/python
import requests, json, time
URLS = ["http://127.0.0.1:8000/stats", "http://127.0.0.1:8000/api/factory/"]
print("FLG REACTOR LIVE - NO BLINK - 6/6 ONLINE")
while True:
    for url in URLS:
        try:
            r = requests.get(url, timeout=1)
            if r.text.strip():
                j = r.json()
                print(f"\n[{time.strftime('%H:%M:%S')}] {j.get('status')} | {j.get('total_throughput')}")
                for b in j.get('belts',[])[-3:]:
                    print(f"  BELT {b.get('id')} {b.get('status')} rpm:{b.get('rpm')}")
                break
        except:
            pass
    time.sleep(2)
