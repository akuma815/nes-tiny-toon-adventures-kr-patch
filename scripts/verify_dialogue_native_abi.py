"""Execute the font-only helper and the unchanged native reader in py65."""
import argparse,hashlib,json
from pathlib import Path
from asm6502 import verify_profile
from verify_dialogue_full_abi import run,Memory,MPU
ROOT=Path(__file__).resolve().parents[1]

def expected_fonts(b,pages,base,cursor,flag):
    if not flag:return None
    for alias in b['aliases']:
        if base==alias['base'] and cursor<alias['cursor_below']:return pages[alias['page_id']]['chr_banks']
    if b['data_start']>>8<=base>>8<((b['data_start']+b['data_bytes']-1)>>8)+1:
        found=[p for p in pages if base+cursor>=p['first_glyph_consumed']]
        if found:return found[-1]['chr_banks']
    return [120,106]

def native_read(prg,base,cur,irq):
    m=Memory(prg,10);c=MPU(memory=m,pc=0xB271);m.cpu=c
    c.sp=0xF7;c.p=0xE1|irq;c.a=0x55;c.x=0xAA;c.y=0xCC
    m.ram[0xBF]=base&255;m.ram[0xC0]=base>>8;m.ram[0x7A9]=cur
    m.ram[0x1F8:0x1FA]=bytes((0xFF,0x6F))
    before=bytes(m.ram)
    for _ in range(20):
        c.step()
        if c.pc==0x7000:break
    else:raise AssertionError('Native reader return')
    assert c.sp==0xF9 and c.x==0xAA and m.even==10 and m.odd==11 and c.p&4==irq
    assert all(x==y for i,(x,y) in enumerate(zip(before,m.ram)) if i not in (0x7A9,0xC0))
    return m,c

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--build',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    b=json.loads((a.build/'build_report.json').read_text());pages=json.loads((a.build/'pages.json').read_text(encoding='utf-8'))
    rom=(a.build/b['output_rom']).read_bytes();assert hashlib.sha256(rom).hexdigest()==b['output_sha256'];prg=rom[16:0x40010]
    src=(ROOT/'original/rom/Tiny Toon Adventures (Japan).nes').read_bytes()
    assert rom[0x17281:0x17290]==src[0x17281:0x17290]
    profile=verify_profile();bases=sorted({p['virtual_start'] for p in pages}|set(b['roots'])|{v['base'] for v in b['aliases']}|{0xA000,0xB3FF,0xB800,0xC000})
    total=0
    for base in bases:
        for cur in range(256):
            for flag in (0,1,2,255):
                for irq in (0,4):
                    m,c=run(prg,10,0xFE8C,base,cur,flag,irq)
                    pair=expected_fonts(b,pages,base,cur,flag)
                    expected=[] if pair is None else [(0xB000,pair[0]&15),(0xB004,pair[0]>>4),(0xB008,pair[1]&15),(0xB00C,pair[1]>>4)]
                    if pair is not None and flag not in (0,1):expected.extend([(0xC008,9),(0xC00C,7)])
                    actual=[(addr,v) for addr,v,_ in m.writes if addr>=0xB000]
                    assert actual==expected,(hex(base),cur,flag,actual,expected)
                    assert c.p&0x82==(2 if not flag or b.get('match_006_font_timing') else 0x80 if flag&128 else 0)
                    if not flag:assert c.processorCycles==12 and m.writes==[]
                    total+=1
    # Read every translated byte with each possible page-crossing cursor form.
    reads=0
    for offset in range(b['data_bytes']):
        address=b['data_start']+offset
        for cur in (0,1,7,255):
            base=address-cur
            for irq in (0,4):
                m,c=native_read(prg,base,cur,irq)
                assert c.a==rom[b['data_file_offset']+offset] and c.y==cur
                assert m.ram[0x7A9]==(cur+1)&255 and m.ram[0xC0]==((base>>8)+int(cur==255))&255
                assert c.p&0x82==(0x80 if c.a&128 else 0)|(2 if c.a==0 else 0)
                assert not any(addr>=0x6000 for addr,_,_ in m.writes)
                assert c.processorCycles==26+int((base&255)+cur>255)+4*int(cur==255)
                reads+=1
    # Cached portrait IRQ remains exactly native timing for all 22 page pairs.
    irq_cases=[]
    for pair in [[120,106]]+[p['chr_banks'] for p in pages]:
        m=Memory(prg,10);c=MPU(memory=m,pc=0xFB72);m.cpu=c;c.p=0x24
        m.prgram[:4]=bytes((pair[0]>>4,pair[0]&15,pair[1]>>4,pair[1]&15))
        for _ in range(200):
            c.step()
            if c.pc==0xFD57:break
        else:raise AssertionError('IRQ return')
        assert c.processorCycles==85 and m.ram[0x41]==1
        irq_cases.append({'pair':pair,'cycles':85})
    result={'status':'PASS','rom_sha256':b['output_sha256'],'profile':profile,'font_cases':total,'native_reader_cases':reads,'native_reader_bytes_exact':True,'reader_no_bank_or_PPU_writes':True,'irq_cases':irq_cases,'scope':'Static CPU model; runtime/direct visuals recorded separately'}
    cross=0
    for bank in (0,2,4,6,8,10,12):
        for base in bases:
            for cur in (0,1,7,255):
                for flag in (1,2):
                    for irq in (0,4):
                        m,c=run(prg,bank,0xFE8C,base,cur,flag,irq)
                        pair=expected_fonts(b,pages,base,cur,flag)
                        assert list(m.prgram[:4])==[pair[0]>>4,pair[0]&15,pair[1]>>4,pair[1]&15]
                        cross+=1
    result['cross_bank_font_cases']=cross
    if b.get('match_006_font_timing'):
        previous=(ROOT/'build/dialogue_full_006/TinyToon_dialogue_full.nes').read_bytes()[16:0x40010]
        comparisons=0
        for base in sorted({p['virtual_start'] for p in pages}|set(b['roots'])|{x['base'] for x in b['aliases']}):
            for cur in range(256):
                for flag in (1,2):
                    _,old=run(previous,10,0xFE8C,base-0x1467,cur,flag,0)
                    _,new=run(prg,10,0xFE8C,base,cur,flag,0)
                    alias_match=any(base==x['base'] and cur<x['cursor_below'] for x in b['aliases'])
                    expected_cycles=old.processorCycles+2*b.get('active_font_nops',0)-(17 if alias_match else 0)
                    assert expected_cycles==new.processorCycles,(hex(base),cur,flag,old.processorCycles,new.processorCycles,expected_cycles)
                    comparisons+=1
        result['font_cycle_reference']='dialogue_full_006'
        result['font_cycle_comparisons']=comparisons
        result['font_cycle_formula']='006 cycles + 2 * active_font_nops; matched returned-caller aliases bypass the 17-cycle address normalization'
    assert not a.output.exists();a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('profile','irq_cases')}))
if __name__=='__main__':main()
