"""Compare declared controller-only gameplay with a title-only source baseline."""
import argparse, csv, hashlib, json
from pathlib import Path
from PIL import Image, ImageChops
from verify_dialogue_full_qa import environment
from verify_dialogue_full_abi import expected_fonts

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    with p.open(newline='') as f:return list(csv.DictReader(f))

def main():
    ap=argparse.ArgumentParser()
    for name in ('build','target','baseline','output'):ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--scope',required=True)
    a=ap.parse_args()
    b=json.loads((a.build/'build_report.json').read_text())
    pages=json.loads((a.build/'pages.json').read_text(encoding='utf-8'))
    rom=a.build/b['output_rom'];source=ROOT/'build/title_kr_ai_004/TinyToon_title_kr_poc.nes'
    assert sha(rom)==b['output_sha256'] and sha(source)==b['title_base_sha256']
    e=environment(a.target,b['output_sha256']);environment(a.baseline,b['title_base_sha256'])
    for p in (a.target,a.baseline):assert json.loads((p/'environment.json').read_text())['carrot_override'] is None
    for name in ('controller_plan.json','controller_inputs.csv'):assert (a.target/name).read_bytes()==(a.baseline/name).read_bytes(),name
    events=rows(a.target/'events.csv');old_events=rows(a.baseline/'events.csv')
    def controls(rr):
        return [(r['frame'],r['event'],r['a'] if r['event']=='native_initializer' else r['mode']) for r in rr if r['event'] in ('native_initializer','token_F7','token_FA','mode_change')]
    assert controls(events)==controls(old_events)
    assert not any(r['event'].startswith('explicit_') for r in events+old_events)
    captures=sorted(a.target.glob('frame_*.png'))
    assert {p.name for p in captures}=={p.name for p in a.baseline.glob('frame_*.png')}
    samples=[]
    for p in captures:
        ram=(a.target/(p.stem+'_ram.bin')).read_bytes();oldram=(a.baseline/(p.stem+'_ram.bin')).read_bytes()
        assert ram[0x57]==oldram[0x57],p.name
        assert ram[0x60:0x83]==oldram[0x60:0x83],(p.name,'player state')
        assert ram[0x7e0:0x7e8]==oldram[0x7e0:0x7e8],(p.name,'HUD state')
        old=Image.open(a.baseline/p.name).convert('RGB');new=Image.open(p).convert('RGB')
        assert old.size==new.size==(256,240)
        diff=ImageChops.difference(old,new)
        changed=sum(v!=(0,0,0) for v in diff.get_flattened_data())
        # This replay starts by skipping the introductory movie. Native Hamton
        # and Shirley put their text at column4/row4, in all stage contexts.
        if ram[0x57]:diff.paste((0,0,0),(32,32,160,88))
        assert diff.getbbox() is None,(p.name,diff.getbbox())
        samples.append({'capture':p.name,'mode':ram[0x57],'text_pixels_different':changed,'outside_text_pixels':0,'player_and_HUD_identical':True})
    for folder,data in ((a.target,rom.read_bytes()),(a.baseline,source.read_bytes())):
        for r in rows(folder/'script_reads.csv'):assert data[int(r['file_offset'],16)]==int(r['value'],16)
    calls=rows(a.target/'font_calls.csv');assert calls
    for r in calls:
        assert r['sp_before']==r['sp_after']
        pair=[int(r['chr0']),int(r['chr400'])]
        assert pair==expected_fonts(b,pages,int(r['base'],16),int(r['cursor'],16),int(r['mode'])),r
    data=rom.read_bytes()
    for p in a.target.glob('font_*.bin'):
        first,second=map(int,p.stem.split('_')[1:])
        assert p.read_bytes()==data[0x40010+first*1024:0x40010+(first+1)*1024]+data[0x40010+second*1024:0x40010+(second+1)*1024]
    old_ram=rows(a.baseline/'workram_access.csv');assert not old_ram
    accesses=rows(a.target/'workram_access.csv');assert accesses
    assert all(0x6000<=int(r['address'],16)<=0x6003 for r in accesses)
    assert all(0x8001<=int(r['pc'],16)<0x8000+b['helper_bytes'] if r['event']=='write' else 0xfb72<=int(r['pc'],16)<0xfba2 for r in accesses)
    a.output.resolve().relative_to(ROOT/'qa/reports');assert not a.output.exists()
    result={'status':'PASS','build_sha256':b['output_sha256'],'scope':a.scope,'capture_scope':e,'target':a.target.as_posix(),'baseline':a.baseline.as_posix(),'pixel_samples':samples,'controller_inputs_identical':True,'native_control_timing_identical':True,'native_initializers':[r for r in events if r['event']=='native_initializer'],'font_calls_checked':len(calls),'work_RAM_source_accesses':0,'patch_cache_accesses':len(accesses),'limitations':['Sampled regression evidence for the declared replay, not full playthrough proof','Direct visual review and exact stage-page glyph assertions recorded separately','CSV review status unchanged']}
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','samples':len(samples),'initializers':len(result['native_initializers'])}))
if __name__=='__main__':main()
