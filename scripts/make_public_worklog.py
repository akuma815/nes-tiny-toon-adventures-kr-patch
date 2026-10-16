"""Compose a public Korean worklog from immutable project evidence."""
import argparse,base64,csv,hashlib,html,json,math,re,zipfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
BG='#F4F1EB';CARD='#FFFFFF';INK='#242936';MUTED='#626B79'
PINK='#BD326F';BLUE='#276397';GREEN='#237556';RED='#AD3C39';LINE='#D9DDE2'
W=1400
FONT='C:/Windows/Fonts/malgun.ttf';BOLD='C:/Windows/Fonts/malgunbd.ttf';JP='C:/Windows/Fonts/msgothic.ttc'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def font(size=32,bold=False,jp=False):return ImageFont.truetype(JP if jp else BOLD if bold else FONT,size)
def text(draw,xy,s,size=32,color=INK,bold=False,jp=False):draw.text(xy,s,font=font(size,bold,jp),fill=color)
def wrap(draw,s,width,size=30,bold=False,jp=False):
    lines=[]
    for paragraph in s.split('\n'):
        line=''
        for char in paragraph:
            if line and draw.textlength(line+char,font=font(size,bold,jp))>width:
                lines.append(line.rstrip());line=char.lstrip()
            else:line+=char
        lines.append(line)
    return lines
def paragraph(draw,xy,s,width,size=30,color=INK,bold=False,jp=False):
    x,y=xy
    for line in wrap(draw,s,width,size,bold,jp):text(draw,(x,y),line,size,color,bold,jp);y+=size+14
    return y
def canvas(title,subtitle,height):
    im=Image.new('RGB',(W,height),BG);d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,12),fill=PINK)
    text(d,(48,34),title,44,bold=True)
    text(d,(48,101),subtitle,27,MUTED)
    return im,d
def box(d,rect,fill=CARD,outline=LINE):d.rounded_rectangle(rect,radius=20,fill=fill,outline=outline,width=2)
def arrow(d,start,end,color=BLUE,width=6):
    d.line((start,end),fill=color,width=width)
    angle=math.atan2(end[1]-start[1],end[0]-start[0]);length=18
    points=[end,(end[0]-length*math.cos(angle-.55),end[1]-length*math.sin(angle-.55)),(end[0]-length*math.cos(angle+.55),end[1]-length*math.sin(angle+.55))]
    d.polygon(points,fill=color)
def bitmap(im,xy,rows,cell=34):
    d=ImageDraw.Draw(im);x,y=xy
    for dy,row in enumerate(rows):
        for dx,value in enumerate(row):
            r=(x+dx*cell,y+dy*cell,x+(dx+1)*cell,y+(dy+1)*cell)
            d.rectangle(r,fill='#FAFAFA' if value=='#' else '#172130',outline='#516170',width=1)
def sheet_rows(char):
    sheet=Image.open(ROOT/'workspace/fonts/galmuri7_8x8/Galmuri7_8x8.png').convert('RGBA');n=ord(char)-0xAC00;x=n%64*8;y=n//64*8
    return [''.join('#' if (p:=sheet.getpixel((x+dx,y+dy)))[3]>0 and max(p[:3])>127 else '.' for dx in range(8)) for dy in range(8)]

