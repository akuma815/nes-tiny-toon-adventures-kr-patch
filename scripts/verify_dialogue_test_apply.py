"""Run the actual Windows CMD/PowerShell helper, including rejection guards."""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--package',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();pkg=a.package.resolve();pkg.relative_to(ROOT/'dist');out=a.output.resolve();out.relative_to(ROOT/'qa/apply');out.mkdir(parents=True,exist_ok=False)
 report=json.loads((pkg/'test_report.json').read_text());source=ROOT/'original/rom/Tiny Toon Adventures (Japan).nes';source_hash=sha(source);assert source_hash==report['source_sha256']
 copy=out/'패치 묶음';copy.mkdir();files=sorted(pkg.iterdir());assert all(p.is_file() for p in files)
 for p in files:shutil.copyfile(p,copy/p.name)
 def run(folder,src,dest=None):
  arguments=[str(folder/'apply.cmd'),str(src)] + ([] if dest is None else [str(dest)])
  assert all('"' not in v for v in arguments)
  command='"'+' '.join('"'+v+'"' for v in arguments)+'"'
  # Pass CMD's complete command line unchanged; list2cmdline escapes interior
  # quotes for CRT argv parsing, which CMD does not use for its /c payload.
  line='"'+os.environ.get('COMSPEC','cmd.exe')+'" /d /s /c '+command
  p=subprocess.run(line,cwd=out,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=60)
  return {'exit_code':p.returncode,'command':command,'stdout':p.stdout.decode('cp949',errors='replace'),'stderr':p.stderr.decode('cp949',errors='replace')}
 valid=run(copy,source);assert valid['exit_code']==0,valid
 applied=copy/'output/TinyToon_ko_test_006.nes';assert applied.stat().st_size==report['output_size'] and sha(applied)==report['output_sha256']
 receipt=json.loads(Path(str(applied)+'.apply.json').read_text(encoding='utf-8-sig'));assert receipt['status']=='PASS' and receipt['output_sha256']==report['output_sha256']
 existing=run(copy,source);assert existing['exit_code']==1 and sha(applied)==report['output_sha256']
 wrong=out/'wrong_source_output.nes';wrong_source=ROOT/'build/title_kr_ai_004/TinyToon_title_kr_poc.nes';wrong_hash=sha(wrong_source)
 badsource=run(copy,wrong_source,wrong);assert badsource['exit_code']==1 and not wrong.exists() and sha(wrong_source)==wrong_hash
 corrupted=out/'corrupt_patch_guard';corrupted.mkdir()
 for p in files:shutil.copyfile(p,corrupted/p.name)
 patch=corrupted/'TinyToon_dialogue_full.ips';data=bytearray(patch.read_bytes());data[20]^=1;patch.write_bytes(data)
 badout=out/'corrupt_patch_output.nes';badpatch=run(corrupted,source,badout);assert badpatch['exit_code']==1 and not badout.exists()
 assert sha(source)==source_hash
 result={'status':'PASS','package':str(pkg),'source_sha256':source_hash,'output_sha256':sha(applied),'output_size':applied.stat().st_size,'output':str(applied),'scope':'Actual apply.cmd under Korean/space-containing Windows paths; valid apply, existing-output refusal, wrong-source refusal, corrupt-patch refusal. Original files unchanged.','checks':{'valid':valid,'existing_output':existing,'wrong_source':badsource,'corrupt_patch':badpatch},'package_contents_sha256':{p.name:sha(p) for p in files},'source_unchanged':True,'receipt':receipt}
 (out/'apply_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':'PASS','output_sha256':sha(applied),'checks':4}))
if __name__=='__main__':main()
