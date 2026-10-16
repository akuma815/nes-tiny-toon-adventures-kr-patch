"""Ending-root font consumer in native cinema; does not reach the game ending."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--rom',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 rom=a.rom.resolve();out=a.output.resolve();out.relative_to(ROOT/'qa');out.mkdir(parents=True,exist_ok=False)
 base=(ROOT/'scripts/capture_dialogue_attract.lua').read_text()
 injection="""
local injectionLog=assert(io.open(out..'/cinema_injections.csv','wb'))
injectionLog:write('frame,old_root,new_root\\n')
emu.addMemoryCallback(function()
 local s=emu.getState();local root=s['cpu.a']
 if root>=12 and root<=15 then
  emu.setState({['cpu.a']=root+10})
  injectionLog:write(string.format('%d,%d,%d\\n',frame,root,root+10));injectionLog:flush()
 end
end,emu.callbackType.exec,0xF7E0,0xF7E0,emu.cpuType.nes)
"""
 base=base.replace('local frame=0','local frame=0\n'+injection)
 script=out/'capture_script_snapshot.lua';script.write_text(base,encoding='utf-8')
 exe=ROOT/'tools/mesen-2.1.1/Mesen.exe';(exe.parent/'settings.json').write_bytes((ROOT/'config/mesen_title_qa.json').read_bytes());env=os.environ.copy();env['TTA_QA_OUT']=str(out)
 cmd=[str(exe),'--testrunner',str(script),str(rom),'--timeout=60','--enableStdout'];p=subprocess.run(cmd,capture_output=True,env=env,creationflags=subprocess.CREATE_NO_WINDOW,timeout=75)
 (out/'stdout.txt').write_bytes(p.stdout);(out/'stderr.txt').write_bytes(p.stderr)
 report={'exit_code':p.returncode,'command':cmd,'rom_sha256':hashlib.sha256(rom.read_bytes()).hexdigest(),'emulator_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'capture_script_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),
  'mode':'Four CPU A substitutions at native F7E0: intro roots12..15 become ending roots22..25. Native cinema rendering/IRQ/font mode1, intro portraits; no RAM/ROM writes. NOT native game-ending reachability or full gameplay QA',
  'files':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in sorted(out.iterdir()) if x.is_file()}}
 (out/'environment.json').write_text(json.dumps(report,indent=2)+'\n');assert p.returncode==0,(p.returncode,p.stdout,p.stderr);assert (out/'frame_4200.png').exists();print(json.dumps({'status':'PASS','output':str(out)}))
if __name__=='__main__':main()
