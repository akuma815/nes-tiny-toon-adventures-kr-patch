"""Verify real ROM/CHR/script consumption and pixel regression outside dialogue."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops

ROOT=Path(__file__).resolve().parents[1]
def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--build',type=Path,required=True)
    ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--runtime',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    build=json.loads((a.build/'build_report.json').read_text(encoding='utf-8'))
    rom=(a.build/build['output_rom']).read_bytes();assert sha(rom)==build['output_sha256']
    env=json.loads((a.runtime/'environment.json').read_text(encoding='utf-8'))
    base_env=json.loads((a.baseline/'environment.json').read_text(encoding='utf-8'))
    assert env['exit_code']==base_env['exit_code']==0
    assert env['rom_sha256']==build['output_sha256'] and base_env['rom_sha256']==build['title_base_sha256']
    comparisons=[]
    for base in sorted(a.baseline.glob('frame_*.png')):
        if not base.stem[6:].isdigit():continue
        target=a.runtime/base.name;assert target.exists()
        old=Image.open(base).convert('RGB');new=Image.open(target).convert('RGB')
        assert old.size==new.size==(256,240)
        points=[(x,y) for y in range(240) for x in range(256) if old.getpixel((x,y))!=new.getpixel((x,y))]
        outside=[p for p in points if not (32<=p[0]<160 and 32<=p[1]<88)]
        comparisons.append({'frame':int(base.stem[6:]),'different_pixels':len(points),
                            'outside_text_pixels':len(outside)})
        if outside:raise AssertionError(f'Outside-text regression at {base.name}: {len(outside)} pixels')
    # The completed Korean first page is captured before its original delay ends.
    ppu=(a.runtime/'frame_0810_ppu.bin').read_bytes()
    maps={}
    for line in (a.runtime/'frame_0810_mapping.txt').read_text().splitlines():
        kind,address,offset,mem=line.split()
        if kind=='PPU':maps[int(address,16)]=int(offset)
    assert maps[0]==0x20000 and maps[0x400]==0x20400
    assert ppu[:0x800]==rom[0x40010:0x40810]
    glyph=json.loads((a.build/'glyph_mapping.json').read_text(encoding='utf-8'))
    mapping=glyph['mapping'];text=build['translation_ko']
    for y,line in enumerate(text.split('\n')):
        for x,char in enumerate(line):
            assert ppu[0x2000+(4+y)*32+4+x]==mapping[char],(y,x,char)
    reads=list(csv.DictReader((a.runtime/'script_reads.csv').open(newline='')))
    target_reads=[r for r in reads if 0x175A9<=int(r['file_offset'],16)<0x175CE]
    assert target_reads
    for r in reads:
        off=int(r['file_offset'],16);assert rom[off]==int(r['value'],16)
    consumed={int(r['file_offset'],16) for r in target_reads}
    assert consumed==set(range(0x175A9,0x175CE)),'First block or neutral padding was not consumed'
    base_reads=list(csv.DictReader((a.baseline/'script_reads.csv').open(newline='')))
    other=lambda values:[r for r in values if not 0x175A9<=int(r['file_offset'],16)<0x175CE]
    assert other(reads)==other(base_reads),'Other script reads or downstream timing changed'
    # Both executions reach the first stage and retain the exact Korean title after reset.
    for frame in (240,2700,3000,3300):
        r=next(c for c in comparisons if c['frame']==frame)
        assert r['different_pixels']==0,(frame,r)
    report={'status':'PASS','build_sha256':build['output_sha256'],'baseline_sha256':build['title_base_sha256'],
            'script_read_values_checked':len(reads),'first_block_consumed_bytes':len(consumed),
            'korean_text_nametable_exact':True,'korean_font_runtime_rom_exact':True,
            'other_script_read_values_and_frame_timing_identical':True,
            'cloned_font_banks_observed':[128,129],'sample_comparisons':comparisons,
            'all_outside_text_pixels_unchanged':True,'title_before_and_after_reset_identical':True,
            'first_stage_samples_identical':True,'visual':'Direct inspection required separately; machine checks do not prove readability',
            'scope':'One translated block and sampled first-stage entry/reset; not full game QA'}
    assert not a.output.exists();a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
