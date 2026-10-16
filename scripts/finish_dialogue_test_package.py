"""Seal a ROM-free test ZIP only after the real helper passes its apply gate."""
import argparse,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--package',type=Path,required=True);ap.add_argument('--apply-report',type=Path,required=True);a=ap.parse_args();pkg=a.package.resolve();pkg.relative_to(ROOT/'dist');archive=pkg.with_suffix('.zip');assert not archive.exists()
 proof=json.loads(a.apply_report.read_text(encoding='utf-8'));assert proof['status']=='PASS' and Path(proof['package'])==pkg
 expected={'README_KO.md','OFL.md','TinyToon_dialogue_full.ips','apply.cmd','apply.ps1','test_report.json'};assert {p.name for p in pkg.iterdir()}==expected
 for name,h in proof['package_contents_sha256'].items():assert sha(pkg/name)==h,name
 p=pkg/'test_report.json';r=json.loads(p.read_text());assert r['status']=='BUILD_VERIFIED_APPLY_PENDING' and proof['source_sha256']==r['source_sha256'] and proof['output_sha256']==r['output_sha256']
 r['status']='LOCAL_TEST_BUILD_AND_WINDOWS_APPLY_VERIFIED';r['Windows_apply_verification']={'report':a.apply_report.resolve().relative_to(ROOT).as_posix(),'sha256':sha(a.apply_report),'valid_apply':True,'original_unchanged':True,'guards':['existing output','wrong source','corrupt patch']}
 p.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
 with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
  for p in sorted(pkg.iterdir()):assert p.is_file() and p.name in expected;z.write(p,p.name)
 with zipfile.ZipFile(archive) as z:
  assert set(z.namelist())==expected and z.testzip() is None
  for p in pkg.iterdir():assert z.read(p.name)==p.read_bytes()
 out=ROOT/'qa/reports'/('dialogue_test_package_'+pkg.name+'.json');assert not out.exists()
 report={'status':'PASS','kind':'local_test_package','package':pkg.relative_to(ROOT).as_posix(),'archive':archive.relative_to(ROOT).as_posix(),'archive_sha256':sha(archive),'output_sha256':r['output_sha256'],'contents_sha256':{p.name:sha(p) for p in sorted(pkg.iterdir())},'ROM_free':True,'actual_Windows_apply_verified':True,'scope':r['scope']}
 out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':'PASS','zip':str(archive),'zip_sha256':sha(archive),'ROM_free':True}))
if __name__=='__main__':main()
