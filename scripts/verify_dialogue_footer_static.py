"""Independent graph, font, write ownership, reproducibility and IPS audit."""
import argparse,csv,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--build',type=Path,required=True);ap.add_argument('--rebuild',type=Path,required=True);ap.add_argument('--applied',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 source=json.loads((ROOT/'manifests/source_rom.json').read_text());src=(ROOT/source['path']).read_bytes();assert sha(src)==source['sha256']
 b=json.loads((a.build/'build_report.json').read_text());rom=(a.build/b['output_rom']).read_bytes();assert sha(rom)==b['output_sha256'] and len(rom)==0x80010
 assert rom[:4]==src[:4] and rom[4:6]==bytes((16,32)) and rom[6:8]==src[6:8] and rom[8]==1 and rom[9:16]==src[9:16]
 assert (a.rebuild/b['output_rom']).read_bytes()==a.applied.read_bytes()==rom
 plan=json.loads((a.build/'expected_writes.json').read_text());owners={'header':(0,16),'preserved_title_prg':(0x3654,0x1A7),'reader_hook':(0x17281,15),'registered_root_pointers':(0x17443,52),'new_prg':(0x20010,0x20000),'moved_chr':(0x40010,0x20000),'page_fonts':(0x60010,0x20000)};allowed=set()
 assert len(plan)==len(owners)
 for w in plan:
  o,n=w['file_offset'],w['length'];assert (o,n)==owners[w['owner']] and w['expected_source_sha256']==sha(src)
  overlap=max(0,min(n,len(src)-o));assert overlap==w['expected_overlap_length'] and sha(src[o:o+overlap])==w['expected_overlap_sha256']
  assert rom[o:o+n]==bytes.fromhex(w['final_hex']);span=set(range(o,o+n));assert not allowed&span;allowed|=span
 diff={i for i in range(len(rom)) if i>=len(src) or rom[i]!=src[i]};assert diff<=allowed
 title=(ROOT/'build/title_kr_ai_004/TinyToon_title_kr_poc.nes').read_bytes();assert sha(title)==b['title_base_sha256']
 expected_prg=bytearray(src[16:0x20010]);expected_prg[0x3644:0x37EB]=title[0x3654:0x37FB]
 expected_prg[0x17271:0x17280]=bytes.fromhex('A5 FF 29 7F 8D 00 20 20 94 FE 09 00 60')+bytes((0xEA,))*2
 expected_prg[0x17433:0x17467]=rom[0x17443:0x17477];assert rom[16:0x20010]==expected_prg
 assert rom[0x17477:0x17845]==src[0x17477:0x17845] and rom[0x40010:0x60010]==title[0x20010:0x40010]
 rows=list(csv.DictReader((ROOT/'workspace/translation/dialogue_ja.csv').open(encoding='utf-8-sig',newline='')))
 assert sha((ROOT/'workspace/translation/dialogue_ja.csv').read_bytes())==b['csv_sha256']
 cat=json.loads((ROOT/'extracted/text/dialogue_20261001/dialogue_tokens.json').read_text(encoding='utf-8'));pages=json.loads((a.build/'pages.json').read_text(encoding='utf-8'));reloc={int(k):v for k,v in json.loads((a.build/'relocation.json').read_text()).items()}
 assert len(pages)==len(rows)==22
 fontdir=ROOT/'workspace/fonts/galmuri7_8x8';sheet=Image.open(fontdir/'Galmuri7_8x8.png').convert('RGBA');ttf=ImageFont.truetype(str(fontdir/'Galmuri7.ttf'),8)
 assert sha((fontdir/'Galmuri7_8x8.png').read_bytes())==b['font_png_sha256'] and sha((fontdir/'Galmuri7.ttf').read_bytes())==b['ttf_sha256']
 override=json.loads((ROOT/b['glyph_override_path']).read_text(encoding='utf-8'));assert sha((ROOT/b['glyph_override_path']).read_bytes())==b['glyph_override_sha256']
 tail=bytearray(0x20000);page_by_old={p['source_start']:p for p in pages};page_by_new={p['virtual_start']:p for p in pages};coverage=set();profiles=[]
 for row,p in zip(rows,pages):
  assert row['entry_id']==p['entry_id'] and row['translation_ko']==p['translation_ko']
  text=p['display_text'];assert text.replace('\n','')==row['translation_ko'].replace('\n','') and max(map(len,text.split('\n')))<=16 and len(text.split('\n'))<=7
  payload=rom[0x24010+p['virtual_start']-0xA000:0x24010+p['virtual_end']-0xA000];assert payload==bytes.fromhex(p['payload_hex'])
  reverse={v:k for k,v in p['mapping'].items()};i=0;decoded=[];speed=3;typing=0;delays=[];positions=[]
  while i<len(payload):
   c=payload[i];i+=1
   if c<128:
    assert c in reverse;decoded.append(reverse[c]);typing+=(speed+1) if c else 0
   elif c==0xF5:decoded.append('\n')
   elif c==0xF8:speed=payload[i];i+=1
   elif c==0xF7:delays.append(payload[i]);i+=1
   elif c==0xF6:positions.append(list(payload[i:i+2]));i+=2
   else:raise AssertionError((p['entry_id'],hex(c)))
  ts=[t for t in cat['tokens'] if p['source_start']<=t['offset']<p['source_end']]
  assert ''.join(decoded)==text and speed==3 and typing==4*sum(t['name']=='glyph' and t['code']!=0 for t in ts)
  assert delays==[t['args'][0] for t in ts if t['name']=='delay'] and positions==[t['args'] for t in ts if t['name']=='position']
  fonts=bytearray(src[0x3E010:0x3E410]+src[0x3A810:0x3AC10]);native=bytes(fonts);overwritten=set()
  for g in p['glyphs']:
   char=g['char'];code=g['code'];ink=[]
   if '\uac00'<=char<='\ud7a3':
    n=ord(char)-0xAC00;x=n%64*8;y=n//64*8
    for dy in range(8):ink.append(sum(1<<(7-dx) for dx in range(8) if (q:=sheet.getpixel((x+dx,y+dy)))[3]>0 and max(q[:3])>127))
   else:
    im=Image.new('L',(8,8));ImageDraw.Draw(im).text((0,0),char,font=ttf,fill=255)
    for dy in range(8):ink.append(sum(1<<(7-dx) for dx in range(8) if im.getpixel((dx,dy))>127))
   if char in override:ink=[sum(1<<(7-x) for x,v in enumerate(row) if v=='#') for row in override[char]['rows']]
   glyph=bytes(8)+bytes(ink);assert glyph==bytes.fromhex(g['bytes_hex']);fonts[code*16:code*16+16]=glyph;overwritten.add(code)
  assert overwritten<=set(range(0x6E,0x80))|set(range(1,0x13))
  for c in range(128):
   if c not in overwritten:assert fonts[c*16:c*16+16]==native[c*16:c*16+16]
  assert all(fonts[c*16:c*16+16]==native[c*16:c*16+16] for c in range(0x3C,0x49))
  off=p['page_id']*0x800;tail[off:off+0x800]=fonts
  profiles.append({'entry_id':p['entry_id'],'unique_new_glyphs':len(overwritten),'reused_kana_slots':p['extra_slots'],'rows':len(text.split('\n')),'typing_frames':typing,'F7':delays})
 assert rom[0x60010:]==tail
 # Independently reconstruct the graph's physical layout and every pointer.
 reconstructed=bytearray();calls=[];skip_end=-1
 for t in cat['tokens']:
  off=t['offset']
  if off<skip_end:continue
  assert reloc[off]==0xA000+len(reconstructed)
  if off in page_by_old:
   p=page_by_old[off];reconstructed.extend(bytes.fromhex(p['payload_hex']));skip_end=p['source_end']
  else:
   data=bytearray.fromhex(t['raw_hex'])
   if t['name']=='call':
    target=int.from_bytes(data[1:],'little')+0xC010;data[1:]=reloc[target].to_bytes(2,'little');calls.append(off)
   reconstructed.extend(data)
 assert rom[0x24010:0x24010+b['data_bytes']]==reconstructed and len(calls)==6
 roots=[reloc[int(r['file_offset'],16)] for r in cat['roots']];assert rom[0x17443:0x17477]==b''.join(x.to_bytes(2,'little') for x in roots)
 inverse={v:k for k,v in reloc.items()};old_tokens={t['offset']:t for t in cat['tokens']};paths=[]
 for root,oldroot in zip(roots,cat['roots']):
  expected=[];skip=-1
  for off in oldroot['token_offsets']:
   # Calls can jump backwards; use page membership, not a monotone skip.
   owner=next((p for p in pages if p['source_start']<=off<p['source_end']),None)
   if owner:
    if off==owner['source_start']:expected.append(('page',owner['entry_id']))
   else:expected.append(('token',off))
  pointer=root;stack=[];got=[]
  for _ in range(200):
   if pointer in page_by_new:
    p=page_by_new[pointer];got.append(('page',p['entry_id']));coverage.add(p['entry_id']);pointer=p['virtual_end'];continue
   assert pointer in inverse;old=inverse[pointer];got.append(('token',old));code=reconstructed[pointer-0xA000]
   if code==0xF4:
    assert not stack;stack.append(pointer+3);pointer=int.from_bytes(reconstructed[pointer-0xA000+1:pointer-0xA000+3],'little')
   elif code==0xF3:assert stack;pointer=stack.pop()
   elif code==0xFA:assert not stack;break
   else:
    assert code in (0xF9,0xF7,0xF8,0xF6,0xF5),hex(code);pointer+=old_tokens[old]['size']
  else:raise AssertionError('nonterminating registered graph')
  assert got==expected,(oldroot['script_id'],got,expected)
  paths.append({'root':oldroot['script_id'],'page_sequence':[v for k,v in got if k=='page'],'terminated':True})
 assert coverage==set(page_by_old[x]['entry_id'] for x in page_by_old)
 asm=json.loads((a.build/'assembly.json').read_text());helper=bytes((17,))+bytes.fromhex(''.join(r['hex'] for r in asm['helper']));stub=bytes.fromhex(''.join(r['hex'] for r in asm['stub']))
 ext=bytearray(0x20000);ext[0x2000:0x2000+len(helper)]=helper;ext[0x4000:0x4000+len(reconstructed)]=reconstructed
 ext[0x1C000:0x1E000]=src[0x1C010:0x1E010];ext[0x1E000:]=src[0x1E010:0x20010];ext[0x1FE8C:0x1FEB2]=stub+bytes((0xEA,))*(38-len(stub))
 irq=bytes.fromhex(''.join(r['hex'] for r in asm['irq']));ext[0x1FB72:0x1FBA2]=irq+bytes((0xEA,))*(48-len(irq));assert rom[0x20010:0x40010]==ext
 for path,h in {'workspace/translation/dialogue_ja_translated_ko.csv':'e274e97e75db79ea5d05b2e025cc70b7e9258a701bc1c10bea279ecbb4e8eb50','extracted/text/dialogue_20261001/dialogue_tokens.json':'506527702802a80da6b9c0710d97c4f028015dcf3f13cb30e3b26cfd2f9ee27a'}.items():assert sha((ROOT/path).read_bytes())==h
 result={'status':'PASS','output_sha256':sha(rom),'source_sha256':sha(src),'expected_writes':len(plan),'changed_bytes_with_append':len(diff),'all_diff_owned':True,'original_Japanese_974_bytes_preserved':True,'title_CHR_exact':True,'independent_font_pixels_and_protected_UI_slots':True,'registered_root_graphs':paths,'translated_blocks':22,'relocated_calls':6,'page_profiles':profiles,'rebuild_byte_identical':True,'real_IPS_apply_byte_identical':True,'scope':'Static/build/apply only. Reused kana slots require scene consumer QA.'}
 assert not a.output.exists();a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':'PASS','pages':22,'roots':26,'output_sha256':sha(rom)}))
if __name__=='__main__':main()
