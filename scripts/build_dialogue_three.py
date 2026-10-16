"""Build three Shirley pages, preserving native A-button tiles and F3 return."""
import argparse,csv,hashlib,json,re,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from asm6502 import assemble,verify_profile
from build_dialogue_poc import encode,decode,FONT_SHA,TTF_SHA,TITLE_SHA,CSV_SHA
ROOT=Path(__file__).resolve().parents[1]
from build_dialogue_paged import page
def sha(data):return hashlib.sha256(data).hexdigest()

def third_page(row,rom,sheet):
    lo=int(row['file_offset'],16);end=int(row['end_exclusive'],16)
    assert (lo,end)==(0x175EE,0x1760A) and bytes.fromhex(row['raw_hex'])==rom[lo:end]
    text=row['translation_ko'];assert max(map(len,text.split('\n')))<=16
    chars=list(dict.fromkeys(c for c in text if '\uac00'<=c<='\ud7a3'));assert len(chars)==12
    mapping={' ':0,'〈':0x6C,'A':0x6B,'〉':0x6D,**dict(zip(chars,range(0x6E,0x80)))}
    fonts=bytearray(rom[0x3E010:0x3E410]+rom[0x3A810:0x3AC10]);old=bytes(fonts);glyphs=[]
    for c in chars:
        idx=ord(c)-0xAC00;x=idx%64*8;y=idx//64*8
        bits=tuple(int((p:=sheet.getpixel((x+dx,y+dy)))[3]>0 and max(p[:3])>127) for dy in range(8) for dx in range(8))
        raw=encode(bits);assert decode(raw)==tuple(2*v for v in bits)
        code=mapping[c];fonts[code*16:code*16+16]=raw
        glyphs.append({'char':c,'code':code,'source':{'png_xy':[x,y]},'bytes_hex':raw.hex()})
    for code in range(0x6E):assert fonts[code*16:code*16+16]==old[code*16:code*16+16]
    assert sum(c not in ' \n' for c in text)==17
    # 26 native nonblank tiles * 4 = first 8 + remaining 16 * 6 = 104.
    body=bytearray((0xF8,7));first=False
    for c in text:
        body.append(0xF5 if c=='\n' else mapping[c])
        if c not in ' \n' and not first:body.extend((0xF8,5));first=True
    body.extend((0xF8,3,0xF3));assert len(body)==28
    # Move the executed F3 one byte earlier within the owned text extent.
    # The source F3 byte remains unchanged and is bypassed after this return.
    callers=[]
    for cpu in (0xB516,0xB51A,0xB543,0xB56C,0xB591,0xB595):
        off=cpu+0xC010;assert rom[off:off+3]==bytes.fromhex('F4 99 B5')
        assert rom[off+3]==0xFA or rom[off+3:off+6]==bytes.fromhex('F7 46 F9')
        callers.append({'root_cpu':cpu,'return_base_cpu':cpu+2,'saved_cursor':1,'continuation_hex':rom[off+3:off+6].hex()})
    return bytes(body),bytes(fonts),{'entry_id':row['entry_id'],'translation_ko':text,'source_start':lo,'source_end':end,
        'mapping':mapping,'glyphs':glyphs,'chr_banks':[132,133],'payload_hex':body.hex(),'typing_frames':104,
        'first_glyph_frames':8,'other_glyph_frames':6,'source_delay_preserved':None,'neutral_tail_bytes':0,
        'speed_restore':'F8 03 before F3; native caller delays remain unchanged',
        'preserved_button_codes':[0x6C,0x6B,0x6D],'callers':callers,'original_F3_preserved_at':0x1760A,
        'executed_F3_at':0x17609,'return_policy':'one-byte-earlier F3 inside owned third-page extent'}


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
    third,fonts3,p3=third_page(rows['JP_175EE'],rom,sheet)
    previous=(ROOT/'build/dialogue_paged_003/TinyToon_dialogue_paged.nes').read_bytes()
    assert sha(previous)=='74429c6658e36ff3f1e71a0bf547b801bdbf6f04700d9529b8c0d24664ce34bb'
    assert first==previous[0x175A9:0x175CE] and second==previous[0x175CF:0x175ED]
    assert fonts1+fonts2==previous[0x60010:0x61010]
    assert fonts1==old_poc[0x40010:0x40810],'First verified Korean font changed'
    p1['chr_banks']=[128,129];p2['chr_banks']=[130,131]
    base=0xB599;constants={'SELECTOR_BANK':17,'SELECTOR_ENTRY':0xA000,'COMMON_LOW':base&255,'COMMON_HIGH':base>>8,
        'SECOND_THRESHOLD':p2['source_start']-p1['source_start']+1,
        'THIRD_THRESHOLD':0x175EE-p1['source_start']+1}
    stub,stub_listing,stub_symbols=assemble((ROOT/'workspace/asm/dialogue_paged_stub.asm').read_text(),0xFE8C,constants)
    selector,selector_listing,selector_symbols=assemble((ROOT/'workspace/asm/dialogue_three_selector.asm').read_text(),0xA000,constants)
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
    chr_tail=fonts1+fonts2+fonts3+bytes(0x20000-0x1800)
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
    register('JP_175EE','Third page and native A-button tiles; executed F3 one byte earlier, speed restored',0x175EE,third)
    register('new_prg','Fresh banks, selector 17 and fixed-bank copies 30/31',0x20010,extension,
             {'bank17_code_length':len(selector),'bank30_source':[0x1C010,0x1E010],
              'bank31_source':[0x1E010,0x20010],'bank31_edit_cpu_range':[0xFE8C,0xFEB2],
              'all_other_new_prg_bytes':0})
    register('moved_chr','Exact verified title CHR, with every other original CHR byte preserved',0x40010,title[0x20010:0x40010],
             {'copy_from_verified_title_range':[0x20010,0x40010],'copy_sha256':sha(title[0x20010:0x40010])})
    register('new_page_fonts','Six cloned banks and explicit fresh CHR padding',0x60010,chr_tail,
             {'font_banks':[128,129,130,131,132,133],'all_remaining_new_chr_bytes':0})
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
    (out/'pages.json').write_text(json.dumps([p1,p2,p3],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'TinyToon_dialogue_three.nes').write_bytes(output)
    report={'source_sha256':sha(rom),'title_base_sha256':TITLE_SHA,'first_poc_sha256':sha(old_poc),
            'output_sha256':sha(output),'output_rom':'TinyToon_dialogue_three.nes','output_size':len(output),
            'translated_blocks':3,'total_blocks':22,'entry_ids':[p1['entry_id'],p2['entry_id'],p3['entry_id']],
            'previous_build_sha256':sha(previous),
            'csv_sha256':CSV_SHA,'font_png_sha256':FONT_SHA,'ttf_sha256':TTF_SHA,'chr_file_base':0x40010,
            'selector_prg_bank':17,'fixed_prg_banks':[30,31],'stub_size':len(stub),'selector_size':len(selector),
            'new_chr_banks':[128,129,130,131,132,133],'no_new_shared_ram':True,'text_relocation':'not needed: three payloads fit original extents',
            'fresh_code_allocation':'expanded bank 17; existing PRG padding is not reclaimed',
            'expected_write_count':len(plan),'changed_bytes_including_append':len(diff),
            'scope':'Three common Shirley pages; all other scripts/glyphs preserved. Runtime and whole-game scope separate.'}
    (out/'build_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
