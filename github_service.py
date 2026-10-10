import json
print("FLG FACTORY STARTING...")
with open("factoryline_vault.jsonl", "w") as f:
    for i in range(1, 1001):
        f.write(json.dumps({"id": f"FLG-{i:04d}", "name": f"Tool {i}", "res": "7680x4320"}) + "\n")
print("DONE - BUILT 1000 LINES")
