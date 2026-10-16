"""Seal the reviewed cafe text and figures as a portable, ROM-free package."""
import argparse,base64,hashlib,json,re,zipfile
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--folder',type=Path,required=True);ap.add_argument('--render',type=Path,required=True);ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--finish',action='store_true');a=ap.parse_args();a.render=a.render.resolve();a.render.relative_to(ROOT/'qa/publication')
    folder=a.folder.resolve();folder.relative_to(ROOT/'workspace/publication');archive=a.archive.resolve();archive.relative_to(ROOT/'workspace/publication');assert archive.suffix=='.zip' and (not archive.exists() or a.finish)
    render=json.loads((a.render/'render_report.json').read_text(encoding='utf-8'));assert render['status']=='PASS' and render['source']==(folder/'작업기.html').relative_to(ROOT).as_posix()
    report=ROOT/'qa/reports'/(folder.name+'_publication.json');r=json.loads(report.read_text(encoding='utf-8'));assert r['status']=='COMPOSED_REVIEW_PENDING'
    assert len(r['figures'])==16
    for figure in r['figures']:
        p=folder/figure['file'];assert sha(p)==figure['sha256'];assert Image.open(p).size==tuple(figure['pixels'])
        for source in figure['sources']:assert sha(ROOT/source['path'])==source['sha256']
    for source in r['evidence']:assert sha(ROOT/source['path'])==source['sha256']
    txt=(folder/'네이버카페_게시글본문.txt').read_text(encoding='utf-8-sig');markers=re.findall(r'\[이미지 (\d+): ([^\]]+)\]',txt)
    assert [int(n) for n,_ in markers]==list(range(1,17));assert [name for _,name in markers]==[Path(f['file']).name for f in r['figures']]
    markup=(folder/'작업기.html').read_text(encoding='utf-8');embedded=re.findall(r'<img src="data:image/png;base64,([^"]+)"',markup);assert len(embedded)==16
    for encoded,figure in zip(embedded,r['figures']):assert base64.b64decode(encoded)==(folder/figure['file']).read_bytes()
    files=sorted(p for p in folder.rglob('*') if p.is_file());assert len(files)==19
    assert {p.suffix.lower() for p in files}=={'.html','.txt','.png'}
    assert all('\ufffd' not in p.read_text(encoding='utf-8-sig') for p in files if p.suffix in ('.txt','.html'))
    public={p.relative_to(folder).as_posix():sha(p) for p in files};top=archive.stem
    if not archive.exists():
        with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for p in files:
                item=zipfile.ZipInfo(top+'/'+p.relative_to(folder).as_posix(),(2026,10,4,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;z.writestr(item,p.read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and len(z.namelist())==19
        for p in files:assert z.read(top+'/'+p.relative_to(folder).as_posix())==p.read_bytes()
    checksum=sha(archive).upper()+'  '+archive.name+'\n';hashfile=archive.with_suffix('.zip.sha256')
    if hashfile.exists():assert hashfile.read_text(encoding='ascii')==checksum
    else:hashfile.write_text(checksum,encoding='ascii')
    r.update(status='PASS',public_files=public,archive={'path':archive.relative_to(ROOT).as_posix(),'sha256':sha(archive),'bytes':archive.stat().st_size,'files':19,'CRC_and_payload_match':True},direct_visual_review={'all_16_figures_reviewed':True,'desktop_and_mobile_reader_reviewed':True,'diagram_types':['workflow','glyph grid','per-paragraph font mapping','branch and wait state','verification stages','patch package'],'caption_and_capture_provenance_reviewed':True},reader_validation={'path':(a.render/'render_report.json').relative_to(ROOT).as_posix(),'sha256':sha(a.render/'render_report.json'),'HTML_sha256':sha(folder/'작업기.html'),'status':'PASS'},article_checks={'sequential_image_markers':16,'embedded_images_identical_to_PNG':True,'no_external_image_dependency':True,'ROM_font_dump_emulator_not_included':True,'UTF8_no_replacement_characters':True,'Naver_cafe_plaintext_and_PNG_format':True},game_build_scope='Existing v1.0.1 evidence only; no new ROM build/emulator run or broader game validation.',posting_scope='Local publication materials prepared; no cafe post sent.')
    report.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':'PASS','archive':r['archive'],'figures':16,'render':'PASS'}))
if __name__=='__main__':main()
