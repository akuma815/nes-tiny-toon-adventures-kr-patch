"""Native cold/attract execution with exact script snapshot and honest metadata."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--rom',type=Path,required=True);ap.add_argument('--scenario',choices=['cold','attract'],required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 rom=a.rom.resolve();out=a.output.resolve();out.relative_to(ROOT/'qa');out.mkdir(parents=True,exist_ok=False)
 script=ROOT/'scripts'/('capture_dialogue_full.lua' if a.scenario=='cold' else 'capture_dialogue_attract.lua')
 snapshot=out/'capture_script_snapshot.lua';snapshot.write_bytes(script.read_bytes())
 exe=ROOT/'tools/mesen-2.1.1/Mesen.exe';(exe.parent/'settings.json').write_bytes((ROOT/'config/mesen_title_qa.json').read_bytes());env=os.environ.copy();env['TTA_QA_OUT']=str(out)
 cmd=[str(exe),'--testrunner',str(snapshot),str(rom),'--timeout=60','--enableStdout'];p=subprocess.run(cmd,capture_output=True,env=env,creationflags=subprocess.CREATE_NO_WINDOW,timeout=75)
 (out/'stdout.txt').write_bytes(p.stdout);(out/'stderr.txt').write_bytes(p.stderr)
 mode='Cold boot, Start/right/left/A controller input; stage entry and reset at3060; stop3300' if a.scenario=='cold' else 'Cold boot; no controller input; natural six-page intro/title/attract demo; stop4200'
 report={'exit_code':p.returncode,'command':cmd,'rom_sha256':hashlib.sha256(rom.read_bytes()).hexdigest(),'emulator_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'capture_script_sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest(),
  'mode':mode+'; no RAM/ROM writes, CPU changes or savestates','scenario':a.scenario,'files':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in sorted(out.iterdir()) if x.is_file()}}
 (out/'environment.json').write_text(json.dumps(report,indent=2)+'\n');assert p.returncode==0,(p.returncode,p.stdout,p.stderr)
 assert (out/('frame_3300.png' if a.scenario=='cold' else 'frame_4200.png')).exists();print(json.dumps({'exit_code':0,'scenario':a.scenario,'output':str(out)}))
if __name__=='__main__':main()
