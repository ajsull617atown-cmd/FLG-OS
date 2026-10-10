from __future__ import annotations
import json, os, py_compile, shutil
from pathlib import Path

VERSION='4.1.2'
ROOT=Path('FL-Desktop-Commander-Rewired')
MODULES = [
    'Executive Summary',
    'Vision and Goals',
    'Competitive Analysis',
    'Platform Architecture',
    'Frontend Architecture',
    'Desktop Client',
    'Mobile Companion',
    'Web Portal',
    'API Gateway',
    'Authentication System',
    'User Profiles',
    'Game Library Engine',
    'Metadata Engine',
    'Launcher Engine',
    'Store Connectors',
    'Steam Connector',
    'Epic Connector',
    'Xbox Connector',
    'GOG Connector',
    'Battle.net Connector',
    'EA Connector',
    'Ubisoft Connector',
    'Riot Connector',
    'Emulation Framework',
    'Achievement Hub',
    'Social Platform',
    'Friends System',
    'Chat Architecture',
    'Collections Engine',
    'Search System',
    'Recommendation Engine',
    'AI Assistant',
    'Theme Engine',
    'Theme Marketplace',
    'Plugin SDK',
    'Plugin Marketplace',
    'Mod Management',
    'Cloud Sync',
    'Save Management',
    'Analytics Platform',
    'Telemetry',
    'Database Architecture',
    'Entity Schema',
    'Caching Layer',
    'File Storage',
    'Security Architecture',
    'Permissions',
    'Encryption',
    'CI CD Pipeline',
    'Testing Strategy',
    'Monitoring',
    'Performance Targets',
    'Accessibility',
    'Monetization',
    'Subscription Tiers',
    'Marketplace Economy',
    'Developer Portal',
    'REST APIs',
    'GraphQL APIs',
    'Event Bus',
    'Microservices',
    'Deployment Strategy',
    'Windows Support',
    'Linux Support',
    'Steam Deck Support',
    'Roadmap Phase 1',
    'Roadmap Phase 2',
    'Roadmap Phase 3',
    'Roadmap Phase 4',
    'Roadmap Phase 5',
]

BACKEND_INIT=f'''"""FactoryLine Gaming OS backend package."""\n__version__ = "{VERSION}"\n'''

