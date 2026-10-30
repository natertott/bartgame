#!/usr/bin/env python3
"""Publish frozen skin/layout studies without changing captured game pixels.

Copies exact native PNGs and full-rate MP4 convenience clips. GIFs are only
published when the complete animation has an exact<=256-color palette; raw
full-frame sequences and excluded files are explicitly archival, not links.
"""
import argparse,hashlib,json,re,shutil,subprocess,sys,zipfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from bloom_suite_gallery import write_gif
from sewer_concept_review import gif_durations
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parent;FPS=16777216/280896
SHA=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
FONT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)

def label(d,xy,s):d.fontmode='1';d.text(xy,s,font=FONT,fill='#e8c878')
def name(b):return b.get('name') or b.get('label') or f"UI{b['ui']}-menu{b.get('menu',0)}"
def encode_walkthrough(work,out,b):
    n=b['variant'];screens=('layout-items','layout-navigate','layout-assigned','layout-key-items','layout-map','layout-map-navigate','layout-zoom-map','layout-focus-return','layout-hud-return')
    report=json.loads((work/f'captures/v{n}/capture.json').read_text());by={r['name']:r for r in report['captures']}
    dst=out/'walkthroughs'/f"layout-{b['menu']:02}.mp4";dst.parent.mkdir(exist_ok=True)
    proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','480x348','-r',str(FPS),'-i','-','-an','-c:v','libx264','-threads','1','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(dst)],stdin=subprocess.PIPE)
    count=0
    try:
        for screen in screens:
            row=by[screen]
            for tick in range(row['frames']):
                native=Image.open(work/f'captures/v{n}/all-frames/{screen}/frame-{tick:03}.png').convert('RGB')
                frame=Image.new('RGB',(480,348),'#101820');d=ImageDraw.Draw(frame)
                label(d,(6,6),f"{b['menu']}. {name(b)} / {screen.replace('layout-','')}")
                frame.paste(native.resize((480,320),Image.Resampling.NEAREST),(0,28));proc.stdin.write(frame.tobytes());count+=1
        proc.stdin.close();assert proc.wait()==0
    except BaseException:proc.kill();proc.wait();raise
    return {'path':str(dst.relative_to(out)),'frames':count,'fps':FPS,'lossy':True,'note':'Actual menu-control segments with explicit screen cuts, not one uninterrupted player run.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--release',type=Path,required=True);p.add_argument('--branch',required=True);a=p.parse_args()
    work=a.work.resolve();out=a.out.resolve();release=a.release.resolve();out.mkdir(parents=True,exist_ok=True);release.mkdir(parents=True,exist_ok=True)
    builds=json.loads((work/'builds.json').read_text());assert len(builds)==16
    shutil.copytree(work/'gallery',out,dirs_exist_ok=True)
    validation=out/'validation';validation.mkdir(exist_ok=True)
    for filename in ('builds.json','audit.json','audit-summary.json','audit.log','review-summary.json','review-batch.log','build-all.log','default-restore.log','gallery-verification.json','runtime-review.md'):
        if(work/filename).exists():shutil.copy2(work/filename,validation/filename)
    for folder,dst in [('ui-remix','source-skin-proofs'),('layouts','source-layout-proofs')]:
        if(work/folder).exists():
            for path in(work/folder).rglob('*'):
                if path.is_file() and path.suffix in ('.png','.gif','.json','.md'):
                    dest=validation/dst/path.relative_to(work/folder);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
    totals=[];omitted=[]
    for b in builds:
        n=b['variant'];src=work/f'captures/v{n}';dst=out/f'actual/v{n}';dst.mkdir(parents=True,exist_ok=True)
        report=json.loads((src/'capture.json').read_text());assert report['passed']==report['total'] and not report['failures']
        assert report['rom_sha256']==SHA(work/f'v{n}/bartgame.gba')
        for row in report['captures']:
            for rel in [row['image'],row['filmstrip'],*row['native_frames']]:
                dest=dst/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src/rel,dest)
            archive={'all_frames':row.pop('all_frames')}
            if row.get('video'):shutil.copy2(src/row['video'],dst/row['video'])
            if row.get('gif'):
                if row['gif_metadata']['exact_palette']:shutil.copy2(src/row['gif'],dst/row['gif'])
                else:
                    archive['gif']=row.pop('gif');archive['gif_reason']='Color union exceeds256; native PNGs/MP4 are the published evidence.'
                    omitted.append({'variant':n,'capture':row['name'],'colors':row['gif_metadata']['colour_count']})
            row['archival_formats']=archive
        report['publication']={'source_report_sha256':SHA(src/'capture.json'),'note':'Native frames/filmstrips/MP4 and exact-palette GIFs are unchanged copies. Raw all-frame sequences and quantized GIFs are archival.'}
        (dst/'capture.json').write_text(json.dumps(report,indent=2)+'\n');totals.append(report)
    walkthroughs={b['menu']:encode_walkthrough(work,out,b) for b in builds if b.get('menu',0)}
    # Animated style comparison uses actual type-on dialogue frames, with labels
    # outside all five native240x160 images.
    skins=[b for b in builds if 6<=b['ui']<=10 and not b.get('menu',0)];screen='dialogue-wizard'
    duration=min(next(c for c in t['captures'] if c['name']==screen)['frames'] for b in skins for t in totals if t['ui_variant']==b['ui'] and not t['menu_variant'])
    frames=[]
    for tick in range(0,duration,2):
        im=Image.new('RGB',(1200,188),'#101820');draw=ImageDraw.Draw(im)
        for i,b in enumerate(skins):label(draw,(i*240+5,5),f'{i+1}. {name(b)}');im.paste(Image.open(work/f"captures/v{b['variant']}/all-frames/{screen}/frame-{tick:03}.png").convert('RGB'),(i*240,28))
        frames.append(im)
    gif=out/'five-skin-dialogue.gif';meta=write_gif(frames,gif_durations(duration),gif)
    if not meta['exact_palette']:gif.unlink();meta['published']=False
    else:meta['published']=True
    roms={}
    for b in builds:
        n=b['variant'];slug=re.sub('[^a-z0-9]+','-',name(b).lower()).strip('-')
        filename=(f"layout-{b['menu']:02}-{slug}.gba" if b.get('menu',0) else f"style-{b['ui']-5:02}-{slug}.gba" if b['ui']>=6 else '00-production-baseline.gba')
        shutil.copy2(work/f'v{n}/bartgame.gba',release/filename);assert SHA(release/filename)==b['rom_sha256'];roms[n]=filename
    source=builds[0]['source_commit'];(release/'builds.json').write_text(json.dumps(builds,indent=2)+'\n')
    (release/'ROM-SHA256.txt').write_text(''.join(f'{SHA(release/f)}  {f}\n' for f in roms.values()))
    (release/'README.txt').write_text(f'''BARTGAME - five new UI skins and ten playable menu layouts

00 is the unchanged-looking production baseline. style01..05 use new skins
with the existing menu layout. layout01..10 use one fixed new skin and ten
interactive arrangements, so structure can be judged independently of color.
All share the final Drain/Bloom/forest/gameplay. No commercial ROM needed.
Source: {source}
Build: make BART_UI=6..10 BART_MENU=0 for skins; BART_UI=6 BART_MENU=1..10 for layouts.
D-pad selects; A/B/L assign selected tools; R cycles pages; Start closes.
On maps A zooms and B returns. Old baseline retains its established controls.

Gallery: https://github.com/natertott/bartgame/blob/{a.branch}/{out.relative_to(REPO)}/README.md
''')
    archive='baseline-and-fifteen-studies.zip'
    with zipfile.ZipFile(release/archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for f in [*roms.values(),'README.txt','ROM-SHA256.txt','builds.json']:z.write(release/f,f)
    with zipfile.ZipFile(release/archive) as z:assert z.testzip() is None
    (release/'SHA256SUMS.txt').write_text(''.join(f'{SHA(release/f)}  {f}\n' for f in [*roms.values(),archive]))
    summary={'source_commit':source,'variants':builds,'rom_files':roms,'zip':archive,'captures':sum(t['capture_count'] for t in totals),'runtime_passed':sum(t['passed'] for t in totals),'runtime_total':sum(t['total'] for t in totals),'walkthroughs':walkthroughs,'dialogue_comparison':meta,'quantized_gifs_omitted':omitted}
    (validation/'publication-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
