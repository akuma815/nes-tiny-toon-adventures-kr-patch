"""Extract the observed NES title background into reversible PNG/index assets."""
import hashlib, json
from pathlib import Path
from collections import Counter
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BOXES = [(48,56,224,104),(64,104,208,144)]
def decode(raw):
    return bytes(((raw[y]>>(7-x))&1)|(((raw[y+8]>>(7-x))&1)<<1) for y in range(8) for x in range(8))
def encode(pixels):
    return bytes(sum(((pixels[y*8+x]>>plane)&1)<<(7-x) for x in range(8)) for plane in range(2) for y in range(8))
def unpack(rom, start=0x3654):
    addr=int.from_bytes(rom[start:start+2],'little'); pos=start+2; result=bytearray(); origins=[]
    while rom[pos]:
        command=rom[pos]; pos+=1
        if command==0x80: raise ValueError('Address-change command requires a multi-segment parser')
        count=command&0x7f
        if command&0x80:
            result.extend(rom[pos:pos+count]); origins.extend(range(pos,pos+count)); pos+=count
        else:
            result.extend([rom[pos]]*count); origins.extend([pos]*count); pos+=1
    return addr,bytes(result),pos+1,origins
def mask_cell(col,row):
    return any(x0<=col*8<x1 and y0<=row*8<y1 for x0,y0,x1,y1 in BOXES) and not (row==16 and col in (24,25)) and not (row==17 and col==24)
def main():
    source=json.loads((ROOT/'manifests/source_rom.json').read_text(encoding='utf-8'))
    rom=(ROOT/source['path']).read_bytes()
    assert hashlib.sha256(rom).hexdigest()==source['sha256']
    evidence=ROOT/'qa/title/original_20261001'
    ppu=(evidence/'frame_0240_ppu.bin').read_bytes(); screen=Image.open(evidence/'frame_0240.png').convert('RGB')
    addr,nt,end,origins=unpack(rom)
    assert addr==0x2000 and len(nt)==1024 and nt==ppu[0x2000:0x2400]
    assert all(decode(rom[i:i+16])==decode(ppu[i-0x2e010:i-0x2e010+16]) for i in range(0x2e010,0x2f010,16))
    indexed=Image.new('L',(256,240)); colors={}
    for row in range(30):
        for col in range(32):
            tile=nt[row*32+col]; pixels=decode(ppu[tile*16:tile*16+16])
            for y in range(8):
                for x in range(8): indexed.putpixel((col*8+x,row*8+y),pixels[y*8+x])
    for value in range(4):
        counts=Counter(screen.getpixel((x,y)) for x in range(48,224) for y in range(56,104) if indexed.getpixel((x,y))==value)
        colors[value]=counts.most_common(1)[0][0]
    crop=indexed.crop((48,56,224,144)); clean=Image.new('RGB',crop.size,colors[0]); mask=Image.new('L',crop.size,0)
    used=set(); outside=set()
    for row in range(30):
        for col in range(32):
            (used if mask_cell(col,row) else outside).add(nt[row*32+col])
    for y in range(88):
        for x in range(176):
            if mask_cell((x+48)//8,(y+56)//8):
                clean.putpixel((x,y),colors[crop.getpixel((x,y))]);mask.putpixel((x,y),255)
    target=ROOT/'extracted/title/title_20261001';target.mkdir(parents=True,exist_ok=True)
    indexed.save(target/'background_indices.png'); clean.save(target/'logo_original.png');mask.save(target/'logo_edit_mask.png')
    clean.resize((1408,704),Image.Resampling.NEAREST).save(target/'logo_original_8x.png')
    nt_file=target/'nametable.bin'; nt_file.write_bytes(nt)
    report={'source_sha256':source['sha256'],'frame':240,'title_rle_start':0x3654,'title_rle_end_exclusive':end,
      'rle_cpu_address':0xb644,'rle_consumer_file_start':0x35a5,'nametable_sha256':hashlib.sha256(nt).hexdigest(),
      'title_decode_matches_runtime':True,'chr_page_matches_runtime':True,'crop_box':[48,56,224,144],
      'editable_boxes':BOXES,'rgb_palette':[colors[i] for i in range(4)],'palette_ppu_indices':list(ppu[0x3f00:0x3f04]),
      'editable_tiles':sorted(used-outside),'shared_protected_tiles':sorted(used&outside),
      'chr_file_base':0x2e010,'observed_bg_chr_banks_1k':[56,57,58,59],
      'limits':'Other scenes and sprite consumers remain to be checked; no complete-game sharing proof.'}
    (target/'title_extraction.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
