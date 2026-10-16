"""Capture an explicit controller timeline without changing RAM/CPU/ROM/state."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--rom',type=Path,required=True);ap.add_argument('--plan',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--source',action='store_true');ap.add_argument('--carrots',type=int,choices=range(100));a=ap.parse_args()
 rom=a.rom.resolve();out=a.output.resolve();out.relative_to(ROOT/'qa/dialogue');out.mkdir(parents=True,exist_ok=False)
 plan=json.loads(a.plan.read_text(encoding='utf-8'));(out/'controller_plan.json').write_bytes(a.plan.read_bytes())
 asm=json.loads((ROOT/'build/dialogue_full_006/assembly.json').read_text());pc=0xB276 if a.source else asm['helper_symbols']['READ_NEW']+2;bank=11 if a.source else 18
 inputs=[]
 for s in plan['inputs']:
  buttons=','.join(json.dumps(v) for v in s['buttons']);extra='' if 'period' not in s else ',period=%d,hold=%d'%(s['period'],s['hold'])
  if 'phase' in s:extra+=',phase=%d'%s['phase']
  if 'auto_jump' in s:extra+=',auto_jump=%d'%s['auto_jump']
  inputs.append('{first=%d,last=%d,buttons={%s}%s}'%(s['first'],s['last'],buttons,extra))
 captures=','.join('[%d]=true'%v for v in plan.get('captures',[]))
 override='' if a.carrots is None else ',carrots=%d'%a.carrots
 (out/'gameplay_config.lua').write_text('return {readpc=%d,readbank=%d,stop=%d,interval=%d,captures={%s},inputs={%s}%s}\n'%(pc,bank,plan['stop'],plan['interval'],captures,','.join(inputs),override))
 script=out/'capture_script_snapshot.lua';script.write_bytes((ROOT/'scripts/capture_dialogue_gameplay.lua').read_bytes())
 exe=ROOT/'tools/mesen-2.1.1/Mesen.exe';(exe.parent/'settings.json').write_bytes((ROOT/'config/mesen_title_qa.json').read_bytes())
 env=os.environ.copy();env['TTA_QA_OUT']=str(out);cmd=[str(exe),'--testrunner',str(script),str(rom),'--timeout=120','--enableStdout']
 p=subprocess.run(cmd,capture_output=True,env=env,creationflags=subprocess.CREATE_NO_WINDOW,timeout=135)
 (out/'stdout.txt').write_bytes(p.stdout);(out/'stderr.txt').write_bytes(p.stderr)
 scope='Cold boot, explicit controller-only plan; no RAM/ROM writes, CPU substitutions or savestates. Exploratory gameplay, not automatically a passed scene test.' if a.carrots is None else 'Cold boot and same controller route; ONE explicit $07E1 carrot counter RAM write at frame5800. Native Hamton room/dispatcher/rendering, controlled branch input; NOT native carrot collection for this value. No ROM writes, CPU substitutions or savestates.'
 report={'exit_code':p.returncode,'command':cmd,'rom_sha256':sha(rom),'emulator_sha256':sha(exe),'capture_script_sha256':sha(script),'mode':scope,'carrot_override':a.carrots,'files':{x.name:sha(x) for x in sorted(out.iterdir()) if x.is_file()}}
 (out/'environment.json').write_text(json.dumps(report,indent=2)+'\n');assert p.returncode==0,(p.returncode,p.stdout,p.stderr);print(json.dumps({'exit_code':0,'output':str(out)}))
if __name__=='__main__':main()