BACKEND=r'''from __future__ import annotations
import asyncio, datetime as dt, hashlib, json, logging, os, pathlib, re, secrets, sqlite3, subprocess, sys, time, urllib.parse
from contextlib import asynccontextmanager
from typing import Any
import httpx, psutil
from fastapi import Cookie, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
try: import pynvml
except Exception: pynvml=None
VERSION='4.1.2'; APP_NAME='FactoryLine Gaming OS'
logging.basicConfig(level=os.getenv('LOG_LEVEL','INFO'),format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')
log=logging.getLogger('factoryline_os')

def bundle_dir():
    if getattr(sys,'frozen',False) and hasattr(sys,'_MEIPASS'): return pathlib.Path(sys._MEIPASS)
    return pathlib.Path(__file__).resolve().parent.parent
BASE_DIR=bundle_dir(); FRONTEND_DIR=BASE_DIR/'frontend'
DATA_DIR=pathlib.Path(os.getenv('FL_DATA_DIR',str(pathlib.Path.home()/'.factoryline-gaming-os')))
BACKUP_DIR=DATA_DIR/'snapshots'; DB_PATH=DATA_DIR/'factoryline.db'; SESSION_SECRET=os.getenv('FL_SESSION_SECRET')
if not SESSION_SECRET: raise RuntimeError('FL_SESSION_SECRET is required.')
MODULES = 'Executive Summary|Vision and Goals|Competitive Analysis|Platform Architecture|Frontend Architecture|Desktop Client|Mobile Companion|Web Portal|API Gateway|Authentication System|User Profiles|Game Library Engine|Metadata Engine|Launcher Engine|Store Connectors|Steam Connector|Epic Connector|Xbox Connector|GOG Connector|Battle.net Connector|EA Connector|Ubisoft Connector|Riot Connector|Emulation Framework|Achievement Hub|Social Platform|Friends System|Chat Architecture|Collections Engine|Search System|Recommendation Engine|AI Assistant|Theme Engine|Theme Marketplace|Plugin SDK|Plugin Marketplace|Mod Management|Cloud Sync|Save Management|Analytics Platform|Telemetry|Database Architecture|Entity Schema|Caching Layer|File Storage|Security Architecture|Permissions|Encryption|CI CD Pipeline|Testing Strategy|Monitoring|Performance Targets|Accessibility|Monetization|Subscription Tiers|Marketplace Economy|Developer Portal|REST APIs|GraphQL APIs|Event Bus|Microservices|Deployment Strategy|Windows Support|Linux Support|Steam Deck Support|Roadmap Phase 1|Roadmap Phase 2|Roadmap Phase 3|Roadmap Phase 4|Roadmap Phase 5'.split('|')

def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def gid(store,key): return f"{store.lower()}-{hashlib.sha256(f'{store}:{key}'.encode()).hexdigest()[:20]}"

class DB:
    def __init__(self,p): self.p=p
    def cx(self): self.p.parent.mkdir(parents=True,exist_ok=True); c=sqlite3.connect(self.p); c.row_factory=sqlite3.Row; return c
    def init(self):
        with self.cx() as c: c.executescript("""PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS games(id TEXT PRIMARY KEY,name TEXT NOT NULL,store TEXT NOT NULL,source TEXT NOT NULL,install_path TEXT,executable TEXT,app_id TEXT,launch_uri TEXT,discovered_at TEXT NOT NULL,metadata_json TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,event_type TEXT NOT NULL,payload_json TEXT NOT NULL,created_at TEXT NOT NULL);""")
    def replace(self,games):
        with self.cx() as c:
            c.execute('DELETE FROM games')
            for g in games: c.execute('INSERT INTO games VALUES(?,?,?,?,?,?,?,?,?,?)',(g['id'],g['name'],g['store'],g['source'],g.get('install_path'),g.get('executable'),g.get('app_id'),g.get('launch_uri'),g['discovered_at'],json.dumps(g,ensure_ascii=False)))
    def games(self):
        with self.cx() as c: rows=c.execute('SELECT metadata_json FROM games ORDER BY lower(name)').fetchall()
        return [json.loads(r[0]) for r in rows]
    def event(self,t,p):
        with self.cx() as c: c.execute('INSERT INTO events(event_type,payload_json,created_at) VALUES(?,?,?)',(t,json.dumps(p),now()))
db=DB(DB_PATH)

def game(store,name,source,install=None,exe=None,appid=None,uri=None,meta=None):
    return {'id':gid(store,appid or install or name),'name':name,'store':store,'source':source,'install_path':install,'executable':exe,'app_id':appid,'launch_uri':uri,'discovered_at':now(),'metadata':meta or {}}

def steam():
    roots=[]
    if sys.platform=='win32': roots += [pathlib.Path(os.getenv('PROGRAMFILES(X86)',''))/'Steam',pathlib.Path(os.getenv('PROGRAMFILES',''))/'Steam']
    roots += [pathlib.Path.home()/'.steam/steam',pathlib.Path.home()/'.local/share/Steam']
    out=[]; seen=set()
    for sr in roots:
        lf=sr/'steamapps/libraryfolders.vdf'
        if not lf.is_file(): continue
        try: text=lf.read_text(errors='replace')
        except OSError: continue
        paths=[str(sr)]+re.findall(r'"path"\s*"([^"]+)"',text,re.I)
        for p in paths:
            md=pathlib.Path(p)/'steamapps'
            for f in md.glob('appmanifest_*.acf') if md.is_dir() else []:
                try: raw=f.read_text(errors='replace')
                except OSError: continue
                a=re.search(r'"appid"\s*"(\d+)"',raw); n=re.search(r'"name"\s*"([^"]+)"',raw); i=re.search(r'"installdir"\s*"([^"]+)"',raw)
                if not a or not n: continue
                key=f"{a.group(1)}:{p}"
                if key in seen: continue
                seen.add(key); install=str(md/'common'/i.group(1)) if i else None
                out.append(game('Steam',n.group(1),str(f),install=install,appid=a.group(1),uri=f"steam://rungameid/{a.group(1)}"))
    return out

def epic():
    root=pathlib.Path(os.getenv('PROGRAMDATA',str(pathlib.Path.home())))/'Epic/EpicGamesLauncher/Data/Manifests'; out=[]
    if not root.is_dir(): return out
    for f in root.glob('*.item'):
        try: d=json.loads(f.read_text())
        except (OSError,json.JSONDecodeError): continue
        n=d.get('DisplayName') or d.get('AppName')
        if n: out.append(game('Epic',n,str(f),d.get('InstallLocation'),d.get('LaunchExecutable'),d.get('AppName'),meta=d))
    return out

def gog():
    roots=[]
    if sys.platform=='win32': roots += [pathlib.Path(os.getenv('PROGRAMDATA',''))/'GOG.com',pathlib.Path(os.getenv('PROGRAMFILES(X86)',''))/'GOG Galaxy']
    roots += [pathlib.Path.home()/'GOG Games',pathlib.Path.home()/'Games/GOG']; out=[]; seen=set()
    for r in roots:
        if not r.is_dir(): continue
        try: children=list(r.iterdir())
        except OSError: continue
        for c in children:
            if c.is_dir() and str(c.resolve()).lower() not in seen:
                seen.add(str(c.resolve()).lower()); out.append(game('GOG',c.name,str(c),str(c)))
    return out

def factoryline():
    roots=[pathlib.Path(x) for x in [os.getenv('FL_LIBRARY_DIR',''),str(DATA_DIR/'games'),str(BASE_DIR/'games')] if x]; out=[]; seen=set()
    for r in roots:
        if not r.is_dir(): continue
        try: children=list(r.iterdir())
        except OSError: continue
        for c in children:
            if c.is_dir() and str(c.resolve()).lower() not in seen:
                seen.add(str(c.resolve()).lower()); out.append(game('FactoryLine',c.name,str(c),str(c)))
    return out

def scan_library():
    providers={'Steam':steam,'Epic':epic,'GOG':gog,'FactoryLine':factoryline}; allg=[]; status={}
    for name,fn in providers.items():
        try:
            g=fn(); allg.extend(g); status[name]={'status':'REAL','count':len(g)}
        except Exception as e: log.exception('provider failed'); status[name]={'status':'ERROR','count':0,'error':str(e)}
    unique={g['id']:g for g in allg}; games=sorted(unique.values(),key=lambda x:x['name'].lower()); db.replace(games)
    return {'status':'SUCCESS','mode':'REAL','games':games,'providers':status,'count':len(games),'timestamp':now()}

class GPU:
    def __init__(self): self.ready=False; self.handles=[]; self.error=None
    def init(self):
        if pynvml is None: self.error='pynvml is not installed'; return
        try:
            pynvml.nvmlInit(); self.handles=[pynvml.nvmlDeviceGetHandleByIndex(i) for i in range(pynvml.nvmlDeviceGetCount())]; self.ready=bool(self.handles)
            if not self.ready: self.error='No NVIDIA GPU devices detected.'
        except Exception as e: self.error=str(e); self.handles=[]; self.ready=False
    def nvml(self):
        if not self.ready: raise RuntimeError(self.error or 'NVML unavailable')
        out=[]
        for i,h in enumerate(self.handles):
            n=pynvml.nvmlDeviceGetName(h); n=n.decode(errors='replace') if isinstance(n,bytes) else str(n); u=pynvml.nvmlDeviceGetUtilizationRates(h); t=pynvml.nvmlDeviceGetTemperature(h,pynvml.NVML_TEMPERATURE_GPU); m=pynvml.nvmlDeviceGetMemoryInfo(h)
            out.append({'index':i,'name':n,'load':int(u.gpu),'temperature':int(t),'memory_used_mb':int(m.used/1048576),'memory_total_mb':int(m.total/1048576),'source':'pynvml','status':'REAL','error':None})
        return out
    def smi(self):
        r=subprocess.run(['nvidia-smi','--query-gpu=index,name,utilization.gpu,temperature.gpu,memory.used,memory.total','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=5,check=True); out=[]
        for line in r.stdout.splitlines():
            p=[x.strip() for x in line.split(',')]
            if len(p)==6: out.append({'index':int(p[0]),'name':p[1],'load':int(p[2]),'temperature':int(p[3]),'memory_used_mb':int(p[4]),'memory_total_mb':int(p[5]),'source':'nvidia-smi','status':'FALLBACK','error':None})
        if not out: raise RuntimeError('nvidia-smi returned no GPU rows')
        return out
    def rocm(self):
        r=subprocess.run(['rocm-smi','--showuse','--showtemp','--showmemuse','--csv'],capture_output=True,text=True,timeout=5,check=True); return [{'index':0,'name':'AMD GPU','load':None,'temperature':None,'memory_used_mb':None,'memory_total_mb':None,'source':'rocm-smi','status':'FALLBACK','error':'Raw ROCm output detected; normalized metrics unavailable.','raw':r.stdout[:4000]}]
    def stats(self):
        for fn in (self.nvml,self.smi,self.rocm):
            try:
                r=fn()
                if r: return r
            except Exception: pass
        return [{'index':0,'name':'UNAVAILABLE','load':None,'temperature':None,'memory_used_mb':None,'memory_total_mb':None,'source':'none','status':'UNAVAILABLE','error':self.error or 'No supported GPU provider available.'}]
    def shutdown(self):
        if self.ready and pynvml:
            try: pynvml.nvmlShutdown()
            except Exception: log.exception('NVML shutdown failed')
        self.ready=False; self.handles=[]
gpu=GPU()

class Chat(BaseModel): prompt:str=Field(min_length=1,max_length=8000); model:str=Field(default='mistral',min_length=1,max_length=100)
class Launch(BaseModel): game_id:str=Field(min_length=1,max_length=200)
class Services:
    def __init__(self): self.boot=time.time(); self.github={'status':'NOT_INITIALIZED','repositories':{},'error':None}
    def metrics(self):
        gs=gpu.stats(); p=gs[0]; m=psutil.virtual_memory(); return {'cpu':psutil.cpu_percent(None),'ram':m.percent,'ram_used_mb':int(m.used/1048576),'ram_total_mb':int(m.total/1048576),'gpu':p['load'],'gpu_name':p['name'],'gpu_temperature':p['temperature'],'gpu_memory_used_mb':p['memory_used_mb'],'gpu_memory_total_mb':p['memory_total_mb'],'gpu_source':p['source'],'gpu_status':p['status'],'gpu_error':p['error'],'gpus':gs,'uptime_seconds':max(0,int(time.time()-self.boot)),'timestamp':now()}
services=Services()

def auth(v):
    if not v or not secrets.compare_digest(v,SESSION_SECRET): raise HTTPException(401,'Unauthorized')

async def github():
    owner=os.getenv('GITHUB_OWNER','FactoryLineGaming'); token=os.getenv('GITHUB_TOKEN'); h={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':APP_NAME};
    if token: h['Authorization']=f'Bearer {token}'
    repos={}
    try:
        async with httpx.AsyncClient(timeout=10,follow_redirects=True) as c:
            for page in range(1,11):
                r=await c.get(f'https://api.github.com/orgs/{owner}/repos',headers=h,params={'per_page':100,'page':page,'sort':'pushed'}); r.raise_for_status(); batch=r.json()
                for x in batch:
                    if x.get('name'): repos[x['name']]={'branch':x.get('default_branch'),'pushed_at':x.get('pushed_at'),'visibility':x.get('visibility'),'language':x.get('language'),'url':x.get('html_url')}
                if len(batch)<100: break
        return {'status':'REAL','repositories':repos,'error':None}
    except Exception as e: return {'status':'ERROR','repositories':{},'error':str(e)}

@asynccontextmanager
async def lifespan(app):
    DATA_DIR.mkdir(parents=True,exist_ok=True); BACKUP_DIR.mkdir(parents=True,exist_ok=True); db.init(); gpu.init()
    if os.getenv('FL_SKIP_GITHUB_REFRESH','0')!='1': services.github=await github()
    yield; gpu.shutdown()
app=FastAPI(title=APP_NAME,version=VERSION,lifespan=lifespan,docs_url=None,redoc_url=None,openapi_url=None); app.mount('/static',StaticFiles(directory=FRONTEND_DIR),name='static')

@app.get('/health')
async def health(request:Request): auth(request.headers.get('x-fl-session')); return {'status':'ok','service':'factoryline-gaming-os','version':VERSION}
@app.get('/')
async def root(token:str):
    auth(token); r=RedirectResponse('/app',303); r.set_cookie('fl_session',SESSION_SECRET,httponly=True,samesite='strict',secure=False); return r
@app.get('/app')
async def page(fl_session:str|None=Cookie(default=None)): auth(fl_session); return FileResponse(FRONTEND_DIR/'index.html')
@app.get('/api/v1/blueprint/status')
async def blueprint(fl_session:str|None=Cookie(default=None)):
    auth(fl_session); return {'name':'Universal Gaming Hub','version':VERSION,'count':len(MODULES),'modules':[{'name':x,'core':'registered','service':'registered','extension':'registered'} for x in MODULES]}
@app.get('/api/v1/modules')
async def modules(fl_session:str|None=Cookie(default=None)): auth(fl_session); return {'modules':MODULES,'count':len(MODULES)}
@app.post('/api/v1/library/real/scan')
async def scan(fl_session:str|None=Cookie(default=None)): auth(fl_session); return scan_library()
@app.get('/api/v1/library/real')
async def real(fl_session:str|None=Cookie(default=None)):
    auth(fl_session); g=db.games(); return scan_library() if not g else {'status':'SUCCESS','mode':'REAL','games':g,'count':len(g),'timestamp':now()}
@app.get('/api/v1/library')
async def library(fl_session:str|None=Cookie(default=None)): auth(fl_session); g=db.games(); return {'status':'SUCCESS','mode':'REAL','library':g,'count':len(g),'github':services.github['repositories'],'github_error':services.github['error']}
@app.get('/api/v1/search')
async def search(q:str='',fl_session:str|None=Cookie(default=None)):
    auth(fl_session); q=q.lower().strip(); g=db.games(); return {'results':[x for x in g if not q or q in x['name'].lower() or q in x['store'].lower()]}
@app.post('/api/v1/games/launch')
async def launch(req:Launch,fl_session:str|None=Cookie(default=None)):
    auth(fl_session); g={x['id']:x for x in db.games()}.get(req.game_id)
    if not g: raise HTTPException(404,'Game not found')
    uri=g.get('launch_uri')
    if uri and urllib.parse.urlparse(uri).scheme in {'steam','com.epicgames.launcher'}:
        if sys.platform=='win32': subprocess.Popen(['cmd','/c','start','','%s'%uri],creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        else: subprocess.Popen(['xdg-open',uri])
        db.event('game.launch',{'id':g['id']}); return {'status':'SUCCESS','mode':'URI','game':g['name']}
    exe=g.get('executable'); install=g.get('install_path')
    if exe and install:
        p=(pathlib.Path(install)/exe).resolve(); root=pathlib.Path(install).resolve()
        if root in p.parents and p.is_file(): subprocess.Popen([str(p)],cwd=str(root)); db.event('game.launch',{'id':g['id']}); return {'status':'SUCCESS','mode':'EXECUTABLE','game':g['name']}
    return {'status':'NOT_LAUNCHABLE','game':g['name'],'store':g['store']}
@app.get('/api/v1/gpu')
async def gpu1(fl_session:str|None=Cookie(default=None)): auth(fl_session); return {'gpu':services.metrics()['gpus'][0]}
@app.get('/api/v1/gpus')
async def gpus(fl_session:str|None=Cookie(default=None)): auth(fl_session); return {'gpus':services.metrics()['gpus']}
@app.get('/api/v1/themes')
async def themes(fl_session:str|None=Cookie(default=None)): auth(fl_session); return {'status':'SUCCESS','themes':[{'id':'factory-red','name':'Factory Red','enabled':True},{'id':'control-room','name':'Control Room','enabled':False}]}
@app.post('/api/v1/github/refresh')
async def gh(fl_session:str|None=Cookie(default=None)): auth(fl_session); services.github=await github(); return {'status':services.github['status'],'repositories':len(services.github['repositories']),'error':services.github['error']}
@app.post('/api/v1/ai/chat')
async def ai(req:Chat,fl_session:str|None=Cookie(default=None)):
    auth(fl_session); base=os.getenv('OLLAMA_URL','http://127.0.0.1:11434');
    try:
        async with httpx.AsyncClient(timeout=60) as c:
            r=await c.post(base.rstrip('/')+'/api/generate',json={'model':req.model,'prompt':req.prompt,'stream':False}); r.raise_for_status(); d=r.json(); return {'status':'SUCCESS','model':req.model,'response':d.get('response','')}
    except httpx.HTTPError as e: raise HTTPException(502,'The local Ollama service is unavailable.') from e
@app.post('/api/v1/snapshots')
async def snap(fl_session:str|None=Cookie(default=None)):
    auth(fl_session); t=dt.datetime.now(dt.timezone.utc); f=BACKUP_DIR/f"snapshot-{t.strftime('%Y%m%dT%H%M%SZ')}.json"; data={'created_at':t.isoformat(),'version':VERSION,'library':db.games(),'github':services.github,'telemetry':services.metrics(),'blueprint_modules':MODULES}; await asyncio.to_thread(f.write_text,json.dumps(data,indent=2),'utf-8'); return {'status':'SUCCESS','file':f.name,'created_at':data['created_at']}
@app.websocket('/ws/telemetry')
async def ws(sock:WebSocket):
    port=os.getenv('FL_PORT','8000'); origin=sock.headers.get('origin',''); allowed={f'http://127.0.0.1:{port}',f'http://localhost:{port}'}
    if origin and origin not in allowed: await sock.close(1008); return
    cookie=sock.cookies.get('fl_session')
    if not cookie or not secrets.compare_digest(cookie,SESSION_SECRET): await sock.close(1008); return
    await sock.accept()
    try:
        while True: await sock.send_json({'type':'TELEMETRY_UPDATE','system':await asyncio.to_thread(services.metrics)}); await asyncio.sleep(1)
    except (WebSocketDisconnect,RuntimeError): pass
'''

