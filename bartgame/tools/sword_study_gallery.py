"""Publish five sword studies from real mGBA captures, without repainting art.

Clean comparisons crop exact native PNG framebuffers, enlarge with nearest
neighbour and add labels/timing bars outside gameplay. Cyan hitbox versions
are explicitly diagnostic composites of the aligned runtime damage rectangle.
Normal GIFs sample two video frames at a time; slow GIFs retain every frame.
The MP4 is a lossy convenience copy at the recorded GBA video rate.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont

from bloom_suite_gallery import write_gif

FACES=('n','e','s','w')
NAMES={'n':'NORTH','e':'EAST','s':'SOUTH','w':'WEST'}
PHASE_NAMES=('Ready','Load','Release','Cut A','Cut B','Follow A','Follow B','Settle')
BG=(12,17,25)
FG=(243,227,174)
DIM=(145,154,149)
WINDUP=(206,167,73)
LIVE=(107,231,227)
RECOVERY=(111,128,137)
FONT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
SMALL=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
TITLE=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)


def read(path):return json.loads(path.read_text())

def write(path,data):path.write_text(json.dumps(data,indent=2)+'\n')

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def copy(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,target)
    assert digest(source)==digest(target),(source,target)


def draw_on(image):
    draw=ImageDraw.Draw(image)
    draw.fontmode='1'  # review labels do not introduce antialiasing colours
    return draw


def display(row):
    view=row['display']
    assert isinstance(view,dict) and 'phase' in view and 'active' in view
    return view


def native(path):
    with Image.open(path) as im:
        assert im.size==(240,160),(path,im.size)
        return im.convert('RGB').copy()


def frame_paths(source,row):
    if row.get('full_frame_paths'):
        paths=[Path(p) if Path(p).is_absolute() else source/p for p in row['full_frame_paths']]
    else:
        local=Path(row['local_all_frames_dir'])
        paths=sorted(local.glob('frame-*.png'))
    assert len(paths)==len(row['trace']),(row['name'],len(paths),len(row['trace']))
    assert all(p.exists() for p in paths),(row['name'],'missing native frame archive')
    return paths


def crop_frame(image,row,tick,diagnostic=False):
    if diagnostic:
        image=image.copy()
        view=display(row['trace'][tick])
        if view['active']:
            x0,y0,x1,y1=view['box'];cx,cy=view['camera']
            draw_on(image).rectangle((x0-cx,y0-cy,x1-cx,y1-cy),outline=LIVE,width=1)
    box=row['crop']
    assert len(box)==4 and 0<=box[0]<box[2]<=240 and 0<=box[1]<box[3]<=160,box
    return image.crop(box)


def load_studies(captures,out):
    studies=[]
    actual=out/'actual'
    if actual.exists():shutil.rmtree(actual)
    for variant in range(1,6):
        source=captures/('v%d'%variant);report=read(source/'capture.json')
        assert int(report['variant'])==variant
        assert not report.get('failures') and all(r.get('passed',True) for r in report['captures'])
        profile=report['profile']
        assert len(profile['durations'])==len(profile['active_flags'])==8
        dest=actual/('v%d'%variant);dest.mkdir(parents=True)
        copy(source/'capture.json',dest/'capture.json')
        names=set()
        for row in report['captures']:
            assert row['name'] not in names;names.add(row['name'])
            for key in ('clean_gif','slow_gif','overlay_gif','video','filmstrip'):
                if row.get(key):copy(source/row[key],dest/row[key])
            for relative in row['native_frames']:
                copy(source/relative,dest/relative);native(dest/relative)
        cases={(r['background'],r['facing']):r for r in report['captures']}
        for face in FACES:assert ('forest',face) in cases,(variant,face)
        studies.append({'source':source,'report':report,'profile':profile,'cases':cases})
    return studies


def timeline(draw,x,y,width,profile,view):
    total=sum(profile['durations']);start=0
    age_flags=[flag for flag,length in zip(profile['active_flags'],profile['durations']) for _ in range(length)]
    first_live=age_flags.index(True)
    for length,active in zip(profile['durations'],profile['active_flags']):
        color=LIVE if active else WINDUP if start<first_live else RECOVERY
        # Segment meaning derives from the shared generated active schedule.
        xa=x+round(start*width/total);xb=x+round((start+length)*width/total)-1
        draw.rectangle((xa,y,xb,y+6),fill=color)
        start+=length
    if view.get('state')==2 and int(view['age'])<total:
        at=x+round((int(view['age'])+.5)*width/total)
        draw.line((at,y-2,at,y+8),fill=FG,width=1)


def status(view,profile):
    if view.get('state')!=2:return 'Rest'
    age=int(view['age']);first=next(i for i,v in enumerate(
        [flag for flag,length in zip(profile['active_flags'],profile['durations']) for _ in range(length)]) if v)
    return 'CUTTING' if view['active'] else 'Windup' if age<first else 'Recovery'


def compose(studies,rows,images,tick,face,speed,diagnostic=False):
    crops=[crop_frame(im,row,tick,diagnostic) for im,row in zip(images,rows)]
    assert len({im.size for im in crops})==1,[im.size for im in crops]
    cw,ch=crops[0].size;scale=3;cell=cw*scale+12
    width=cell*5;height=42+34+ch*scale+55
    height+=(height&1)
    out=Image.new('RGB',(width,height),BG);d=draw_on(out)
    suffix=' / CYAN = ACTUAL DAMAGE BOX (diagnostic)' if diagnostic else ' / clean actual mGBA crops'
    d.text((8,7),NAMES[face]+' / '+speed+suffix,font=TITLE,fill=FG)
    for index,(study,row,crop) in enumerate(zip(studies,rows,crops)):
        x=index*cell+6;view=display(row['trace'][tick]);p=study['profile']
        d.text((x,43),str(index+1)+'  '+p['name'],font=FONT,fill=FG)
        out.paste(crop.resize((cw*scale,ch*scale),Image.Resampling.NEAREST),(x,76))
        y=79+ch*scale
        color=LIVE if view['active'] else DIM
        d.text((x,y),status(view,p)+' / '+str(sum(p['durations']))+' ticks total',font=SMALL,fill=color)
        timeline(d,x,y+20,cw*scale,p,view)
        d.text((x,y+30),'windup   cutting   recovery',font=SMALL,fill=DIM)
    return out


def timing(samples,total,fps):
    ends=samples[1:]+[total]
    return [round(end*100/fps)*10-round(start*100/fps)*10 for start,end in zip(samples,ends)]


def comparisons(studies,out,fps):
    results=[];archives={}
    for face in FACES:
        rows=[s['cases']['forest',face] for s in studies]
        traces=[len(r['trace']) for r in rows];assert len(set(traces))==1,traces
        total=traces[0]
        # The five prototypes must compare the same unmodified generated view.
        for key in ('seed','cell','position','camera','input'):
            values=[r[key] for r in rows]
            assert all(v==values[0] for v in values),(face,key,values)
        frames=[[native(path) for path in frame_paths(s['source'],r)] for s,r in zip(studies,rows)]
        archives[face]=(rows,frames)
        for diagnostic in (False,True):
            name='comparison-'+face+('-hitbox' if diagnostic else '')
            normal_ticks=list(range(0,total,2))
            pictures=[compose(studies,rows,[f[t] for f in frames],t,face,'NORMAL SPEED / ~30fps GIF',diagnostic) for t in normal_ticks]
            info=write_gif(pictures,timing(normal_ticks,total,fps),out/(name+'.gif'))
            results.append({'file':name+'.gif','face':face,'diagnostic':diagnostic,'speed':1,**info})
            slow=[compose(studies,rows,[f[t] for f in frames],t,face,'3x SLOW / every video frame',diagnostic) for t in range(total)]
            slow_durations=[round((t+1)*300/fps)*10-round(t*300/fps)*10 for t in range(total)]
            info=write_gif(slow,slow_durations,out/(name+'-slow.gif'))
            results.append({'file':name+'-slow.gif','face':face,'diagnostic':diagnostic,'speed':1/3,**info})
    return results,archives


def phase_tick(row,phase):
    return next(i for i,tr in enumerate(row['trace']) if display(tr)['phase']==phase and display(tr).get('state')==2)


def still_boards(studies,archives,out):
    rows,frames=archives['e'];cw,ch=rows[0]['crop'][2]-rows[0]['crop'][0],rows[0]['crop'][3]-rows[0]['crop'][1]
    cellw=cw*2;rowh=ch*2+53
    board=Image.new('RGB',(cellw*8,rowh*5+40),BG);d=draw_on(board)
    d.text((8,8),'All five / EAST / actual mGBA key poses / 2x nearest-neighbour',font=TITLE,fill=FG)
    for index,(study,row,sequence) in enumerate(zip(studies,rows,frames)):
        y=40+index*rowh;p=study['profile']
        d.text((8,y),str(index+1)+'  '+p['name']+' / '+str(sum(p['durations']))+' logic ticks',font=FONT,fill=FG)
        for phase in range(8):
            tick=phase_tick(row,phase);x=phase*cellw
            crop=crop_frame(sequence[tick],row,tick)
            board.paste(crop.resize((cellw,ch*2),Image.Resampling.NEAREST),(x,y+24))
            d.text((x+5,y+25+ch*2),PHASE_NAMES[phase]+(' [LIVE]' if p['active_flags'][phase] else ''),font=SMALL,fill=LIVE if p['active_flags'][phase] else DIM)
    board.save(out/'pose-sequences.png')
    # An at-a-glance contact board shows three moments with each style's own
    # first clear forward contact, never pretending all input ages are equal.
    scale=3;cell=cw*scale+12;rh=ch*scale+25
    overview=Image.new('RGB',(cell*5,53+rh*3),BG);d=draw_on(overview)
    d.text((8,8),'Five sword studies / actual mGBA / ready, cutting and recovery poses',font=TITLE,fill=FG)
    for index,(study,row,sequence) in enumerate(zip(studies,rows,frames)):
        p=study['profile'];x=index*cell+6
        d.text((x,34),str(index+1)+'  '+p['name'],font=FONT,fill=FG)
        active=[i for i,v in enumerate(p['active_flags']) if v]
        phases=(1,active[len(active)//2],6)
        for rr,phase in enumerate(phases):
            tick=phase_tick(row,phase);crop=crop_frame(sequence[tick],row,tick);y=57+rr*rh
            overview.paste(crop.resize((cw*scale,ch*scale),Image.Resampling.NEAREST),(x,y))
            d.text((x,y+ch*scale+3),PHASE_NAMES[phase]+' / age '+str(display(row['trace'][tick])['age']),font=SMALL,fill=LIVE if p['active_flags'][phase] else DIM)
    overview.save(out/'overview.png')


def movie(studies,archives,out,fps):
    first_face='n';rows,frames=archives[first_face]
    example=compose(studies,rows,[f[0] for f in frames],0,first_face,'NORMAL SPEED / native GBA timing')
    width,height=example.size;target=out/'sword-studies.mp4'
    command=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{width}x{height}',
             '-framerate',str(fps),'-i','pipe:0','-an','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(target)]
    process=subprocess.Popen(command,stdin=subprocess.PIPE)
    count=0
    try:
        for face in FACES:
            rows,frames=archives[face];total=len(rows[0]['trace'])
            # Two synchronized normal cycles, then one clearly labelled 3x
            # slow cycle. Every original captured video frame is preserved.
            for repeat in range(2):
                for tick in range(total):
                    picture=compose(studies,rows,[f[tick] for f in frames],tick,face,'NORMAL SPEED / native GBA timing')
                    process.stdin.write(picture.tobytes());count+=1
            for tick in range(total):
                picture=compose(studies,rows,[f[tick] for f in frames],tick,face,'3x SLOW / every original video frame')
                for repeat in range(3):process.stdin.write(picture.tobytes());count+=1
        process.stdin.close();assert process.wait()==0
    except BaseException:
        process.kill();raise
    return {'file':target.name,'frames':count,'fps':fps,'seconds':count/fps,'size':[width,height],
            'method':'Actual native PNG crops enlarged 3x, labels/timing bars outside gameplay; two native-timing cycles and one 3x slow cycle per facing. Silent lossy convenience copy.'}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--captures',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--fps',type=float,default=59.727500569606)
    ap.add_argument('--no-video',action='store_true')
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    studies=load_studies(args.captures,args.out)
    comparison_rows,archives=comparisons(studies,args.out,args.fps)
    still_boards(studies,archives,args.out)
    report={'method':__doc__.strip(),'prototypes_only':True,'selected_variant':None,'fps':args.fps,
            'variants':[{'variant':i+1,'profile':s['profile'],'rom_sha256':s['report']['rom_sha256'],
                         'capture_report':f'actual/v{i+1}/capture.json','cases':len(s['report']['captures'])} for i,s in enumerate(studies)],
            'comparisons':comparison_rows,'palette_note':'Raw native PNGs are unchanged. Comparison GIF metadata records whether its combined colour union fits 256 colours. Video is a lossy convenience.'}
    if not args.no_video:report['video']=movie(studies,archives,args.out,args.fps)
    report['files']=[{'path':str(p.relative_to(args.out)),'bytes':p.stat().st_size,'sha256':digest(p)}
                     for p in sorted(args.out.rglob('*')) if p.is_file() and p.name not in ('README.md','gallery-manifest.json')]
    write(args.out/'gallery-manifest.json',report)
    print(json.dumps({'variants':len(studies),'cases':sum(len(s['report']['captures']) for s in studies),
                      'files':len(report['files']),'bytes':sum(r['bytes'] for r in report['files']),
                      'video':report.get('video')},indent=2))


if __name__=='__main__':main()
