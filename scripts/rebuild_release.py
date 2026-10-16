"""Rebuild the adopted final release from a hash-pinned owned original and Git.

Run in a fresh checkout: python scripts/rebuild_release.py --rom SOURCE [--font-dir DIR]
Baseline recipes hold source references, fill runs and edited spans, never a ROM.
Legacy intermediate/QA scripts are retained as history, not all runnable standalone.
"""
from pathlib import Path
import argparse, csv, hashlib, json, shutil, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
def sha(b): return hashlib.sha256(b).hexdigest()
def load(p): return json.loads(p.read_text('utf-8-sig'))
def put(p, d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf-8')
def restore(src, spec):
    assert sha(src)==spec['source_sha256']
    out=bytearray()
    for op in spec['operations']:
        if 'copy_source' in op:
            p,n=op['copy_source'],op['length'];assert p>=0 and n>0 and p+n<=len(src)
            out.extend(src[p:p+n])
        elif 'fill' in op:
            assert 0<=op['fill']<=255 and op['length']>0
            out.extend(bytes([op['fill']])*op['length'])
        else: out.extend(bytes.fromhex(op['write_hex']))
        assert len(out)<=spec['output_size']
    assert len(out)==spec['output_size'] and sha(out)==spec['output_sha256']
    return bytes(out)
def run(script,*args):
    result=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'scripts'/script),*map(str,args)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    log=ROOT/'build/reproduction_logs'/f'{script}.txt';log.parent.mkdir(parents=True,exist_ok=True);log.write_text(result.stdout+'\n'+result.stderr,'utf-8')
    if result.returncode: raise RuntimeError(f'{script} failed; see {log}\n{result.stderr[-3000:]}')
    return log
