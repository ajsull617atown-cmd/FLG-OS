#!/data/data/com.termux/files/usr/bin/python
import requests, time, os, json
URLS = ["http://127.0.0.1:8000/stats", "http://127.0.0.1:8000/api/factory/", "http://127.0.0.1:8000/", "http://127.0.0.1:8080/stats"]
while True:
    os.system('clear')
    print("FLG REACTOR LIVE - 6/6 ONLINE - FL-9000 LIVE")
    found=False
    for url in URLS:
        try:
            r=requests.get(url,timeout=1)
            if r.text.strip():
                print(f"Source: {url}")
                j=r.json()
                print(json.dumps(j, indent=2)[:3000])
                found=True
                break
        except:
            pass
    if not found:
        print("NO BROKER - run: python ~/FLG-OS/simple_broker.py &")
    time.sleep(1.5)
