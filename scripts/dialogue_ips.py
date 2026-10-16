"""Local dialogue-PoC IPS create/apply with append support and exact hash guards."""
import argparse
import hashlib
import json
from pathlib import Path

def sha(data):return hashlib.sha256(data).hexdigest()

def make(source,target):
    assert len(source)<=len(target)<0x1000000
    patch=bytearray(b'PATCH');i=0
    while i<len(target):
        if i<len(source) and source[i]==target[i]:i+=1;continue
        start=i
        while i<len(target) and (i>=len(source) or source[i]!=target[i]) and i-start<65535:i+=1
        assert start!=0x454F46,'IPS EOF-offset ambiguity'
        patch.extend(start.to_bytes(3,'big'));patch.extend((i-start).to_bytes(2,'big'));patch.extend(target[start:i])
    return bytes(patch+b'EOF')

def apply(source,patch):
    assert patch[:5]==b'PATCH';target=bytearray(source);pos=5;covered=set()
    while True:
        assert pos+3<=len(patch),'Missing IPS EOF'
        if patch[pos:pos+3]==b'EOF':break
        assert pos+5<=len(patch)
        offset=int.from_bytes(patch[pos:pos+3],'big');size=int.from_bytes(patch[pos+3:pos+5],'big');pos+=5
        assert size and pos+size<=len(patch),'Truncated or unsupported RLE record'
        assert offset<=len(target),'Unexpected hole in local append patch'
        region=set(range(offset,offset+size));assert not region&covered;covered|=region
        target[offset:offset+size]=patch[pos:pos+size];pos+=size
    assert pos+3==len(patch),'Trailing IPS bytes'
    return bytes(target)

def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='mode',required=True)
    create=sub.add_parser('create');create.add_argument('--source',type=Path,required=True)
    create.add_argument('--target',type=Path,required=True);create.add_argument('--patch',type=Path,required=True)
    create.add_argument('--scope',default='Experimental JP_175A9 + existing Korean title; not a full release')
    install=sub.add_parser('apply');install.add_argument('--source',type=Path,required=True)
    install.add_argument('--patch',type=Path,required=True);install.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();source=a.source.read_bytes();meta_path=a.patch.with_suffix('.json')
    if a.mode=='create':
        target=a.target.read_bytes();patch=make(source,target);assert apply(source,patch)==target
        assert not a.patch.exists() and not meta_path.exists()
        a.patch.write_bytes(patch)
        meta={'source_sha256':sha(source),'output_sha256':sha(target),'output_size':len(target),
              'patch_sha256':sha(patch),'scope':a.scope}
        meta_path.write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
        print('IPS created; full appended CHR included; internal apply matches target')
    else:
        meta=json.loads(meta_path.read_text(encoding='utf-8'));patch=a.patch.read_bytes()
        assert sha(source)==meta['source_sha256'] and sha(patch)==meta['patch_sha256']
        target=apply(source,patch);assert sha(target)==meta['output_sha256'] and len(target)==meta['output_size']
        assert not a.output.exists() and a.output.resolve()!=a.source.resolve()
        a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(target)
        print('Applied and verified SHA-256: '+sha(target))

if __name__=='__main__':main()