SERVER=r'''import multiprocessing,os,uvicorn
from backend.app import app
def main():
    multiprocessing.freeze_support(); uvicorn.run(app,host='127.0.0.1',port=int(os.getenv('FL_PORT','8000')),reload=False,workers=1,access_log=False,log_level=os.getenv('LOG_LEVEL','info').lower())
if __name__=='__main__': main()
'''
DEV=r'''import os,secrets,subprocess,sys
def main():
    e=os.environ.copy(); e['FL_SESSION_SECRET']=secrets.token_hex(32); e['FL_PORT']='8000'; e['FL_SKIP_GITHUB_REFRESH']='1'; subprocess.run([sys.executable,'server_entry.py'],env=e,check=True)
if __name__=='__main__': main()
'''
MAIN=r'''const {app,BrowserWindow,dialog}=require('electron');const {spawn}=require('child_process');const crypto=require('crypto');const net=require('net');const path=require('path');let child=null,win=null,quitting=false;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function port(){return new Promise((res,rej)=>{const s=net.createServer();s.listen(0,'127.0.0.1',()=>{const p=s.address().port;s.close(()=>res(p))});s.on('error',rej)})}
function logs(c){c.stdout?.on('data',d=>console.log('[backend]',d.toString()));c.stderr?.on('data',d=>console.error('[backend]',d.toString()));c.on('error',e=>console.error('Backend error',e));c.on('exit',(code,signal)=>{console.log('Backend exited',{code,signal});if(!quitting){dialog.showErrorBox('FactoryLine Gaming OS',`Backend stopped. Exit code: ${code??'unknown'}`);quitting=true;app.quit()}})}
function start(p,s){const env={...process.env,FL_PORT:String(p),FL_SESSION_SECRET:s};const c=app.isPackaged?spawn(path.join(process.resourcesPath,'fl_os_server.exe'),[],{env,windowsHide:true}):spawn(process.platform==='win32'?'python':'python3',['server_entry.py'],{cwd:__dirname,env,windowsHide:true});logs(c);return c}
async function wait(p,s,c){for(let i=0;i<80;i++){if(c.exitCode!==null)throw Error(`Backend exited with code ${c.exitCode}`);try{const r=await fetch(`http://127.0.0.1:${p}/health`,{headers:{'x-fl-session':s}});if(r.ok&&((await r.json()).service==='factoryline-gaming-os'))return}catch(_){}await sleep(250)}throw Error('FactoryLine backend startup timed out.')}
async function create(){const p=await port(),s=crypto.randomBytes(32).toString('hex');child=start(p,s);await wait(p,s,child);win=new BrowserWindow({width:1440,height:900,minWidth:980,minHeight:680,backgroundColor:'#050505',title:'FactoryLine Gaming OS v4.1.2',autoHideMenuBar:true,webPreferences:{nodeIntegration:false,contextIsolation:true,sandbox:true}});const origin=`http://127.0.0.1:${p}`;win.webContents.on('will-navigate',(e,u)=>{try{if(new URL(u).origin!==origin)e.preventDefault()}catch(_){e.preventDefault()}});win.webContents.setWindowOpenHandler(()=>({action:'deny'}));await win.loadURL(`${origin}/?token=${encodeURIComponent(s)}`);win.on('closed',()=>win=null)}
function stop(){if(child&&!child.killed)try{child.kill()}catch(_){}child=null}app.whenReady().then(create).catch(e=>{dialog.showErrorBox('FactoryLine Gaming OS',e.message);quitting=true;stop();app.quit()});app.on('window-all-closed',()=>{quitting=true;stop();if(process.platform!=='darwin')app.quit()});app.on('before-quit',()=>{quitting=true;stop()});
'''

