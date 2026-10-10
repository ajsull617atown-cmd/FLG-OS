from fastapi import FastAPI
import uvicorn, time
app = FastAPI()
@app.get("/api/factory/stats")
def stats():
    return {"belt_speed": 1.8, "rpm": 2840, "raw_cost_per_apk": 0.042, "status": "local Note20 Ultra"}
@app.post("/api/factory/trigger")
def trigger(data: dict):
    return {"build_id": f"note20_{int(time.time())}", "selected_gpu": "local-note20-12gb", "raw_compute_cost": 0.00, "projected_margin": 14.99, "telemetry_stream": "wss://local"}
