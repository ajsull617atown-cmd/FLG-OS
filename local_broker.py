#!/usr/bin/env python3
"""FLG local_broker.py - Phase 2: real telemetry + build trigger."""
import json, os, secrets, subprocess, threading, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
try:
    import psutil
except ImportError:
    psutil = None

HOST, PORT = "127.0.0.1", 8000
DOCS_DIR = Path(os.environ.get("FLG_DOCS", "~/storage/documents/FLG OS/docs")).expanduser()
VAULT = Path(os.environ.get("FLG_VAULT", "~/factoryline_vault.jsonl")).expanduser()
OLLAMA = os.environ.get("FLG_OLLAMA", "http://127.0.0.1:11434")
PROJECT = Path(os.environ.get("FLG_PROJECT", Path(__file__).resolve().parent)).expanduser()
FLG_DIR = Path("~/.flg").expanduser()
BUILD_TIMEOUT = int(os.environ.get("FLG_BUILD_TIMEOUT", "1800"))
START = time.time()
TOKEN = None
_cache = {}

JOBS = {
    "build_py": (".", ["python3", "build.py"]),
    "factoryline_final": (".", ["python3", "build_factoryline_final.py"]),
    "gradle_debug": ("FLG.Bridge.Android", ["sh", "gradlew", "assembleDebug"]),
}

def cached(key, ttl, fn):
    t, v = _cache.get(key, (0, None))
    if time.time() - t > ttl:
        try:
            v = fn()
        except Exception:
            v = None
        _cache[key] = (time.time(), v)
    return v

def docs():
    return sum(1 for _ in DOCS_DIR.rglob("*.md")) if DOCS_DIR.is_dir() else None

def vault():
    if not VAULT.is_file():
        return None
    with VAULT.open("rb") as f:
        return sum(1 for line in f if line.strip())

def ollama():
    with urllib.request.urlopen(OLLAMA + "/api/tags", timeout=1.5) as r:
        return [m["name"] for m in json.load(r).get("models", [])]

def battery():
    out = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=4).stdout
    j = json.loads(out)
    return {"percent": j.get("percentage"), "temp_c": j.get("temperature"), "status": j.get("status")}

def memory():
    if psutil:
        m = psutil.virtual_memory()
        return {"used_gb": round(m.used / 2**30, 2), "total_gb": round(m.total / 2**30, 2), "percent": m.percent}
    d = {}
    for line in open("/proc/meminfo"):
        k, v = line.split(":")
        d[k] = int(v.split()[0]) * 1024
    used = d["MemTotal"] - d["MemAvailable"]
    return {"used_gb": round(used / 2**30, 2), "total_gb": round(d["MemTotal"] / 2**30, 2), "percent": round(100 * used / d["MemTotal"], 1)}

def cpu():
    return psutil.cpu_percent(interval=None) if psutil else None

BUILDS, LOCK = {}, threading.Lock()

def job_problem(name):
    folder, argv = JOBS[name]
    d = PROJECT / folder
    if not d.is_dir():
        return f"folder missing: {d}"
    target = argv[1] if argv[0] in ("python3", "sh") else argv[0]
    if not (d / target).is_file():
        return f"file missing: {d / target}"
    return None