HTML=r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'self';script-src 'self';style-src 'self';connect-src 'self' ws://127.0.0.1:* ws://localhost:*;img-src 'self' data:;object-src 'none';base-uri 'none';frame-ancestors 'none';"><title>FactoryLine Gaming OS</title><link rel="stylesheet" href="/static/styles.css"></head><body><header><b>FACTORYLINE GAMING OS</b><span id="connection">CONNECTING</span></header><nav><button data-tab="dashboard">CONTROL ROOM</button><button data-tab="library">LIBRARY</button><button data-tab="ai">AI</button><button data-tab="ecosystem">ECOSYSTEM</button></nav><main><section id="dashboard" class="view active"><div class="cols"><article class="panel hero"><div class="core">FL</div><h1>UNIVERSAL GAMING HUB</h1><p id="blueprint">Loading...</p></article><article class="panel"><h2>HARDWARE TELEMETRY</h2><div id="telemetry"></div></article></div></section><section id="library" class="view"><article class="panel"><div class="head"><h2>REAL LOCAL LIBRARY</h2><button id="scan">SCAN STORES</button></div><p id="libraryStatus">Loading...</p><div id="games"></div></article></section><section id="ai" class="view"><article class="panel narrow"><h2>LOCAL AI ASSISTANT</h2><label>Model</label><input id="model" value="mistral" maxlength="100"><label>Prompt</label><textarea id="prompt" maxlength="8000"></textarea><button id="send">SEND</button><pre id="answer">AI ready.</pre></article></section><section id="ecosystem" class="view"><div class="cols"><article class="panel"><h2>BLUEPRINT MODULES</h2><div id="modules"></div></article><article class="panel"><h2>SYSTEM</h2><button id="snapshot">CREATE SNAPSHOT</button><p id="snapshotStatus">Ready.</p><button id="github">REFRESH GITHUB</button><p id="githubStatus">Ready.</p></article></div></section></main><script src="/static/app.js"></script></body></html>'''
CSS=r'''*{box-sizing:border-box}:root{--bg:#050505;--panel:rgba(18,0,0,.84);--line:rgba(255,30,30,.4);--red:#ff3030;--muted:#999}body{margin:0;min-height:100vh;padding:18px;background:radial-gradient(circle at 50% 20%,rgba(255,0,0,.12),transparent 60%),var(--bg);color:#fff;font-family:"Segoe UI",Arial,sans-serif}header,.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;box-shadow:0 0 28px rgba(255,0,0,.12)}header{padding:14px 18px;display:flex;justify-content:space-between}header span,h1,h2,.value{color:var(--red)}nav{display:flex;gap:8px;margin:14px 0;flex-wrap:wrap}button,input,textarea{width:100%;padding:10px;border-radius:7px;border:1px solid var(--red);background:#080808;color:#fff}button{cursor:pointer;color:var(--red);font-weight:700}nav button{width:auto}.view{display:none}.view.active{display:block}.cols{display:grid;grid-template-columns:1fr 1fr;gap:14px}.panel{padding:18px}.hero{min-height:360px;text-align:center}.core{margin:20px auto;width:170px;height:170px;border-radius:50%;display:grid;place-items:center;border:3px solid var(--red);box-shadow:0 0 70px rgba(255,0,0,.8);background:radial-gradient(circle at 30% 30%,#ff2020,#050505 68%);font-size:54px;font-weight:900}.head{display:flex;justify-content:space-between;gap:12px}.head button{width:auto}.metric,.game,.module{padding:9px;margin:6px 0;background:rgba(255,255,255,.045);border-left:3px solid var(--red);border-radius:6px}.metric{display:flex;justify-content:space-between}.game{display:flex;justify-content:space-between;gap:10px}.game button{width:auto}.module{font-size:13px;color:#ddd}label{display:block;margin-top:12px;color:var(--muted)}textarea{min-height:160px}pre{white-space:pre-wrap;max-height:340px;overflow:auto}.narrow{max-width:850px;margin:auto}@media(max-width:900px){.cols{grid-template-columns:1fr}}'''
JS=r'''"use strict";const $=id=>document.getElementById(id);async function api(u,o={}){const r=await fetch(u,{...o,headers:{"Content-Type":"application/json",...(o.headers||{})}});const d=await r.json().catch(()=>({detail:`HTTP ${r.status}`}));if(!r.ok)throw Error(d.detail||`HTTP ${r.status}`);return d}function metric(a,b){const x=document.createElement('div');x.className='metric';const l=document.createElement('span');l.textContent=a;const v=document.createElement('strong');v.className='value';v.textContent=String(b);x.append(l,v);return x}async function blueprint(){const d=await api('/api/v1/blueprint/status');$('blueprint').textContent=`${d.count} ecosystem modules registered`;$('modules').replaceChildren(...d.modules.map(m=>{const x=document.createElement('div');x.className='module';x.textContent=m.name;return x}))}function telemetry(s){$('telemetry').replaceChildren(...[['CPU',`${Math.round(s.cpu||0)}%`],['RAM',`${Math.round(s.ram||0)}%`],['GPU',s.gpu_name||'UNAVAILABLE'],['GPU LOAD',s.gpu==null?'--':`${Math.round(s.gpu)}%`],['GPU TEMP',s.gpu_temperature==null?'--':`${s.gpu_temperature} °C`],['GPU SOURCE',s.gpu_source||'none'],['GPU STATUS',s.gpu_status||'UNAVAILABLE'],['VRAM',s.gpu_memory_total_mb==null?'--':`${s.gpu_memory_used_mb}/${s.gpu_memory_total_mb} MB`],['UPTIME',`${Math.floor((s.uptime_seconds||0)/86400)}d`]].map(x=>metric(...x)))}function ws(){const p=location.protocol==='https:'?'wss':'ws';const s=new WebSocket(`${p}://${location.host}/ws/telemetry`);s.onopen=()=>$('connection').textContent='LIVE';s.onmessage=e=>{try{const m=JSON.parse(e.data);if(m.type==='TELEMETRY_UPDATE')telemetry(m.system)}catch(_){}};s.onclose=()=>{ $('connection').textContent='RECONNECTING';setTimeout(ws,2000)}}async function library(){const d=await api('/api/v1/library/real');$('libraryStatus').textContent=`${d.count} real local games discovered`;$('games').replaceChildren(...d.games.map(g=>{const x=document.createElement('div');x.className='game';const i=document.createElement('div');const n=document.createElement('b');n.textContent=g.name;const m=document.createElement('small');m.textContent=`${g.store} • ${g.source}`;i.append(n,m);const b=document.createElement('button');b.textContent='LAUNCH';b.disabled=!(g.launch_uri||(g.install_path&&g.executable));b.onclick=async()=>{b.disabled=true;try{const r=await api('/api/v1/games/launch',{method:'POST',body:JSON.stringify({game_id:g.id})});b.textContent=r.status==='SUCCESS'?'STARTED':'UNAVAILABLE'}catch(e){b.textContent='ERROR';b.title=e.message}};x.append(i,b);return x}))} $('scan').onclick=async()=>{ $('scan').disabled=true;try{await api('/api/v1/library/real/scan',{method:'POST'});await library()}finally{$('scan').disabled=false}};$('send').onclick=async()=>{try{const r=await api('/api/v1/ai/chat',{method:'POST',body:JSON.stringify({prompt:$('prompt').value,model:$('model').value})});$('answer').textContent=r.response||'(Empty response)'}catch(e){$('answer').textContent=e.message}};$('snapshot').onclick=async()=>{try{$('snapshotStatus').textContent=`Saved: ${(await api('/api/v1/snapshots',{method:'POST'})).file}`}catch(e){$('snapshotStatus').textContent=e.message}};$('github').onclick=async()=>{try{const r=await api('/api/v1/github/refresh',{method:'POST'});$('githubStatus').textContent=r.error||`${r.repositories} repositories loaded`}catch(e){$('githubStatus').textContent=e.message}};document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.view').forEach(v=>v.classList.remove('active'));document.getElementById(b.dataset.tab).classList.add('active')});Promise.all([blueprint(),library()]).catch(e=>$('libraryStatus').textContent=e.message);ws();'''

