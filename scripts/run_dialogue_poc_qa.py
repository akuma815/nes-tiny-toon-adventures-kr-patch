"""Execute the declared ROM in Mesen, controller input only, preserving older QA."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--rom',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--script',type=Path,default=ROOT/'scripts/capture_dialogue_poc.lua');a=ap.parse_args()
    rom=a.rom.resolve();data=rom.read_bytes();assert data[:4]==b'NES\x1a'
    out=a.output.resolve();out.relative_to((ROOT/'qa').resolve());out.mkdir(parents=True,exist_ok=False)
    exe=ROOT/'tools/mesen-2.1.1/Mesen.exe'
    (exe.parent/'settings.json').write_bytes((ROOT/'config/mesen_title_qa.json').read_bytes())
    env=os.environ.copy();env['TTA_QA_OUT']=str(out)
    script=a.script.resolve();assert script.is_file()
    cmd=[str(exe),'--testrunner',str(script),str(rom),'--timeout=60','--enableStdout']
    p=subprocess.run(cmd,capture_output=True,env=env,creationflags=subprocess.CREATE_NO_WINDOW,timeout=75)
    (out/'stdout.txt').write_bytes(p.stdout);(out/'stderr.txt').write_bytes(p.stderr)
    report={'command':cmd,'exit_code':p.returncode,'rom_sha256':hashlib.sha256(data).hexdigest(),
            'emulator_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),
            'capture_script_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),
            'mode':'cold boot; controller input only; reset after stage; no RAM/ROM writes or savestate',
            'files':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in sorted(out.iterdir()) if x.is_file()}}
    (out/'environment.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    assert p.returncode==0
    assert (out/'frame_3300.png').exists()
    print(json.dumps({'exit_code':p.returncode,'output':str(out)}))

if __name__=='__main__':main()