def _run(b):
    folder, argv = JOBS[b["job"]]
    try:
        with open(b["log"], "wb") as log:
            p = subprocess.Popen(argv, cwd=PROJECT / folder, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = p.wait(timeout=BUILD_TIMEOUT)
            except subprocess.TimeoutExpired:
                p.kill()
                code = p.wait()
                b["note"] = "timed out"
        b["exit_code"] = code
        b["state"] = "passed" if code == 0 else "failed"
    except Exception as e:
        b["state"], b["note"] = "failed", str(e)[:200]
    b["finished"] = int(time.time())

def start_build(name):
    with LOCK:
        if any(x["state"] == "running" for x in BUILDS.values()):
            return None, "a build is already running", 409
        problem = job_problem(name)
        if problem:
            return None, problem, 400
        (FLG_DIR / "builds").mkdir(parents=True, exist_ok=True)
        bid = f"{name}_{int(time.time() * 1000)}"
        b = {"build_id": bid, "job": name, "state": "running", "started": int(time.time()), "finished": None, "exit_code": None, "note": None, "log": str(FLG_DIR / "builds" / f"{bid}.log")}
        BUILDS[bid] = b
        for old in list(BUILDS)[:-20]:
            BUILDS.pop(old)
        threading.Thread(target=_run, args=(b,), daemon=True).start()
        return b, None, 202

def public(b, tail=False):
    d = {k: v for k, v in b.items() if k!= "log"}
    d["duration_s"] = (b["finished"] or int(time.time())) - b["started"]
    if tail:
        try:
            with open(b["log"], "rb") as f:
                f.seek(0, 2)
                f.seek(max(0, f.tell() - 3000))
                d["log_tail"] = f.read().decode("utf-8", "replace").splitlines()[-20:]
        except OSError:
            d["log_tail"] = []
    return d

def snapshot():
    d, v = cached("docs", 10, docs), cached("vault", 10, vault)
    o, b, m = cached("ollama", 5, ollama), cached("battery", 15, battery), cached("mem", 2, memory)
    belts = [("broker", True), ("docs", d is not None), ("vault", v is not None), ("ollama", o is not None), ("battery", b is not None), ("memory", m is not None)]
    live = sum(ok for _, ok in belts)
    with LOCK:
        done = list(BUILDS.values())
    running = next((x["build_id"] for x in done if x["state"] == "running"), None)
    return {
        "ts": int(time.time()), "uptime_s": int(time.time() - START),
        "belts": [{"id": i + 1, "name": n, "live": ok} for i, (n, ok) in enumerate(belts)],
        "active": live, "total": len(belts), "active_pct": round(100 * live / len(belts)),
        "docs": d, "vault_apps": v,
        "ollama": {"online": o is not None, "models": o or []},
        "battery": b, "memory": m, "cpu_percent": cached("cpu", 2, cpu),
        "jobs": [n for n in JOBS if job_problem(n) is None],
        "builds": {"running": running, "passed": sum(x["state"] == "passed" for x in done), "failed": sum(x["state"] == "failed" for x in done), "last": public(done[-1]) if done else None},
    }

def load_token():
    t = os.environ.get("FLG_TOKEN")
    if t:
        return t
    f = FLG_DIR / "token"
    if f.is_file():
        return f.read_text().strip()
    FLG_DIR.mkdir(parents=True, exist_ok=True)
    t = secrets.token_urlsafe(24)
    fd = os.open(f, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(t)
    return t

class H(BaseHTTPRequestHandler):
    def _send(self, code, body=None):
        data = b"" if body is None else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-FLG-Token")
        if body is not None:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def do_OPTIONS(self):
        self._send(204)
    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/stats", "/api/factory/stats"):
            self._send(200, snapshot())
        elif path.startswith("/api/factory/build/"):
            with LOCK:
                b = BUILDS.get(path.rsplit("/", 1)[1])
            self._send(200, public(b, tail=True)) if b else self._send(404, {"error": "no such build"})
        elif path == "/health":
            self._send(200, {"ok": True})
        else:
            self._send(404, {"error": "not found"})
    def do_POST(self):
        if self.path.split("?")[0]!= "/api/factory/trigger":
            return self._send(404, {"error": "not found"})
        sent = self.headers.get("X-FLG-Token", "").encode()
        if not TOKEN or not secrets.compare_digest(sent, TOKEN.encode()):
            return self._send(401, {"error": "missing or wrong X-FLG-Token"})
        n = int(self.headers.get("Content-Length") or 0)
        if n > 4096:
            return self._send(413, {"error": "body too large"})
        try:
            data = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            return self._send(400, {"error": "invalid JSON"})
        name = data.get("job") if isinstance(data, dict) else None
        if not isinstance(name, str) or name not in JOBS:
            return self._send(400, {"error": "unknown job", "jobs": list(JOBS)})
        b, err, code = start_build(name)
        self._send(code, public(b) if b else {"error": err})
    def log_message(self, *a):
        pass

if __name__ == "__main__":
    TOKEN = load_token()
    try:
        if psutil:
            psutil.cpu_percent(interval=None)
    except Exception:
        pass
    print(f"FLG broker on http://{HOST}:{PORT} (token: {FLG_DIR / 'token'})")
    ThreadingHTTPServer((HOST, PORT), H).serve_forever()
