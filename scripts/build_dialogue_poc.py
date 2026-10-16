"""Build a narrowly scoped Galmuri7 dialogue PoC alongside the verified title.

No new instructions, cave allocation, text relocation or original font overwrite.
Two copied CHR banks are appended; four IRQ mapper constants select them.
Only JP_175A9 is translated. Unused source codes are scoped to the known script
and must still pass scene comparison before promotion to a full implementation.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import sys
from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version

ROOT=Path(__file__).resolve().parents[1]
FONT_SHA='a2be473e22a62942164c95db60f3f5aa88a99f76b525994d194e9f5f9df387ea'
TTF_SHA='3882bd35066c26b0392cd4963ff9b3c151041dec34adc9d5633d137d1d9b9855'
TITLE_SHA='beb669edda6c666a10c7b933f5ebee5eecda81ca46d31d17e33d51d6657103b4'
CSV_SHA='85aa940ba608ad8e5edd6ed782f106c89f703d18288f923e0298e5b51bc5eafc'

def sha(data):return hashlib.sha256(data).hexdigest()

def encode(bits):
    assert len(bits)==64 and set(bits)<={0,1}
    # The observed font uses pixel value 2: low plane zero, high plane ink.
    return bytes(8)+bytes(sum(bits[y*8+x]<<(7-x) for x in range(8)) for y in range(8))

def decode(data):
    assert len(data)==16
    return tuple(((data[y]>>(7-x))&1)|(((data[y+8]>>(7-x))&1)<<1) for y in range(8) for x in range(8))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--font-png',type=Path,required=True)
    ap.add_argument('--symbol-font',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    source=json.loads((ROOT/'manifests/source_rom.json').read_text(encoding='utf-8'))
    rom=(ROOT/source['path']).read_bytes()
    assert len(rom)==source['size_bytes'] and sha(rom)==source['sha256']
    assert rom[:6]==b'NES\x1a\x08\x10' and len(rom)==0x40010
    assert sha(a.font_png.read_bytes())==FONT_SHA,'Supplied font PNG identity mismatch'
    assert sha(a.symbol_font.read_bytes())==TTF_SHA,'Companion symbol font identity mismatch'
    csv_path=ROOT/'workspace/translation/dialogue_ja.csv'
    assert sha(csv_path.read_bytes())==CSV_SHA,'PoC translation input differs; review explicit profile'
    rows=list(csv.DictReader(csv_path.open(encoding='utf-8-sig',newline='')))
    row=next(r for r in rows if r['entry_id']=='JP_175A9')
    text=row['translation_ko'];assert text=='하이~ 셜리 더 룬이야\n난 예언자거든'
    assert row['raw_hex']==rom[0x175A9:0x175CE].hex(' ').upper()
    assert all(len(line)<=16 for line in text.split('\n'))
    tokens=json.loads((ROOT/'extracted/text/dialogue_20261001/dialogue_tokens.json').read_text(encoding='utf-8'))
    original_codes={int(k,16) for k in tokens['glyphs']}
    # $3C-$48 are used by partner-selection UI. This replacement pool was
    # absent from both nametables outside the text rectangle in six source
    # dialogue captures; preserve all known Japanese/Latin codes and UI tiles.
    pool=list(range(0x6E,0x7C))
    assert not original_codes.intersection(pool)
    chars=list(dict.fromkeys(c for c in text if c not in ' \n'))
    assert len(chars)==len(pool)==14
    mapping={' ':0,**dict(zip(chars,pool))}
    sheet=Image.open(a.font_png).convert('RGBA');assert sheet.size==(512,1400)
    symbol=ImageFont.truetype(str(a.symbol_font),8)
    # These two banks were observed at PPU $0000/$0400 in the text scanlines.
    banks=bytearray(rom[0x3E010:0x3E410]+rom[0x3A810:0x3AC10])
    before=bytes(banks);glyphs=[]
    assert set(decode(before[16:32]))=={0,2},'Source font ink palette index changed'
    for c in chars:
        if '\uac00'<=c<='\ud7a3':
            index=ord(c)-0xAC00;x=index%64*8;y=index//64*8
            tile=sheet.crop((x,y,x+8,y+8))
            bits=tuple(int(tile.getpixel((px,py))[3]>0 and max(tile.getpixel((px,py))[:3])>127)
                       for py in range(8) for px in range(8))
            origin={'kind':'supplied_png','atlas_xy':[x,y]}
        elif c=='~':
            # PNG contains Hangul only; use the same family's supplied local TTF.
            tile=Image.new('L',(8,8));ImageDraw.Draw(tile).text((0,0),c,font=symbol,fill=255)
            assert set(tile.get_flattened_data())<={0,255},'Non-native antialiased symbol'
            bits=tuple(int(v>127) for v in tile.get_flattened_data())
            origin={'kind':'same_family_ttf','size_px':8,'draw_xy':[0,0]}
        else:raise ValueError(f'Unmapped PoC character {c!r}')
        assert any(bits),'Empty glyph'
        raw=encode(bits);assert decode(raw)==tuple(2*b for b in bits)
        code=mapping[c];banks[code*16:code*16+16]=raw
        glyphs.append({'char':c,'tile_code':f'{code:02X}','source':origin,'chr_hex':raw.hex()})
    for code in original_codes:
        assert banks[code*16:code*16+16]==before[code*16:code*16+16]
    assert before[:16]==bytes(16) and banks[:16]==bytes(16)
    # Maintain original extent, continuation, and next-page timing. Spaces are
    # skipped within one reader tick; each nonblank tile uses four frames at
    # speed 3. A shorter Korean page otherwise advances talking animation early.
    body=bytearray.fromhex('F8 03 F6 04 04')
    for c in text:body.append(0xF5 if c=='\n' else mapping[c])
    body.extend(bytes.fromhex('F7 46'))
    source_tiles=[int(k,16) for k in re.findall(r'\{tile:([0-9A-F]{2})\}',row['source_tokens'])]
    timing_compensation=(sum(v!=0 for v in source_tiles)-sum(c not in ' \n' for c in text))*4
    assert timing_compensation==48
    # Delay n resumes after n+1 frames in this original parser.
    body.extend((0xF7,timing_compensation-1))
    padding=37-len(body);assert padding>=0 and padding%2==0
    body.extend(bytes.fromhex('F8 03')*(padding//2));assert len(body)==37
    reverse={v:k for k,v in mapping.items()}
    decoded=''.join('\n' if b==0xF5 else reverse[b] for b in body[5:5+len(text)])
    assert decoded==text
    title_dir=ROOT/'build/title_kr_ai_004'
    title=(title_dir/'TinyToon_title_kr_poc.nes').read_bytes();assert sha(title)==TITLE_SHA
    plan=json.loads((title_dir/'expected_writes.json').read_text(encoding='utf-8'))
    for w in plan:w['owner']='preserved_'+w['owner']
    check=bytearray(rom)
    for w in plan:
        off=w['file_offset'];assert rom[off:off+w['length']]==bytes.fromhex(w['expected_hex'])
        check[off:off+w['length']]=bytes.fromhex(w['final_hex'])
    assert bytes(check)==title,'Verified title cannot be reproduced from declared writes'
    def write(owner,reason,offset,expected,final):
        assert rom[offset:offset+len(expected)]==expected and len(expected)==len(final)
        plan.append({'owner':owner,'reason':reason,'file_offset':offset,'length':len(final),
                     'expected_hex':expected.hex(),'final_hex':final.hex()})
    write('chr_extent','iNES CHR count 16 -> 17 (append 8KiB)',5,b'\x10',b'\x11')
    old_irq=bytes.fromhex('A9 08 A2 07 8D 00 B0 8E 04 B0 A9 0A A2 06 8D 08 B0 8E 0C B0')
    new_irq=bytes.fromhex('A9 00 A2 08 8D 00 B0 8E 04 B0 A9 01 A2 08 8D 08 B0 8E 0C B0')
    write('text_chr_selection','Same IRQ instruction sequence; select cloned banks 128/129 instead of 120/106',0x1FEA0,old_irq,new_irq)
    write('JP_175A9','User translation; same entry, continuation and controls; neutral speed padding',0x175A9,rom[0x175A9:0x175CE],bytes(body))
    tail=bytes(banks)+bytes(0x1800)
    plan.append({'owner':'poc_font_banks','reason':'Append two 1KiB copies with 14 new glyphs, plus declared 6KiB CHR padding',
                 'file_offset':len(rom),'length':len(tail),'expected_source_size':len(rom),
                 'expected_hex':'','final_hex':tail.hex(),'kind':'append'})
    allowed=set()
    for w in plan:
        off=w['file_offset'];region=set(range(off,off+w['length']))
        assert not allowed.intersection(region),'Write ownership collision'
        allowed.update(region)
        if w.get('kind')=='append':assert off==len(rom) and w['expected_source_size']==len(rom)
        else:assert rom[off:off+w['length']]==bytes.fromhex(w['expected_hex'])
    output=bytearray(rom)
    for w in plan:output[w['file_offset']:w['file_offset']+w['length']]=bytes.fromhex(w['final_hex'])
    diff={i for i,(x,y) in enumerate(zip(rom,output)) if x!=y}|set(range(len(rom),len(output)))
    assert diff<=allowed and len(output)==len(rom)+0x2000
    # Independent short instruction decode, no code generation or relocation.
    sys.path.insert(0,str(ROOT/'tools/python/py65-1.2.0'))
    from py65.devices.mpu6502 import MPU
    from py65.disassembler import Disassembler
    memory=bytearray(65536);memory[0xFE90:0xFEA4]=new_irq
    dis=Disassembler(MPU(memory=memory));pc=0xFE90;instructions=[]
    while pc<0xFEA4:
        size,line=dis.instruction_at(pc);assert '???' not in line
        instructions.append([f'{pc:04X}',line]);pc+=size
    assert pc==0xFEA4 and len(instructions)==8
    out=a.output.resolve();out.relative_to((ROOT/'build').resolve());out.mkdir(parents=True,exist_ok=False)
    (out/'expected_writes.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
    (out/'glyph_mapping.json').write_text(json.dumps({'mapping':mapping,'glyphs':glyphs},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'TinyToon_dialogue_kr_poc.nes').write_bytes(output)
    preview=Image.new('RGB',(16*8,7*8));draw=ImageDraw.Draw(preview)
    for y,line in enumerate(text.split('\n')):
        for x,c in enumerate(line):
            raw=banks[mapping[c]*16:mapping[c]*16+16]
            tile=Image.new('L',(8,8));tile.putdata([255 if b else 0 for b in decode(raw)])
            preview.paste(tile.convert('RGB'),(x*8,y*8))
    preview.resize((768,336),Image.Resampling.NEAREST).save(out/'dialogue_bitmap_preview.png')
    report={'source_sha256':sha(rom),'title_base_sha256':sha(title),'output_sha256':sha(output),
            'font_png_sha256':sha(a.font_png.read_bytes()),'symbol_ttf_sha256':TTF_SHA,'csv_sha256':CSV_SHA,
            'output_rom':'TinyToon_dialogue_kr_poc.nes','output_size':len(output),
            'scope':'JP_175A9 only; experimental visibility PoC, not full dialogue translation',
            'entry_id':'JP_175A9','translation_ko':text,'translated_blocks':1,'total_blocks':22,
            'script_payload_bytes':37,'neutral_padding_bytes':padding,'timing_compensation_frames':timing_compensation,
            'source_delay_preserved':'F7 46','additional_delay':'F7 2F','text_roundtrip':True,
            'original_font_tiles_unchanged_in_clones':True,'source_chr_preserved_except_verified_title':True,
            'original_script_other_bytes_preserved':True,'poc_font_glyphs':len(glyphs),'known_original_glyph_codes':len(original_codes),
            'new_chr_banks':[128,129],'cloned_source_banks':[120,106],'text_ink_pixel_value':2,
            'new_codes_not_used_in_known_text':True,'other_graphic_consumers':'must be checked in sampled runtime; not proven for all game states',
            'irq_instruction_decode':instructions,'changed_bytes_including_append':len(diff),
            'expected_write_count':len(plan),'python_version':sys.version,'pillow_version':pillow_version,
            'runtime':'NOT YET RUN; see separate QA'}
    (out/'build_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('output_sha256','output_size','script_payload_bytes','neutral_padding_bytes','poc_font_glyphs')},indent=2))

if __name__=='__main__':main()
