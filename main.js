const { app, BrowserWindow, ipcMain } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const Database = require('better-sqlite3');
const isWin = process.platform === 'win32';
function getEmuBase(){ return app.isPackaged ? path.join(process.resourcesPath,'emulators') : path.join(process.cwd(),'build','emulators'); }
function parseArgs(tpl,rom){ return tpl.replaceAll('{binExt}',isWin?'.exe':'').replaceAll('{libExt}',isWin?'.dll':'.so').replaceAll('{rom}','__ROM__').match(/(?:[^\s"]+|"[^"]*")+/g).map(s=>s==='__ROM__'?rom:s.replace(/"/g,'')); }
function executeLocalRuntime(manifestId){
  const db = new Database(path.join(app.getPath('userData'),'flg.db'));
  const item = db.prepare(`SELECT mp.*, ec.* FROM manifest_platforms mp JOIN emulator_cores ec ON mp.emulator_core_id=ec.id WHERE mp.manifest_id=?`).get(manifestId);
  const emuBase = getEmuBase();
  let binary = path.join(emuBase, item.binary_path.replace('{binExt}', isWin?'.exe':''));
  const romPath = path.join(process.cwd(),'vault','games',item.platform_id,manifestId);
  let args = parseArgs(item.args_template, romPath);
  let cmd=binary; if(!isWin && item.requires_wine){ args=[binary,...args]; cmd='wine'; }
  spawn(cmd,args,{detached:true,stdio:'ignore'}).unref();
  return {launched:true};
}
app.whenReady().then(()=>{ const win=new BrowserWindow({width:1920,height:1080,webPreferences:{nodeIntegration:true,contextIsolation:false}}); win.loadFile('src/renderer/RedHUD/RedHUD.html'); ipcMain.handle('launch-game',(_,id)=>executeLocalRuntime(id)); });
