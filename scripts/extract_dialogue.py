"""Extract every root in the registered Japanese dialogue table, without ROM writes.

The original token stream is authoritative. Human-readable NFC text is a view.
CSV translation fields are initialized only when absent, never overwritten.
"""
import argparse, csv, hashlib, json, unicodedata
from collections import Counter, defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TABLE=0x17443
COUNT=26
START=0x17477
BASE=0xC010 # file = CPU + 0xC010, for this observed PRG bank only
KANA=' あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんゃゅょっ'
GLYPHS={i:c for i,c in enumerate(KANA)}
GLYPHS.update({0x33:'\u3099',0x34:'\u309a',0x35:'？',0x36:'！',0x37:'「',0x38:'」',0x39:'・',0x3A:'3',0x3B:'0',
 0x49:'I',0x4A:'U',0x4B:'P',0x4C:'ア',0x4D:'イ',0x4E:'エ',0x4F:'カ',0x50:'キ',0x51:'ク',0x52:'ク',0x53:'シ',0x54:'ス',0x55:'タ',0x56:'テ',0x57:'ト',0x58:'ナ',0x59:'ニ',0x5A:'ハ',0x5B:'ヒ',0x5C:'フ',0x5D:'ホ',0x5E:'マ',0x5F:'ム',0x60:'メ',0x61:'モ',0x62:'ラ',0x63:'リ',0x64:'ル',0x65:'レ',0x66:'ン',0x67:'ー',0x68:'ァ',0x69:'ッ',0x6A:'ャ',0x6B:'A',0x6C:'〈',0x6D:'〉'})
# Duplicate ク glyph slots are kept distinct by tile tokens.
OPS={0xFF:('graphic',0),0xFE:('graphic',0),0xFD:('graphic',0),0xFC:('graphic',0),0xFB:('graphic',0),
 0xFA:('end',0),0xF9:('clear',0),0xF8:('speed',1),0xF7:('delay',1),0xF6:('position',2),0xF5:('br',0),0xF4:('call',2),0xF3:('return',0)}
def sha(b):return hashlib.sha256(b).hexdigest()
def token_at(data,p):
    b=data[p]
    if b in OPS:
        name,n=OPS[b];raw=data[p:p+1+n]
        assert len(raw)==n+1
        token='{'+name+(':'+raw[1:].hex(',').upper() if n else (':'+f'{255-b:02X}' if name=='graphic' else ''))+'}'
        return {'offset':p,'code':b,'name':name,'raw_hex':raw.hex(' ').upper(),'token':token,'size':n+1,'args':list(raw[1:])}
    assert b in GLYPHS,f'Unmapped tile {b:02X} at {p:05X}'
    return {'offset':p,'code':b,'name':'glyph','raw_hex':f'{b:02X}','token':f'{{tile:{b:02X}}}','size':1,'args':[]}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--initialize-translation',action='store_true');a=ap.parse_args()
    manifest=json.loads((ROOT/'manifests/source_rom.json').read_text(encoding='utf-8'))
    data=(ROOT/manifest['path']).read_bytes();assert sha(data)==manifest['sha256'] and len(data)==manifest['size_bytes']
    roots=[int.from_bytes(data[TABLE+i*2:TABLE+i*2+2],'little')+BASE for i in range(COUNT)]
    tokens={};root_paths={};references=defaultdict(set)
    for index,start in enumerate(roots):
        p=start;stack=[];path=[]
        for _ in range(10000):
            assert START<=p<0x17850
            t=token_at(data,p);tokens[p]=t;path.append(p);references[p].add(index);p+=t['size']
            if t['name']=='call':
                stack.append(p);p=int.from_bytes(bytes(t['args']),'little')+BASE
            elif t['name']=='return':
                assert stack,'Return without call';p=stack.pop()
            elif t['name']=='end':
                assert not stack;break
        else:raise AssertionError('Nonterminating root')
        root_paths[index]=path
    end=max(p+t['size'] for p,t in tokens.items())
    covered={i for p,t in tokens.items() for i in range(p,p+t['size'])}
    assert covered==set(range(START,end)), 'Unclaimed bytes inside dialogue extent'
    rebuilt=b''.join(bytes.fromhex(tokens[p]['raw_hex']) for p in sorted(tokens))
    assert rebuilt==data[START:end]
    pages=[];current=[]
    def flush():
        if not any(t['name']=='glyph' for t in current):current.clear();return
        lo=current[0]['offset'];hi=current[-1]['offset']+current[-1]['size']
        readable=''.join(GLYPHS[t['code']] if t['name']=='glyph' else '\n' if t['name']=='br' else '' for t in current)
        ids=sorted(set.union(*(references[t['offset']] for t in current)))
        pages.append({'entry_id':f'JP_{lo:05X}','file_offset':f'0x{lo:05X}','end_exclusive':f'0x{hi:05X}','script_ids':','.join(f'{i:02d}' for i in ids),
         'original_jp':unicodedata.normalize('NFC',readable),'source_tokens':''.join(t['token'] for t in current),
         'raw_hex':data[lo:hi].hex(' ').upper(),'source_sha256':manifest['sha256']})
        current.clear()
    for p in sorted(tokens):
        t=tokens[p]
        if t['name'] in ('clear','end','return','call'):flush()
        elif t['name'] in ('glyph','br','delay','speed','position'):current.append(t)
    flush()
    out=a.output.resolve();assert ROOT/'original' not in out.parents
    out.mkdir(parents=True,exist_ok=False)
    (out/'dialogue_tokens.json').write_text(json.dumps({'source':manifest,'table_file_offset':f'0x{TABLE:05X}','root_count':COUNT,
     'extent':[f'0x{START:05X}',f'0x{end:05X}'],'roots':[{'script_id':i,'pointer_file_offset':f'0x{TABLE+i*2:05X}','cpu_address':f'${p-BASE:04X}','file_offset':f'0x{p:05X}','token_offsets':root_paths[i]} for i,p in enumerate(roots)],
     'tokens':[tokens[p] for p in sorted(tokens)],'glyphs':{f'{i:02X}':c for i,c in GLYPHS.items()},'pages':pages},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    fields=list(pages[0])
    with (out/'dialogue_original.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(pages)
    if a.initialize_translation:
        dest=ROOT/'workspace/translation/dialogue_ja.csv';assert not dest.exists(),'Existing translation SSOT must be preserved'
        dest.parent.mkdir(parents=True,exist_ok=True)
        fields=['entry_id','scene','speaker','speaker_en','speaker_status','addressee','original_jp','translation_ko','status','speaker_basis','source_urls','script_ids','file_offset','end_exclusive','source_tokens','raw_hex','source_sha256','notes']
        with dest.open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
            for row in pages:w.writerow({**row,'status':'untranslated'})
    report={'source_sha256':sha(data),'pointer_slots':COUNT,'unique_root_addresses':len(set(roots)),'unique_pages':len(pages),
     'extent_start':f'0x{START:05X}','extent_end_exclusive':f'0x{end:05X}','owned_bytes':len(covered),'roundtrip':'PASS','unmapped_tiles':0,
     'scope':'All 26 roots and their called script in the observed Japanese dialogue consumer. Global absence of other render paths and full gameplay not proven.'}
    (out/'extraction_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    for row in pages:print(row['entry_id'],row['script_ids'],repr(row['original_jp']))
if __name__=='__main__':main()
