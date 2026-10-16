"""Check a submitted CSV against the immutable extracted source, without editing it."""
import argparse, csv, hashlib, json, re
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FIELDS=['entry_id','scene','speaker','speaker_en','speaker_status','addressee','original_jp','translation_ko','status','speaker_basis','source_urls','script_ids','file_offset','end_exclusive','source_tokens','raw_hex','source_sha256','notes']
MUTABLE={'translation_ko','status','notes'}
def readcsv(path):
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f);assert reader.fieldnames==FIELDS,'CSV header mismatch'
        rows=list(reader)
    assert all(set(r)==set(FIELDS) and all(v is not None for v in r.values()) for r in rows),'Malformed CSV row'
    assert len({r['entry_id'] for r in rows})==len(rows),'Duplicate IDs'
    return rows
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--prepare-import',type=Path)
    a=ap.parse_args();incoming=a.input.resolve();rows=readcsv(incoming)
    baseline=readcsv(ROOT/'backups/translation/dialogue_ja_before_import_20261001.csv') if (ROOT/'backups/translation/dialogue_ja_before_import_20261001.csv').exists() else readcsv(ROOT/'workspace/translation/dialogue_ja.csv')
    expected={r['entry_id']:r for r in baseline};actual={r['entry_id']:r for r in rows}
    assert actual.keys()==expected.keys() and len(rows)==22,'Missing or extra IDs'
    for key,row in actual.items():
        assert all(row[k]==expected[key][k] for k in FIELDS if k not in MUTABLE),(key,'Protected field changed')
        assert row['translation_ko'].strip(),(key,'Empty translation')
    source=json.loads((ROOT/'extracted/text/dialogue_20261001/dialogue_tokens.json').read_text(encoding='utf-8'))
    manifest=json.loads((ROOT/'manifests/source_rom.json').read_text(encoding='utf-8'))
    rom=ROOT/manifest['path'];assert sha(rom)==manifest['sha256']
    for page in source['pages']:
        for field,value in page.items():assert actual[page['entry_id']][field]==value,(page['entry_id'],field)
    linebreak_changes=[r['entry_id'] for r in rows if r['original_jp'].count('\n')!=r['translation_ko'].count('\n')]
    japanese=[r['entry_id'] for r in rows if re.search('[\u3040-\u30ff]',r['translation_ko'])]
    assert not japanese,'Japanese remains in translation'
    chars=set(''.join(r['translation_ko'] for r in rows))-{'\n'}
    hangul=sorted(c for c in chars if '\uac00'<=c<='\ud7a3')
    longlines=[{'entry_id':r['entry_id'],'line_number':i+1,'text':line,'cells_if_one_char_per_tile':len(line)} for r in rows for i,line in enumerate(r['translation_ko'].split('\n')) if len(line)>16]
    title=ROOT/'build/title_kr_ai_004/TinyToon_title_kr_poc.nes'
    assert sha(title)=='beb669edda6c666a10c7b933f5ebee5eecda81ca46d31d17e33d51d6657103b4'
    report={'status':'PASS','scope':'Source protection and translation presence checks only; not final language or build approval',
     'input_path':str(incoming.relative_to(ROOT)),'input_sha256':sha(incoming),'source_sha256':sha(rom),'title_sha256':sha(title),
     'entries':len(rows),'nonempty_translations':22,'missing_ids':[],'duplicate_ids':[],'protected_fields':'PASS',
     'japanese_remaining':japanese,'linebreak_count_changes':linebreak_changes,'submitted_status_counts':dict(Counter(r['status'] for r in rows)),
     'hangul_syllable_count':len(hangul),'hangul_syllables':''.join(hangul),'printable_character_count_including_space':len(chars),
     'other_characters':''.join(sorted(chars-set(hangul))),'maximum_hangul_syllables_per_entry':max(len(set(r['translation_ko'])&set(hangul)) for r in rows),
     'maximum_printable_characters_per_entry':max(len(set(r['translation_ko'])-{'\n'}) for r in rows),
     'layout_candidates_16_columns':longlines,'layout_note':'16-column projection assumes one 8x8 tile per Korean character. Korean glyph design, wrapping, supply, and scene QA remain unverified.',
     'validation_classes':{'static':'PASS','build_apply':'not performed','emulator_runtime':'not performed this session','scene_visual':'not performed this session'}}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if a.prepare_import:
        imported=[]
        for base in baseline:
            row=base.copy();new=actual[row['entry_id']]
            row.update(translation_ko=new['translation_ko'],notes=new['notes'],status='needs_review');imported.append(row)
        a.prepare_import.parent.mkdir(parents=True,exist_ok=True)
        a.prepare_import.write_text(json.dumps({'fields':FIELDS,'rows':imported,'input_sha256':sha(incoming)},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('status','entries','nonempty_translations','protected_fields','submitted_status_counts','hangul_syllable_count','maximum_hangul_syllables_per_entry','maximum_printable_characters_per_entry','layout_candidates_16_columns')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
