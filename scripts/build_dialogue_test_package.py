"""Assemble a ROM-free local test bundle from the already verified006 artifacts."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();out=a.output.resolve();out.relative_to(ROOT/'dist');assert not out.exists();archive=out.with_suffix('.zip');assert not archive.exists()
 b=json.loads((ROOT/'build/dialogue_full_006/build_report.json').read_text());target=b['output_sha256'];assert target=='6d834cdde925dd808ef6d911ebf2f13f5a88e440c9da4bfc50b424035309483d'
 reports={}
 for kind in ('static','abi','stage_guard','runtime','cinema','visual','hamton','hamton_visual'):
  p=ROOT/f'qa/reports/dialogue_full_006_{kind}.json';r=json.loads(p.read_text(encoding='utf-8'));assert r['status']=='PASS' and r.get('build_sha256',r.get('output_sha256'))==target;reports[kind]={'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
 patch=ROOT/'build/dialogue_full_006/TinyToon_dialogue_full.ips';assert sha(patch)=='ff6b10f01a323519780bcc2a3f320de8a7ec4a426df00088fc12fbc496f4826c'
 source=ROOT/'original/rom/Tiny Toon Adventures (Japan).nes';assert sha(source)==b['source_sha256']
 out.mkdir(parents=True)
 inputs={'TinyToon_dialogue_full.ips':patch,'apply.ps1':ROOT/'scripts/apply_dialogue_test.ps1','README_KO.md':ROOT/'docs/README_DIALOGUE_TEST_KO.md','OFL.md':ROOT/'workspace/fonts/galmuri7_8x8/OFL.md'}
 for name,p in inputs.items():
  if name=='README_KO.md':
   text=p.read_text(encoding='utf-8').replace('(../dist/dialogue_test_002/test_report.json)','(test_report.json)').replace('(../workspace/fonts/galmuri7_8x8/OFL.md)','(OFL.md)');(out/name).write_bytes(text.encode('utf-8'))
  else:(out/name).write_bytes(p.read_bytes())
 cmd='@echo off\r\nif "%~1"=="" (\r\n  echo Drag the supported Japan NES ROM onto this file.\r\n  exit /b 2\r\n)\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0apply.ps1" "%~1" "%~2"\r\nexit /b %errorlevel%\r\n'
 (out/'apply.cmd').write_bytes(cmd.encode('ascii'))
 report={'kind':'local_test_package','status':'BUILD_VERIFIED_APPLY_PENDING','date':'2026-10-04','source_size':262160,'source_sha256':b['source_sha256'],'output_size':524304,'output_sha256':target,'patch_sha256':sha(patch),'font':'User selected Galmuri7 native8x8 PNG; OFL notice included','translated_registered_blocks':22,'CSV_needs_review':22,'verification_reports':reports,'scope':'Native intro/Shirley/Hamton30 and first-stage progress; controlled Hamton29; injected all-page/all-root/cinema consumers. Full playthrough/native ending/other-stage hints/hardware/other emulators/final translation review pending.','contents_sha256':{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()},'excluded':['source ROM','patched ROM','extracted images','font PNG/TTF','emulator']}
 (out/'test_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'output':str(out),'scope':'Local test bundle. ZIP creation waits for real Windows apply verification.'}))
if __name__=='__main__':main()
