"""Use the original reader and fit all translated scripts in the known JP asset.

This invokes the preserved full builder to encode the submitted text, then
registers a new source-based Expected Write plan BEFORE applying any ROM writes.
Only the explicit glyph override is allowed to depart from the supplied atlas.
"""
import argparse, hashlib, json
from pathlib import Path
import build_dialogue_full as old
from asm6502 import assemble

ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()

def build(override_path=None,match_font_timing=False,active_font_nops=0):
    _, previous, _, pages, _, helper_asm, relocation = old.build()
    src=(ROOT/'original/rom/Tiny Toon Adventures (Japan).nes').read_bytes()
    assert sha(src)==previous['source_sha256']
    title=(ROOT/'build/title_kr_ai_004/TinyToon_title_kr_poc.nes').read_bytes()
    override_path=override_path or ROOT/'workspace/fonts/galmuri7_8x8/glyph_overrides_dialogue_008.json'
    overrides=json.loads(override_path.read_text(encoding='utf-8'))
    assert set(overrides)<=set(g['char'] for p in pages for g in p['glyphs']), 'Unused glyph override'
    delta=0xB467-0xA000
    relocation={k:v+delta for k,v in relocation.items()}
    roots=[v+delta for v in previous['roots']]
    aliases=[dict(a,base=a['base']+delta) for a in previous['aliases']]
    for p in pages:
        for key in ('virtual_start','virtual_end','first_glyph_consumed'):p[key]+=delta
        for g in p['glyphs']:
            if g['char'] in overrides:
                rows=overrides[g['char']]['rows']
                assert len(rows)==8 and all(len(row)==8 and set(row)<={'#','.'} for row in rows)
                raw=bytes(8)+bytes(sum(1<<(7-x) for x,c in enumerate(row) if c=='#') for row in rows)
                g['bytes_hex']=raw.hex();g['source']={'override_file':str(override_path.relative_to(ROOT)).replace('\\','/'),'override_char':g['char']}
    # Re-encode only relocated F4 operands in the preserved complete graph.
    data=bytearray()
    by_old={p['source_start']:p for p in pages}
    cat=json.loads((ROOT/'extracted/text/dialogue_20261001/dialogue_tokens.json').read_text(encoding='utf-8'))
    skip=-1
    for t in cat['tokens']:
        off=t['offset']
        if off<skip:continue
        assert relocation[off]==0xB467+len(data)
        if off in by_old:
            p=by_old[off];data.extend(bytes.fromhex(p['payload_hex']));skip=p['source_end']
        elif t['name']=='call':
            target=int.from_bytes(bytes(t['args']),'little')+0xC010
            data.extend(bytes([0xF4])+relocation[target].to_bytes(2,'little'))
        else:data.extend(bytes.fromhex(t['raw_hex']))
    assert len(data)==previous['data_bytes'] and len(data)<=0x17845-0x17477
    # Rebuild the selector with the actual native-bank addresses. The obsolete
    # fetch entry is removed; every dialogue read remains the unmodified B271.
    start=helper_asm.index('FONT:\n');end=helper_asm.index('FETCH:\n')
    helper_asm='TXA\nPHA\n'+helper_asm[start:end]
    for k,(a,b) in enumerate(zip(previous['aliases'],aliases)):
        before=f'LDA $BF\nCMP #${a["base"]&255:02X}\nBNE @ALIAS_{k}\nLDA $C0\nCMP #${a["base"]>>8:02X}\nBNE @ALIAS_{k}\n'
        after=f'LDA $BF\nCMP #${b["base"]&255:02X}\nBNE @ALIAS_{k}\nLDA $C0\nCMP #${b["base"]>>8:02X}\nBNE @ALIAS_{k}\n'
        assert helper_asm.count(before)==1;helper_asm=helper_asm.replace(before,after)
    helper_asm=helper_asm.replace('CMP #$A0\n','CMP #$B4\n').replace('CMP #$A4\n','CMP #$B8\n')
    # Each page comparison appears once and is paired with a unique NEXT label.
    if match_font_timing:
        marker='ADC #$00\nTAX\nPLA\n'
        assert helper_asm.count(marker)==1
        helper_asm=helper_asm.replace(marker,marker+'SEC\nSBC #$67\nPHA\nTXA\nSBC #$14\nTAX\nPLA\n')
    else:
        for p in pages:
            pid=p['page_id'];oldaddr=p['first_glyph_consumed']-delta;newaddr=p['first_glyph_consumed']
            before=f'CPX #${oldaddr>>8:02X}\nBCC @NEXT_{pid}\nBNE @MATCH_{pid}\nCMP #${oldaddr&255:02X}\n'
            after=f'CPX #${newaddr>>8:02X}\nBCC @NEXT_{pid}\nBNE @MATCH_{pid}\nCMP #${newaddr&255:02X}\n'
            assert helper_asm.count(before)==1;helper_asm=helper_asm.replace(before,after)
    helper,listing,symbols=assemble(helper_asm,0x8001);helper=bytes([17])+helper
    stub_asm='FONT_ENTRY:\nLDY $57\nBEQ @RETURN\nPHP\nSEI\nLDA $8000\nPHA\nLDA #$11\nSTA $8000\nJSR $8001\nPLA\nSTA $8000\nPLP\nRETURN:\nRTS\n'
    if match_font_timing:
        stub_asm=stub_asm.replace('PHP\n','LDA #$00\nJMP @COMMON\nCOMMON:\nPHP\n').replace('PLP\n','LDA #$00\nPLP\n')
    stub_asm=stub_asm.replace('PHP\n','NOP\n'*active_font_nops+'PHP\n')
    stub,stub_listing,stub_symbols=assemble(stub_asm,0xFE8C)
    assert len(stub)<=38
    extension=bytearray(0x20000);extension[0x2000:0x2000+len(helper)]=helper
    extension[0x1C000:0x1E000]=src[0x1C010:0x1E010];extension[0x1E000:]=src[0x1E010:0x20010]
    extension[0x1FE8C:0x1FEB2]=stub+bytes([0xEA])*(38-len(stub))
    irq_asm='BIT $00\nLDY #$6E\nJSR $F8BE\nLDA $6000\nLDX $6001\nLDY $6003\nSTX $B000\nSTA $B004\nLDA $6002\nSTY $B008\nSTA $B00C\nINC $41\nJMP $FD57\n'
    irq,irq_listing,_=assemble(irq_asm,0xFB72);extension[0x1FB72:0x1FBA2]=irq+bytes([0xEA])*(48-len(irq))
    tail=bytearray(0x20000)
    for p in pages:
        fonts=bytearray(src[0x3E010:0x3E410]+src[0x3A810:0x3AC10])
        for g in p['glyphs']:fonts[g['code']*16:g['code']*16+16]=bytes.fromhex(g['bytes_hex'])
        tail[p['page_id']*0x800:(p['page_id']+1)*0x800]=fonts
    plan=[]
    def reg(owner,offset,final,reason):
        overlap=max(0,min(len(final),len(src)-offset))
        plan.append(dict(owner=owner,file_offset=offset,length=len(final),expected_source_sha256=sha(src),expected_overlap_length=overlap,expected_overlap_sha256=sha(src[offset:offset+overlap]),final_hex=bytes(final).hex(),reason=reason))
    hdr=bytearray(src[:16]);hdr[4]=16;hdr[5]=32;hdr[8]=1
    reg('header',0,hdr,'Expanded font/helper storage and explicit IRQ font cache RAM')
    for w in json.loads((ROOT/'build/title_kr_ai_004/expected_writes.json').read_text()):
        if w['file_offset']<0x20010:reg('preserved_title_prg',w['file_offset'],bytes.fromhex(w['final_hex']),w['reason'])
    reg('registered_root_pointers',0x17443,b''.join(v.to_bytes(2,'little') for v in roots),'26 graph roots in native bank11')
    reg('dialogue_in_place',0x17477,data+bytes(0x17845-0x17477-len(data)),'Replace only known Japanese dialogue asset; original reader retained')
    reg('new_prg',0x20010,extension,'Font-only helper17 and copied fixed banks30/31; no banked reader')
    reg('moved_chr',0x40010,title[0x20010:0x40010],'Preserve title CHR exactly')
    reg('page_fonts',0x60010,tail,'22 cloned font pairs with explicit few-glyph override')
    target=bytearray(src);owned=set()
    for w in sorted(plan,key=lambda w:w['file_offset']):
        off=w['file_offset'];n=w['length'];span=set(range(off,off+n));assert not span&owned;owned|=span
        assert sha(src[off:off+w['expected_overlap_length']])==w['expected_overlap_sha256']
        target[off:off+n]=bytes.fromhex(w['final_hex'])
    assert len(target)==0x80010 and target[0x17281:0x17290]==src[0x17281:0x17290]
    assert all(i in owned for i in range(len(target)) if i>=len(src) or target[i]!=src[i])
    report=dict(previous,output_sha256=sha(target),data_bank=11,data_start=0xB467,data_file_offset=0x17477,helper_bytes=len(helper),stub_bytes=len(stub),aliases=aliases,roots=roots,reader='unmodified original B271',match_006_font_timing=match_font_timing,glyph_override_path=str(override_path.relative_to(ROOT)).replace('\\','/'),glyph_override_sha256=sha(override_path.read_bytes()),scope='Native reader repair; user-reported corruption still requires reproduced runtime regression')
    report['active_font_nops']=active_font_nops
    assembly=dict(helper=listing,stub=stub_listing,irq=irq_listing,helper_symbols=symbols,stub_symbols=stub_symbols,profile=old.verify_profile())
    return target,report,plan,pages,assembly,helper_asm,relocation

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--overrides',type=Path);ap.add_argument('--match-006-font-timing',action='store_true');ap.add_argument('--active-font-nops',type=int,choices=[0,1,2],default=0);a=ap.parse_args()
    values=build(a.overrides.resolve() if a.overrides else None,a.match_006_font_timing,a.active_font_nops);out=a.output.resolve();out.relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
    target,report,plan,pages,assembly,helper,reloc=values
    for name,val in [('build_report',report),('expected_writes',plan),('pages',pages),('assembly',assembly),('relocation',reloc)]:
        (out/(name+'.json')).write_text(json.dumps(val,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'helper.asm').write_text(helper,encoding='ascii');(out/report['output_rom']).write_bytes(target)
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
