"""Execute the assembled stub/selector with a banked memory model and py65."""
import argparse,json,hashlib
from pathlib import Path
from asm6502 import MPU,verify_profile
ROOT=Path(__file__).resolve().parents[1]

class Memory:
    def __init__(self,prg,bank):
        self.prg=prg;self.even=bank;self.odd=bank+1
        self.ram=bytearray(0x800);self.writes=[];self.cpu=None
    def __getitem__(self,a):
        if a<0x800:return self.ram[a]
        if a<0x8000:return 0
        bank=self.even if a<0xA000 else self.odd if a<0xC000 else 30 if a<0xE000 else 31
        return self.prg[bank*0x2000+(a&0x1FFF)]
    def __setitem__(self,a,v):
        self.writes.append((a,v,bool(self.cpu.p&4)))
        if a<0x800:self.ram[a]=v
        elif a==0xA000:self.odd=v&31
        else:assert a in (0xB000,0xB004,0xB008,0xB00C,0xC008,0xC00C),hex(a)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--build',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    report=json.loads((a.build/'build_report.json').read_text());rom=(a.build/report['output_rom']).read_bytes()
    assert hashlib.sha256(rom).hexdigest()==report['output_sha256'];prg=rom[16:0x40010]
    # This is the native pair-bank restore contract used by F8DD/F8EA.
    native_banks=list(range(0,14,2))
    assert [prg[b*0x2000] for b in native_banks]==native_banks
    count=0;max_cycles=0
    for base in (0xB599,0xB598,0xB499):
      for cursor in range(256):
       for flag in (0,1,2,255):
        for bank in native_banks:
         for irq in (0,4):
          m=Memory(prg,bank);cpu=MPU(memory=m,pc=0xFE8C);m.cpu=cpu
          cpu.sp=0xF7;cpu.p=0x20|irq;cpu.a=0x55;cpu.x=0xAA;cpu.y=0xCC
          m.ram[0x57]=flag;m.ram[0xBF]=base&255;m.ram[0xC0]=base>>8;m.ram[0x7A9]=cursor
          m.ram[0x1F8:0x1FA]=bytes((0xFF,0x6F))
          before=bytes(m.ram)
          for _ in range(80):
              cpu.step()
              if cpu.pc==0x7000:break
          else:raise AssertionError('No balanced return')
          assert cpu.sp==0xF9 and m.odd==bank+1
          assert (cpu.p&4)==irq
          assert all(0x100<=p<0x200 or p>=0x8000 for p,_,_ in m.writes)
          assert all(x==y for p,(x,y) in enumerate(zip(before,m.ram)) if not 0x100<=p<0x200)
          switches=[(p,v,i) for p,v,i in m.writes if p==0xA000]
          chr_writes=[(p,v) for p,v,_ in m.writes if p>=0xB000]
          if flag==0:assert switches==[] and chr_writes==[]
          else:
              assert switches==[(0xA000,17,True),(0xA000,bank+1,True)]
              fonts=(128,129) if base==0xB599 and cursor<39 else (130,131) if base==0xB599 and cursor<70 else (120,106)
              expected=[(0xB000,fonts[0]&15),(0xB004,fonts[0]>>4),(0xB008,fonts[1]&15),(0xB00C,fonts[1]>>4)]
              if flag!=1:expected.extend(((0xC008,9),(0xC00C,7)))
              assert chr_writes==expected,(base,cursor,flag)
          count+=1;max_cycles=max(max_cycles,cpu.processorCycles)
    result={'status':'PASS','build_sha256':report['output_sha256'],'cases':count,
            'cursor_values':256,'native_pair_banks':native_banks,'dialogue_flags':[0,1,2,255],
            'irq_enabled_and_disabled':True,'balanced_stack_and_bank_restore':True,
            'all_temporary_prg_switches_irq_masked':True,'new_shared_ram_writes':0,
            'maximum_stub_cycles_in_model':max_cycles,'assembler_profile':verify_profile(),
            'scope':'Instruction/ABI model only; real Mesen execution is a separate gate'}
    assert not a.output.exists();a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
