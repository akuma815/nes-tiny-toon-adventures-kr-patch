"""Relocate the registered 26 roots/22 translated pages into fresh PRG bank18."""
import argparse,csv,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from asm6502 import assemble,verify_profile
from build_dialogue_poc import encode,FONT_SHA,TTF_SHA,CSV_SHA,TITLE_SHA
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def wrap(text):
 out=[]
 for line in text.split('\n'):
  while len(line)>16:
   n=line.rfind(' ',0,16)+1 or 16;out.append(line[:n]);line=line[n:]
  out.append(line)
 assert len(out)<=7
 return '\n'.join(out)
def build():
 manifest=json.loads((ROOT/'manifests/source_rom.json').read_text());src=(ROOT/manifest['path']).read_bytes();assert sha(src)==manifest['sha256']
 title=(ROOT/'build/title_kr_ai_004/TinyToon_title_kr_poc.nes').read_bytes();assert sha(title)==TITLE_SHA
 csvpath=ROOT/'workspace/translation/dialogue_ja.csv';assert sha(csvpath.read_bytes())==CSV_SHA
 rows=list(csv.DictReader(csvpath.open(encoding='utf-8-sig',newline='')))
 catalog=json.loads((ROOT/'extracted/text/dialogue_20261001/dialogue_tokens.json').read_text(encoding='utf-8'))
 fontdir=ROOT/'workspace/fonts/galmuri7_8x8';assert sha((fontdir/'Galmuri7_8x8.png').read_bytes())==FONT_SHA
 assert sha((fontdir/'Galmuri7.ttf').read_bytes())==TTF_SHA
 sheet=Image.open(fontdir/'Galmuri7_8x8.png').convert('RGBA');ttf=ImageFont.truetype(str(fontdir/'Galmuri7.ttf'),8)
 native={' ':0,'3':0x3A,'0':0x3B,'!':0x36,'「':0x37,'」':0x38,'〈':0x6C,'A':0x6B,'〉':0x6D}
 slots=list(range(0x6E,0x80))+list(range(1,0x13));pages=[];bodies={}
 for pid,row in enumerate(rows):
  start=int(row['file_offset'],16);end=int(row['end_exclusive'],16)
  assert bytes.fromhex(row['raw_hex'])==src[start:end]
  ts=[t for t in catalog['tokens'] if start<=t['offset']<end];text=wrap(row['translation_ko'])
  chars=list(dict.fromkeys(c for c in text if c!='\n' and c not in native));assert len(chars)<=len(slots)
  mapping={c:native[c] for c in text if c in native};mapping.update(zip(chars,slots))
  fonts=bytearray(src[0x3E010:0x3E410]+src[0x3A810:0x3AC10]);glyphs=[]
  for c in chars:
   if '\uac00'<=c<='\ud7a3':
    idx=ord(c)-0xAC00;x=idx%64*8;y=idx//64*8
    bits=tuple(int((p:=sheet.getpixel((x+dx,y+dy)))[3]>0 and max(p[:3])>127) for dy in range(8) for dx in range(8));origin={'png_xy':[x,y]}
   else:
    im=Image.new('L',(8,8));ImageDraw.Draw(im).text((0,0),c,font=ttf,fill=255)
    assert set(im.get_flattened_data())<={0,255};bits=tuple(int(v>127) for v in im.get_flattened_data());origin={'ttf_px':8}
   assert any(bits);raw=encode(bits);code=mapping[c];fonts[code*16:code*16+16]=raw
   glyphs.append({'char':c,'code':code,'bytes_hex':raw.hex(),'source':origin})
  # Copy non-visible prefix/suffix exactly except original speed is replaced.
  visible=[i for i,t in enumerate(ts) if t['name'] in ('glyph','br')];lo=min(visible);hi=max(visible)
  prefix=b''.join(bytes.fromhex(t['raw_hex']) for t in ts[:lo] if t['name']!='speed')
  suffix=b''.join(bytes.fromhex(t['raw_hex']) for t in ts[hi+1:])
  middle=[t for t in ts[lo:hi+1] if t['name'] not in ('glyph','br')]
  count=sum(t['name']=='glyph' and t['code']!=0 for t in ts);new_count=sum(c not in ' \n' for c in text)
  duration,remainder=divmod(count*4,new_count);assert duration>=1
  body=bytearray((0xF8,duration+remainder-1));body.extend(prefix)
  first=False;printed=0;first_glyph=None
  # Last-page pauses retain all eight F7 14 commands, mapped to Korean anchors.
  anchors={10:1,15:2,16:3,17:2} if middle else {}
  assert not middle or row['entry_id']=='JP_1780B' and len(middle)==8 and all(t['raw_hex']=='F7 14' for t in middle)
  for c in text:
   if c=='\n':body.append(0xF5);continue
   if c!=' ' and first_glyph is None:first_glyph=len(body)
   body.append(mapping[c])
   if c!=' ':
    printed+=1
    if not first and remainder:body.extend((0xF8,duration-1))
    first=True
    for _ in range(anchors.get(printed,0)):body.extend((0xF7,0x14))
  body.extend((0xF8,3));body.extend(suffix)
  assert sum(anchors.values())==len(middle)
  p={'entry_id':row['entry_id'],'page_id':pid,'translation_ko':row['translation_ko'],'display_text':text,
     'source_start':start,'source_end':end,'mapping':mapping,'glyphs':glyphs,'chr_banks':[128+pid*2,129+pid*2],
     'payload_hex':body.hex(),'first_glyph_relative':first_glyph,'typing_frames':count*4,
     'original_delays':[t['args'][0] for t in ts if t['name']=='delay'],'middle_pause_anchors':anchors,
     'extra_slots':[mapping[c] for c in chars if mapping[c]<0x6E]}
  pages.append(p);bodies[start]=(end,bytes(body),bytes(fonts))
 # Rebuild complete original token graph; only approved pointers/calls relocate.
 data=bytearray();reloc={};calls=[];i=0;tokens=catalog['tokens']
 while i<len(tokens):
  t=tokens[i];off=t['offset'];reloc[off]=0xA000+len(data)
  if off in bodies:
   end,body,_=bodies[off];p=next(p for p in pages if p['source_start']==off)
   p['virtual_start']=0xA000+len(data);p['first_glyph_consumed']=p['virtual_start']+p['first_glyph_relative']+1
   data.extend(body);p['virtual_end']=0xA000+len(data)
   while i<len(tokens) and tokens[i]['offset']<end:i+=1
   continue
  if t['name']=='call':calls.append((len(data),off,int.from_bytes(bytes(t['args']),'little')+0xC010))
  data.extend(bytes.fromhex(t['raw_hex']));i+=1
 assert len(data)<0x2000
 for pos,off,target in calls:data[pos+1:pos+3]=reloc[target].to_bytes(2,'little')
 roots=[reloc[int(r['file_offset'],16)] for r in catalog['roots']]
 aliases=[]
 for pos,off,target in calls:
  assert target==0x175A9
  continuation=src[off+3];return_base=reloc[off]+2
  if continuation==0xFA:threshold=3
  else:
   nxt=next(p for p in pages if p['source_start']>off)
   threshold=nxt['first_glyph_consumed']-return_base
  assert 0<threshold<256
  aliases.append({'base':return_base,'cursor_below':threshold,'page_id':10,'source_call':off})
 # Fresh code in bank17 at 8000. Mode/result and native pair-bank are on stack.
 code=['TXA','PHA','TSX','LDA $0105,X','BEQ @FONT','JMP @FETCH','FONT:',
       'LDY $57','BNE @ACTIVE_FONT','JMP @DONE','ACTIVE_FONT:']
 for k,a in enumerate(aliases):
  label=f'ALIAS_{k}'
  code+=['LDA $BF',f'CMP #${a["base"]&255:02X}',f'BNE @{label}','LDA $C0',f'CMP #${a["base"]>>8:02X}',f'BNE @{label}',
         'LDA $07A9',f'CMP #${a["cursor_below"]:02X}',f'BCS @{label}',f'LDX #${a["page_id"]:02X}','JMP @SELECT',label+':']
 code+=['LDA $C0','CMP #$A0','BCS @LOW_OK','JMP @ORIGINAL','LOW_OK:',f'CMP #${((0xA000+len(data)-1)>>8)+1:02X}','BCC @HIGH_OK','JMP @ORIGINAL','HIGH_OK:',
        'LDA $BF','CLC','ADC $07A9','PHA','LDA $C0','ADC #$00','TAX','PLA']
 for p in reversed(pages):
  addr=p['first_glyph_consumed'];label=f'NEXT_{p["page_id"]}';match=f'MATCH_{p["page_id"]}'
  code+=[f'CPX #${addr>>8:02X}',f'BCC @{label}',f'BNE @{match}',f'CMP #${addr&255:02X}',f'BCC @{label}',match+':',f'LDX #${p["page_id"]:02X}','JMP @SELECT',label+':']
 code+=['JMP @ORIGINAL','SELECT:','TXA','ASL A','ORA #$80','PHA','LSR A','LSR A','LSR A','LSR A','TAX','PLA','AND #$0F',
        'STA $B000','STX $B004','ORA #$01','STA $B008','STX $B00C',
        'STA $6003','STX $6002','AND #$FE','STA $6001','STX $6000','JMP @EXTRA',
        'ORIGINAL:','LDY $57','BNE @NATIVE_FONT','JMP @DONE','NATIVE_FONT:','LDA #$08','LDX #$07','STA $B000','STX $B004',
        'STA $6001','STX $6000','LDA #$0A','LDX #$06','STA $B008','STX $B00C','STA $6003','STX $6002',
        'EXTRA:','LDY $57','BEQ @DONE','DEY','BEQ @DONE',
        'LDA #$09','LDX #$07','STA $C008','STX $C00C','DONE:','PLA','TAX','CLC','RTS',
        'FETCH:','LDA $C0','CMP #$A0','BCC @NATIVE_READ',f'CMP #${((0xA000+len(data)-1)>>8)+1:02X}','BCS @NATIVE_READ',
        'LDA $0104,X','CLC','ADC #$01','PHA','LDA #$12','STA $A000','LDY $07A9','READ_NEW:','LDA ($BF),Y',
        'STA $0105,X','PLA','STA $A000','JMP @ADVANCE','NATIVE_READ:','LDY $07A9','LDA ($BF),Y','STA $0105,X',
        'ADVANCE:','INC $07A9','BNE @READ_DONE','INC $C0','READ_DONE:','PLA','TAX','SEC','RTS']
 # Preserve the native $8000 bank identifier contract, including nested NMI.
 asm='\n'.join(code)+'\n';helper,listing,symbols=assemble(asm,0x8001);helper=bytes((17,))+helper;assert len(helper)<0x2000
 stub,stub_listing,stub_symbols=assemble((ROOT/'workspace/asm/dialogue_full_stub.asm').read_text(),0xFE8C)
 assert len(stub)<=38 and stub_symbols['READ_ENTRY']==0xFE94
 # SEI does not mask NMI. Disable only PPUCTRL.7 before temporary banking;
 # the stub restores the native FF shadow through D1FF after BOTH banks return.
 assert src[0x1D20F:0x1D215]==bytes.fromhex('A5 FF 8D 00 20 60')
 reader,reader_listing,_=assemble('LDA $FF\nAND #$7F\nSTA $2000\nJSR $FE94\nORA #$00\nRTS\n',0xB271);assert len(reader)==13
 assert src[0x17281:0x17290]==bytes.fromhex('AC A9 07 B1 BF EE A9 07 D0 02 E6 C0 09 00 60')
 extension=bytearray(0x20000);extension[0x2000:0x2000+len(helper)]=helper;extension[0x4000:0x4000+len(data)]=data
 extension[0x1C000:0x1E000]=src[0x1C010:0x1E010];extension[0x1E000:]=src[0x1E010:0x20010]
 extension[0x1FE8C:0x1FEB2]=stub+bytes((0xEA,))*(38-len(stub))
 # Intro/ending raster IRQ restores text fonts again below the portrait.
 # Cache four register values in explicit patch-owned PRG RAM. The IRQ
 # reads them directly, avoiding the variable-duration page lookup here.
 assert src[0x1FB99:0x1FBAD]==bytes.fromhex('A9 07 A2 08 A0 0A 8E 00 B0 8D 04 B0 A9 06 8C 08 B0 8D 0C B0')
 irq_asm='BIT $00\nLDY #$6E\nJSR $F8BE\nLDA $6000\nLDX $6001\nLDY $6003\nSTX $B000\nSTA $B004\nLDA $6002\nSTY $B008\nSTA $B00C\nINC $41\nJMP $FD57\n'
 irq,irq_listing,_=assemble(irq_asm,0xFB72);assert len(irq)==36
 extension[0x1FB72:0x1FBA2]=irq+bytes((0xEA,))*(48-len(irq))
 tail=b''.join(bodies[p['source_start']][2] for p in pages);tail+=bytes(0x20000-len(tail))
 plan=[]
 def reg(owner,offset,final,reason):
  overlap=max(0,min(len(final),len(src)-offset));plan.append({'owner':owner,'file_offset':offset,'length':len(final),
   'expected_source_sha256':sha(src),'expected_overlap_length':overlap,'expected_overlap_sha256':sha(src[offset:offset+overlap]),'final_hex':bytes(final).hex(),'reason':reason})
 hdr=bytearray(src[:16]);hdr[4]=16;hdr[5]=32;hdr[8]=1;reg('header',0,hdr,'PRG/CHR 256KiB each; explicit 8KiB PRG RAM')
 for w in json.loads((ROOT/'build/title_kr_ai_004/expected_writes.json').read_text()):
  if w['file_offset']<0x20010:reg('preserved_title_prg',w['file_offset'],bytes.fromhex(w['final_hex']),w['reason'])
 reg('reader_hook',0x17281,reader+bytes((0xEA,))*2,'NMI guarded banked read; original cursor/flags contract')
 reg('registered_root_pointers',0x17443,b''.join(x.to_bytes(2,'little') for x in roots),'Exactly 26 approved root pointers')
 reg('new_prg',0x20010,extension,'Helper bank17/data18; original fixed banks copied to30/31')
 reg('moved_chr',0x40010,title[0x20010:0x40010],'Exact verified title CHR')
 reg('page_fonts',0x60010,tail,'22 separate cloned pairs; explicit fresh padding')
 target=bytearray(src);owned=set()
 for w in sorted(plan,key=lambda w:w['file_offset']):
  off=w['file_offset'];n=w['length'];r=set(range(off,off+n));assert not r&owned;owned|=r
  assert sha(src[off:off+w['expected_overlap_length']])==w['expected_overlap_sha256']
  target[off:off+n]=bytes.fromhex(w['final_hex'])
 assert len(target)==0x80010
 assert all(i in owned for i in range(len(target)) if i>=len(src) or target[i]!=src[i])
 assert target[0x17477:0x17845]==src[0x17477:0x17845]
 report={'source_sha256':sha(src),'title_base_sha256':TITLE_SHA,'csv_sha256':CSV_SHA,'font_png_sha256':FONT_SHA,
  'ttf_sha256':TTF_SHA,'output_rom':'TinyToon_dialogue_full.nes','output_sha256':sha(target),'output_size':len(target),
  'translated_blocks':22,'registered_roots':26,'data_bank':18,'helper_bank':17,'data_bytes':len(data),'helper_bytes':len(helper),
  'stub_bytes':len(stub),'helper_entry':0x8001,'helper_bank_identifier':17,'raster_font_hook':0xFB72,'chr_file_base':0x40010,'aliases':aliases,'roots':roots,'expected_write_count':len(plan),
  'no_new_shared_RAM':False,'patch_owned_PRG_RAM':[0x6000,0x6001,0x6002,0x6003],'font_slots':slots,'scope':'All registered Japanese dialogue; full-game QA separate'}
 assembly={'helper':listing,'stub':stub_listing,'reader':reader_listing,'irq':irq_listing,'helper_symbols':symbols,'stub_symbols':stub_symbols,'profile':verify_profile()}
 return target,report,plan,pages,assembly,asm,reloc
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 target,report,plan,pages,assembly,asm,reloc=build();out=a.output.resolve();out.relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 for name,v in [('build_report',report),('expected_writes',plan),('pages',pages),('assembly',assembly),('relocation',reloc)]:
  (out/(name+'.json')).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (out/'helper.asm').write_text(asm,encoding='ascii');(out/report['output_rom']).write_bytes(target);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
