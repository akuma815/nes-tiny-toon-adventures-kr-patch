"""Run source-only dialogue trace with isolated Mesen settings and no ROM writes."""
import argparse, hashlib, json, os, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    manifest=json.loads((ROOT/'manifests/source_rom.json').read_text(encoding='utf-8'))
    rom=ROOT/manifest['path'];assert hashlib.sha256(rom.read_bytes()).hexdigest()==manifest['sha256']
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    exe=ROOT/'tools/mesen-2.1.1/Mesen.exe';lua=ROOT/'scripts/trace_dialogue.lua'
    (exe.parent/'settings.json').write_bytes((ROOT/'config/mesen_title_qa.json').read_bytes())
    env=os.environ.copy();env['TTA_QA_OUT']=str(out)
    cmd=[str(exe),'--testrunner',str(lua),str(rom),'--timeout=60','--enableStdout']
    p=subprocess.run(cmd,capture_output=True,env=env,creationflags=subprocess.CREATE_NO_WINDOW,timeout=75)
    (out/'stdout.txt').write_bytes(p.stdout);(out/'stderr.txt').write_bytes(p.stderr)
    report={'command':cmd,'exit_code':p.returncode,'source_sha256':manifest['sha256'],'mode':'cold boot, controller input only; no savestate or RAM/ROM writes','files':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in out.iterdir() if x.is_file()}}
    (out/'environment.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    assert p.returncode==0
    print(json.dumps({'exit_code':p.returncode,'output':str(out)}))
if __name__=='__main__':main()
