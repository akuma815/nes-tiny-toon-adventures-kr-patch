import argparse,json
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw
from extract_title import mask_cell
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--original',type=Path,required=True);ap.add_argument('--patched',type=Path,required=True);args=ap.parse_args()
    images=sorted(args.original.glob('frame_*.png'));sheet=Image.new('RGB',(512,len(images)*260),'#303030');draw=ImageDraw.Draw(sheet);rows=[]
    for i,p in enumerate(images):
        a=Image.open(p).convert('RGB');b=Image.open(args.patched/p.name).convert('RGB');diff=ImageChops.difference(a,b)
        outside=sum(a.getpixel((x,y))!=b.getpixel((x,y)) for y in range(240) for x in range(256) if not mask_cell(x//8,y//8))
        rows.append({'frame':int(p.stem.split('_')[1]),'diff_bbox':diff.getbbox(),'outside_logo_different_pixels':outside})
        draw.text((4,i*260),p.name+' original / patched',fill='white');sheet.paste(a,(0,i*260+20));sheet.paste(b,(256,i*260+20))
    sheet.save(args.patched/'comparison_contact.png');(args.patched/'comparison.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
