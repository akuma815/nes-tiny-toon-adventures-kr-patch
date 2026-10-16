"""Execute the shipped banked reader/font code with the complete py65 ISA."""
import argparse,json,hashlib
from pathlib import Path
from asm6502 import MPU,verify_profile
ROOT=Path(__file__).resolve().parents[1]
class Memory:
 def __init__(self,prg,bank):
  self.prg=prg;self.even=bank;self.odd=bank+1;self.ram=bytearray(0x800);self.prgram=bytearray(0x2000);self.writes=[];self.cpu=None;self.ppuctrl=0xA8;self.bank=bank
 def __getitem__(self,a):
  if a<0x800:return self.ram[a]
  if 0x6000<=a<0x8000:return self.prgram[a-0x6000]
  if a<0x8000:return 0
  bank=self.even if a<0xA000 else self.odd if a<0xC000 else 30 if a<0xE000 else 31
  return self.prg[bank*0x2000+(a&0x1FFF)]
 def __setitem__(self,a,v):
  self.writes.append((a,v,bool(self.cpu.p&4)))
  if a<0x800:self.ram[a]=v
  elif 0x6000<=a<=0x6003:self.prgram[a-0x6000]=v
  elif a==0x2000:
   self.ppuctrl=v
   if v&128:assert self.even==self.bank and self.odd==self.bank+1
  elif a==0x8000:self.even=v&31
  elif a==0xA000:self.odd=v&31
  else:assert a in (0xB000,0xB004,0xB008,0xB00C,0xC000,0xC004,0xC008,0xC00C),hex(a)
def expected_fonts(b,pages,base,cursor,flag,previous=None):
 if not flag:return None
 for alias in b['held_font_aliases']:
  if base==alias['base'] and cursor<alias['cursor_below']:return previous if previous and 7<=previous[0]>>4<11 else [120,106]
 for alias in b['aliases']:
  if base==alias['base'] and cursor<alias['cursor_below']:return pages[alias['page_id']]['chr_banks']
 if 0xA0<=base>>8<=((0xA000+b['data_bytes']-1)>>8):
  matches=[p for p in pages if base+cursor>=p['first_glyph_consumed']]
  if matches:return matches[-1]['chr_banks']
 return [120,106] if flag else None
