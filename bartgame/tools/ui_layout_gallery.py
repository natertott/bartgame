#!/usr/bin/env python3
"""Compose skin and layout comparisons from unchanged native mGBA frames.

No source game art is painted here. Captions are outside240x160 screenshots;
all enlargements use integer nearest-neighbour. These boards compare five
skins with the legacy layout, then ten layouts with one fixed skin.
"""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
BG='#101820';FG='#e8c878';FONT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
SHA=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def label(draw,xy,s):draw.fontmode='1';draw.text(xy,s,font=FONT,fill=FG)
def save(im,p):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True)
def title(build):return build.get('name') or build.get('label') or f"UI{build['ui']} / menu{build.get('menu',0)}"

def board(work,rows,screen,columns=5):
    height=((len(rows)+columns-1)//columns)*186;im=Image.new('RGB',(columns*240,height),BG);d=ImageDraw.Draw(im)
    for i,b in enumerate(rows):
        x=(i%columns)*240;y=(i//columns)*186;path=work/f"captures/v{b['variant']}/{screen}.png"
        native=Image.open(path).convert('RGB');assert native.size==(240,160)
        label(d,(x+5,y+5),f"{i+1}. {title(b)}");im.paste(native,(x,y+24))
    return im

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True);builds=json.loads((a.work/'builds.json').read_text())
    skins=[b for b in builds if 6<=b['ui']<=10 and not b.get('menu',0)]
    layouts=sorted([b for b in builds if b.get('menu',0)],key=lambda b:b['menu'])
    assert len(skins)==5 and len(layouts)==10
    files=[]
    skin_screens=('hud-sewer-max','hud-ammo-99','hud-healthy','hud-blighted','hud-cave','menu-items','menu-key-items','menu-map','menu-map-zoom','shop','dialogue-wizard','reward-chest','title-continue','victory')
    skin_boards={}
    for screen in skin_screens:
        im=board(a.work,skins,screen);path=a.out/'skins'/f'{screen}.png';save(im,path);skin_boards[screen]=im;files.append(str(path.relative_to(a.out)))
    overview=Image.new('RGB',(1200,186*5),BG)
    for row,screen in enumerate(('hud-sewer-max','menu-items','menu-key-items','shop','dialogue-wizard')):overview.paste(skin_boards[screen],(0,row*186))
    save(overview,a.out/'five-skin-overview.png')
    layout_screens=('layout-items','layout-seeds','layout-bow','layout-assigned','layout-key-items','layout-map','layout-zoom-map','layout-focus-return','layout-empty-items','layout-empty-key-items','layout-fog-map','layout-fog-zoom','layout-hud-return')
    for screen in layout_screens:
        im=board(a.work,layouts,screen);path=a.out/'layouts'/f'{screen}.png';save(im,path);files.append(str(path.relative_to(a.out)))
    for i,b in enumerate(layouts,1):
        im=Image.new('RGB',(480,2*186),BG);d=ImageDraw.Draw(im)
        for j,screen in enumerate(('layout-items','layout-key-items','layout-map','layout-zoom-map')):
            x=(j%2)*240;y=(j//2)*186;native=Image.open(a.work/f"captures/v{b['variant']}/{screen}.png").convert('RGB')
            label(d,(x+5,y+5),f'{i}. '+screen.replace('layout-',''));im.paste(native,(x,y+24))
        save(im,a.out/'layouts'/f'layout-{i:02}-four-pages.png')
        save(im.resize((960,744),Image.Resampling.NEAREST),a.out/'layouts'/f'layout-{i:02}-four-pages-2x.png')
    catalogue={'method':__doc__,'skins':skins,'layouts':layouts,'skin_screens':list(skin_screens),'layout_screens':list(layout_screens),'source_commit':builds[0]['source_commit']}
    (a.out/'catalogue.json').write_text(json.dumps(catalogue,indent=2)+'\n')
    manifest={str(q.relative_to(a.out)):SHA(q) for q in sorted(a.out.rglob('*')) if q.is_file() and q.name!='gallery-manifest.json'}
    (a.out/'gallery-manifest.json').write_text(json.dumps({'method':'Actual native game pixels preserved; caption-only composition.','files':manifest},indent=2)+'\n')
    print(json.dumps({'files':len(manifest),'skins':len(skins),'layouts':len(layouts)},indent=2))
if __name__=='__main__':main()