TEST=r'''import os
os.environ['FL_SESSION_SECRET']='factoryline-test-secret';os.environ['FL_SKIP_GITHUB_REFRESH']='1';os.environ['FL_DATA_DIR']='.test-factoryline-data'
from fastapi.testclient import TestClient
from backend.app import app
S='factoryline-test-secret'
def test_unauthorized_health():
    with TestClient(app) as c: assert c.get('/health').status_code==401
def test_health():
    with TestClient(app) as c:
        r=c.get('/health',headers={'x-fl-session':S}); assert r.status_code==200; assert r.json()['version']=='4.1.2'
def test_blueprint():
    with TestClient(app) as c:
        c.get('/',params={'token':S}); r=c.get('/api/v1/blueprint/status'); assert r.status_code==200; assert r.json()['count']==70
def test_gpu_contract():
    with TestClient(app) as c:
        c.get('/',params={'token':S}); d=c.get('/api/v1/gpus').json(); assert 'gpus' in d and 'status' in d['gpus'][0]
'''

SPEC=r'''from PyInstaller.utils.hooks import collect_all,collect_submodules
pynvml_data,pynvml_binaries,pynvml_hidden=collect_all('pynvml'); uvicorn_hidden=collect_submodules('uvicorn')
a=Analysis(['server_entry.py'],pathex=['.'],binaries=pynvml_binaries,datas=pynvml_data+[('frontend','frontend')],hiddenimports=list(dict.fromkeys(pynvml_hidden+uvicorn_hidden+['backend','backend.app'])),hookspath=[],hooksconfig={},runtime_hooks=[],excludes=[],noarchive=False)
p=PYZ(a.pure)
exe=EXE(p,a.scripts,a.binaries,a.datas,[],name='fl_os_server',debug=False,bootloader_ignore_signals=False,strip=False,upx=True,console=False)
'''
PACKAGE=json.dumps({'name':'fl-desktop-commander-rewired','version':VERSION,'description':'FactoryLine Gaming OS Universal Gaming Hub desktop control center','main':'main.js','scripts':{'start':'electron .','test:python':'python -m pytest','pack:python':'pyinstaller --clean --noconfirm fl_os_server.spec','build:directory':'npm run test:python && npm run pack:python && electron-builder --win dir','build':'npm run test:python && npm run pack:python && electron-builder --win x64'},'devDependencies':{'electron':'^38.0.0','electron-builder':'^26.0.0'},'build':{'appId':'com.factoryline.gamingos','productName':'FactoryLine Gaming OS','directories':{'output':'dist-installer'},'win':{'target':[{'target':'nsis','arch':['x64']}]},'files':['main.js','package.json'],'extraResources':[{'from':'dist/fl_os_server.exe','to':'fl_os_server.exe'}]}},indent=2)+'\n'
REQ='''fastapi==0.116.1\nhttpx==0.28.1\npsutil==7.0.0\npydantic==2.11.7\npynvml==12.0.0\nuvicorn[standard]==0.35.0\npyinstaller==6.15.0\npytest==8.3.3\n'''
WORKFLOW='''name: Windows Build Artifact\non:\n  push:\n    branches: [main]\n  workflow_dispatch:\njobs:\n  build:\n    runs-on: windows-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n        with:\n          python-version: "3.11"\n          cache: pip\n      - uses: actions/setup-node@v4\n        with:\n          node-version: "20"\n          cache: npm\n      - run: python -m pip install --upgrade pip\n      - run: pip install -r requirements.txt\n      - run: npm ci\n      - run: npm run build\n        env:\n          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}\n      - shell: pwsh\n        run: |\n          if (-not (Test-Path "dist/fl_os_server.exe")) { throw "Python executable missing" }\n          if (-not (Get-ChildItem "dist-installer/*.exe" -ErrorAction SilentlyContinue)) { throw "Installer missing" }\n      - uses: actions/upload-artifact@v4\n        with:\n          name: factoryline-gaming-os-windows\n          path: dist-installer/*.exe\n'''
README=f'''# FactoryLine Gaming OS: Rewired Edition\n\n**Version {VERSION}**\n\nUnified local desktop gaming hub based on the supplied V4.1 Rewired project and Universal Gaming Hub blueprint.\n\nImplemented: Electron desktop shell, FastAPI service, authenticated localhost session, CSP/navigation controls, real CPU/RAM telemetry, multi-GPU provider fallback, real Steam/Epic/GOG/FactoryLine discovery, SQLite persistence, validated game launch targets, GitHub metadata, local Ollama, snapshots, themes, search, WebSocket telemetry, 70 blueprint module registrations, tests, CI, PyInstaller and Electron Builder packaging.\n\n## Development\n\n```powershell\npython -m venv .venv\n.venv\\Scripts\\Activate.ps1\npip install -r requirements.txt\nnpm install\nnpm start\n```\n\n## Build\n\n`npm run build`\n\nPyInstaller: `dist\\fl_os_server.exe`\nPackaged resource: `resources\\fl_os_server.exe`\nInstaller: `dist-installer\\*.exe`\n\nThe blueprint names 70 ecosystem areas. This implementation registers all 70 and implements the local desktop/library/telemetry/API/security foundation; external services are not marked connected merely by registration.\n'''
IGNORE='''__pycache__/\n*.pyc\n.venv/\nnode_modules/\ndist/\nbuild/\ndist-installer/\n.pytest_cache/\n.test-factoryline-data/\n.factoryline-gaming-os/\n.env\n'''