def replay(src,target,writes):
    model=bytearray(src);owned=bytearray(len(target))
    for w in sorted(writes,key=lambda w:w['file_offset']):
        p,n=w['file_offset'],w['length'];assert p>=0 and n>0 and p+n<=len(target)
        assert not any(owned[p:p+n]);owned[p:p+n]=bytes([1])*n
        if 'expected_hex' in w: assert src[p:p+n]==bytes.fromhex(w['expected_hex'])
        else:
            assert sha(src)==w['expected_source_sha256']
            assert sha(src[p:p+w['expected_overlap_length']])==w['expected_overlap_sha256']
        raw=bytes.fromhex(w['final_hex']);assert len(raw)==n
        model[p:p+n]=raw
    assert model==target
    assert all(owned[i] for i in range(len(target)) if i>=len(src) or target[i]!=src[i])
    return len(writes)
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--font-dir',type=Path,help='Part 1 only: supplied Galmuri7_8x8.png and Galmuri7.ttf')
    a=parser.parse_args();config=load(ROOT/'rebuild/config.json');src=a.rom.read_bytes()
    assert len(src)==262160 and sha(src)==config['source_sha256'],'Wrong original; file is untouched'
    # Never overwrite any previous build or substitute an existing input silently.
    assert not (ROOT/'build').exists(),'Use a fresh checkout: build/ must not exist'
    for rel,h in config['inputs'].items(): assert sha((ROOT/rel).read_bytes())==h,rel
    orig=ROOT/load(ROOT/'manifests/source_rom.json')['path']
    if orig.exists(): assert orig.read_bytes()==src
    else: orig.parent.mkdir(parents=True,exist_ok=True);orig.write_bytes(src)
    if config['part']==1:
        assert a.font_dir is not None,'Part 1 requires --font-dir'
        fontdir=ROOT/'workspace/fonts/galmuri7_8x8'
        for name,h in config['external_fonts'].items():
            raw=(a.font_dir/name).read_bytes();assert sha(raw)==h,name
            dest=fontdir/name
            if dest.exists(): assert dest.read_bytes()==raw
            else: dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        title=restore(src,load(ROOT/'rebuild/adopted_title.json'))
        base=ROOT/'build/title_kr_ai_004';base.mkdir(parents=True);(base/'TinyToon_title_kr_poc.nes').write_bytes(title)
        writes=[]
        for w in load(ROOT/'rebuild/title_prg_writes.json'):
            p,n=w['file_offset'],w['length'];w.update(final_hex=title[p:p+n].hex(),expected_hex=src[p:p+n].hex(),reason='Adopted title PNG converted to fixed NES tile/layout data');writes.append(w)
        put(base/'expected_writes.json',writes)
        run('extract_dialogue.py','--output',ROOT/'extracted/text/dialogue_20261001')
        out=ROOT/'build/final_reproduced'
        run('build_dialogue_footer_fix.py','--active-font-nops','2','--output',out)
        final=out/'TinyToon_dialogue_full.nes'
    else:
        base=ROOT/'build/dialogue_kr_poc_051';base.mkdir(parents=True)
        adopted=restore(src,load(ROOT/'rebuild/adopted_051.json'));(base/'TinyToon2_dialogue_kr_poc.nes').write_bytes(adopted)
        writes=load(ROOT/'rebuild/baseline_write_ranges.json')
        for w in writes:
            p,n=w['file_offset'],w['length'];w.update(expected_hex=src[p:p+n].hex(),final_hex=adopted[p:p+n].hex())
        replay(src,adopted,writes);put(base/'expected_writes.json',writes)
        run('build_opening11_186_v2.py','--output',ROOT/'build/opening11_poc_053')
        run('build_opening_layout193.py','--output',ROOT/'build/opening11_poc_055')
        run('build_homebooth11_199.py','--output',ROOT/'build/homebooth11_candidate_057')
        run('build_ordinary11_204.py','--output',ROOT/'build/ordinary11_candidate_059')
        render_credits()
        put(ROOT/'build/dialogue_kr_poc_037/ui_korean_page_mapping.json',load(ROOT/'rebuild/credits_native_timing.json'))
        out=ROOT/'build/final_reproduced';run('build_credits11_211.py','--output',out)
        final=out/'TinyToon2_Text11_Candidate062.nes'
    target=final.read_bytes();assert sha(target)==config['target_sha256'],'Final release identity mismatch'
    writes=load(out/'expected_writes.json');count=replay(src,target,writes)
    sys.path.insert(0,str(ROOT/'scripts'));from dialogue_ips import make,apply
    patch=make(src,target);assert apply(src,patch)==target
    (out/'final.ips').write_bytes(patch)
    result={'status':'PASS','part':config['part'],'source_sha256':sha(src),'target_sha256':sha(target),'target_bytes':len(target),'ROM':str(final.relative_to(ROOT)),'source_ExpectedWrites':count,'source_guards_and_full_replay':'PASS','IPS_apply_byte_exact':True,'original_input_unchanged':a.rom.read_bytes()==src,'inputs_verified':len(config['inputs']),'emulator':'NOT_RUN','visual_QA':'NOT_RUN','full_playthrough':'NOT_RUN'}
    put(out/'REBUILD_RESULT.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))

def render_credits():
    """Original 202 renderer without its historical report/handoff side effects."""
    from PIL import Image, ImageDraw, ImageFont
    sys.path.insert(0,str(ROOT/'scripts'));from extract_title_png import encode,decode
    rows=[r for r in csv.DictReader((ROOT/'workspace/translation/text_ja.csv').open(encoding='utf-8-sig')) if r['entry_id'] in ('MAIN_05939','MAIN_05999','MAIN_059E7')]
    face=ImageFont.truetype(str(ROOT/'workspace/fonts/galmuri11_candidate185/Galmuri11.ttf'),12)
    cases=[]
    for latin in (12,16):
        slots={bytes(64):0};atlas=bytearray(2048);pages=[]
        for r in rows:
            lines=r['translation_ko'].split('\n');im=Image.new('L',(256,len(lines)*16));d=ImageDraw.Draw(im);widths=[]
            for y,line in enumerate(lines):
                x=0
                for c in line:
                    advance=8 if c.isspace() else 12 if '\uac00'<=c<='\ud7a3' else latin
                    glyph=Image.new('L',(16,16));ImageDraw.Draw(glyph).text((0,-1),c,font=face,fill=2);box=glyph.getbbox()
                    assert c.isspace() or box
                    assert box is None or box[2]<=advance
                    d.text((x,y*16-1),c,font=face,fill=2);x+=advance
                assert x<=256;widths.append(x)
            codes=[]
            for y in range(0,im.height,8):
                line=[]
                for x in range(0,256,8):
                    bits=bytes(im.crop((x,y,x+8,y+8)).get_flattened_data())
                    if bits not in slots:
                        code=len(slots);slots[bits]=code;raw=encode(bits);assert decode(raw)==bits
                        if code<128: atlas[code*16:code*16+16]=raw
                    line.append(slots[bits])
                codes.append(line)
            pages.append({'entry_id':r['entry_id'],'unaltered_text':r['translation_ko'],'lines':lines,'line_widths':widths,'line_count':len(lines),'NT_rows':codes})
        cases.append({'shared_three_page_tiles':len(slots),'pages':pages})
        if latin==16:
            path=ROOT/'workspace/review/credits11_202/credits11_latin16_font.chr';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(atlas)
    assert [c['shared_three_page_tiles'] for c in cases]==[144,106]
    put(ROOT/'qa/reports/credits11_202_capacity.json',{'cases':cases})

if __name__=='__main__': main()
