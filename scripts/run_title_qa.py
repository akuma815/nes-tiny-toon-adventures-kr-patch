"""Run an isolated Mesen 2.1.1 headless cold-boot/input/reset capture."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--rom',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    exe=ROOT/'tools/mesen-2.1.1/Mesen.exe';script=ROOT/'scripts/capture_title.lua'
    config=ROOT/'config/mesen_title_qa.json'
    (exe.parent/'settings.json').write_bytes(config.read_bytes())
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    env=os.environ.copy();env['TTA_QA_OUT']=str(output)
    command=[str(exe),'--testrunner',str(script),str(args.rom.resolve()),'--timeout=60','--enableStdout']
    result=subprocess.run(command,capture_output=True,env=env,creationflags=subprocess.CREATE_NO_WINDOW,timeout=75)
    (output/'stdout.txt').write_bytes(result.stdout);(output/'stderr.txt').write_bytes(result.stderr)
    report={'emulator':'Mesen 2.1.1','exe_path':str(exe),'exe_sha256':sha(exe),'rom_path':str(args.rom.resolve()),'rom_sha256':sha(args.rom),
      'lua_sha256':sha(script),'config_sha256':sha(config),'command':command,'exit_code':result.returncode,'mode':'headless test runner; no savestate',
      'input_sequence':'Start at 240..247 and 600..607, A for 8 frames every 120 frames from 900; reset at 1500; stop at 2100',
      'files':{p.name:sha(p) for p in output.iterdir() if p.is_file()},
      'scope':'Captured emulator execution; visual inspection and comparisons reported separately. Audio listening not performed.'}
    (output/'environment.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    assert result.returncode==0,f'Mesen failed: {result.returncode}; see stdout/stderr'
    assert (output/'frame_2100.png').is_file()
    print(json.dumps({k:v for k,v in report.items() if k not in ('files','command')},indent=2))
if __name__=='__main__':main()
