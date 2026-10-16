"""Audit the two-page cold boot, font switching, PRG restore and sampled visuals."""
import argparse,csv,hashlib,json
from pathlib import Path
from PIL import Image
def sha(b):return hashlib.sha256(b).hexdigest()
def rows(p):return list(csv.DictReader(p.open(newline='')))
def maps(p):return {(k,int(a,16)):int(v) for k,a,v,_ in (s.split() for s in p.read_text().splitlines())}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--build',type=Path,required=True)
    ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--runtime',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    build=json.loads((a.build/'build_report.json').read_text());rom=(a.build/build['output_rom']).read_bytes()
    assert sha(rom)==build['output_sha256'];pages=json.loads((a.build/'pages.json').read_text(encoding='utf-8'))
    for folder,expected in ((a.runtime,build['output_sha256']),(a.baseline,build['title_base_sha256'])):
        env=json.loads((folder/'environment.json').read_text());assert env['exit_code']==0 and env['rom_sha256']==expected
        for name,value in env['files'].items():assert sha((folder/name).read_bytes())==value
    comparisons=[]
    for f in sorted(a.baseline.glob('frame_*.png')):
        if not f.stem[6:].isdigit():continue
        old=Image.open(f).convert('RGB');new=Image.open(a.runtime/f.name).convert('RGB');assert old.size==new.size==(256,240)
        points=[(x,y) for y in range(240) for x in range(256) if old.getpixel((x,y))!=new.getpixel((x,y))]
        outside=[p for p in points if not(32<=p[0]<160 and 32<=p[1]<88)]
        assert not outside,(f.name,len(outside))
        comparisons.append({'frame':int(f.stem[6:]),'different_pixels':len(points),'outside_text_pixels':0})
    assert len(comparisons)==28
    for page,frame in zip(pages,(840,1050)):
        tag=f'frame_{frame:04d}';ppu=(a.runtime/(tag+'_ppu.bin')).read_bytes();m=maps(a.runtime/(tag+'_mapping.txt'))
        banks=page['chr_banks'];assert m['PPU',0]==banks[0]*1024 and m['PPU',0x400]==banks[1]*1024
        off=build['chr_file_base']+banks[0]*1024;assert ppu[:0x800]==rom[off:off+0x800]
        for y,line in enumerate(page['translation_ko'].split('\n')):
            for x,c in enumerate(line):assert ppu[0x2000+(4+y)*32+4+x]==page['mapping'][c],(page['entry_id'],c)
    m=maps(a.runtime/'frame_1200_mapping.txt');assert m['PPU',0]==120*1024 and m['PPU',0x400]==106*1024
    reads=rows(a.runtime/'script_reads.csv');base_reads=rows(a.baseline/'script_reads.csv')
    for r in reads:assert rom[int(r['file_offset'],16)]==int(r['value'],16)
    for p in pages:
        consumed={int(r['file_offset'],16) for r in reads if p['source_start']<=int(r['file_offset'],16)<p['source_end']}
        assert consumed==set(range(p['source_start'],p['source_end']))
    other=lambda rr:[r for r in rr if not 0x175A9<=int(r['file_offset'],16)<0x175ED]
    assert other(reads)==other(base_reads),'Untouched scripts or downstream frame timing changed'
    # Native F7 delay starts at the same frame, preserving speaking/holding phases.
    hold=[]
    for p in pages:
        pick=lambda rr:[int(r['frame']) for r in rr if p['source_start']<=int(r['file_offset'],16)<p['source_end'] and r['value']=='F7']
        assert pick(reads)==pick(base_reads);hold.append({'entry_id':p['entry_id'],'F7_frames':pick(reads)})
    calls=rows(a.runtime/'selector_calls.csv');assert len(calls)%2==0;active=0;font_pairs=set()
    for enter,leave in zip(calls[::2],calls[1::2]):
        assert enter['event']=='enter' and leave['event']=='leave'
        for k in ('frame','flag','base','cursor','sp','a000_prg'):assert enter[k]==leave[k],(k,enter,leave)
        if int(enter['flag'],16):
            active+=1;base=int(enter['base'],16);cursor=int(enter['cursor'],16)
            expected=(128,129) if base==0xB599 and cursor<39 else (130,131) if base==0xB599 and cursor<70 else (120,106)
            pair=(int(leave['ppu0_chr'])//1024,int(leave['ppu400_chr'])//1024);assert pair==expected
            font_pairs.add(pair)
    assert {(128,129),(130,131),(120,106)}<=font_pairs
    mapper=rows(a.runtime/'mapper_writes.csv')
    switches=[r for r in mapper if r['cpu_address']=='A000' and r['pc'] in ('FE9D','FEA4')]
    assert len(switches)==active*2
    for x,y in zip(switches[::2],switches[1::2]):assert x['value']=='11' and int(y['value'],16) in range(1,16,2)
    for f in (240,600,888,891,892,893,1072,1073,1074,1200,1440,1800,2100,2400,2700,3000,3300):
        assert next(c for c in comparisons if c['frame']==f)['different_pixels']==0,f
    result={'status':'PASS','build_sha256':build['output_sha256'],'baseline_sha256':build['title_base_sha256'],
            'translated_blocks_consumed':2,'script_read_values_checked':len(reads),
            'other_script_values_and_timing_identical':True,'native_F7_timing':hold,
            'selector_calls':len(calls)//2,'active_selector_calls':active,'PRG_switches_restored':len(switches)//2,
            'font_pairs_observed':sorted(map(list,font_pairs)),'PPU_font_bytes_and_Korean_nametables_exact':True,
            'sample_comparisons':comparisons,'all_sampled_outside_text_pixels_identical':True,
            'title_stage_and_reset_samples_identical':True,
            'scope':'Two common Shirley pages, transitions, first-stage entry and reset samples; full gameplay unperformed',
            'visual':'Readability requires direct inspection separately'}
    assert not a.output.exists();a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
