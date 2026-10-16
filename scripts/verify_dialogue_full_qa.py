"""Separate native scene, injected consumer, control-flow and sampled pixel gates."""
import argparse,csv,hashlib,json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def rows(p):return list(csv.DictReader(p.open(newline='')))
def maps(p):return {(k,int(a,16)):int(v) for k,a,v,_ in (s.split() for s in p.read_text().splitlines())}
def environment(folder,expected):
 e=json.loads((folder/'environment.json').read_text());assert e['exit_code']==0 and e['rom_sha256']==expected
 for name,h in e['files'].items():assert sha((folder/name).read_bytes())==h,(folder,name)
 return e['mode']
def pixels(baseline,target,mask,pattern):
 result=[]
 for f in sorted(baseline.glob(pattern)):
  old=Image.open(f).convert('RGB');new=Image.open(target/f.name).convert('RGB');assert old.size==new.size==(256,240)
  diff=[(x,y) for y in range(240) for x in range(256) if old.getpixel((x,y))!=new.getpixel((x,y))]
  outside=[p for p in diff if not(mask[0]<=p[0]<mask[2] and mask[1]<=p[1]<mask[3])]
  assert not outside,(f.name,len(outside),outside[:12]);result.append({'capture':f.stem,'text_pixels_different':len(diff),'outside_text_pixels':0})
 return result
