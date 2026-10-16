"""Independently audit moved/copied regions, glyphs, scripts and build/apply."""
import argparse,csv,hashlib,json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--build',type=Path,required=True)
    ap.add_argument('--rebuild',type=Path,required=True);ap.add_argument('--applied',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    source=json.loads((ROOT/'manifests/source_rom.json').read_text());src=(ROOT/source['path']).read_bytes()
    assert sha(src)==source['sha256'] and len(src)==source['size_bytes']
    b=json.loads((a.build/'build_report.json').read_text());target=(a.build/b['output_rom']).read_bytes()
    assert sha(target)==b['output_sha256'] and len(target)==0x80010
    assert target[:4]==src[:4] and target[4:6]==bytes((16,32)) and target[6:16]==src[6:16]
    assert (a.rebuild/b['output_rom']).read_bytes()==target and a.applied.read_bytes()==target
    plan=json.loads((a.build/'expected_writes.json').read_text());allowed=set()
    extents={'header':(0,16),'preserved_title_prg':(0x3654,0x1A7),'JP_175A9':(0x175A9,37),
             'JP_175CF':(0x175CF,30),'new_prg':(0x20010,0x20000),'moved_chr':(0x40010,0x20000),
             'new_page_fonts':(0x60010,0x20000)}
    assert len(plan)==len(extents)
    for w in plan:
        o=w['file_offset'];n=w['length'];assert (o,n)==extents[w['owner']]
        assert w['expected_source_sha256']==sha(src)
        overlap=max(0,min(n,len(src)-o));assert w['expected_overlap_length']==overlap
        assert w['expected_overlap_sha256']==sha(src[o:o+overlap])
        assert target[o:o+n]==bytes.fromhex(w['final_hex']);region=set(range(o,o+n))
        assert not region&allowed;allowed|=region
    diff={i for i in range(len(target)) if i>=len(src) or target[i]!=src[i]};assert diff<=allowed
    title=(ROOT/'build/title_kr_ai_004/TinyToon_title_kr_poc.nes').read_bytes();assert sha(title)==b['title_base_sha256']
    old=(ROOT/'build/dialogue_kr_poc_004/TinyToon_dialogue_kr_poc.nes').read_bytes();assert sha(old)==b['first_poc_sha256']
    assert target[0x40010:0x60010]==title[0x20010:0x40010]
    expected=bytearray(src[16:0x20010]);expected[0x3644:0x37EB]=title[0x3654:0x37FB]
    pages=json.loads((a.build/'pages.json').read_text(encoding='utf-8'))
    csvpath=ROOT/'workspace/translation/dialogue_ja.csv';assert sha(csvpath.read_bytes())==b['csv_sha256']
    rows={r['entry_id']:r for r in csv.DictReader(csvpath.open(encoding='utf-8-sig',newline=''))}
    tokens=json.loads((ROOT/'extracted/text/dialogue_20261001/dialogue_tokens.json').read_text(encoding='utf-8'))
    font=ROOT/'workspace/fonts/galmuri7_8x8';png=font/'Galmuri7_8x8.png'
    assert sha(png.read_bytes())==b['font_png_sha256'] and sha((font/'Galmuri7.ttf').read_bytes())==b['ttf_sha256']
    sheet=Image.open(png).convert('RGBA');new=bytearray(0x20000)
    for page in pages:
        start=page['source_start'];end=page['source_end'];payload=target[start:end]
        expected[start-16:end-16]=payload
        assert page['translation_ko']==rows[page['entry_id']]['translation_ko']
        reverse={v:k for k,v in page['mapping'].items()};text=[];i=0;speed=3;typing=0;holds=[]
        while i<len(payload):
            code=payload[i];i+=1
            if code==0xF8:speed=payload[i];i+=1
            elif code==0xF6:i+=2
            elif code==0xF7:holds.append(payload[i]);i+=1
            elif code==0xF5:text.append('\n')
            else:
                assert code in reverse;text.append(reverse[code])
                if code:typing+=speed+1
        assert ''.join(text)==page['translation_ko'] and holds==[0x46]
        assert typing==page['typing_frames'] and typing in (108,100)
        fonts=bytearray(src[0x3E010:0x3E410]+src[0x3A810:0x3AC10]);original=bytes(fonts)
        for c,code in page['mapping'].items():
            if not code:continue
            assert 0x6E<=code<0x80
            if c=='~':glyph=old[0x40010+code*16:0x40010+code*16+16]
            else:
                idx=ord(c)-0xAC00;x=idx%64*8;y=idx//64*8;ink=[]
                for dy in range(8):
                    row=0
                    for dx in range(8):
                        p=sheet.getpixel((x+dx,y+dy))
                        if p[3] and max(p[:3])>127:row|=1<<(7-dx)
                    ink.append(row)
                glyph=bytes(8)+bytes(ink)
            fonts[code*16:code*16+16]=glyph
        for code in (int(k,16) for k in tokens['glyphs']):assert fonts[code*16:code*16+16]==original[code*16:code*16+16]
        off=page['chr_banks'][0]*1024-0x20000;new[off:off+0x800]=fonts
    assert target[16:0x20010]==expected
    assert target[0x60010:]==new
    asm=json.loads((a.build/'assembly.json').read_text());selector=bytes.fromhex(''.join(r['hex'] for r in asm['selector']))
    stub=bytes.fromhex(''.join(r['hex'] for r in asm['stub']))
    extension=bytearray(0x20000);extension[0x2000:0x2000+len(selector)]=selector
    extension[0x1C000:0x1E000]=src[0x1C010:0x1E010];extension[0x1E000:]=src[0x1E010:0x20010]
    extension[0x1FE8C:0x1FEB2]=stub+bytes((0xEA,))*(38-len(stub))
    assert target[0x20010:0x40010]==extension
    preserved={'workspace/translation/dialogue_ja_translated_ko.csv':'e274e97e75db79ea5d05b2e025cc70b7e9258a701bc1c10bea279ecbb4e8eb50',
               'extracted/text/dialogue_20261001/dialogue_tokens.json':'506527702802a80da6b9c0710d97c4f028015dcf3f13cb30e3b26cfd2f9ee27a'}
    for p,h in preserved.items():assert sha((ROOT/p).read_bytes())==h
    result={'status':'PASS','source_sha256':sha(src),'output_sha256':sha(target),'output_size':len(target),
            'expected_writes':len(plan),'changed_bytes_including_append':len(diff),'all_diff_owned':True,
            'immutable_PRG_except_declared_title_and_two_text_pages':True,'moved_title_CHR_exact':True,
            'new_PRG_copy_and_fresh_padding_exact':True,'font_pixels_independently_checked':True,
            'all_original_97_glyphs_preserved':True,'script_roundtrip_and_native_typing_intervals':True,
            'pointer_table_and_other_text_unchanged':True,'rebuild_byte_identical':True,'ips_CLI_apply_byte_identical':True,
            'scope':'Static/build/apply only; model/runtime/visual checks separate'}
    assert not a.output.exists();a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