FILES={'backend/__init__.py':BACKEND_INIT,'backend/app.py':BACKEND,'server_entry.py':SERVER,'dev_server.py':DEV,'main.js':MAIN,'frontend/index.html':HTML,'frontend/styles.css':CSS,'frontend/app.js':JS,'tests/test_backend.py':TEST,'fl_os_server.spec':SPEC,'package.json':PACKAGE,'requirements.txt':REQ,'.github/workflows/build.yml':WORKFLOW,'README.md':README,'.gitignore':IGNORE}

def validate(root):
    required=list(FILES)
    missing=[x for x in required if not (root/x).is_file()]
    if missing: raise RuntimeError(f'Missing files: {missing}')
    json.loads((root/'package.json').read_text())
    for p in root.rglob('*.py'): py_compile.compile(str(p),doraise=True)
    html=(root/'frontend/index.html').read_text(); js=(root/'frontend/app.js').read_text(); main=(root/'main.js').read_text(); back=(root/'backend/app.py').read_text()
    checks={'CSP':'Content-Security-Policy' in html,'sandbox':'sandbox:true' in main,'contextIsolation':'contextIsolation:true' in main,'nav guard':'will-navigate' in main,'window guard':'setWindowOpenHandler' in main,'no innerHTML':'innerHTML' not in js,'auth compare':'compare_digest' in back,'WS origin':'allowed=' in back}
    bad=[k for k,v in checks.items() if not v]
    if bad: raise RuntimeError(f'Security checks failed: {bad}')

def write_workspace():
    root=ROOT
    root.mkdir(parents=True,exist_ok=True)
    for rel,content in FILES.items():
        p=root/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(content.strip()+'\n',encoding='utf-8'); print('[+] Generated',rel)
    validate(root)
    print(f'\n[SUCCESS] FactoryLine Gaming OS Rewired/V10 Unified {VERSION} generated at {root.resolve()}')
    print('Next: cd',root.name,'; python -m venv .venv ; pip install -r requirements.txt ; npm install ; npm start')

if __name__=='__main__': write_workspace()
