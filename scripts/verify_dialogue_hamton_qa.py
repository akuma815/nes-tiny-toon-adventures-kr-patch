"""Separate a controller-only Hamton visit from one counter-controlled branch."""
import argparse,csv,hashlib,json
from pathlib import Path
from PIL import Image,ImageChops
from verify_dialogue_full_abi import expected_fonts
from verify_dialogue_full_qa import environment
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):return list(csv.DictReader(p.open(newline='')))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--build',type=Path,required=True)
 for name in ('native','nativebaseline','controlled','controlledbaseline','output'):ap.add_argument('--'+name,type=Path,required=True)
 a=ap.parse_args();build=a.build.resolve();b=json.loads((build/'build_report.json').read_text());pages=json.loads((build/'pages.json').read_text(encoding='utf-8'))
 rom=(build/b['output_rom']).read_bytes();assert hashlib.sha256(rom).hexdigest()==b['output_sha256']
 source=ROOT/'build/title_kr_ai_004/TinyToon_title_kr_poc.nes';assert sha(source)==b['title_base_sha256'];src=source.read_bytes()
 reports=[];covered=set()
 for case in ('native','controlled'):
  target=getattr(a,case).resolve();baseline=getattr(a,case+'baseline').resolve()
  environment(target,b['output_sha256']);environment(baseline,b['title_base_sha256'])
  e=json.loads((target/'environment.json').read_text());eb=json.loads((baseline/'environment.json').read_text())
  assert e.get('carrot_override')==eb.get('carrot_override')==(None if case=='native' else 29)
  assert (target/'controller_plan.json').read_bytes()==(baseline/'controller_plan.json').read_bytes()
  assert (target/'controller_inputs.csv').read_bytes()==(baseline/'controller_inputs.csv').read_bytes()
  events=rows(target/'events.csv');old_events=rows(baseline/'events.csv')
  def controls(rr):return [(r['frame'],r['event'],r['a'] if r['event']=='native_initializer' else r['mode']) for r in rr if r['event'] in ('native_initializer','token_F7','token_FA','mode_change')]
  assert controls(events)==controls(old_events)
  mutations=[r for r in events if r['event'].startswith('explicit_carrot_override')]
  assert mutations==[] if case=='native' else len(mutations)==1 and mutations[0]['frame']=='5800' and mutations[0]['event']=='explicit_carrot_override_30_to_29'
  wanted=[0,20,18] if case=='native' else [0,21,18]
  init=[int(r['a']) for r in events if r['event']=='native_initializer' and int(r['frame'])>5800];assert init==wanted
  captures=sorted(target.glob('frame_*.png'));assert {p.name for p in captures}=={p.name for p in baseline.glob('frame_*.png')}
  samples=[]
  for p in captures:
   ram=(target/(p.stem+'_ram.bin')).read_bytes();oldram=(baseline/(p.stem+'_ram.bin')).read_bytes();assert ram[0x57]==oldram[0x57]
   # Player movement and HUD counters must match; pointers/text buffers differ.
   assert ram[0x60:0x83]==oldram[0x60:0x83],p.name
   assert ram[0x7E0:0x7E8]==oldram[0x7E0:0x7E8],p.name
   old=Image.open(baseline/p.name).convert('RGB');new=Image.open(p).convert('RGB');assert old.size==new.size==(256,240)
   diff=ImageChops.difference(old,new);total=sum(v!=(0,0,0) for v in diff.get_flattened_data())
   if ram[0x57]:diff.paste((0,0,0),(32,32,160,88))
   assert diff.getbbox() is None,(case,p.name,diff.getbbox())
   samples.append({'capture':p.name,'mode':ram[0x57],'text_pixels_different':total,'outside_text_pixels':0})
  rr=rows(target/'script_reads.csv')
  for r in rr:assert rom[int(r['file_offset'],16)]==int(r['value'],16)
  for r in rows(baseline/'script_reads.csv'):assert src[int(r['file_offset'],16)]==int(r['value'],16)
  checks=[]
  for idx,f in ([(0,5945),(1,6189),(2,6360),(4,6729)] if case=='native' else [(0,5945),(1,6189),(3,6432),(4,6670)]):
   p=pages[idx];tag=f'frame_{f:05d}';ppu=(target/(tag+'_ppu.bin')).read_bytes()
   for y,line in enumerate(p['display_text'].split('\n')):
    for x,ch in enumerate(line):assert ppu[0x2000+(4+y)*32+4+x]==p['mapping'][ch],(case,idx,x,y,ch)
   start=0x24010+p['virtual_start']-0xA000;end=0x24010+p['virtual_end']-0xA000
   consumed={int(r['file_offset'],16) for r in rr if int(r['frame'])>5800};assert set(range(start,end))<=consumed,(case,idx)
   covered.add(p['entry_id']);checks.append({'page':p['entry_id'],'capture':tag+'.png','glyph_codes_exact':True,'entire_page_consumed':True})
  calls=rows(target/'font_calls.csv');assert calls
  for r in calls:
   assert r['sp_before']==r['sp_after']
   pair=[int(r['chr0']),int(r['chr400'])];expected=expected_fonts(b,pages,int(r['base'],16),int(r['cursor'],16),int(r['mode']))
   assert pair==expected,(r,expected)
  for p in target.glob('font_*.bin'):
   first,second=map(int,p.stem.split('_')[1:]);assert p.read_bytes()==rom[0x40010+first*1024:0x40010+(first+1)*1024]+rom[0x40010+second*1024:0x40010+(second+1)*1024]
  original_ram=rows(baseline/'workram_access.csv');assert original_ram==[]
  accesses=rows(target/'workram_access.csv');assert accesses and all(0x6000<=int(r['address'],16)<=0x6003 for r in accesses)
  assert all(0x8001<=int(r['pc'],16)<0x8000+b['helper_bytes'] if r['event']=='write' else 0xFB72<=int(r['pc'],16)<0xFBA2 for r in accesses)
  ram_before=(target/'frame_05800_ram.bin').read_bytes();ram_after=(target/('frame_06840_ram.bin' if case=='native' else 'frame_06840_ram.bin')).read_bytes()
  assert ram_before[0x7E1]==(30 if case=='native' else 29)
  assert ram_after[0x7E1]==(0 if case=='native' else 29)
  reports.append({'case':case,'scope':e['mode'],'native_initializer_ids':init,'Hamton_font_mode':1,'before_carrots':ram_before[0x7E1],'after_carrots':ram_after[0x7E1],'samples':samples,'exact_page_checks':checks,'font_calls_checked':len(calls),'work_RAM_source_accesses':0,'patch_cache_accesses':len(accesses),'controller_inputs_identical':True,'control_timing_identical':True,'player_and_HUD_state_identical':True})
 assert covered=={p['entry_id'] for p in pages[:5]}
 out=a.output.resolve();out.relative_to(ROOT/'qa/reports');assert not out.exists()
 result={'status':'PASS','build_sha256':b['output_sha256'],'Hamton_pages':sorted(covered),'cases':reports,'visual':'Automated tile/font/pixel assertions; direct visual review recorded separately','limitations':['29 carrots uses ONE declared RAM write; not native carrot collection','Native30 visit, stage1-1 clear and stage1-2 progress only; full game/actual ending/other stage hints/hardware unperformed','CSV review status unchanged']}
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':'PASS','Hamton_pages':5,'pixel_samples':sum(len(r['samples']) for r in reports)}))
if __name__=='__main__':main()
