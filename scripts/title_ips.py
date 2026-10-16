"""Create/apply a title experiment IPS, guarded by exact source/output SHA-256."""
import argparse,hashlib,json
from pathlib import Path
def sha(data):return hashlib.sha256(data).hexdigest()
def make(source,target):
    assert len(source)==len(target)<0x1000000
    patch=bytearray(b'PATCH');i=0
    while i<len(source):
        if source[i]==target[i]:i+=1;continue
        start=i
        while i<len(source) and source[i]!=target[i] and i-start<65535:i+=1
        patch.extend(start.to_bytes(3,'big'));patch.extend((i-start).to_bytes(2,'big'));patch.extend(target[start:i])
    return bytes(patch+b'EOF')
def apply(source,patch):
    assert patch[:5]==b'PATCH';target=bytearray(source);pos=5;covered=set()
    while patch[pos:pos+3]!=b'EOF':
        offset=int.from_bytes(patch[pos:pos+3],'big');size=int.from_bytes(patch[pos+3:pos+5],'big');pos+=5
        assert size and pos+size<=len(patch) and offset+size<=len(target)
        region=set(range(offset,offset+size));assert not region&covered;covered|=region
        target[offset:offset+size]=patch[pos:pos+size];pos+=size
    assert pos+3==len(patch)
    return bytes(target)
def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='mode',required=True)
    create=sub.add_parser('create');create.add_argument('--source',type=Path,required=True);create.add_argument('--target',type=Path,required=True);create.add_argument('--patch',type=Path,required=True)
    install=sub.add_parser('apply');install.add_argument('--source',type=Path,required=True);install.add_argument('--patch',type=Path,required=True);install.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();source=args.source.read_bytes();meta_path=args.patch.with_suffix('.json')
    if args.mode=='create':
        target=args.target.read_bytes();patch=make(source,target);assert apply(source,patch)==target
        assert not args.patch.exists() and not meta_path.exists()
        args.patch.write_bytes(patch);meta_path.write_text(json.dumps({'source_sha256':sha(source),'output_sha256':sha(target),'patch_sha256':sha(patch),'scope':'Experimental title logo only; not a full translation release.'},indent=2)+'\n')
        print('IPS created, internal apply matches target')
    else:
        meta=json.loads(meta_path.read_text());patch=args.patch.read_bytes()
        assert sha(source)==meta['source_sha256'],'Source identity mismatch'
        assert sha(patch)==meta['patch_sha256'],'Patch identity mismatch'
        target=apply(source,patch);assert sha(target)==meta['output_sha256'],'Output identity mismatch'
        assert not args.output.exists() and args.output.resolve()!=args.source.resolve()
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_bytes(target)
        print('Applied and verified SHA-256: '+sha(target))
if __name__=='__main__':main()
