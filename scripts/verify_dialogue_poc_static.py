"""Audit PoC Expected Writes, append extent, rebuild/apply and protected sources."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--build',type=Path,required=True)
    ap.add_argument('--rebuild',type=Path,required=True);ap.add_argument('--applied',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    source=json.loads((ROOT/'manifests/source_rom.json').read_text(encoding='utf-8'))
    rom=(ROOT/source['path']).read_bytes();assert sha(rom)==source['sha256'] and len(rom)==source['size_bytes']
    report=json.loads((a.build/'build_report.json').read_text(encoding='utf-8'))
    target=(a.build/report['output_rom']).read_bytes();assert sha(target)==report['output_sha256']
    assert len(target)==len(rom)+8192 and target[5]==17 and target[:5]==rom[:5] and target[6:16]==rom[6:16]
    rebuild=(a.rebuild/report['output_rom']).read_bytes();assert rebuild==target
    assert a.applied.read_bytes()==target
    plan=json.loads((a.build/'expected_writes.json').read_text(encoding='utf-8'))
    registered={};allowed_new={'chr_extent':(5,1),'text_chr_selection':(0x1FEA0,20),
                               'JP_175A9':(0x175A9,37),'poc_font_banks':(0x40010,8192)}
    for w in plan:
        offset=w['file_offset'];final=bytes.fromhex(w['final_hex']);assert len(final)==w['length']
        assert target[offset:offset+len(final)]==final
        if not w['owner'].startswith('preserved_'):
            assert (offset,w['length'])==allowed_new[w['owner']]
        if w.get('kind')=='append':
            assert offset==len(rom) and w['expected_source_size']==len(rom) and not w['expected_hex']
        else:assert rom[offset:offset+w['length']]==bytes.fromhex(w['expected_hex'])
        for i in range(offset,offset+w['length']):
            assert i not in registered,'Write overlap';registered[i]=w['owner']
    diff=[i for i in range(len(target)) if i>=len(rom) or target[i]!=rom[i]]
    assert all(i in registered for i in diff)
    title_dir=ROOT/'build/title_kr_ai_004';title=(title_dir/'TinyToon_title_kr_poc.nes').read_bytes()
    assert sha(title)==report['title_base_sha256']
    assert target[0x20010:0x40010]==title[0x20010:0x40010]
    assert target[0x17443:0x175A9]==rom[0x17443:0x175A9]
    assert target[0x175CE:0x17845]==rom[0x175CE:0x17845]
    assert [i for i in range(20) if rom[0x1FEA0+i]!=target[0x1FEA0+i]]==[1,3,11,13]
    font=ROOT/'workspace/fonts/galmuri7_8x8'
    font_report=json.loads((font/'font_source.json').read_text(encoding='utf-8'))
    for name,value in font_report['source_sha256'].items():assert sha((font/name).read_bytes())==value
    assert font_report['source_sha256']['Galmuri7_8x8.png']==report['font_png_sha256']
    preserved={'workspace/translation/dialogue_ja.csv':'85aa940ba608ad8e5edd6ed782f106c89f703d18288f923e0298e5b51bc5eafc',
               'workspace/translation/dialogue_ja_translated_ko.csv':'e274e97e75db79ea5d05b2e025cc70b7e9258a701bc1c10bea279ecbb4e8eb50'}
    for name,value in preserved.items():assert sha((ROOT/name).read_bytes())==value
    result={'status':'PASS','source_sha256':sha(rom),'output_sha256':sha(target),'output_size':len(target),
            'expected_write_count':len(plan),'diff_bytes_including_append':len(diff),'all_diff_owned':True,
            'header_change_only_chr_size':True,'irq_change_only_four_immediate_operands':True,
            'title_and_existing_chr_preserved':True,'other_text_and_pointer_table_preserved':True,
            'rebuild_byte_identical':True,'ips_cli_apply_byte_identical':True,
            'preserved_translation_sha256':preserved,'registered_font_hashes_verified':True,
            'scope':'Static/build/apply only; runtime and visual QA separate'}
    assert not a.output.exists();a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
