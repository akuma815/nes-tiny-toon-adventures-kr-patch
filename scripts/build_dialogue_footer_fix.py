"""Keep the actually displayed Hamton font during the shared farewell prelude."""
import argparse,hashlib,json
from pathlib import Path
import build_dialogue_full as old
from asm6502 import assemble
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def build(font_nops=0):
    _,b,plan,pages,assembly,asm,reloc=old.build()
    src=(ROOT/'original/rom/Tiny Toon Adventures (Japan).nes').read_bytes()
    assert sha(src)==b['source_sha256']
    spec_path=ROOT/'workspace/fonts/galmuri7_8x8/glyph_overrides_dialogue_008.json'
    spec=json.loads(spec_path.read_text(encoding='utf-8'))
    applied=set()
    for p in pages:
        for g in p['glyphs']:
            if g['char'] in spec:
                rows=spec[g['char']]['rows'];assert len(rows)==8 and all(len(r)==8 and set(r)<={'#','.'} for r in rows)
                raw=bytes(8)+bytes(sum(1<<(7-x) for x,v in enumerate(r) if v=='#') for r in rows)
                g['bytes_hex']=raw.hex();g['source']={'override_file':spec_path.relative_to(ROOT).as_posix(),'override_char':g['char']};applied.add(g['char'])
    assert applied==set(spec)
    base=b['roots'][18];threshold=pages[4]['first_glyph_consumed']-base;assert threshold==6
    guard='\n'.join(['LDA $BF',f'CMP #${base&255:02X}','BNE @FOOTER_NOT_HELD','LDA $C0',f'CMP #${base>>8:02X}','BNE @FOOTER_NOT_HELD','LDA $07A9',f'CMP #${threshold:02X}','BCS @FOOTER_NOT_HELD','LDA $6000','CMP #$07','BCC @FOOTER_CACHE_EMPTY','CMP #$0B','BCS @FOOTER_CACHE_EMPTY','LDA $6001','STA $B000','LDA $6000','STA $B004','LDA $6003','STA $B008','LDA $6002','STA $B00C','JMP @EXTRA','FOOTER_CACHE_EMPTY:','JMP @ORIGINAL','FOOTER_NOT_HELD:'])+'\n'
    assert asm.count('ACTIVE_FONT:\n')==1
    asm=asm.replace('ACTIVE_FONT:\n','ACTIVE_FONT:\n'+'NOP\n'*font_nops+guard)
    helper,listing,symbols=assemble(asm,0x8001);helper=bytes([17])+helper;assert len(helper)<0x2000
    new_plan=[]
    for w in plan:
        w=dict(w)
        if w['owner']=='new_prg':
            extension=bytearray.fromhex(w['final_hex']);extension[0x2000:0x4000]=bytes(0x2000);extension[0x2000:0x2000+len(helper)]=helper
            w['final_hex']=extension.hex();w['reason']='006 reader/data/fixed banks retained; farewell prelude restores last displayed font cache'
        if w['owner']=='page_fonts':
            tail=bytearray.fromhex(w['final_hex'])
            for p in pages:
                for g in p['glyphs']:
                    off=p['page_id']*0x800+g['code']*16;tail[off:off+16]=bytes.fromhex(g['bytes_hex'])
            w['final_hex']=tail.hex();w['reason']='006 page fonts with only the explicit few-glyph override'
        new_plan.append(w)
    # Guard every source-derived ROM write before creating the candidate.
    owned=set()
    for w in new_plan:
        off=w['file_offset'];n=w['length'];span=set(range(off,off+n));assert not span&owned;owned|=span
        assert w['expected_source_sha256']==sha(src) and sha(src[off:off+w['expected_overlap_length']])==w['expected_overlap_sha256']
    target=bytearray(src)
    for w in sorted(new_plan,key=lambda w:w['file_offset']):
        off=w['file_offset'];target[off:off+w['length']]=bytes.fromhex(w['final_hex'])
    assert len(target)==0x80010 and all(i in owned for i in range(len(target)) if i>=len(src) or target[i]!=src[i])
    assert target[0x17477:0x17845]==src[0x17477:0x17845]
    b=dict(b,output_sha256=sha(target),helper_bytes=len(helper),held_font_aliases=[{'base':base,'cursor_below':threshold,'previous_pages':[2,3],'reason':'shared root18 F7/F9 prelude retains the actually displayed counting or insufficient paragraph'}],glyph_override_path=spec_path.relative_to(ROOT).as_posix(),glyph_override_sha256=sha(spec_path.read_bytes()),active_font_nops=font_nops,scope='Reproduced Hamton farewell-prelude font regression; 006 architecture preserved')
    assembly=dict(assembly,helper=listing,helper_symbols=symbols)
    return target,b,new_plan,pages,assembly,asm,reloc
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--active-font-nops',type=int,choices=[0,1,2],default=0);a=ap.parse_args()
    target,b,plan,pages,asm,helper,reloc=build(a.active_font_nops);out=a.output.resolve();out.relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
    for name,value in [('build_report',b),('expected_writes',plan),('pages',pages),('assembly',asm),('relocation',reloc)]:
        (out/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'helper.asm').write_text(helper,encoding='ascii');(out/b['output_rom']).write_bytes(target);print(json.dumps(b,indent=2))
if __name__=='__main__':main()