def exact_text(folder,tag,page,col,row):
 ppu=(folder/(tag+'_ppu.bin')).read_bytes();m=maps(folder/(tag+'_mapping.txt'));banks=page['chr_banks']
 assert [m['PPU',0]//1024,m['PPU',0x400]//1024]==banks,(tag,m,banks)
 for y,line in enumerate(page['display_text'].split('\n')):
  for x,char in enumerate(line):assert ppu[0x2000+(row+y)*32+col+x]==page['mapping'][char],(tag,x,y,char)
 return ppu[:0x800]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--build',type=Path,required=True)
 for name in ('cold','coldbaseline','intro','introbaseline','harness','harnessbaseline','roots','rootsbaseline','output'):ap.add_argument('--'+name,type=Path,required=True)
 a=ap.parse_args();b=json.loads((a.build/'build_report.json').read_text());rom=(a.build/b['output_rom']).read_bytes();assert sha(rom)==b['output_sha256']
 for name in ('cold','coldbaseline','intro','introbaseline','harness','harnessbaseline','roots','rootsbaseline'):setattr(a,name,getattr(a,name).resolve())
 pages=json.loads((a.build/'pages.json').read_text(encoding='utf-8'));cat=json.loads((ROOT/'extracted/text/dialogue_20261001/dialogue_tokens.json').read_text(encoding='utf-8'))
 source=json.loads((ROOT/'manifests/source_rom.json').read_text());src=(ROOT/source['path']).read_bytes();reloc={int(k):v for k,v in json.loads((a.build/'relocation.json').read_text()).items()}
 scopes={}
 for name in ('cold','intro','harness','roots'):
  scopes[name]=environment(getattr(a,name),b['output_sha256']);environment(getattr(a,name+'baseline'),b['title_base_sha256'])
 cold=pixels(a.coldbaseline,a.cold,(32,32,160,88),'frame_*.png');assert len(cold)==44
 intro=pixels(a.introbaseline,a.intro,(64,144,192,200),'*.png');assert len(intro)==50
 harness=pixels(a.harnessbaseline,a.harness,(32,32,160,88),'JP_*.png');assert len(harness)==22
 # Exact PPU font bytes and fully displayed glyph codes in native and injected scenes.
 checked=[]
 for p,folder,tag,col,row in [(pages[i],a.cold,f'frame_{f:04d}',4,4) for i,f in zip((8,9,10,11),(840,1050,1200,1836))]+[(pages[i],a.intro,next(a.intro.glob(f'delay_{d:02d}_*.png')).stem,8,18) for i,d in zip(range(12,18),(2,4,6,8,11,13))]+[(p,a.harness,p['entry_id'],4,4) for p in pages]:
  font=exact_text(folder,tag,p,col,row);off=0x40010+p['chr_banks'][0]*1024;assert font==rom[off:off+0x800];checked.append({'page':p['entry_id'],'capture':str((folder/(tag+'.png')).relative_to(ROOT))})
 # Every real read value must come from the declared ROM.
 for folder in (a.cold,a.intro,a.harness,a.roots):
  for r in rows(folder/'script_reads.csv'):assert rom[int(r['file_offset'],16)]==int(r['value'],16)
 # All native intro F7 starts, including repeated pauses, match the source.
 holds=[];r0=rows(a.introbaseline/'script_reads.csv');r1=rows(a.intro/'script_reads.csv')
 for p in pages[12:18]:
  old=[int(r['frame']) for r in r0 if p['source_start']<=int(r['file_offset'],16)<p['source_end'] and r['value']=='F7']
  new=[int(r['frame']) for r in r1 if p['virtual_start']<=int(r['cpu_address'],16)<p['virtual_end'] and r['value']=='F7']
  assert old==new;holds.append({'page':p['entry_id'],'F7_frames':new})
 # Normalize only approved pointer arguments; compare outside-page controls.
 old_region=lambda off:any(p['source_start']<=off<p['source_end'] for p in pages)
 byte_map={}
 for t in cat['tokens']:
  if old_region(t['offset']):continue
  for j in range(t['size']):byte_map[0x24010+reloc[t['offset']]-0xA000+j]=t['offset']+j
 def external(rr,new):
  result=[]
  for r in rr:
   off=int(r['file_offset'],16)
   if new:
    if off not in byte_map:continue
    old=byte_map[off];result.append((old,src[old]))
   elif not old_region(off):result.append((off,int(r['value'],16)))
  return result
 assert external(rows(a.cold/'script_reads.csv'),True)==external(rows(a.coldbaseline/'script_reads.csv'),False)
 rr0=rows(a.rootsbaseline/'script_reads.csv');rr1=rows(a.roots/'script_reads.csv');root_report=[];covered=set()
 for root in range(26):
  old=[r for r in rr0 if int(r['root'])==root];new=[r for r in rr1 if int(r['root'])==root]
  assert old and new and old[-1]['value']==new[-1]['value']=='FA'
  assert external(new,True)==external(old,False),(root,'outside controls')
  consumed={int(r['file_offset'],16) for r in new};displayed=[]
  for p in pages:
   start=0x24010+p['virtual_start']-0xA000;end=0x24010+p['virtual_end']-0xA000
   if start in consumed:
    assert set(range(start,end))<=consumed,(root,p['entry_id']);covered.add(p['entry_id']);displayed.append(p['entry_id'])
  root_report.append({'root':root,'pages_fully_consumed':displayed,'native_FA':True,'outside_page_controls_identical':True})
 assert len(covered)==22
 calls=rows(a.cold/'selector_calls.csv');assert len(calls)%2==0
 from verify_dialogue_full_abi import expected_fonts
 for enter,leave in zip(calls[::2],calls[1::2]):
  assert enter['event']=='enter' and leave['event']=='leave'
  for k in ('frame','flag','base','cursor','sp','a000_prg'):assert enter[k]==leave[k],(k,enter,leave)
  expected=expected_fonts(b,pages,int(enter['base'],16),int(enter['cursor'],16),int(enter['flag'],16))
  if expected:assert [int(leave['ppu0_chr'])//1024,int(leave['ppu400_chr'])//1024]==expected
 # Source never touched work RAM during this native intro + demo. New accesses
 # are exactly the private cache and the declared raster code.
 original_ram=rows(a.introbaseline/'workram_access.csv');assert original_ram==[]
 ram=rows(a.intro/'workram_access.csv');assert ram and all(0x6000<=int(r['address'],16)<=0x6003 for r in ram)
 assert all(0x8001<=int(r['pc'],16)<0x8001+b['helper_bytes'] if r['event']=='write' else 0xFB72<=int(r['pc'],16)<0xFBA2 for r in ram)
 result={'status':'PASS','build_sha256':b['output_sha256'],'native_cold_blocks':4,'native_intro_blocks':6,'forced_page_blocks':22,'forced_registered_roots':26,
  'native_cold_samples':cold,'native_intro_samples':intro,'forced_page_samples':harness,'PPU_text_and_font_checks':checked,'native_intro_F7_timing':holds,
  'registered_root_consumer_checks':root_report,'native_font_calls_paired':len(calls)//2,'work_RAM_source_accesses':0,'work_RAM_patch_cache_accesses':ram,
  'all_sampled_outside_text_pixels_identical':True,'scopes':scopes,'visual':'Separate direct inspection is required; automated assertions do not establish readability',
  'pending':['Native Hampton and stage-specific hint contexts','Native four-page ending reachability/graphics','Full playthrough, hardware and other emulators','CSV needs_review remains unchanged']}
 assert not a.output.exists();a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':'PASS','native_blocks':10,'forced_blocks':22,'registered_roots':26,'pixel_samples':len(cold)+len(intro)+len(harness)}))
if __name__=='__main__':main()
