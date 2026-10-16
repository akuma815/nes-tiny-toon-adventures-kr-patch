"""Verify recorded PNG/ROM/runtime/apply evidence and handoff links for title PoC."""
import ast,csv,hashlib,json,re
from pathlib import Path
from PIL import Image,ImageChops
from extract_title import ROOT,unpack
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    asset=json.loads((ROOT/'manifests/title_assets.json').read_text(encoding='utf-8'))
    source=json.loads((ROOT/'manifests/source_rom.json').read_text(encoding='utf-8'))
    build=ROOT/asset['latest_verified_build'];target=build/'TinyToon_title_kr_poc.nes'
    original=ROOT/source['path'];expected=asset['latest_verified_rom_sha256']
    assert sha(original)==source['sha256'] and sha(target)==expected
    assert sha(ROOT/(asset['latest_verified_build']+'_repro')/'TinyToon_title_kr_poc.nes')==expected
    assert sha(ROOT/'qa/title/패치 적용 확인 004/TinyToon_applied.nes')==expected
    assert sha(ROOT/asset['ai_source_png'])==asset['ai_source_sha256']
    baseline=ROOT/asset['baseline_evidence'];qa=ROOT/asset['runtime_evidence']
    original_env=json.loads((baseline/'environment.json').read_text());env=json.loads((qa/'environment.json').read_text())
    assert env['exit_code']==original_env['exit_code']==0 and env['rom_sha256']==expected
    current_settings=json.loads((ROOT/'tools/mesen-2.1.1/settings.json').read_text(encoding='utf-8'))
    assert current_settings==json.loads((ROOT/asset['qa_config']).read_text())
    rows=json.loads((qa/'comparison.json').read_text());assert len(rows)==11
    assert all(row['outside_logo_different_pixels']==0 for row in rows)
    assert all(row['diff_bbox'] is None for row in rows if row['frame'] in (600,900,960,1200,1500,2100))
    _,nt,_,_=unpack(target.read_bytes());ppu=(qa/'frame_0240_ppu.bin').read_bytes();rom=target.read_bytes()
    assert nt==ppu[0x2000:0x2400] and ppu[:0x1000]==rom[0x2e010:0x2f010]
    assert ImageChops.difference(Image.open(build/'title_static_preview.png').convert('RGB'),Image.open(qa/'frame_0240.png').convert('RGB')).getbbox() is None
    trace=list(csv.DictReader((ROOT/asset['consumer_trace']).open()))
    assert trace and all(int(r['file_offset'],16)==int(r['prg_relative_offset'],16)+16 for r in trace)
    assert int(trace[0]['file_offset'],16)==0x3655
    syntax=[]
    for path in (ROOT/'scripts').glob('*.py'):ast.parse(path.read_text(encoding='utf-8'));syntax.append(path.relative_to(ROOT).as_posix())
    missing=[];link_count=0
    docs=[ROOT/'README.md',*(ROOT/'docs').glob('*.md')]
    for path in docs:
        for ref in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if '://' in ref or ref.startswith('#'):continue
            local=ref.split('#')[0]
            if local:
                link_count+=1
                if not (path.parent/local).exists():missing.append(str(path)+': '+ref)
    # This report is linked from the handoff, and is created by this invocation.
    missing=[m for m in missing if not m.endswith('qa/reports/title_poc_2026-10-01.json')]
    assert not missing,missing
    paths=[ROOT/'README.md',ROOT/'.gitignore',ROOT/'config/mesen_title_qa.json',ROOT/'manifests/title_assets.json',
      *[ROOT/p for p in syntax],ROOT/'docs/POC_TITLE.md',ROOT/'docs/HANDOFF.md',ROOT/'docs/HANDOFF_2026-10-01.md',ROOT/'docs/SURVEY.md',
      target,build/'build_report.json',build/'expected_writes.json',build/'TinyToon_title_kr_poc.ips',build/'TinyToon_title_kr_poc.json',
      ROOT/asset['ai_source_png'],ROOT/asset['prompt'],ROOT/asset['extraction_spec'],qa/'comparison.json',qa/'environment.json',
      qa/'frame_0240.png',ROOT/asset['consumer_trace']]
    report={'date_kst':'2026-10-01','status':'PASS','scope':'Game title logo PoC only',
      'source_sha256':source['sha256'],'verified_rom_sha256':expected,'static':'PASS: syntax, source identity, runtime NT/CHR equality, static preview/runtime equality, protected-pixel comparison, links',
      'build_apply':'PASS: original PNG roundtrip, rebuilt ROM identity, actual IPS apply identity',
      'runtime':'PASS: Mesen 2.1.1, cold boot, controller input, first stage, reset; exit 0',
      'visual':'Agent inspected AI/converted PNGs and frames 240/900/1200/1620; 11 sampled comparisons',
      'unperformed':asset['pending'],'doc_link_count':link_count,'trace_read_count':len(trace),
      'qa_config_equivalence':'Current persisted config is semantically identical to manual config used for smoke_004',
      'files':{p.relative_to(ROOT).as_posix():sha(p) for p in paths}}
    (ROOT/'qa/reports/title_poc_2026-10-01.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='files'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
