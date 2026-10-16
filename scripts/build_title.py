"""Build a local title PoC from a PNG, with protected tiles and Expected Writes."""
import argparse, hashlib, json, sys
from pathlib import Path
from PIL import Image, __version__ as pillow_version
from extract_title import ROOT, decode, encode, unpack, mask_cell

def sha(data): return hashlib.sha256(data).hexdigest()
def pack(data):
    # Shortest stream for one repeat/literal segment. 0x80 starts a new address.
    n=len(data); cost=[0]*(n+1); choice=[None]*n
    for i in range(n-1,-1,-1):
        candidates=[(1+k+cost[i+k],True,k) for k in range(1,min(127,n-i)+1)]
        run=1
        while run<127 and i+run<n and data[i+run]==data[i]:run+=1
        candidates.extend((2+cost[i+k],False,k) for k in range(1,run+1))
        cost[i],literal,length=min(candidates);choice[i]=(literal,length)
    result=bytearray();i=0
    while i<n:
        literal,length=choice[i];result.append(length|(0x80 if literal else 0))
        result.extend(data[i:i+length] if literal else data[i:i+1]);i+=length
    return bytes(result)
def normalize(raw, palette, mask):
    im=Image.open(raw).convert('RGB').resize((176,88),Image.Resampling.BOX)
    result=Image.new('L',im.size);clipped=0
    for y in range(88):
        for x in range(176):
            color=im.getpixel((x,y))
            v=min(range(4),key=lambda i:sum((color[j]-palette[i][j])**2 for j in range(3)))
            if not mask.getpixel((x,y)):
                clipped+=v!=0;v=0
            result.putpixel((x,y),v)
    if clipped: raise ValueError(f'AI image crosses protected mask: {clipped} pixels')
    return result
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--png',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--rom',type=Path);ap.add_argument('--roundtrip',action='store_true');args=ap.parse_args()
    source=json.loads((ROOT/'manifests/source_rom.json').read_text(encoding='utf-8'))
    rom=(args.rom or ROOT/source['path']).read_bytes()
    assert len(rom)==source['size_bytes'] and sha(rom)==source['sha256'], 'Source identity mismatch'
    asset=ROOT/'extracted/title/title_20261001'
    info=json.loads((asset/'title_extraction.json').read_text(encoding='utf-8'))
    assert info['source_sha256']==source['sha256']
    start,end=info['title_rle_start'],info['title_rle_end_exclusive'];addr,nt,actual_end,_=unpack(rom,start)
    assert end==actual_end and sha(nt)==info['nametable_sha256'] and addr==0x2000
    base=info['chr_file_base']; mask=Image.open(asset/'logo_edit_mask.png');palette=info['rgb_palette']
    indices=normalize(args.png,palette,mask); new_nt=bytearray(nt);plan=[]
    if args.roundtrip:
        for row in range(7,18):
            for col in range(6,28):
                if mask_cell(col,row):
                    tile=nt[row*32+col];raw=rom[base+tile*16:base+(tile+1)*16]
                    piece=bytes(indices.crop(((col-6)*8,(row-7)*8,(col-5)*8,(row-6)*8)).get_flattened_data())
                    assert encode(piece)==raw,'Original PNG roundtrip mismatch'
        unique_count=0; packed_size=end-start
    else:
        blank=bytes(16);patterns={blank:0};pool=iter(info['editable_tiles']);new_tiles={}
        assert rom[base:base+16]==blank
        for row in range(7,18):
            for col in range(6,28):
                if not mask_cell(col,row):continue
                raw=encode(bytes(indices.crop(((col-6)*8,(row-7)*8,(col-5)*8,(row-6)*8)).get_flattened_data()))
                if raw not in patterns:
                    try: tile=next(pool)
                    except StopIteration:raise ValueError('Title tile budget exceeded')
                    patterns[raw]=tile;new_tiles[tile]=raw
                new_nt[row*32+col]=patterns[raw]
        unique_count=len(new_tiles)
        for tile,raw in new_tiles.items():
            offset=base+tile*16
            plan.append({'owner':'title_logo','reason':f'PNG-derived 2bpp tile {tile:02X}', 'file_offset':offset,
                         'length':16,'expected_hex':rom[offset:offset+16].hex(),'final_hex':raw.hex()})
        compressed=pack(new_nt);packed_size=len(compressed)+3
        if packed_size>end-start:raise ValueError(f'Title stream budget exceeded: {packed_size}>{end-start}')
        replacement=addr.to_bytes(2,'little')+compressed+b'\0'+rom[start+packed_size:end]
        plan.append({'owner':'title_layout','reason':'Repacked title nametable, same extent, attributes unchanged',
                     'file_offset':start,'length':end-start,'expected_hex':rom[start:end].hex(),'final_hex':replacement.hex()})
    # Validate every write against the immutable source, then apply once.
    allowed=set();new_rom=bytearray(rom)
    for write in plan:
        offset=write['file_offset'];length=write['length'];expected=bytes.fromhex(write['expected_hex']);final=bytes.fromhex(write['final_hex'])
        assert rom[offset:offset+length]==expected and len(final)==length
        region=set(range(offset,offset+length));assert not region&allowed;allowed|=region
    for write in plan:
        offset=write['file_offset'];new_rom[offset:offset+write['length']]=bytes.fromhex(write['final_hex'])
    diff={i for i,(a,b) in enumerate(zip(rom,new_rom)) if a!=b};assert diff<=allowed and len(new_rom)==len(rom)
    _,actual_nt,actual_end,_=unpack(new_rom,start);assert actual_nt==new_nt and actual_end<=end
    assert new_nt[960:]==nt[960:]
    for row in range(30):
        for col in range(32):
            if not mask_cell(col,row):
                old=nt[row*32+col];new=new_nt[row*32+col]
                assert old==new and rom[base+old*16:base+(old+1)*16]==new_rom[base+new*16:base+(new+1)*16]
    output=args.output.resolve();assert ROOT/'original' not in output.parents and output!=ROOT/'original';output.mkdir(parents=True,exist_ok=False)
    # The complete plan is persisted before the ROM output.
    (output/'expected_writes.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
    name='TinyToon_title_roundtrip.nes' if args.roundtrip else 'TinyToon_title_kr_poc.nes'
    (output/name).write_bytes(new_rom);indices.save(output/'logo_indices.png')
    rgb=Image.new('RGB',indices.size);rgb.putdata([tuple(palette[v]) for v in indices.get_flattened_data()]);rgb.save(output/'logo_nes.png')
    preview=Image.open(ROOT/'qa/title/original_20261001/frame_0240.png').convert('RGB')
    original_indices=Image.open(asset/'background_indices.png')
    for y in range(88):
        for x in range(176):
            if mask.getpixel((x,y)):
                original_background=tuple(palette[original_indices.getpixel((x+48,y+56))])
                # Preserve sprite pixels that overlay the editable background.
                if preview.getpixel((x+48,y+56))==original_background:
                    preview.putpixel((x+48,y+56),rgb.getpixel((x,y)))
    if not args.roundtrip:preview.save(output/'title_static_preview.png')
    report={'source_sha256':sha(rom),'output_sha256':sha(new_rom),'png_sha256':sha(args.png.read_bytes()),
      'output_rom':name,'roundtrip_identity':bytes(new_rom)==rom,'unique_nonblank_tiles':unique_count,
      'available_title_tiles':len(info['editable_tiles']),'rle_used_bytes':packed_size,'rle_capacity_bytes':end-start,
      'changed_bytes':len(diff),'expected_write_count':len(plan),'header_preserved':new_rom[:16]==rom[:16],
      'protected_title_pixels_preserved':True,'python_version':sys.version,'pillow_version':pillow_version,
      'scope':'Static build. Runtime evidence must be generated separately.'}
    (output/'build_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