class Composer:
    def __init__(self,out):
        self.out=out;self.images=out/'images';self.images.mkdir();self.figures=[]
        self.pages=json.loads((ROOT/'build/dialogue_footer_fix_003/pages.json').read_text(encoding='utf-8'))
        self.visual=json.loads((ROOT/'qa/reports/dialogue_footer_003_visual.json').read_text(encoding='utf-8'))
        self.csv=list(csv.DictReader((ROOT/'workspace/translation/dialogue_ja.csv').open(encoding='utf-8-sig',newline='')))
    def capture(self,pid):return Path(self.visual['captions'][self.pages[pid]['entry_id']]['capture'])
    def register(self,im,name,title,caption,kind,sources):
        path=self.images/name;assert not path.exists();im.save(path)
        self.figures.append({'file':'images/'+name,'title':title,'caption':caption,'kind':kind,'pixels':list(im.size),'sha256':sha(path),'sources':[{'path':Path(p).as_posix(),'sha256':sha(ROOT/p)} for p in dict.fromkeys(sources)]})
    def game(self,im,path,xy,scale=2,crop=None):
        raw=Image.open(ROOT/path).convert('RGB')
        if crop:raw=raw.crop(crop)
        im.paste(raw.resize((raw.width*scale,raw.height*scale),Image.Resampling.NEAREST),xy)
    def gallery(self,name,title,subtitle,items,caption):
        rows=math.ceil(len(items)/2);im,d=canvas(title,subtitle,170+rows*575)
        sources=[]
        for j,(label,path) in enumerate(items):
            x=48+j%2*660;y=162+j//2*575;box(d,(x,y,x+644,y+555))
            text(d,(x+25,y+15),label,29,bold=True);self.game(im,path,(x+66,y+62),2);sources.append(path)
        self.register(im,name,title,caption,'actual_capture_composition',sources)
    def make(self):
        title=Path('qa/dialogue/footer003_attract_221_001/frame_00240.png')
        oldtitle=Path('qa/title/original_20261001/frame_0240.png')
        im,d=canvas('타이니 툰 어드벤처스 한글화 작업기','8×8 픽셀의 한글부터, 당근 교환 대사의 폰트 오류까지',1240)
        self.game(im,title,(188,168),4)
        for x,large,small in [(48,'22블록','등록 대사·내레이션'),(490,'8×8px','Galmuri7 글자 칸'),(932,'v1.0.1','2026.10.04 검증 기준')]:
            box(d,(x,1140,x+420,1220));text(d,(x+20,1150),large,32,PINK,True);text(d,(x+20,1191),small,23,MUTED)
        self.register(im,'01_cover.png','작업 결과 한눈에 보기','현재 검증본의 실제 타이틀 화면. 회사명·저작권과 PUSH START는 유지했습니다.','actual_capture_composition',[title])

        im,d=canvas('전체 작업은 이렇게 이어졌습니다','글을 읽는 순서 · 로고 작업과 대사 작업은 서로 다른 자산을 다룹니다',1110)
        steps=[('01','원본 확인','원본은 보존하고, 해시로 기준 파일을 고정'),('02','로고와 대사 추출','로고는 PNG로, 대사는 제어 명령까지 CSV·토큰으로 정리'),('03','번역과 폰트 설계','번역문을 반영하고, 8×8 글자 칸과 문단별 폰트를 준비'),('04','한글 재삽입','한 문단부터 시험한 뒤, 22블록과 호출·복귀를 연결'),('05','실제 화면과 오류 확인','선택·당근·도입·엔딩 및 문단 사이 대기 구간을 검사'),('06','차분 패치 배포','원본에서 재빌드하고, 실제 Windows 적용 결과까지 비교')]
        for j,(n,label,body) in enumerate(steps):
            y=166+j*151;box(d,(48,y,1352,y+119));text(d,(76,y+30),n,38,PINK,True);text(d,(171,y+19),label,33,bold=True);text(d,(171,y+67),body,27,MUTED)
            if j<5:arrow(d,(700,y+121),(700,y+146))
        self.register(im,'02_workflow.png','작업 흐름','원본 확인부터 차분 패치 배포까지. 글자 추출·번역·실제 출력 검증을 각각 진행했습니다.','explanatory_diagram',['docs/POC_TITLE.md','docs/DIALOGUE_EXTRACTION.md','docs/HAMTON_FONT_FIX_2026-10-04.md'])

        self.gallery('03_title_before_after.png','게임명 로고를 한글로','실제 게임 캡처 · 로고 주변 캐릭터와 영문 안내는 유지', [('변경 전 로고',oldtitle),('변경 후 로고',title)],'원본 영문 게임명과 한글 로고를 비교했습니다. 한글 로고는 생성형 AI 시안을 NES용 타일과 색상 제약에 맞춰 변환한 결과입니다.')

        im,d=canvas('대사를 CSV로 정리했습니다','실제 작업 데이터 일부 · 제어 명령과 원본 바이트는 별도로 보존',810)
        cols=[48,290,705,1352];head=['화자 / 판정','일본어 원문','반영한 한국어 문구']
        box(d,(48,160,1352,735))
        for j in range(3):text(d,(cols[j]+18,176),head[j],30,PINK,True)
        for j,pid in enumerate((0,2,8)):
            y=240+j*157;d.line((48,y-15,1352,y-15),fill=LINE,width=2);r=self.csv[pid]
            paragraph(d,(cols[0]+18,y),r['speaker']+'\n자기소개·장면으로 확인',206,25)
            paragraph(d,(cols[1]+18,y),r['original_jp'].strip().replace('\n\n','\n'),370,27,jp=True)
            paragraph(d,(cols[2]+18,y),r['translation_ko'].strip().replace('\n\n','\n'),605,29)
        text(d,(48,761),'화자 메타데이터는 추출 단계의 판정이며, 공식 한국어 더빙명을 인증한 표기가 아닙니다.',25,MUTED)
        self.register(im,'04_dialogue_csv.png','대사와 화자 정리 예시','CSV의 실제 세 항목을 읽기 쉽게 재구성했습니다. 인물 대사와 내레이션, 확인된 화자와 문맥상 유력한 화자를 구분했습니다.','data_table',['workspace/translation/dialogue_ja.csv'])

        im,d=canvas('한 글자가 들어갈 자리는 8×8 픽셀','현재 대사 영역은 16열 × 7행 · 빈 줄과 공백도 칸을 차지합니다',930)
        box(d,(48,159,638,847));box(d,(661,159,1352,847))
        p=self.capture(8);self.game(im,p,(87,222),2)
        # Overlay only explains geometry. It is explicitly not a clean capture.
        x,y=87+32*2,222+32*2
        for j in range(17):d.line((x+j*16,y,x+j*16,y+112),fill='#66E0FF',width=1)
        for j in range(8):d.line((x,y+j*16,x+256,y+j*16),fill='#66E0FF',width=1)
        d.rectangle((x,y,x+256,y+112),outline='#66E0FF',width=3)
        text(d,(76,178),'실제 화면 + 설명용 격자',28,bold=True)
        paragraph(d,(78,732),'푸른 격자는 대사 칸의 위치를\n설명하려고 덧그렸습니다.',514,27,MUTED)
        text(d,(690,178),'Galmuri7의 ‘한’ 확대',28,bold=True);bitmap(im,(817,245),sheet_rows('한'),38)
        for i in range(8):text(d,(827+i*38,215),str(i+1),20,MUTED)
        paragraph(d,(702,593),'가로 8칸 × 세로 8칸\n받침까지 이 작은 칸 안에서 읽혀야 합니다.\n8×16·16×16은 같은 창에서 줄 수와 글자 수가 줄어듭니다.',608,29)
        self.register(im,'05_font_8x8.png','8×8 글자 칸과 화면 영역','왼쪽은 실제 캡처에 설명용 격자를 표시한 그림, 오른쪽은 지정 폰트의 한 글자를 격자로 확대한 그림입니다.','annotated_capture_and_font_diagram',[p,'workspace/fonts/galmuri7_8x8/Galmuri7_8x8.png','docs/FONT_SIZE_SURVEY.md'])

        im,d=canvas('문단마다 필요한 글자를 공급하는 방식','화면의 글자 번호와 폰트 그림이 같은 문단을 가리켜야 합니다',740)
        for x,pid,label in [(48,2,'세어 보는 대사'),(932,3,'당근이 부족한 대사')]:
            box(d,(x,170,x+420,656));text(d,(x+24,192),label,30,bold=True)
            page=self.pages[pid];char=next(c for c,v in page['mapping'].items() if v==0x70)
            raw=bytes.fromhex(next(g['bytes_hex'] for g in page['glyphs'] if g['char']==char));rows=[''.join('#' if (raw[y]|raw[y+8])>>(7-k)&1 else '.' for k in range(8)) for y in range(8)]
            bitmap(im,(x+74,268),rows,34);text(d,(x+25,567),'같은 번호 0x70 → ‘'+char+'’',29,PINK,True)
        box(d,(494,280,906,543),fill='#EDF3F8')
        paragraph(d,(523,317),'같은 글자 번호도\n선택한 폰트에 따라\n다른 글자가 됩니다.',355,30,bold=True)
        arrow(d,(468,399),(492,399));arrow(d,(908,399),(930,399))
        text(d,(48,690),'고정 한글 폰트 한 장에 모두 넣는 대신, 각 문단의 글자 그림 묶음을 준비했습니다.',27,MUTED)
        self.register(im,'06_page_fonts.png','같은 번호가 다른 글자로 보이는 이유','실제 페이지별 매핑에서 0x70은 세어 보는 문단의 ‘몇’, 부족 안내 문단의 ‘쉽’입니다. 대사와 폰트의 연결이 중요합니다.','explanatory_diagram',['build/dialogue_footer_fix_003/pages.json'])

        im,d=canvas('‘몇’ 한 글자도 따로 다듬었습니다','8×8 칸 유지 · 지정 폰트 PNG는 보존하고 삽입 글리프만 조정',720)
        override=json.loads((ROOT/'workspace/fonts/galmuri7_8x8/glyph_overrides_dialogue_008.json').read_text(encoding='utf-8'))
        for x,label,rows in [(48,'지정 폰트의 원래 모양',sheet_rows('몇')),(730,'삽입용으로 획을 분리한 모양',override['몇']['rows'])]:
            box(d,(x,164,x+620,609));text(d,(x+25,188),label,29,bold=True);bitmap(im,(x+145,265),rows,35)
        paragraph(d,(48,642),'작은 글자는 정상 출력 여부와 읽기 쉬운 모양을 각각 확인해야 했습니다.',1304,30,MUTED)
        self.register(im,'07_few_glyph.png','받침과 획의 가독성 조정','‘몇’에서 붙어 보이던 획을 분리했습니다. 원본 폰트 파일을 덮어쓰지 않고 해당 삽입 글리프만 조정했습니다.','font_pixel_comparison',['workspace/fonts/galmuri7_8x8/Galmuri7_8x8.png','workspace/fonts/galmuri7_8x8/glyph_overrides_dialogue_008.json'])

        source=Path('qa/dialogue/native009_scene_stage1_221_baseline_001/frame_00814.png')
        self.gallery('08_dialogue_before_after.png','원문 안내가 한국어로 바뀐 순간','셜리의 자기소개 · 현재 검증본과 일본어 대사 기준선의 실제 캡처', [('원문 대사',source),('한글 대사',self.capture(8))],'한 문단을 실제 게임에서 먼저 확인하고, 문단 전환과 선택 조작을 연결한 뒤 전체 대사로 넓혔습니다.')
        self.gallery('09_selection.png','선택 화면의 대사와 조작 안내','자기소개 → 동료 선택 → 버튼 안내 → 다음 진행',[(label,self.capture(pid)) for label,pid in [('셜리의 자기소개',8),('동료 선택 안내',9),('방향키 / A 버튼 안내',10),('작별 대사',11)]],'버튼 기호를 보존한 한글 안내입니다. 여섯 선택 장면은 원래 처리기로 진입하는 명시적 RAM 장면 스킵으로 확인했습니다.')
        self.gallery('10_hamton.png','햄튼의 당근 교환 대사','30개 교환과 부족 분기, 마지막 작별 안내를 함께 확인',[(label,self.capture(pid)) for label,pid in [('당근 30개당 추가 목숨',1),('당근 수를 세는 문구',2),('당근이 부족한 경우',3),('다시 찾아오라는 안내',4)]],'정상 30개 교환은 실제 조작 경로로, 부족 분기는 당근 카운터 한 번의 RAM 쓰기로 확인했습니다. 마지막 줄까지 표시되는 실제 캡처입니다.')

        old=Path('qa/dialogue/full_native_walk_020/frame_06540.png');new=Path('qa/dialogue/hamton_footer003_mesen221_30_001/frame_06540.png')
        im,d=canvas('배포 후 발견한 당근 교환의 글자 깨짐','동일한 세어 보기 문구가 남아 있는 대기 구간 · 실제 수정 전후 캡처',1040)
        for y,label,p in [(164,'수정 전: 다른 문단의 폰트가 먼저 적용됨',old),(586,'수정 후: 현재 문단의 폰트를 유지',new)]:
            box(d,(48,y,1352,y+398));text(d,(76,y+18),label,30,RED if p==old else GREEN,True);self.game(im,p,(284,y+86),4,(24,24,232,96))
        self.register(im,'11_bug_before_after.png','글자 깨짐 수정 전후','위는 기존 v1.0에서 재현한 오류, 아래는 v1.0.1입니다. 문구를 다시 번역한 결과가 아니라 대기 중 폰트 전환을 고친 결과입니다.','actual_capture_comparison',[old,new])

        im,d=canvas('당근 수에 따라 분기한 뒤, 같은 작별 대사로 합류','문단 사이 대기에도 직전 문구가 화면에 남아 있습니다',860)
        for y,title,body in [(205,'정상 30개 교환','세어 보기 문구 표시'),(460,'당근 부족','부족 안내 문구 표시')]:
            box(d,(48,y,464,y+170));text(d,(77,y+28),title,32,bold=True);text(d,(77,y+91),body,29,MUTED)
        box(d,(532,320,929,513),fill='#EDF3F8');text(d,(562,344),'공통 대기 구간',32,BLUE,True);paragraph(d,(562,408),'이전 문구가 화면에 남음',335,27)
        box(d,(998,320,1352,513));text(d,(1023,344),'작별 대사 출력',31,bold=True);paragraph(d,(1023,403),'당근을 더 모아\n다시 방문',302,27,MUTED)
        arrow(d,(465,290),(529,374));arrow(d,(465,539),(529,457));arrow(d,(930,415),(996,415))
        box(d,(48,668,1352,813),fill='#FCECEE');text(d,(75,688),'오류 원인',30,RED,True);text(d,(285,688),'정상 분기에서도 건너뛴 ‘부족 안내’ 폰트를 선택',28)
        text(d,(75,749),'수정 방법',30,GREEN,True);text(d,(285,749),'새 문구가 시작될 때까지 실제 직전 폰트를 유지',28)
        self.register(im,'12_branch_fix.png','대기 구간의 폰트 선택 구조','주소상 앞선 문단을 고르는 규칙이 정상 교환의 분기를 놓쳤습니다. 공통 대기에서는 실제로 표시 중인 폰트를 유지하도록 바꿨습니다.','explanatory_diagram',['docs/HAMTON_FONT_FIX_2026-10-04.md','qa/reports/dialogue_footer_003_runtime.json'])

        self.gallery('13_intro.png','도입부에도 한국어가 이어집니다','무입력 자연 도입부의 실제 게임 캡처',[(label,self.capture(pid)) for label,pid in [('사건의 시작',12),('TV에 등장한 몬태나',13),('몬태나의 대사',14),('밥스의 구조 요청',15)]],'자연 도입부의 6문단을 검증했고, 여기에는 그중 네 장면을 담았습니다. 인물 대사와 내레이션을 구분해 정리했습니다.')

        im,d=canvas('검증은 네 가지로 나눠 진행했습니다','파일이 맞는 것과, 실제 게임에서 읽히는 것은 각각 확인',1040)
        values=[('01 정적 검사','원본 해시와 변경 범위\n글자 매핑·UI 보호·호출/복귀 구조'),('02 재빌드와 패치 적용','별도 재빌드·IPS 결과 바이트 동일\nWindows 적용 8검사 + 최종 ZIP 적용'),('03 에뮬레이터 실행','Mesen 2.2.1: 등록 22블록\nMesen 2.1.1: 교환 두 분기 재확인'),('04 실제 화면 검사','본문 밖 1,491 공통 표본 비교\n대기 300캡처의 본문 픽셀 대조')]
        for j,(label,body) in enumerate(values):
            x=48+j%2*660;y=168+j//2*331;box(d,(x,y,x+644,y+305));text(d,(x+25,y+24),label,34,PINK,True);paragraph(d,(x+25,y+105),body,590,29)
        box(d,(48,858,1352,1000),fill='#EAEFF3');paragraph(d,(74,883),'범위: 선택·엔딩은 명시적 RAM 장면 스킵으로 원래 처리기를 실행했습니다.\n전체 완주·실기 테스트와 번역문/화자의 최종 검토는 아직 수행하지 않았습니다.',1250,28)
        self.register(im,'14_validation.png','검증 결과와 범위','정적 검사, 재빌드·실제 적용, 에뮬레이터 실행, 직접 시각 검토를 나눴습니다. 대기 구간도 별도 회귀 검사에 포함했습니다.','verification_summary',['qa/reports/dialogue_footer_003_static.json','qa/reports/dialogue_footer_003_runtime.json','qa/reports/dialogue_footer_003_abi.json','qa/reports/release_TinyToonAdventures_KR_Patch_v1.0.1_20261004_final.json'])

        im,d=canvas('배포는 xdelta 차분 패치로','기존 배포와 동일한 11파일 구성 · 원본 ROM은 동봉하지 않습니다',860)
        nodes=[(48,'일본판 원본 ROM','사용자가 준비'),(532,'v1.0.1 차분 패치','apply.cmd로 적용'),(998,'새 한글 ROM','원본과 별도 파일')]
        for x,label,body in nodes:box(d,(x,169,x+354,330));text(d,(x+22,196),label,29,bold=True);text(d,(x+22,264),body,27,MUTED)
        arrow(d,(403,249),(530,249));arrow(d,(887,249),(996,249))
        box(d,(48,387,1352,762))
        text(d,(78,410),'배포 폴더 안의 파일',33,PINK,True)
        paragraph(d,(80,485),'xdelta 패치\napply.cmd / apply.ps1\n적용 설명서 / 릴리즈 글\nSHA256.txt / release_report.json',592,28)
        paragraph(d,(744,485),'tools/\n  xdelta3 실행 파일·설명·라이선스\nlicenses/\n  Galmuri 폰트 라이선스',565,28)
        text(d,(48,798),'원본에 새로 적용 → 새 이름의 ROM으로 시작 → 이전 대화 저장 상태는 사용하지 않기',27,MUTED)
        self.register(im,'15_patch_package.png','차분 패치 적용과 배포 구성','원본과 새 한글 ROM을 구분하고, 실제 Windows 적용 검사와 ZIP 추출본 적용도 확인했습니다.','explanatory_diagram',['dist/TinyToonAdventures_KR_Patch_v1.0.1_20261004/release_report.json'])
        self.gallery('16_ending_spoiler.png','엔딩 대사 확인 — 결말 스포일러','실제 엔딩 처리기로 진입한 캡처 · 최종 보스 승리 플레이를 뜻하지 않습니다',[(label,self.capture(pid)) for label,pid in [('결말의 시작',18),('구조 이후',19),('일상으로 돌아온 일행',20),('마지막 문구',21)]],'원래 엔딩 처리기를 명시적 RAM 스킵으로 실행했습니다. 완주 증거와 구분하며, 마지막 대사까지의 화면 출력 확인에 사용했습니다.')

