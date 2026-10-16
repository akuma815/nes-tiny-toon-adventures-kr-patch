"""Fourth-page checkpoint from immutable source and verified three-page plan."""
import argparse,csv,json,hashlib
from pathlib import Path
from PIL import Image
from asm6502 import assemble,verify_profile
from build_dialogue_poc import encode,FONT_SHA,CSV_SHA
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 source=json.loads((ROOT/'manifests/source_rom.json').read_text());src=(ROOT/source['path']).read_bytes();assert sha(src)==source['sha256']
 prior=ROOT/'build/dialogue_three_001';old=(prior/'TinyToon_dialogue_three.nes').read_bytes()
 assert sha(old)=='55768abfe461919f1c916df8976dd6dfbb025992ac80ce10e3af0276c2ab1e86'
 csvpath=ROOT/'workspace/translation/dialogue_ja.csv';assert sha(csvpath.read_bytes())==CSV_SHA
 row=next(r for r in csv.DictReader(csvpath.open(encoding='utf-8-sig')) if r['entry_id']=='JP_1760C')
 assert bytes.fromhex(row['raw_hex'])==src[0x1760C:0x17618]
 png=ROOT/'workspace/fonts/galmuri7_8x8/Galmuri7_8x8.png';assert sha(png.read_bytes())==FONT_SHA
 sheet=Image.open(png).convert('RGBA');chars=list(dict.fromkeys(c for c in row['translation_ko'] if c!=' '));mapping={' ':0,**dict(zip(chars,range(0x6E,0x80)))}
 fonts=bytearray(src[0x3E010:0x3E410]+src[0x3A810:0x3AC10]);glyphs=[]
 for c in chars:
  i=ord(c)-0xAC00;x=i%64*8;y=i//64*8
  bits=tuple(int((p:=sheet.getpixel((x+dx,y+dy)))[3]>0 and max(p[:3])>127) for dy in range(8) for dx in range(8))
  raw=encode(bits);fonts[mapping[c]*16:mapping[c]*16+16]=raw
  glyphs.append({'char':c,'code':mapping[c],'source':{'png_xy':[x,y]},'bytes_hex':raw.hex()})
 body=bytes((0xF8,6))+bytes(mapping[c] for c in row['translation_ko'])+bytes.fromhex('F8 03 F7 46');assert len(body)==12
 pages=json.loads((prior/'pages.json').read_text(encoding='utf-8'))
 pages.append({'entry_id':row['entry_id'],'translation_ko':row['translation_ko'],'source_start':0x1760C,'source_end':0x17618,
  'mapping':mapping,'glyphs':glyphs,'chr_banks':[134,135],'payload_hex':body.hex(),'typing_frames':28,
  'first_glyph_frames':7,'other_glyph_frames':7,'source_delay_preserved':'F7 46','neutral_tail_bytes':0})
 assembly=json.loads((prior/'assembly.json').read_text());selector,listing,symbols=assemble((ROOT/'workspace/asm/dialogue_four_selector.asm').read_text(),0xA000,assembly['constants'])
 assembly.update(selector=listing,selector_symbols=symbols,profile=verify_profile())
 plan=json.loads((prior/'expected_writes.json').read_text())
 for w in plan:
  if w['owner']=='new_prg':
   region=bytearray.fromhex(w['final_hex']);region[0x2000:0x4000]=bytes(0x2000);region[0x2000:0x2000+len(selector)]=selector;w['final_hex']=region.hex();w['rule']['bank17_code_length']=len(selector)
  if w['owner']=='new_page_fonts':
   region=bytearray.fromhex(w['final_hex']);region[0x1800:0x2000]=fonts;w['final_hex']=region.hex();w['rule']['font_banks']+=[134,135]
 plan.append({'owner':'JP_1760C','reason':'Fourth Korean page, native total typing/hold time','file_offset':0x1760C,'length':12,
  'expected_source_sha256':sha(src),'expected_overlap_length':12,'expected_overlap_sha256':sha(src[0x1760C:0x17618]),'final_hex':body.hex(),'rule':None})
 output=bytearray(src);owned=set()
 for w in sorted(plan,key=lambda w:w['file_offset']):
  off=w['file_offset'];n=w['length'];assert sha(src[off:off+w['expected_overlap_length']])==w['expected_overlap_sha256']
  r=set(range(off,off+n));assert not r&owned;owned|=r;output[off:off+n]=bytes.fromhex(w['final_hex'])
 assert len(output)==0x80010 and all(i in owned for i in range(len(output)) if i>=len(src) or output[i]!=src[i])
 assert output[0x175A9:0x1760C]==old[0x175A9:0x1760C] and output[0x60010:0x61810]==old[0x60010:0x61810]
 out=a.output.resolve();out.relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 report=json.loads((prior/'build_report.json').read_text());report.update(output_rom='TinyToon_dialogue_four.nes',output_sha256=sha(output),
  translated_blocks=4,entry_ids=[p['entry_id'] for p in pages],previous_build_sha256=sha(old),new_chr_banks=list(range(128,136)),selector_size=len(selector),expected_write_count=len(plan),
  changed_bytes_including_append=sum(i>=len(src) or output[i]!=src[i] for i in range(len(output))),scope='Four Shirley pages; not full-game validation')
 for name,v in [('build_report',report),('expected_writes',plan),('pages',pages),('assembly',assembly)]:
  (out/(name+'.json')).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (out/report['output_rom']).write_bytes(output);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
