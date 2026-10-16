"""Verify declared stage/real-ending skips against the Japanese scene execution."""
import argparse, csv, hashlib, json, re
from pathlib import Path
from PIL import Image, ImageChops
from verify_dialogue_full_abi import expected_fonts
from verify_dialogue_full_qa import environment

ROOT=Path(__file__).resolve().parents[1]
def rows(p):
    with p.open(newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--suffix',default='001')
    ap.add_argument('--output',type=Path,default=ROOT/'qa/reports/dialogue_full_006_scene_skip.json')
    a=ap.parse_args();assert re.fullmatch(r'[a-zA-Z0-9_]+',a.suffix)
    out=a.output.resolve();out.relative_to(ROOT/'qa/reports');assert not out.exists()
    build=ROOT/'build/dialogue_full_006'
    b=json.loads((build/'build_report.json').read_text())
    pages=json.loads((build/'pages.json').read_text(encoding='utf-8'))
    rom=build/b['output_rom'];src=ROOT/'build/title_kr_ai_004/TinyToon_title_kr_poc.nes'
    assert sha(rom)==b['output_sha256'] and sha(src)==b['title_base_sha256']
    data=rom.read_bytes();source=src.read_bytes();cases=[];covered=set()
    levels=[0,5,10,15,20,21,23]
    for index,case in enumerate(['stage1','stage2','stage3','stage4','stage5','stage6','ending']):
        t=ROOT/f'qa/dialogue/full_scene_{case}_skip_{a.suffix}'
        o=ROOT/f'qa/dialogue/full_scene_{case}_skip_baseline_{a.suffix}'
        scope=environment(t,b['output_sha256']);environment(o,b['title_base_sha256'])
        skips=rows(t/'scene_skip.csv');assert skips==rows(o/'scene_skip.csv')
        assert [(r['address'],int(r['new_value'],16)) for r in skips]==([('0053',levels[index])] if case!='ending' else [('0053',23),('004C',16),('05BA',0),('05BB',0)])
        assert all(r['frame']=='664' for r in skips)
        assert (t/'controller_inputs.csv').read_bytes()==(o/'controller_inputs.csv').read_bytes()
        et=rows(t/'events.csv');eo=rows(o/'events.csv')
        def controls(rr):
            return [(r['frame'],r['event'],r['a'] if r['event']=='native_initializer' else r['mode']) for r in rr if r['event'] in ('native_initializer','token_FA','mode_change') or (case!='ending' and r['event']=='token_F7')]
        assert controls(et)==controls(eo),(case,'scene timing')
        roots=[int(r['a']) for r in et if r['event']=='native_initializer']
        assert roots==([index+6,19] if case!='ending' else [22,23,24,25]),(case,roots)
        assert not any(r['event'].startswith('explicit_') for r in et+eo)
        rr=rows(t/'script_reads.csv');ro=rows(o/'script_reads.csv')
        for folder,reads,content in ((t,rr,data),(o,ro,source)):
            for r in reads:assert content[int(r['file_offset'],16)]==int(r['value'],16)
        samples=[];names={p.name for p in t.glob('frame_*.png')}&{p.name for p in o.glob('frame_*.png')}
        if case!='ending':assert names=={p.name for p in t.glob('frame_*.png')}=={p.name for p in o.glob('frame_*.png')}
        for name in sorted(names):
            ram=(t/(name[:-4]+'_ram.bin')).read_bytes();oldram=(o/(name[:-4]+'_ram.bin')).read_bytes()
            assert ram[0x57]==oldram[0x57] and ram[0x60:0x83]==oldram[0x60:0x83] and ram[0x7e0:0x7e8]==oldram[0x7e0:0x7e8],(case,name,'scene/player/HUD')
            old=Image.open(o/name).convert('RGB');new=Image.open(t/name).convert('RGB');assert old.size==new.size==(256,240)
            diff=ImageChops.difference(old,new);total=sum(v!=(0,0,0) for v in diff.get_flattened_data())
            # Fixed native text coordinates: stage column4,row4; cinema column8,row18.
            # Protect all portraits, borders, cards, gameplay and credits outside these 16x7 cells.
            if ram[0x57]:diff.paste((0,0,0),(64,144,192,200) if case=='ending' else (32,32,160,88))
            assert diff.getbbox() is None,(case,name,diff.getbbox())
            samples.append({'capture':name,'mode':ram[0x57],'text_pixels_different':total,'outside_text_pixels':0})
        checks=[];wanted=list(range(18,22)) if case=='ending' else [8,9,10,11]+({1:[5],2:[6],3:[7]}.get(index,[]))
        for i in wanted:
            p=pages[i];st=0x24010+p['virtual_start']-0xa000;en=0x24010+p['virtual_end']-0xa000
            consumed={int(r['file_offset'],16) for r in rr};assert set(range(st,en))<=consumed,(case,p['entry_id'],'not fully read')
            col,row=(8,18) if case=='ending' else (4,4)
            first,second=p['chr_banks'];font=data[0x40010+first*1024:0x40010+(first+1)*1024]+data[0x40010+second*1024:0x40010+(second+1)*1024]
            matches=[]
            for capture in sorted(t.glob('frame_*_ppu.bin')):
                ppu=capture.read_bytes()
                if ppu[:0x800]!=font:continue
                if all(ppu[0x2000+(row+y)*32+col+x]==p['mapping'][ch] for y,line in enumerate(p['display_text'].split('\n')) for x,ch in enumerate(line)):
                    matches.append(capture.name.replace('_ppu.bin','.png'))
            assert matches,(case,p['entry_id'],'no full glyph/font capture')
            covered.add(p['entry_id']);checks.append({'page':p['entry_id'],'capture':matches[0],'glyph_codes_exact':True,'font_bytes_exact':True,'entire_page_consumed':True})
        holds=[]
        if case=='ending':
            for i in range(18,22):
                p=pages[i];st=0x24010+p['virtual_start']-0xa000;en=0x24010+p['virtual_end']-0xa000
                new=[int(r['frame']) for r in rr if st<=int(r['file_offset'],16)<en and r['value']=='F7']
                old=[int(r['frame']) for r in ro if p['source_start']<=int(r['file_offset'],16)<p['source_end'] and r['value']=='F7']
                if i!=21:assert new==old
                else:assert len(new)==len(old)==10 and new[0]==old[0] and new[-1]==old[-1]
                holds.append({'page':p['entry_id'],'source_F7_frames':old,'target_F7_frames':new,'eight_middle_pauses_redistributed':i==21,'first_and_final_holds_identical':True})
        calls=rows(t/'font_calls.csv');assert calls
        for r in calls:
            assert r['sp_before']==r['sp_after']
            assert [int(r['chr0']),int(r['chr400'])]==expected_fonts(b,pages,int(r['base'],16),int(r['cursor'],16),int(r['mode']))
        for f in t.glob('font_*.bin'):
            first,second=map(int,f.stem.split('_')[1:]);assert f.read_bytes()==data[0x40010+first*1024:0x40010+(first+1)*1024]+data[0x40010+second*1024:0x40010+(second+1)*1024]
        assert not rows(o/'workram_access.csv')
        access=rows(t/'workram_access.csv');assert access
        assert all(0x6000<=int(r['address'],16)<=0x6003 for r in access)
        assert all(0x8001<=int(r['pc'],16)<0x8000+b['helper_bytes'] if r['event']=='write' else 0xfb72<=int(r['pc'],16)<0xfba2 for r in access)
        cases.append({'case':case,'scope':scope,'native_initializer_ids':roots,'declared_RAM_writes':skips,'controller_inputs_identical':True,'scene_and_FA_timing_identical':True,'samples':samples,'exact_pages':checks,'ending_holds':holds,'font_calls_checked':len(calls),'source_work_RAM_accesses':0,'patch_cache_accesses':len(access),'target':str(t.relative_to(ROOT)),'baseline':str(o.relative_to(ROOT))})
    assert covered=={p['entry_id'] for p in pages[5:12]+pages[18:22]}
    result={'status':'PASS','build_sha256':b['output_sha256'],'cases':cases,'unique_pages':sorted(covered),'pixel_samples':sum(len(c['samples']) for c in cases),'scope':'Six stage selection scenes and the real four-page ending/credits through declared RAM-only original-dispatcher scene skips. User-requested dialogue-focused QA, not a full playthrough.','visual':'Direct review is recorded separately.','limitations':['Ending JP_1780B retains eight middle pauses with redistributed positions; first/final hold and completion timing match source','Other emulators/hardware not tested','CSV needs_review unchanged; local test build']}
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','cases':len(cases),'unique_pages':len(covered),'pixel_samples':result['pixel_samples']}))
if __name__=='__main__':main()