TITLE='8×8 픽셀 안에 한글을 넣기 — 타이니 툰 어드벤처스 한글화 작업기'
BLOCKS=[
 ('p','NES용 「타이니 툰 어드벤처스」의 일본어 대사를 한국어로 바꾸는 작업을 정리해 봤습니다. 타이틀 로고부터 시작해 대사 추출, 작은 한글 폰트, 실제 게임 출력, 배포 후 발견한 오류 수정까지 이어진 기록입니다.'),
 ('fig',1),
 ('p','현재 기준은 2026년 10월 4일의 v1.0.1입니다. 조사한 대사 처리 경로의 22개 대사·내레이션 블록을 삽입하고 화면 출력을 확인했습니다. 영문 UI와 스태프롤은 그대로 두었습니다. 전체 완주나 최종 번역 검수까지 끝낸 상태는 아니라는 점은 글 뒤의 검증 범위에 따로 적었습니다.'),
 ('fig',2),
 ('h','1. 먼저 타이틀 로고를 바꿨습니다'),
 ('p','처음 손댄 곳은 게임명 로고였습니다. 원본 로고를 PNG로 추출하고, 그 이미지를 참조해 생성형 AI로 한글 시안을 만들었습니다. 다만 PNG가 보기 좋다고 바로 게임에 들어가는 것은 아니었습니다.'),
 ('fig',3),
 ('p','NES 화면에 넣으려면 작은 그림 조각인 ‘타일’로 나누고, 사용할 수 있는 색과 타일 수에 맞춰야 했습니다. 최종 로고는 176×88 픽셀, 4색 조건으로 변환했습니다. 로고 주변 캐릭터와 TM, 회사명·저작권, PUSH START 안내를 함께 확인하며 게임 화면에 다시 넣었습니다.'),
 ('h','2. 대사는 글자뿐 아니라 명령도 함께 추출했습니다'),
 ('p','다음은 일본어 대사였습니다. 게임 안의 데이터에는 문장 사이에 줄바꿈, 잠시 기다리기, 화면 지우기, 다른 대사 호출하기 같은 명령이 섞여 있었습니다. 보이는 글자만 뽑으면 다시 넣을 때 흐름이 달라질 수 있어, 원본 바이트와 제어 명령을 함께 보관했습니다.'),
 ('fig',4),
 ('p','확인한 경로에는 대사 시작 주소를 담는 26개 슬롯이 있었고, 중복과 공통 호출을 따라가니 고유 대사·내레이션은 22블록이었습니다. 이를 CSV로 정리해 제출받은 한국어 문구를 반영했습니다. 화자와 상대, 장면, 판정 근거도 별도 칸으로 두었습니다.'),
 ('p','햄튼과 셜리는 자기소개와 장면으로 확인할 수 있었습니다. 다른 인물은 대사의 맥락으로 유력한 경우와 내레이션을 구분했습니다. 캐릭터가 언급됐다는 이유만으로 그 인물을 화자로 확정하지는 않았고, 원작 설정과 게임 안 역할도 참고했습니다. 이 이름 표기는 공식 한국어 더빙명을 인증한 것이 아닙니다.'),
 ('h','3. 한글은 8×8 픽셀 안에서 읽혀야 했습니다'),
 ('p','대사 한 글자에 주어진 칸은 8×8 픽셀이었습니다. 본문 영역은 16열 × 7행이었고, 공백과 빈 줄도 이 공간을 차지했습니다. 글자를 크게 만들면 더 읽기 쉬울 수 있지만, 같은 창에서 표시할 수 있는 글자와 줄 수가 줄어들어 출력 구조를 더 바꿔야 했습니다.'),
 ('fig',5),
 ('p','이번에는 지정한 Galmuri7의 8×8 비트맵을 사용했습니다. 또 하나의 문제는 글자 종류였습니다. 번역문에 필요한 한글은 156종인데, 기존 문자 자리를 모두 마음대로 바꿀 수는 없었습니다. 버튼 안내나 주변 그림까지 망가뜨리지 않으려면 폰트 공급 방식이 필요했습니다.'),
 ('fig',6),
 ('p','선택한 방법은 문단마다 필요한 글자 그림 묶음을 만들고, 그 문단이 표시될 때 해당 폰트를 선택하는 것이었습니다. 덕분에 같은 글자 번호를 다른 문단에서는 다른 한글에 쓸 수 있었습니다. 대신 “지금 화면의 대사”와 “지금 선택된 폰트”가 항상 맞아야 한다는 조건이 생겼습니다. 이 조건이 뒤의 오류와도 연결됩니다.'),
 ('fig',7),
 ('p','작은 폰트는 정상적으로 표시돼도 읽기 어려운 글자가 남았습니다. 특히 ‘몇’은 획이 붙어 보인다는 피드백이 있어, 8×8 칸을 유지하면서 삽입용 글리프의 획을 분리했습니다. 원본 폰트 PNG를 덮어쓰지는 않았습니다.'),
 ('h','4. 한 문단을 먼저 확인하고, 전체 대사로 넓혔습니다'),
 ('p','처음부터 모든 대사를 한 번에 넣기보다는 셜리의 자기소개 한 문단으로 한국어 출력부터 확인했습니다. 그다음 문단 전환, 동료 선택, 방향키와 A 버튼 안내, 대사 종료 후 진행을 연결했습니다.'),
 ('fig',8),
 ('fig',9),
 ('p','전체 삽입 단계에서는 제출된 문구를 유지하면서 16열 안에 들어가도록 줄을 배치했습니다. 타이핑에 걸리는 시간과 대기 명령, 공통 대사의 호출·복귀도 확인했습니다. 대사를 읽는 코드와 폰트 선택을 연결하고, 원본에서 같은 결과를 다시 만들 수 있게 빌드 절차를 남겼습니다.'),
 ('fig',10),
 ('h','5. 배포 후, 당근 교환 대사에서 뜻밖의 오류가 나왔습니다'),
 ('p','초기 배포 뒤에 당근 교환 화면의 마지막 줄, 띄어쓰기와 글자 가독성에 대한 피드백이 왔습니다. 특히 정상 문구와 실제 실행 화면의 글자가 다르게 보이는 사진이 중요한 단서였습니다. 기존 패치 ROM에서 같은 상태를 다시 확인하니, 당근 30개를 교환한 뒤 문단 사이에서 기다리는 구간에 문제가 있었습니다.'),
 ('fig',11),
 ('p','화면에는 “그럼 몇 개인지 / 세어 볼게”의 글자 번호가 그대로 남아 있었습니다. 그런데 폰트는 다음 주소에 있는, 실제로는 건너뛴 당근 부족 안내의 것으로 바뀌어 있었습니다. 그래서 같은 글자 번호가 “.아 쉽 지만당 / 근이 조금”처럼 읽혔습니다.'),
 ('fig',12),
 ('p','정상 교환과 당근 부족은 서로 다른 문구를 표시한 뒤 공통 작별 대사로 합류합니다. 그 앞의 대기 구간에서 주소만 보고 앞선 문단의 폰트를 고른 규칙이 정상 교환 분기를 놓친 것이었습니다. 수정본은 새 문구가 시작될 때까지 실제로 직전에 표시한 폰트를 유지하도록 바꿨습니다.'),
 ('p','이전 검사는 완성된 문단의 대표 화면을 확인했지만, 그 사이의 대기를 놓쳤습니다. 이후에는 두 분기의 대기 구간을 연속 프레임으로 모아 글자 번호와 실제 잉크·빈 픽셀까지 비교하는 검사를 추가했습니다. 이번 작업에서 가장 크게 남은 것은 “문단이 잘 보이는 순간뿐 아니라, 문단과 문단 사이도 확인해야 한다”는 점이었습니다.'),
 ('h','6. 도입·선택·교환·엔딩을 나눠 확인했습니다'),
 ('fig',13),
 ('p','도입부는 입력 없이 자연스럽게 재생되는 경로로 확인했습니다. 당근 30개 교환은 실제 조작 경로로, 부족 안내는 카운터 한 번의 RAM 쓰기로 분기를 만들어 확인했습니다. 여섯 선택 화면과 엔딩은 명시적인 RAM 장면 스킵으로 원래 게임 처리기를 실행했습니다. 장면 출력 검증과 전체 완주를 구분하기 위한 기록도 함께 남겼습니다.'),
 ('fig',14),
 ('p','파일 구조와 폰트 매핑을 확인하는 정적 검사, 별도 재빌드와 실제 패치 적용, 에뮬레이터 실행, 화면의 직접 시각 검토를 나눴습니다. Mesen 2.2.1과 2.1.1에서 교환의 두 분기를 확인했고, 22블록의 완전 출력과 문단 전환을 검사했습니다. 원문 기준선과 비교한 1,491개 공통 화면에서는 본문 밖 픽셀 차이가 없었고, 두 버전에서 모은 대기 구간 300캡처의 본문도 따로 대조했습니다.'),
 ('p','확인한 것은 이 등록 대사 경로와 명시한 장면들입니다. 전체 완주와 실기 테스트, 번역 문구·화자의 최종 검토는 아직 수행하지 않았습니다. CSV의 22개 항목도 검토가 필요한 상태로 유지하고 있습니다.'),
 ('h','7. 배포는 원본 없는 차분 패치로 묶었습니다'),
 ('fig',15),
 ('p','최신 묶음은 v1.0.1 xdelta 패치입니다. 기존 배포와 같은 구성으로 패치, apply.cmd / apply.ps1, 적용 설명서, 릴리즈 글, 체크섬, 검증 보고서와 도구·폰트 라이선스를 넣었습니다. 게임 ROM은 동봉하지 않습니다.'),
 ('p','적용 도구는 일본판 원본에 패치를 적용해 별도의 새 한글 ROM을 만듭니다. 한글과 공백이 있는 Windows 경로에서 실제로 적용해 결과를 비교했고, 기존 출력 덮어쓰기나 잘못된 원본을 거부하는 검사도 했습니다. 마지막으로 배포 ZIP을 다시 풀어 그 안의 도구로 적용한 결과까지 확인했습니다.'),
 ('p','사용할 때는 원본에 새로 적용한 ROM을 처음부터 실행해 주세요. 오류가 발생했던 대화 도중의 예전 저장 상태는 화면과 폰트 상태를 다시 가져올 수 있어, 수정 확인에는 사용하지 않는 편이 좋습니다.'),
 ('p','작은 글자 안에 받침을 넣는 일부터 문단 사이의 폰트 상태를 따라가는 일까지, 눈에 보이는 문장 뒤에 생각보다 많은 연결이 있었습니다. 여기까지의 결과와 시행착오를 공유합니다. 플레이 중 이상한 문구나 화면을 발견하면 패치 버전, 에뮬레이터, 발생 장면과 캡처를 함께 알려주시면 확인에 도움이 됩니다.'),
 ('note','사용 폰트: Galmuri7 / Lee Minseo / SIL Open Font License 1.1. 적용 도구: xdelta3 / Apache License 2.0. 타이틀 시안에는 생성형 AI를 사용했으며, 게시글의 게임 화면은 실제 에뮬레이터 캡처입니다. 게임과 캐릭터의 권리는 각 권리자에게 있습니다.'),
 ('spoiler','엔딩 화면 더 보기 — 결말 스포일러'),
 ('p','아래는 출력 확인에 사용한 엔딩 네 장면입니다. 원래 엔딩 처리기로 진입한 캡처이며, 최종 보스 승리나 전체 완주 기록은 아닙니다.'),
 ('fig',16),
]

