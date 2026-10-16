"""Build two genuine page fonts using new PRG/CHR space and guarded source writes."""
import argparse,csv,hashlib,json,re,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from asm6502 import assemble,verify_profile
from build_dialogue_poc import encode,decode,FONT_SHA,TTF_SHA,TITLE_SHA,CSV_SHA
ROOT=Path(__file__).resolve().parents[1]
def sha(data):return hashlib.sha256(data).hexdigest()

def page(row,rom,sheet,font,prefix):
    lo=int(row['file_offset'],16);end=int(row['end_exclusive'],16)
    assert bytes.fromhex(row['raw_hex'])==rom[lo:end]
    text=row['translation_ko'];lines=text.split('\n');assert max(map(len,lines))<=16
    chars=list(dict.fromkeys(c for c in text if c not in ' \n'))
    assert len(chars)<=18,'This gate preserves Japanese codes; a larger page needs a new approved slot profile'
    mapping={' ':0,**dict(zip(chars,range(0x6E,0x80)))}
    banks=bytearray(rom[0x3E010:0x3E410]+rom[0x3A810:0x3AC10]);old=bytes(banks);glyphs=[]
    for c in chars:
        if '\uac00'<=c<='\ud7a3':
            index=ord(c)-0xAC00;x=index%64*8;y=index//64*8
            tile=sheet.crop((x,y,x+8,y+8))
            bits=tuple(int(tile.getpixel((px,py))[3]>0 and max(tile.getpixel((px,py))[:3])>127)
                       for py in range(8) for px in range(8));origin={'png_xy':[x,y]}
        elif c=='~':
            im=Image.new('L',(8,8));ImageDraw.Draw(im).text((0,0),c,font=font,fill=255)
            assert set(im.get_flattened_data())<={0,255}
            bits=tuple(int(v>127) for v in im.get_flattened_data());origin={'ttf_size_px':8}
        else:raise ValueError(f'Unmapped character {c!r}')
        assert any(bits);raw=encode(bits);assert decode(raw)==tuple(2*v for v in bits)
        code=mapping[c];banks[code*16:code*16+16]=raw
        glyphs.append({'char':c,'code':code,'source':origin,'bytes_hex':raw.hex()})
    tokens=json.loads((ROOT/'extracted/text/dialogue_20261001/dialogue_tokens.json').read_text(encoding='utf-8'))
    for code in map(lambda x:int(x,16),tokens['glyphs']):assert banks[code*16:code*16+16]==old[code*16:code*16+16]
    body=bytearray(prefix)
    original_nonblank=sum(int(t,16)!=0 for t in re.findall(r'\{tile:([0-9A-F]{2})\}',row['source_tokens']))
    compensation=(original_nonblank-sum(c not in ' \n' for c in text))*4
    assert 0<compensation<=256
    # Match the native typing interval, including the mouth-animation phase.
    # Keep F7 46 at its native frame, rather than extending the closed-mouth hold.
    printed=sum(c not in ' \n' for c in text)
    duration,remainder=divmod(original_nonblank*4,printed)
    first_duration=duration+remainder
    assert 1<=duration<=first_duration<=256
    if body[:2]==bytes.fromhex('F8 03'):
        body[1]=first_duration-1
    else:
        body.extend((0xF8,first_duration-1))
    first_printed=False
    for c in text:
        body.append(0xF5 if c=='\n' else mapping[c])
        if c not in ' \n' and not first_printed:
            body.extend((0xF8,duration-1));first_printed=True
    body.extend((0xF8,0x03,0xF7,0x46))
    timing_mode=f'typing: first glyph {first_duration} frames, remaining {printed-1} glyphs {duration} frames; native F7 46'
    gap=end-lo-len(body);padding=gap;assert gap>=0
    if gap%2:
        # Idempotent final cursor position, followed by idempotent speed commands.
        body.extend((0xF6,4+len(lines[-1]),4+len(lines)-1));gap-=3;assert gap>=0
    body.extend(bytes.fromhex('F8 03')*(gap//2));assert len(body)==end-lo
    return bytes(body),bytes(banks),{'entry_id':row['entry_id'],'translation_ko':text,'source_start':lo,'source_end':end,
           'mapping':mapping,'glyphs':glyphs,'timing_compensation_frames':compensation,'timing_mode':timing_mode,'source_delay_preserved':'F7 46',
           'payload_hex':body.hex(),'neutral_tail_bytes':padding,
           'typing_frames':original_nonblank*4,'first_glyph_frames':first_duration,'other_glyph_frames':duration}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    source=json.loads((ROOT/'manifests/source_rom.json').read_text(encoding='utf-8'))
    rom=(ROOT/source['path']).read_bytes();assert len(rom)==source['size_bytes'] and sha(rom)==source['sha256']
    title_dir=ROOT/'build/title_kr_ai_004';title=(title_dir/'TinyToon_title_kr_poc.nes').read_bytes();assert sha(title)==TITLE_SHA
    old_poc=(ROOT/'build/dialogue_kr_poc_004/TinyToon_dialogue_kr_poc.nes').read_bytes()
    assert sha(old_poc)=='2ea18504ce157ad16ab21dba70986f6cad1872346e9122d597af6aef690bebf2'
    csvfile=ROOT/'workspace/translation/dialogue_ja.csv';assert sha(csvfile.read_bytes())==CSV_SHA
    rows={r['entry_id']:r for r in csv.DictReader(csvfile.open(encoding='utf-8-sig',newline=''))}
    fontdir=ROOT/'workspace/fonts/galmuri7_8x8'
    assert sha((fontdir/'Galmuri7_8x8.png').read_bytes())==FONT_SHA and sha((fontdir/'Galmuri7.ttf').read_bytes())==TTF_SHA
    sheet=Image.open(fontdir/'Galmuri7_8x8.png').convert('RGBA');font=ImageFont.truetype(str(fontdir/'Galmuri7.ttf'),8)
    first,fonts1,p1=page(rows['JP_175A9'],rom,sheet,font,bytes.fromhex('F8 03 F6 04 04'))
    second,fonts2,p2=page(rows['JP_175CF'],rom,sheet,font,b'')
    assert fonts1==old_poc[0x40010:0x40810],'First verified Korean font changed'
    p1['chr_banks']=[128,129];p2['chr_banks']=[130,131]
    base=0xB599;constants={'SELECTOR_BANK':17,'SELECTOR_ENTRY':0xA000,'COMMON_LOW':base&255,'COMMON_HIGH':base>>8,
        'SECOND_THRESHOLD':p2['source_start']-p1['source_start']+1,
        'THIRD_THRESHOLD':0x175EE-p1['source_start']+1}
    stub,stub_listing,stub_symbols=assemble((ROOT/'workspace/asm/dialogue_paged_stub.asm').read_text(),0xFE8C,constants)
    selector,selector_listing,selector_symbols=assemble((ROOT/'workspace/asm/dialogue_paged_selector.asm').read_text(),0xA000,constants)
    assert len(stub)<=38 and len(selector)<0x2000
    original_irq=bytes.fromhex('A4 57 F0 21 A9 08 A2 07 8D 00 B0 8E 04 B0 A9 0A A2 06 8D 08 B0 8E 0C B0 88 F0 0A A9 09 A2 07 8D 08 C0 8E 0C C0 60')
    assert rom[0x1FE9C:0x1FEC2]==original_irq and len(original_irq)==38
    # Expand to power-of-two 256KiB PRG / 256KiB CHR. Move fixed bank copies
    # to PRG 30/31, preserving every native CPU address. Old banks remain intact.
    extension=bytearray(0x20000)
    extension[0x2000:0x2000+len(selector)]=selector  # new PRG 17, CPU A000
    extension[0x1C000:0x1E000]=rom[0x1C010:0x1E010] # new fixed PRG 30
    extension[0x1E000:]=rom[0x1E010:0x20010]        # new fixed PRG 31
    stub_off=0x1E000+0x1E8C
    extension[stub_off:stub_off+38]=stub+bytes([0xEA])*(38-len(stub))
    chr_tail=fonts1+fonts2+bytes(0x20000-0x1000)
    # Immutable-source plan. A moved/expanded container has explicit copy rules.
    plan=[]
    def register(owner,reason,offset,final,rule=None):
        overlap=max(0,min(len(final),len(rom)-offset))
        plan.append({'owner':owner,'reason':reason,'file_offset':offset,'length':len(final),
                     'expected_source_sha256':source['sha256'],'expected_overlap_length':overlap,
                     'expected_overlap_sha256':sha(rom[offset:offset+overlap]),
                     'final_hex':bytes(final).hex(),'rule':rule})
    header=bytearray(rom[:16]);header[4]=16;header[5]=32
    register('header','Power-of-two PRG/CHR expansion, all other fields identical',0,header)
    # Retain existing title writes in PRG only; moved title CHR is exact golden data.
    for w in json.loads((title_dir/'expected_writes.json').read_text(encoding='utf-8')):
        if w['file_offset']<0x20010:
            assert rom[w['file_offset']:w['file_offset']+w['length']]==bytes.fromhex(w['expected_hex'])
            register('preserved_title_prg',w['reason'],w['file_offset'],bytes.fromhex(w['final_hex']))
    register('JP_175A9','Same Korean wording/font; native typing and hold intervals restored',0x175A9,first)
    register('JP_175CF','Second Korean page, same extent and next-page timing',0x175CF,second)
    register('new_prg','Fresh banks, selector 17 and fixed-bank copies 30/31',0x20010,extension,
             {'bank17_code_length':len(selector),'bank30_source':[0x1C010,0x1E010],
              'bank31_source':[0x1E010,0x20010],'bank31_edit_cpu_range':[0xFE8C,0xFEB2],
              'all_other_new_prg_bytes':0})
    register('moved_chr','Exact verified title CHR, with every other original CHR byte preserved',0x40010,title[0x20010:0x40010],
             {'copy_from_verified_title_range':[0x20010,0x40010],'copy_sha256':sha(title[0x20010:0x40010])})
    register('new_page_fonts','Four cloned banks and explicit fresh CHR padding',0x60010,chr_tail,
             {'font_banks':[128,129,130,131],'all_remaining_new_chr_bytes':0})
    allowed=set()
    for w in plan:
        offset=w['file_offset'];length=w['length'];region=set(range(offset,offset+length))
        assert not allowed&region;allowed|=region
        assert sha(rom[offset:offset+w['expected_overlap_length']])==w['expected_overlap_sha256']
    output=bytearray(rom)
    for w in sorted(plan,key=lambda w:w['file_offset']):
        assert w['file_offset']<=len(output)
        output[w['file_offset']:w['file_offset']+w['length']]=bytes.fromhex(w['final_hex'])
    assert len(output)==0x80010
    diff={i for i in range(len(output)) if i>=len(rom) or output[i]!=rom[i]};assert diff<=allowed
    assert output[0x40010:0x60010]==title[0x20010:0x40010]
    assert output[0x3C010:0x3E010]==rom[0x1C010:0x1E010]
    assert output[0x10:0x3654]==rom[0x10:0x3654]
    out=a.output.resolve();out.relative_to((ROOT/'build').resolve());out.mkdir(parents=True,exist_ok=False)
    (out/'expected_writes.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
    (out/'assembly.json').write_text(json.dumps({'constants':constants,'stub':stub_listing,'selector':selector_listing,
       'stub_symbols':stub_symbols,'selector_symbols':selector_symbols,'profile':verify_profile()},indent=2)+'\n',encoding='utf-8')
    (out/'pages.json').write_text(json.dumps([p1,p2],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'TinyToon_dialogue_paged.nes').write_bytes(output)
    report={'source_sha256':sha(rom),'title_base_sha256':TITLE_SHA,'first_poc_sha256':sha(old_poc),
            'output_sha256':sha(output),'output_rom':'TinyToon_dialogue_paged.nes','output_size':len(output),
            'translated_blocks':2,'total_blocks':22,'entry_ids':[p1['entry_id'],p2['entry_id']],
            'csv_sha256':CSV_SHA,'font_png_sha256':FONT_SHA,'ttf_sha256':TTF_SHA,'chr_file_base':0x40010,
            'selector_prg_bank':17,'fixed_prg_banks':[30,31],'stub_size':len(stub),'selector_size':len(selector),
            'new_chr_banks':[128,129,130,131],'no_new_shared_ram':True,'text_relocation':'not needed: both payloads fit original extents',
            'fresh_code_allocation':'expanded bank 17; existing PRG padding is not reclaimed',
            'expected_write_count':len(plan),'changed_bytes_including_append':len(diff),
            'scope':'Two common Shirley pages; all other scripts/glyphs preserved. Runtime and whole-game scope separate.'}
    (out/'build_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