def run(prg,bank,entry,base,cursor,flag,irq,previous=None):
 m=Memory(prg,bank)
 if previous:m.prgram[:4]=bytes((previous[0]>>4,previous[0]&15,previous[1]>>4,previous[1]&15))
 cpu=MPU(memory=m,pc=entry);m.cpu=cpu
 cpu.sp=0xF7;cpu.p=0xE1|irq;cpu.a=0x55;cpu.x=0xAA;cpu.y=0xCC
 m.ram[0x57]=flag;m.ram[0xBF]=base&255;m.ram[0xC0]=base>>8;m.ram[0x7A9]=cursor;m.ram[0xFF]=0xA8
 m.ram[0x1F8:0x1FA]=bytes((0xFF,0x6F));before=bytes(m.ram)
 for _ in range(500):
  cpu.step()
  if cpu.pc==0x7000:break
 else:raise AssertionError('unbalanced return')
 assert cpu.sp==0xF9 and cpu.x==0xAA and m.even==bank and m.odd==bank+1
 assert cpu.p&4==irq
 assert all(masked for addr,_,masked in m.writes if addr>=0x8000)
 permitted={0x7A9,0xC0} if entry in (0xB271,0xFE94) else set()
 assert all(x==y for i,(x,y) in enumerate(zip(before,m.ram)) if i not in permitted and not 0x100<=i<0x200)
 assert all(addr in permitted or 0x100<=addr<0x200 or addr>=0x8000 or 0x6000<=addr<=0x6003 and entry==0xFE8C or addr==0x2000 and entry in (0xB271,0xFE94) for addr,_,_ in m.writes)
 ppu=[v for addr,v,_ in m.writes if addr==0x2000]
 assert ppu==([0x28,0xA8] if entry==0xB271 else [0xA8] if entry==0xFE94 else [])
 return m,cpu
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--build',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 b=json.loads((a.build/'build_report.json').read_text());pages=json.loads((a.build/'pages.json').read_text(encoding='utf-8'))
 rom=(a.build/b['output_rom']).read_bytes();assert hashlib.sha256(rom).hexdigest()==b['output_sha256'];prg=rom[16:0x40010]
 banks=list(range(0,14,2));assert [prg[x*0x2000] for x in banks]==banks
 bases=sorted({p['virtual_start'] for p in pages}|set(b['roots'])|{x['base'] for x in b['aliases']}|{0xA3FF,0x9FFF,0xB599,0xB518})
 cases=0;max_cycles=0;fetches=0
 for base in bases:
  for cur in range(256):
   for flag in (0,1,2,255):
    for irq in (0,4):
     # Full cursor/flag/IRQ Cartesian coverage in the dialogue bank.
     m,c=run(prg,10,0xFE8C,base,cur,flag,irq);pair=expected_fonts(b,pages,base,cur,flag)
     writes=[(x,v) for x,v,_ in m.writes if x>=0xB000]
     expected=[] if pair is None else [(0xB000,pair[0]&15),(0xB004,pair[0]>>4),(0xB008,pair[1]&15),(0xB00C,pair[1]>>4)]
     if pair is not None and flag not in (0,1):expected.extend(((0xC008,9),(0xC00C,7)))
     assert writes==expected,(hex(base),cur,flag,writes,expected)
     assert list(m.prgram[:4])==([pair[0]>>4,pair[0]&15,pair[1]>>4,pair[1]&15] if pair else [0]*4)
     # Entry LDA #0 sets N/Z before PHP; other live flags remain unchanged.
     assert c.p&0xEF==(((0xE1|irq)&0x7D)|2)
     if not flag:assert c.processorCycles==12 and m.writes==[], 'Mode0 must match native font return exactly'
     cases+=1;max_cycles=max(max_cycles,c.processorCycles)
 # Exercise each preceding branch font through every hold cursor and CPU bank.
 held_cases=0
 for previous in ([120,106],pages[2]['chr_banks'],pages[3]['chr_banks']):
  for bank in banks:
   for cur in range(6):
    for flag in (1,2,255):
     for irq in (0,4):
      m,c=run(prg,bank,0xFE8C,0xA078,cur,flag,irq,previous)
      writes=[(x,v) for x,v,_ in m.writes if x>=0xB000]
      expected=[(0xB000,previous[0]&15),(0xB004,previous[0]>>4),(0xB008,previous[1]&15),(0xB00C,previous[1]>>4)]
      if flag!=1:expected.extend(((0xC008,9),(0xC00C,7)))
      assert writes==expected
      assert list(m.prgram[:4])==[previous[0]>>4,previous[0]&15,previous[1]>>4,previous[1]&15]
      assert not any(0x6000<=x<=0x6003 for x,v,_ in m.writes)
      held_cases+=1
 # Every relocated byte through the real reader; also cursor carry and native fallback.
 for bank in banks:
  for irq in (0,4):
   for base,cur in [(0xA000+i,0) for i in range(b['data_bytes'])]+[(0xA000+i-255,255) for i in range(255,b['data_bytes'])]+[(0xB467,0),(0xB400,255)]:
    # B271 belongs to native bank11; other banks exercise its fixed read entry.
    entry=0xB271 if bank==10 else 0xFE94
    m,c=run(prg,bank,entry,base,cur,2,irq);address=base+cur
    expected=prg[18*0x2000+address-0xA000] if 0xA0<=base>>8<=0xA3 else prg[(bank if address<0xA000 else bank+1)*0x2000+(address&0x1FFF)]
    assert c.a==expected and c.y==cur,(bank,hex(base),cur,c.a,expected,c.y,m.writes)
    assert m.ram[0x7A9]==(cur+1)&255 and m.ram[0xC0]==((base>>8)+int(cur==255))&255
    if entry==0xB271:assert c.p&0x82==(0x80 if expected&128 else 0)|(2 if expected==0 else 0)
    fetches+=1;max_cycles=max(max_cycles,c.processorCycles)
 # Cross-bank font selection, including each page and all returned caller aliases.
 cross=0
 for bank in banks:
  for base in bases:
   for cur in (0,1,7,255):
    for irq in (0,4):
     run(prg,bank,0xFE8C,base,cur,2,irq);cross+=1
 # The cached raster path must match native total instruction timing.
 # Restore the original IRQ bytes in a separate model for the reference.
 source=json.loads((ROOT/'manifests/source_rom.json').read_text());src=(ROOT/source['path']).read_bytes();reference=bytearray(prg)
 reference[31*0x2000+0x1B72:31*0x2000+0x1BA2]=src[0x1FB82:0x1FBB2]
 irq_cases=[]
 for pair in [[120,106]]+[p['chr_banks'] for p in pages]:
  samples=[]
  for code in (reference,prg):
   m=Memory(code,10);c=MPU(memory=m,pc=0xFB72);m.cpu=c;c.p=0x24
   m.prgram[:4]=bytes((pair[0]>>4,pair[0]&15,pair[1]>>4,pair[1]&15))
   for _ in range(200):
    c.step()
    if c.pc==0xFD57:break
   else:raise AssertionError('raster did not return')
   samples.append(c.processorCycles)
  assert samples[0]==samples[1]==85,samples
  registers={addr:value&15 for addr,value,_ in m.writes if addr>=0x8000}
  assert [registers[x] for x in (0xB004,0xB000,0xB00C,0xB008)]==[pair[0]>>4,pair[0]&15,pair[1]>>4,pair[1]&15]
  assert m.ram[0x41]==1
  irq_cases.append({'pair':pair,'native_cycles':85,'new_cycles':85})
 result={'status':'PASS','rom_sha256':b['output_sha256'],'held_font_cases':held_cases,'font_cases':cases,'reader_cases':fetches,'cross_bank_cases':cross,'native_pair_banks':banks,
  'balanced_stack_both_PRG_banks_and_irq_restored':True,'only_native_reader_cursor_and_four_private_PRG_RAM_bytes_written':True,'all_relocated_bytes_fetched':True,
  'raster_cycle_cases':irq_cases,'maximum_cycles':max_cycles,'assembler_profile':verify_profile(),'scope':'Complete ISA instruction/ABI model; emulator and scene QA separate'}
 assert not a.output.exists();a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