def write_text(out,figures):
    parts=[TITLE,'작업 기록: 2026.10.01–10.04 / 기준 패치: v1.0.1','']
    for kind,value in BLOCKS:
        if kind=='fig':
            f=figures[value-1];parts.append(f'[이미지 {value:02d}: {Path(f["file"]).name}]\n{f["caption"]}')
        elif kind=='h':parts.append('\n'+value+'\n'+'─'*26)
        elif kind=='spoiler':parts.append('\n[스포일러 주의] '+value)
        else:parts.append(value)
    (out/'네이버카페_게시글본문.txt').write_text('\n\n'.join(parts)+'\n',encoding='utf-8-sig')

def write_html(out,figures):
    esc=html.escape;body=[];spoiler=False
    for kind,value in BLOCKS:
        if kind=='fig':
            f=figures[value-1];data=base64.b64encode((out/f['file']).read_bytes()).decode();alt=esc(f['title']);body.append(f'<figure><button class="zoom" aria-label="{alt} 크게 보기"><img src="data:image/png;base64,{data}" width="{f["pixels"][0]}" height="{f["pixels"][1]}" alt="{alt}"></button><figcaption><b>그림 {value:02d}</b> {esc(f["caption"])}</figcaption></figure>')
        elif kind=='h':body.append('<h2>'+esc(value)+'</h2>')
        elif kind=='spoiler':body.append('<details class="spoiler"><summary>'+esc(value)+'</summary>');spoiler=True
        elif kind=='note':body.append('<aside>'+esc(value)+'</aside>')
        else:body.append('<p>'+esc(value)+'</p>')
    if spoiler:body.append('</details>')
    css='''*{box-sizing:border-box}html{color:#242936;background:#f4f1eb;font-family:"Malgun Gothic",system-ui,sans-serif}body{margin:0}header,main,footer{max-width:1040px;margin:auto}header{padding:65px 45px 28px}.eyebrow{word-break:keep-all;color:#a52d65;font-weight:700;letter-spacing:.1em;font-size:14px}h1{font-size:42px;line-height:1.4;word-break:keep-all;overflow-wrap:break-word;letter-spacing:-.045em;margin:18px 0}header .meta{color:#68717d;font-size:15px}.bar{height:7px;background:linear-gradient(90deg,#bd326f,#6b62ba,#276397)}main{background:white;padding:16px 45px 50px;border-radius:22px;box-shadow:0 4px 30px #22222208}p{font-size:19px;line-height:1.95;word-break:keep-all;overflow-wrap:break-word;margin:26px 0}h2{margin:65px 0 24px;font-size:28px;line-height:1.5;letter-spacing:-.035em;border-left:5px solid #bd326f;padding-left:17px}figure{margin:30px 0 38px}figure img{width:100%;height:auto;display:block;border-radius:12px}.zoom{display:block;width:100%;padding:0;border:0;background:transparent;cursor:zoom-in}.zoom:focus-visible{outline:3px solid #276397;outline-offset:5px}figcaption{font-size:15px;line-height:1.8;color:#58616f;margin-top:11px}figcaption b{color:#a52d65;margin-right:5px}aside{font-size:14px;line-height:1.9;background:#f2f5f7;padding:20px 24px;border-radius:12px;margin:40px 0}.spoiler{border:1px solid #d8dde2;border-radius:14px;padding:19px 25px;margin-top:35px}.spoiler summary{cursor:pointer;font-size:18px;font-weight:700;color:#7c3659}footer{padding:30px 45px 45px;font-size:13px;line-height:1.8;color:#66707c}dialog{width:96vw;height:94vh;max-width:none;max-height:none;padding:0;border:0;border-radius:12px;background:#202735;overflow:auto}dialog::backdrop{background:#101827dc}dialog .close{position:sticky;top:12px;left:12px;background:white;border:0;border-radius:9px;padding:12px 20px;font-weight:700;z-index:1;cursor:pointer}dialog img{display:block;width:auto;max-width:none;height:auto;margin:20px auto 40px}.hint{font-size:13px;color:#68717d}@media(max-width:600px){header{padding:35px 22px 18px}h1{font-size:30px}main{padding:10px 20px 30px;border-radius:0}p{font-size:17px;line-height:1.9}h2{font-size:24px;margin-top:45px}figure{margin:24px -8px 30px}figcaption{padding:0 8px;font-size:13px}.spoiler{padding:15px}footer{padding:25px 22px}}@media print{html{background:white}main{box-shadow:none}header,main{max-width:none;padding-left:0;padding-right:0}.hint{display:none}h2{break-after:avoid}figure{break-inside:avoid}dialog{display:none}}'''
    script='''const modal=document.querySelector("dialog"),large=modal.querySelector("img");document.querySelectorAll(".zoom").forEach(button=>button.addEventListener("click",()=>{large.src=button.querySelector("img").src;large.alt=button.querySelector("img").alt;modal.showModal();modal.scrollTo(0,0);}));modal.querySelector(".close").addEventListener("click",()=>modal.close());modal.addEventListener("click",e=>{if(e.target===modal)modal.close();});'''
    page='<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(TITLE)+'</title><style>'+css+'</style><body><div class="bar"></div><header><div class="eyebrow">TINY TOON ADVENTURES · 한글화 작업 기록</div><h1>'+esc(TITLE)+'</h1><div class="meta">2026.10.01–10.04 · v1.0.1 기준 · 실제 게임 캡처와 설명용 구조도</div><p class="hint">이미지를 누르면 원래 크기로 확대할 수 있습니다. 엔딩 화면은 글 끝의 접힌 항목에 있습니다.</p></header><main>'+''.join(body)+'</main><footer>이 파일은 이미지를 내장한 읽기용 완성본입니다. 게시판에 옮길 때는 동봉한 네이버카페_게시글본문.txt와 images/의 번호순 PNG를 사용하세요. 패치 게시 위치는 게시할 때 추가해 주세요.</footer><dialog aria-label="이미지 확대"><button class="close">닫기 / Esc</button><img alt=""></dialog><script>'+script+'</script></body></html>'
    (out/'작업기.html').write_text(page,encoding='utf-8')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();out=a.output.resolve();out.relative_to(ROOT/'workspace/publication');out.mkdir(parents=True,exist_ok=False)
    for name in ('static','runtime','abi','visual'):
        r=json.loads((ROOT/f'qa/reports/dialogue_footer_003_{name}.json').read_text(encoding='utf-8'));assert r['status']=='PASS' and r.get('rom_sha256',r.get('output_sha256'))=='d57b816fce99d99eb700ebecc3d2397a1d039418ead3b1233d720c712fb2df3d'
    runtime=json.loads((ROOT/'qa/reports/dialogue_footer_003_runtime.json').read_text(encoding='utf-8'));assert sum(len(r['frames']) for r in runtime['held_regressions'])==300
    c=Composer(out);c.make();write_text(out,c.figures);write_html(out,c.figures)
    guide='''네이버 카페에 올리는 순서

1. 작업기.html을 브라우저에서 열어 완성된 글을 먼저 읽습니다.
   HTML은 이미지를 내장했으므로 이 파일만 따로 옮겨도 읽을 수 있습니다.
   그림을 누르면 확대되고, 엔딩은 접힌 항목에 있습니다.
2. 네이버카페_게시글본문.txt의 첫 줄을 게시글 제목으로 사용하고,
   그 아래 날짜/기준 버전부터 본문을 카페 글쓰기 편집기에 붙여 넣습니다.
3. [이미지 NN: 파일명] 위치마다 images/의 같은 번호 PNG를 업로드합니다.
   업로드 후 표시용 [이미지 ...] 줄은 지우고 아래 설명은 남깁니다.
4. 16_ending_spoiler.png는 결말을 포함합니다. HTML 완성본에서는 접혀 있습니다.
   카페에 옮길 때는 마지막의 스포일러 경고 뒤에 배치하거나 생략합니다.
5. 패치 게시 주소·제작자 이름·게시 날짜는 게시할 때 추가하세요.
   현재 로컬 패치 파일: TinyToonAdventures_KR_Patch_v1.0.1_20261004.zip

글과 그림은 v1.0.1의 기록을 기준으로 작성했습니다. 기존 타이틀과 원문·오류
캡처는 비교 자료로 구분했습니다. 설명용 격자/구조도는 실제 캡처와 표시를
구분했으며 게임 화면의 글자를 새로 그려 넣지 않았습니다.
HTML은 읽기용이며 카페 편집기에 HTML 코드를 붙여 넣는 용도가 아닙니다.
이미지는 설명 글씨가 작아지지 않도록 본문에서 충분히 크게 배치하세요.
게임 ROM·전체 폰트 파일·메모리 덤프·에뮬레이터는 이 묶음에 없습니다.
패치 ZIP은 기존 파일 그대로이며, 이 작업기 묶음에는 별도로 넣지 않았습니다.
'''
    (out/'업로드안내.txt').write_text(guide,encoding='utf-8-sig')
    manifest={'status':'COMPOSED_REVIEW_PENDING','title':TITLE,'build_sha256':'d57b816fce99d99eb700ebecc3d2397a1d039418ead3b1233d720c712fb2df3d','figures':c.figures,'figure_count':len(c.figures),'evidence':[{'path':p,'sha256':sha(ROOT/p)} for p in ['docs/POC_TITLE.md','docs/DIALOGUE_EXTRACTION.md','docs/FONT_SIZE_SURVEY.md','docs/HAMTON_FONT_FIX_2026-10-04.md','qa/reports/dialogue_footer_003_runtime.json','qa/reports/dialogue_footer_003_visual.json','workspace/translation/dialogue_ja.csv']],'public_files':{p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file()},'scope':'Public worklog composition only; no ROM rebuild, translation change, emulator re-run or external posting.'}
    report=ROOT/'qa/reports'/(out.name+'_publication.json');assert not report.exists();report.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output':out.relative_to(ROOT).as_posix(),'figures':len(c.figures),'files':len(manifest['public_files']),'report':report.relative_to(ROOT).as_posix()}))
if __name__=='__main__':main()
