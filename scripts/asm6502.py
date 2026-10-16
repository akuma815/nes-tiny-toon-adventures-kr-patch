"""Strict label glue around py65 1.2.0's complete official NMOS 6502 ISA.

Instruction encoding/decoding belongs to py65, not a game-specific subset.
Branches are range checked here because the upstream assembler masks offsets.
"""
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/python/py65-1.2.0'))
from py65.assembler import Assembler
from py65.disassembler import Disassembler
from py65.devices.mpu6502 import MPU

BRANCHES={'BCC','BCS','BEQ','BMI','BNE','BPL','BVC','BVS'}

def encode_statement(assembler,statement,pc):
    raw=bytes(assembler.assemble(statement,pc))
    parts=statement.upper().split(None,1)
    # py65 otherwise contracts disassembled absolute $0000 to zero page.
    # Preserve explicit four-digit absolute operands through its full ISA table.
    if len(parts)==2 and parts[0] not in BRANCHES and re.fullmatch(r'\$[0-9A-F]{4}(,[XY])?',parts[1]):
        mnemonic,mode=assembler._mpu.disassemble[raw[0]]
        absolute={'zpg':'abs','zpx':'abx','zpy':'aby'}.get(mode)
        if absolute and (mnemonic,absolute) in assembler._mpu.disassemble:
            opcode=assembler._mpu.disassemble.index((mnemonic,absolute))
            raw=bytes((opcode,raw[1],0))
    return raw

def assemble(text,origin,constants=None):
    assembler=Assembler(MPU());symbols=dict(constants or {});rows=[];pc=origin
    for raw in text.splitlines():
        line=raw.split(';')[0].strip()
        if not line:continue
        if line.endswith(':'):
            label=line[:-1];assert label not in symbols;symbols[label]=pc;continue
        provisional=re.sub(r'@([A-Za-z_][\w]*)',lambda m:f'${symbols.get(m[1],0xFFFF):04X}',line)
        size=len(encode_statement(assembler,provisional,pc));rows.append((pc,line,size));pc+=size
    code=bytearray();listing=[];starts={p for p,_,_ in rows}
    for pc,line,size in rows:
        actual=re.sub(r'@([A-Za-z_][\w]*)',lambda m:f'${symbols[m[1]]:04X}',line)
        mnemonic=actual.split()[0].upper()
        if mnemonic in BRANCHES:
            target=int(actual.split()[1][1:],16)
            assert -128<=target-pc-2<=127,'Branch range exceeded'
            assert target in starts,'Branch target not an instruction'
        raw=encode_statement(assembler,actual,pc);assert len(raw)==size
        code.extend(raw);listing.append({'pc':pc,'source':line,'resolved':actual,'hex':raw.hex()})
    memory=bytearray(65536);memory[origin:origin+len(code)]=code
    dis=Disassembler(MPU(memory=memory));pc=origin
    for item in listing:
        size,decoded=dis.instruction_at(pc)
        assert '???' not in decoded and encode_statement(assembler,decoded,pc)==bytes.fromhex(item['hex'])
        item['disassembly']=decoded;pc+=size
    assert pc==origin+len(code)
    return bytes(code),listing,symbols

def verify_profile():
    memory=bytearray(65536);mpu=MPU(memory=memory);assembler=Assembler(mpu);dis=Disassembler(mpu)
    count=0
    for opcode,(mnemonic,mode) in enumerate(mpu.disassemble):
        if mnemonic=='???':continue
        count+=1
        for low,high in ((0,0),(0x7F,0x12),(0x80,0xA0),(0xFF,0xFF)):
            memory[0x8000:0x8003]=bytes((opcode,low,high))
            size,line=dis.instruction_at(0x8000)
            raw=encode_statement(assembler,line,0x8000)
            assert raw==bytes(memory[0x8000:0x8000+size]),(opcode,line)
    assert count==151
    return {'profile':'NES 2A03 official NMOS 6502 instruction encoding; no undocumented opcodes',
            'valid_opcode_mode_pairs':count,'vectors':count*4,'roundtrip':'PASS',
            'assembler_disassembler':'py65 1.2.0','CPU_decimal_arithmetic':'not used by new code'}
