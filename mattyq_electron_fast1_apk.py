from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import subprocess, json, shutil, uuid
app = FastAPI(title="MATTYq REAL")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
BUILD_ROOT = Path.home() / "storage/downloads/builds"
BUILD_ROOT.mkdir(parents=True, exist_ok=True)
class BuildReq(BaseModel):
    electron_src: str
    app_name: str
    belt_id: str = "belt_1"
@app.get("/api/factory/stats")
def stats():
    return {"apks": len(list(BUILD_ROOT.rglob("*.apk")))}
@app.post("/build")
def build(req: BuildReq):
    job_id = uuid.uuid4().hex[:8]
    belt_dir = BUILD_ROOT / f"{req.belt_id}_{job_id}"
    src = Path(req.electron_src)
    if src.exists(): shutil.copytree(src, belt_dir, dirs_exist_ok=True)
    else: belt_dir.mkdir(parents=True, exist_ok=True)
    apk = belt_dir / "app/build/outputs/apk/debug/app-debug.apk"
    return {"job_id": job_id, "apk_path": str(apk), "status": "built" if apk.exists() else "building"}
