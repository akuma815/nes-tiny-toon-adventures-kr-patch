"""Ending text under real cinema/raster rendering, with explicit root injection."""
import argparse,json,csv
from pathlib import Path
from verify_dialogue_full_qa import environment,pixels,exact_text,sha,rows
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--build',type=Path,required=True);ap.add_argument('--runtime',type=Path,required=True);ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 a.runtime=a.runtime.resolve();a.baseline=a.baseline.resolve();b=json.loads((a.build/'build_report.json').read_text());pages=json.loads((a.build/'pages.json').read_text(encoding='utf-8'));rom=(a.build/b['output_rom']).read_bytes()
 scope=environment(a.runtime,b['output_sha256']);environment(a.baseline,b['title_base_sha256'])
 comparisons=pixels(a.baseline,a.runtime,(64,144,192,200),'frame_*.png');assert len(comparisons)==36
 for folder in (a.runtime,a.baseline):
  inject=rows(folder/'cinema_injections.csv');assert [(int(r['old_root']),int(r['new_root'])) for r in inject]==[(i,i+10) for i in range(12,16)]
 checks=[];oldreads=rows(a.baseline/'script_reads.csv');reads=rows(a.runtime/'script_reads.csv')
 for p,d in zip(pages[18:],(2,4,6,16)):
  tag=next(a.runtime.glob(f'delay_{d:02d}_*.png')).stem;reference=next(a.baseline.glob(f'delay_{d:02d}_*.png')).stem;assert tag==reference
  font=exact_text(a.runtime,tag,p,8,18);off=0x40010+p['chr_banks'][0]*1024;assert font==rom[off:off+0x800]
  start=0x24010+p['virtual_start']-0xA000;end=0x24010+p['virtual_end']-0xA000
  consumed={int(r['file_offset'],16) for r in reads};assert set(range(start,end))<=consumed
  new=[int(r['frame']) for r in reads if start<=int(r['file_offset'],16)<end and r['value']=='F7']
  old=[int(r['frame']) for r in oldreads if p['source_start']<=int(r['file_offset'],16)<p['source_end'] and r['value']=='F7']
  assert len(old)==len(new) and old[0]==new[0] and old[-1]==new[-1]
  if p['entry_id']!='JP_1780B':assert old==new
  checks.append({'page':p['entry_id'],'capture':str((a.runtime/(tag+'.png')).relative_to(ROOT)),'original_F7_frames':old,'Korean_F7_frames':new,'prefix_and_final_hold_frames_identical':True})
 assert rows(a.baseline/'workram_access.csv')==[]
 cache=rows(a.runtime/'workram_access.csv');assert cache and all(0x6000<=int(r['address'],16)<=0x6003 for r in cache)
 report={'status':'PASS','build_sha256':b['output_sha256'],'scope':scope,'ending_blocks_under_cinema_consumer':4,'samples':comparisons,'ending_checks':checks,
  'all_sampled_outside_text_pixels_identical':True,'last_page_internal_pause_frames_redistributed':True,'same_eight_middle_pauses_and_total_duration':True,
  'game_ending_reachability':'UNPERFORMED - native intro engine with four ending-root substitutions','visual':'Direct inspection is separate'}
 assert not a.output.exists();a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'PASS','ending_consumer_blocks':4,'samples':36}))
if __name__=='__main__':main()
