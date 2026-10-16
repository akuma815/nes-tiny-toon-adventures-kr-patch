"""Explicit RAM-injected consumer QA. Does not establish native scene reachability."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--build',type=Path,required=True);ap.add_argument('--source',action='store_true');ap.add_argument('--limit',type=int,default=22);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 b=json.loads((a.build/'build_report.json').read_text());pages=json.loads((a.build/'pages.json').read_text(encoding='utf-8'))[:a.limit]
 assembly=json.loads((a.build/'assembly.json').read_text())
 cat=json.loads((ROOT/'extracted/text/dialogue_20261001/dialogue_tokens.json').read_text(encoding='utf-8'))
 if a.source:rom=ROOT/'build/title_kr_ai_004/TinyToon_title_kr_poc.nes'
 else:rom=a.build.resolve()/b['output_rom']
 rows=[]
 for p in pages:
  if a.source:
   visible=[t for t in cat['tokens'] if p['source_start']<=t['offset']<p['source_end'] and t['name']=='glyph' and t['code']!=0]
   start=p['source_start']-0xC010;last=visible[-1]['offset'];pc=0xB276
  else:
   payload=bytes.fromhex(p['payload_hex']);i=0;visible=[]
   while i<len(payload):
    code=payload[i]
    if 0<code<128:visible.append(i)
    i+=3 if code==0xF6 else 2 if code in (0xF7,0xF8) else 1
   start=p['virtual_start'];last=0x24010+start-0xA000+visible[-1];pc=assembly['helper_symbols']['READ_NEW']+2
  rows.append('{id="%s",start=%d,last=%d}'%(p['entry_id'],start,last))
 out=a.output.resolve();out.relative_to(ROOT/'qa');out.mkdir(parents=True,exist_ok=False)
 config='return {pc=%d,bank=%d,pages={%s}}\n'%(pc,11 if a.source else 18,','.join(rows));(out/'harness_config.lua').write_text(config,encoding='ascii')
 exe=ROOT/'tools/mesen-2.1.1/Mesen.exe';(exe.parent/'settings.json').write_bytes((ROOT/'config/mesen_title_qa.json').read_bytes())
 script=ROOT/'scripts/capture_dialogue_full_harness.lua';(out/'capture_script_snapshot.lua').write_bytes(script.read_bytes());env=os.environ.copy();env['TTA_QA_OUT']=str(out)
 cmd=[str(exe),'--testrunner',str(script),str(rom),'--timeout=180','--enableStdout']
 proc=subprocess.run(cmd,capture_output=True,env=env,creationflags=subprocess.CREATE_NO_WINDOW,timeout=195)
 (out/'stdout.txt').write_bytes(proc.stdout);(out/'stderr.txt').write_bytes(proc.stderr)
 report={'command':cmd,'exit_code':proc.returncode,'rom_sha256':hashlib.sha256(rom.read_bytes()).hexdigest(),'emulator_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),
  'capture_script_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'source_baseline':a.source,'pages':len(pages),
  'mode':'Explicit RAM-injected page consumer harness in Shirley scene; no ROM writes; NOT native story/ending/gameplay QA',
  'injected_RAM':['BF/C0 page pointer','07A8 active/stop flag','07A9 cursor','07AA/07AB column/row','07AC/07AD speed','07AE wait','07AF clear-row count','57 font mode 2'],
  'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file()}}
 (out/'environment.json').write_text(json.dumps(report,indent=2)+'\n');assert proc.returncode==0,(proc.returncode,proc.stdout,proc.stderr)
 assert all((out/(p['entry_id']+'.png')).exists() for p in pages);print(json.dumps({'exit_code':proc.returncode,'pages':len(pages),'output':str(out)}))
if __name__=='__main__':main()
