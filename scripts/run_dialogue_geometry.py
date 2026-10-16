"""Capture the source dialogue geometry without writing ROM/RAM or translation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'manifests/source_rom.json').read_text(encoding='utf-8'))
    rom = ROOT / manifest['path']
    assert hashlib.sha256(rom.read_bytes()).hexdigest() == manifest['sha256']
    out = args.output.resolve()
    out.relative_to((ROOT / 'qa').resolve())
    out.mkdir(parents=True, exist_ok=False)
    exe = ROOT / 'tools/mesen-2.1.1/Mesen.exe'
    (exe.parent / 'settings.json').write_bytes((ROOT / 'config/mesen_title_qa.json').read_bytes())
    env = os.environ.copy()
    env['TTA_QA_OUT'] = str(out)
    command = [str(exe), '--testrunner', str(ROOT / 'scripts/capture_dialogue_geometry.lua'),
               str(rom), '--timeout=60', '--enableStdout']
    proc = subprocess.run(command, capture_output=True, env=env,
                          creationflags=subprocess.CREATE_NO_WINDOW, timeout=75)
    (out / 'stdout.txt').write_bytes(proc.stdout)
    (out / 'stderr.txt').write_bytes(proc.stderr)
    report = {'command': command, 'exit_code': proc.returncode,
              'source_sha256': manifest['sha256'],
              'mode': 'cold boot; Start only; no ROM/RAM writes, savestate or A advance',
              'files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in sorted(out.iterdir()) if p.is_file()}}
    (out / 'environment.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    assert proc.returncode == 0
    for frame in (840, 960, 1200, 1440):
        assert (out / f'frame_{frame:04d}_ppu.bin').stat().st_size == 0x4000
    print(json.dumps({'exit_code': proc.returncode, 'output': str(out)}))


if __name__ == '__main__':
    main()
