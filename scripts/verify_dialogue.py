"""Verify dialogue CSV protected fields, reversible tokens, ROM, and real read trace."""
import argparse,csv,hashlib,json,re
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,default=ROOT/'qa/reports/dialogue_extraction_2026-10-01.json')
    args=ap.parse_args()
    manifest=json.loads((ROOT/'manifests/source_rom.json').read_text(encoding='utf-8'))
    rom=(ROOT/manifest['path']).read_bytes();assert hashlib.sha256(rom).hexdigest()==manifest['sha256']
    out=args.output.resolve()
    assert out.is_relative_to(ROOT/'qa/reports'),'Output must stay within qa/reports'
    out.write_text('{"status":"IN_PROGRESS"}\n',encoding='utf-8')
    base=ROOT/'extracted/text/dialogue_20261001'
    tokens=json.loads((base/'dialogue_tokens.json').read_text(encoding='utf-8'))
    csvpath=ROOT/'workspace/translation/dialogue_ja.csv'
    assert csvpath.read_bytes().startswith(b'\xef\xbb\xbf')
    rows=list(csv.DictReader(csvpath.open(encoding='utf-8-sig',newline='')))
    pages=tokens['pages'];assert len(rows)==len(pages)==22
    assert len({r['entry_id'] for r in rows})==len(rows)
    opcodes={'end':0xFA,'clear':0xF9,'speed':0xF8,'delay':0xF7,'position':0xF6,'br':0xF5,'call':0xF4,'return':0xF3}
    for row,page in zip(rows,pages):
        for key,value in page.items():assert row[key]==value,(row['entry_id'],key)
        lo=int(row['file_offset'],16);hi=int(row['end_exclusive'],16)
        assert bytes.fromhex(row['raw_hex'])==rom[lo:hi]
        rebuilt=bytearray()
        for match in re.finditer(r'\{([^}:]+)(?::([^}]+))?\}',row['source_tokens']):
            name,args=match.groups()
            if name=='tile':rebuilt.append(int(args,16))
            else:
                rebuilt.append(opcodes[name])
                if args:rebuilt.extend(int(x,16) for x in args.split(','))
        assert bytes(rebuilt)==rom[lo:hi]
        assert row['speaker'] and row['speaker_basis'] and row['speaker_status']
    lo,hi=map(lambda s:int(s,16),tokens['extent'])
    stream=b''.join(bytes.fromhex(t['raw_hex']) for t in tokens['tokens'])
    assert stream==rom[lo:hi]
    reads=list(csv.DictReader((ROOT/'qa/dialogue/original_trace_002/script_reads.csv').open()))
    assert len(reads)==75
    for read in reads:assert rom[int(read['file_offset'],16)]==int(read['value'],16)
    assert any(r['file_offset']=='175A9' for r in reads) and any(r['file_offset']=='17618' for r in reads)
    title=ROOT/'build/title_kr_ai_004/TinyToon_title_kr_poc.nes'
    assert digest(title)=='beb669edda6c666a10c7b933f5ebee5eecda81ca46d31d17e33d51d6657103b4'
    # Local Markdown links in the modified project entry documents.
    docs=['README.md','docs/HANDOFF.md','docs/HANDOFF_2026-10-01.md','docs/DIALOGUE_EXTRACTION.md']
    link_count=0
    for name in docs:
        path=ROOT/name
        for target in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):continue
            target=target.split('#')[0]
            assert (path.parent/target).exists(),(name,target);link_count+=1
    files=['workspace/translation/dialogue_ja.csv','scripts/extract_dialogue.py','scripts/verify_dialogue.py','scripts/trace_dialogue.lua','scripts/run_dialogue_trace.py',
     'extracted/text/dialogue_20261001/dialogue_tokens.json','extracted/text/dialogue_20261001/dialogue_original.csv','extracted/text/dialogue_20261001/extraction_report.json',
     'docs/SURVEY.md','docs/LOCALIZATION_WORK_PLAN.md','work/dialogue_20261001/prepare_speakers.py','work/dialogue_20261001/finalize_csv.mjs',
     'qa/reports/dialogue_reextract_repro_2026-10-01.json',*docs]
    report={'status':'PASS','source_sha256':manifest['sha256'],'title_build_preserved_sha256':digest(title),
     'pointer_slots':26,'unique_root_addresses':21,'unique_pages':len(rows),'script_extent_bytes':len(stream),
     'protected_csv_fields':'PASS','token_to_raw_roundtrip':'PASS','whole_script_roundtrip':'PASS','csv_encoding':'UTF-8 BOM / RFC4180 multiline',
     'speaker_counts':dict(Counter(r['speaker'] for r in rows)),'real_consumer_read_checks':len(reads),'local_document_links_checked':link_count,
     'nonempty_translation_rows':sum(bool(r['translation_ko'].strip()) for r in rows),'translation_status_counts':dict(Counter(r['status'] for r in rows)),
     'runtime':'Prior-session Mesen 2.1.1 original cold boot trace exit 0; Shirley selection sample only; not rerun by this verifier',
     'visual':'Original Shirley portrait/partner selection frame_0960 inspected; other dialogue scenes not played or visually verified',
     'build_apply':'Not performed in this session; extraction only',
     'limitations':['Coverage complete for all 26 roots of this consumer; global absence of another Japanese render path not proven','Full game and ending scene visual QA not performed','Montana Max, Babs, and Buster speaker attribution is a strong inference, without explicit speaker IDs','Korean translation layout, glyph supply, and reinsertion remain unverified'],
     'files':{name:digest(ROOT/name) for name in files}}
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('files','limitations')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
