"""Build native final-Drain source sheets and five-way actual UI comparisons.

The room/source atlases are indexed asset assemblies, not screenshots. Actual
UI boards only paste unmodified mGBA240x160 frames; labels remain outside them.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps
from bloom_suite_gallery import write_gif

ROOT=Path(__file__).resolve().parents[1]
FONT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
TITLE=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
BG='#101820';FG='#e8e0c0';GOLD='#e8c878'
FIXTURES=(
 ('floor','Brick, inset paving and debris',(48,208,208,268)),
 ('north-wall','North retaining masonry and large leaking pipe',(8,8,128,64)),
 ('ladder','Taller forest ladder, consistent arch and arrow above',(120,0,184,88)),
 ('cistern','Split-water cistern and consistent arch lighting',(184,8,296,112)),
 ('market','Final frog market',(8,48,136,120)),
 ('wizard','Selected worn wizard corner',(280,40,392,120)),
 ('bridge','River crossing',(208,128,272,224)),
 ('rail','Upper railing',(80,120,208,176)),
 ('left-outlet','Left-edge profile outlet and discharge',(0,136,88,200)),
 ('storage','Crates and barrel',(392,48,472,112)),
 ('grate','Floor drain',(192,216,288,264)),
 ('lower-bank','Lower rail and water bank',(64,248,192,320)),
 ('left-wall','Side-facing left wall',(0,64,48,272)),
 ('right-wall','Side-facing right wall',(432,64,480,272)),
)
SCREENS=('hud-sewer-max','hud-healthy','hud-blighted','hud-cave','hud-empty-low',
 'hud-ammo-0','hud-ammo-9','hud-ammo-99','hud-ammo-255','hud-non-ammo-equipment',
 'menu-items','menu-equipped','menu-key-items','menu-map','menu-map-zoom',
 'shop','shop-selected','shop-purchase-response','dialogue-wizard',
 'shop-unaffordable','dialogue-wizard-page2','reward-chest','death-return',
 'title-start','title-continue','title-new-game-selected','victory')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def label(draw,xy,text,font=FONT,fill=FG):
    draw.fontmode='1';draw.text(xy,text,font=font,fill=fill)


def save(im,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    im.convert('RGB').save(path,optimize=True)


def source_room(tick=0):
    import sewer_final as S
    import sewer_final_contracts as C
    import reboot_core as R
    import reboot_actors as A
    import sewer_concepts_npcs as N
    image=Image.new('RGBA',(480,320),BG);palette=S.palette()
    for layer in ('ground','overlay'):
        if layer=='overlay':
            R.paste(image,N.peddler_body(1,'rest'),(56,62),N.peddler_palette(1))
            R.paste(image,N.peddler_head(1,'open'),(64,68),N.peddler_palette(1))
            R.paste(image,N.wizard(1,'idle'),(328,62),N.wizard_palette(1))
            R.paste(image,N.flame(1,'w0'),(351,63),N.wizard_palette(1))
            R.paste(image,A.hero_frame('idle_s'),(184,238),R.PALETTES['hero'])
        for row in C.ROOM[layer]:
            for name in row:
                if not name:continue
                _,x,y=C.parse_name(name);frames,speed=S.frame_spec(layer,x,y)
                phase=(tick//max(1,speed))%frames
                R.paste(image,S.paint(name,phase),(x*16,y*16),palette)
    rail=S.rail_sprite()
    for x in list(range(16,224,16))+list(range(256,464,16)):
        R.paste(image,rail,(x,136),R.PALETTES['gold'])
    return image.convert('RGB')


def source_gallery(out):
    import sewer_final as S
    import sewer_final_contracts as C
    import reboot_core as R
    out.mkdir(parents=True,exist_ok=True)
    room=source_room()
    save(room,out/'final-room-native.png');save(room.resize((960,640),Image.Resampling.NEAREST),out/'final-room-2x.png')
    save(ImageOps.grayscale(room).convert('RGB'),out/'final-room-values.png')
    for slug,title,box in FIXTURES:
        crop=room.crop(box);board=Image.new('RGB',(max(crop.width*3,420),crop.height*3+42),BG)
        label(ImageDraw.Draw(board),(8,8),title+' / source assets at3x',TITLE,GOLD)
        board.paste(crop.resize((crop.width*3,crop.height*3),Image.Resampling.NEAREST),(0,42))
        save(board,out/'fixtures'/f'{slug}.png')
    records=[];animation_paths=[];drawing_count=0
    for start in range(0,len(C.CLONES),100):
        rows=C.CLONES[start:start+100];board=Image.new('RGB',(800,52+10*54),BG);draw=ImageDraw.Draw(board)
        label(draw,(8,8),'FINAL DRAIN PLACEMENT TILES / native16px enlarged2x',TITLE,GOLD)
        for index,row in enumerate(rows):
            name=row['name'];layer,x,y=row['layer'],row['x'],row['y'];frames,speed=S.frame_spec(layer,x,y)
            hashes=[]
            for phase in range(frames):
                im=S.paint(name,phase)
                assert im.mode=='P' and im.size==(16,16) and set(im.tobytes())<=set(range(16))
                hashes.append(hashlib.sha256(im.tobytes()).hexdigest());drawing_count+=1
            px=(index%10)*80;py=52+(index//10)*54
            im=R.rgba(S.paint(name),S.palette()).resize((32,32),Image.Resampling.NEAREST)
            board.paste(im,(px+4,py),im)
            label(draw,(px+3,py+34),f'{layer[0]}{x:02},{y:02}')
            record={**row,'frames':frames,'anim_speed':speed,'indexed_frame_sha256':hashes,
                    'atlas':f'tiles/placements-{start//100+1:02}.png'}
            records.append(record)
            if frames>1:
                film=Image.new('RGBA',(max(420,frames*36),86),BG);fd=ImageDraw.Draw(film)
                label(fd,(8,5),name+f' / {frames} frames, hold{speed}',FONT,GOLD)
                for phase in range(frames):
                    R.paste(film,S.paint(name,phase).resize((32,32),Image.Resampling.NEAREST),(phase*36,30),S.palette())
                    label(fd,(phase*36+3,65),str(phase))
                filename=f'animation-frames/{name}.png';save(film,out/filename);animation_paths.append(filename)
        save(board,out/f'tiles/placements-{start//100+1:02}.png')
    # Correct per-cell source clocks, with captions outside the source pixels.
    motion=[]
    for tick in range(0,128,4):
        room=source_room(tick);parts=[room.crop(box) for slug,_,box in FIXTURES if slug in ('north-wall','cistern','left-outlet')]
        board=Image.new('RGB',(480,150),BG);draw=ImageDraw.Draw(board)
        label(draw,(8,5),'NATIVE SOURCE WATER STUDY / not emulator output',FONT,GOLD)
        x=0
        for part in parts:board.paste(part,(x,34));x+=part.width+12
        motion.append(board)
    durations=[round((tick+4)/(16777216/280896)*100)*10-round(tick/(16777216/280896)*100)*10 for tick in range(0,128,4)]
    gif=write_gif(motion,durations,out/'source-water-motion.gif')
    report={'method':'Native indexed source assets, not emulator screenshots. Source world map uses final clone placements and per-cell animation clocks.',
            'room_size':[480,320],'placement_ids':len(records),'frame_drawings':drawing_count,
            'palette':S.palette(),'records':records,'animation_filmstrips':animation_paths,'water_gif':gif,
            'physical_contract':'Original per-cell collision/type/prop/glitter are copied by integration; this source gallery is not the independent physical audit.'}
    (out/'catalogue.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def actual_boards(work,out,names):
    rows=[]
    for screen in SCREENS:
        paths=[work/f'captures/v{n}/{screen}.png' for n in range(1,6)]
        if not all(p.exists() for p in paths):continue
        board=Image.new('RGB',(1200,190),BG);draw=ImageDraw.Draw(board)
        for n,path in enumerate(paths,1):
            im=Image.open(path).convert('RGB');assert im.size==(240,160)
            label(draw,((n-1)*240+6,5),f'{n}. {names[n]}',FONT,GOLD)
            board.paste(im,((n-1)*240,30))
        save(board,out/'comparisons'/f'{screen}.png');rows.append(screen)
    key=('hud-sewer-max','menu-items','menu-key-items','menu-map','shop','dialogue-wizard')
    overview=Image.new('RGB',(1200,len(key)*194),BG)
    for index,name in enumerate(key):
        path=out/'comparisons'/f'{name}.png'
        if path.exists():overview.paste(Image.open(path),(0,index*194))
    save(overview,out/'five-ui-overview.png')
    # Magnified head bands preserve the base HUD and conditional ammo.
    bands=Image.new('RGB',(960,5*72),BG);draw=ImageDraw.Draw(bands)
    for index,n in enumerate(range(1,6)):
        path=work/f'captures/v{n}/hud-sewer-max.png'
        if not path.exists():continue
        label(draw,(6,index*72+2),f'{n}. {names[n]} / exact top12px,4x',FONT,GOLD)
        crop=Image.open(path).crop((0,0,240,12)).resize((960,48),Image.Resampling.NEAREST)
        bands.paste(crop,(0,index*72+22))
    save(bands,out/'hud-bands-4x.png')
    maps=Image.new('RGB',(800,104),BG);md=ImageDraw.Draw(maps)
    for index,n in enumerate(range(1,6)):
        path=work/f'captures/v{n}/hud-healthy.png'
        if not path.exists():continue
        label(md,(index*160+4,4),f'{n}. {names[n]}',FONT,GOLD)
        crop=Image.open(path).crop((222,142,238,158)).resize((64,64),Image.Resampling.NEAREST)
        maps.paste(crop,(index*160+6,30))
    save(maps,out/'minimap-4x.png')
    return rows


def ui_source_atlas(out,names):
    code="import json,reboot_ui as U; print(json.dumps({'tiles':U.TILES,'palette':U.RGB}))"
    options={}
    for number in range(1,6):
        env={**os.environ,'BART_UI':str(number),'PYTHONPATH':str(ROOT/'art')}
        options[number]=json.loads(subprocess.check_output([sys.executable,'-c',code],env=env,text=True,cwd=ROOT))
    tile_names=list(options[1]['tiles'])
    board=Image.new('RGB',(880,54+len(tile_names)*34),BG);draw=ImageDraw.Draw(board)
    label(draw,(8,8),'NATIVE UI KIT / five styles,8px tiles enlarged3x',TITLE,GOLD)
    for number in range(1,6):label(draw,(180+(number-1)*140,32),f'{number}. {names[number]}',FONT,GOLD)
    records=[]
    for row,name in enumerate(tile_names):
        y=54+row*34;label(draw,(8,y+5),name)
        record={'name':name,'styles':{}}
        for number in range(1,6):
            value=options[number];pixels=value['tiles'][name];im=Image.new('RGB',(8,8),BG)
            for py,line in enumerate(pixels):
                for px,ch in enumerate(line):
                    if ch!='.':im.putpixel((px,py),tuple(value['palette'][ch]))
            board.paste(im.resize((24,24),Image.Resampling.NEAREST),(200+(number-1)*140,y))
            record['styles'][number]={'rows':pixels,'palette':value['palette']}
        records.append(record)
    save(board,out/'ui-kit-five-styles.png')
    (out/'ui-kit-catalogue.json').write_text(json.dumps(records,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--source-only',action='store_true')
    parser.add_argument('--actual-only',action='store_true',help='Add actual comparisons to an existing frozen source gallery')
    args=parser.parse_args();sys.path.insert(0,str(ROOT/'art'))
    import ui_studies as U
    sources={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'art').glob('*.py')}
    args.out.mkdir(parents=True,exist_ok=True)
    if args.actual_only:
        previous=json.loads((args.out/'gallery-manifest.json').read_text())
        assert previous['source_hashes']==sources,'Actual boards require the same frozen source gallery'
        report=json.loads((args.out/'source/catalogue.json').read_text())
    else:
        report=source_gallery(args.out/'source');ui_source_atlas(args.out/'source',U.STYLE_NAMES)
    actual=[] if args.source_only else actual_boards(args.work,args.out,U.STYLE_NAMES)
    assert sources=={name:sha(ROOT/name) for name in sources},'Source changed while gallery rendered; rerun after freeze'
    manifest={str(p.relative_to(args.out)):sha(p) for p in args.out.rglob('*') if p.is_file() and p.name!='gallery-manifest.json'}
    metadata={'source_hashes':sources,'source_room_placements':report['placement_ids'],'source_frame_drawings':report['frame_drawings'],
              'actual_comparison_screens':actual,'files':manifest,'native_source_not_emulator':True}
    (args.out/'gallery-manifest.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps({'files':len(manifest),'source_placements':report['placement_ids'],'source_frames':report['frame_drawings'],'actual_comparisons':len(actual)},indent=2))


if __name__=='__main__':main()
