"""Run all registered roots through the real engine, injecting only initializer A."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--build',type=Path,required=True);ap.add_argument('--source',action='store_true');ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 b=json.loads((a.build/'build_report.json').read_text());asm=json.loads((a.build/'assembly.json').read_text())
 rom=ROOT/'build/title_kr_ai_004/TinyToon_title_kr_poc.nes' if a.source else a.build.resolve()/b['output_rom']
 out=a.output.resolve();out.relative_to(ROOT/'qa');out.mkdir(parents=True,exist_ok=False)
 (out/'roots_config.lua').write_text('return {pc=%d,bank=%d}\n'%((0xB276 if a.source else asm['helper_symbols']['READ_NEW']+2),(11 if a.source else 18)),encoding='ascii')
 exe=ROOT/'tools/mesen-2.1.1/Mesen.exe';(exe.parent/'settings.json').write_bytes((ROOT/'config/mesen_title_qa.json').read_bytes())
 script=ROOT/'scripts/capture_dialogue_roots.lua';(out/'capture_script_snapshot.lua').write_bytes(script.read_bytes());env=os.environ.copy();env['TTA_QA_OUT']=str(out)
 cmd=[str(exe),'--testrunner',str(script),str(rom),'--timeout=180','--enableStdout'];p=subprocess.run(cmd,capture_output=True,env=env,creationflags=subprocess.CREATE_NO_WINDOW,timeout=195)
 (out/'stdout.txt').write_bytes(p.stdout);(out/'stderr.txt').write_bytes(p.stderr)
 report={'exit_code':p.returncode,'command':cmd,'rom_sha256':hashlib.sha256(rom.read_bytes()).hexdigest(),'emulator_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'capture_script_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),
  'mode':'26 roots; only CPU A changed at native B20E Shirley initializer. No RAM/ROM writes. Forced root consumer QA, NOT native scene/gameplay QA',
  'files':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in sorted(out.iterdir()) if x.is_file()}}
 (out/'environment.json').write_text(json.dumps(report,indent=2)+'\n');assert p.returncode==0,(p.returncode,p.stdout,p.stderr)
 assert all((out/('root_%02d.png'%i)).exists() for i in range(26));print(json.dumps({'status':'PASS','roots':26,'output':str(out)}))
if __name__=='__main__':main()
