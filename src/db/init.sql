BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS manifest (id TEXT PRIMARY KEY, title TEXT);
CREATE TABLE IF NOT EXISTS manifest_platforms (manifest_id TEXT, platform_id TEXT, execution_type TEXT, emulator_core_id TEXT);
CREATE TABLE IF NOT EXISTS emulator_cores (id TEXT PRIMARY KEY, name TEXT, binary_path TEXT NOT NULL, args_template TEXT NOT NULL, requires_wine INTEGER DEFAULT 0);
DELETE FROM emulator_cores;
INSERT INTO emulator_cores VALUES
('mupen64plus','RetroArch N64','retroarch/retroarch{binExt}','-L cores/mupen64plus_next_libretro{libExt} {rom} -f',0),
('dolphin','Dolphin','dolphin/Dolphin{binExt}','-e {rom} -b',0),
('pcsx2','PCSX2','pcsx2/pcsx2-qtx64{binExt}','-batch {rom}',0),
('rpcs3','RPCS3','rpcs3/rpcs3{binExt}','--no-gui {rom}',0),
('xenia','Xenia','xenia/xenia.exe','{rom}',1);
COMMIT;
