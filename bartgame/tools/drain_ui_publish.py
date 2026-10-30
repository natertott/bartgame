"""Publish final Drain assets and five actual UI studies without grading images.

Run after six frozen builds, the source/actual gallery and all runtime captures.
Native selected frames, filmstrips, videos and retained GIFs are byte copies;
the only compositing adds captions outside the five original game frames.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

from PIL import Image,ImageDraw,ImageFont
from bloom_suite_gallery import write_gif
from sewer_concept_review import gif_durations

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parent
FPS=16777216/280896
FONT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def comparison(work,out,screen,names,total_limit=None):
    reports=[json.loads((work/f'captures/v{n}/capture.json').read_text()) for n in range(1,6)]
    rows=[next(r for r in report['captures'] if r['name']==screen) for report in reports]
    count=min(r['frames'] for r in rows)
    if total_limit:count=min(count,total_limit)
    frames=[]
    for tick in range(0,count,2):
        frame=Image.new('RGB',(1200,190),'#101820');draw=ImageDraw.Draw(frame);draw.fontmode='1'
        for n in range(1,6):
            path=work/f'captures/v{n}/all-frames/{screen}/frame-{tick:03}.png'
            im=Image.open(path).convert('RGB');assert im.size==(240,160)
            draw.text(((n-1)*240+6,6),f'{n}. {names[n]}',font=FONT,fill='#e8c878')
            frame.paste(im,((n-1)*240,30))
        frames.append(frame)
    info=write_gif(frames,gif_durations(count),out/(screen+'-five.gif'))
    # Exact native PNGs remain available if a five-theme GIF exceeds256colors.
    info['source']='Five actual mGBA framebuffers, captions outside the240x160 game pixels.'
    return info


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--release',type=Path,required=True);parser.add_argument('--branch',required=True)
    args=parser.parse_args();work=args.work.resolve();out=args.out.resolve();release=args.release.resolve()
    out.mkdir(parents=True,exist_ok=True);release.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(ROOT/'art'));import ui_studies as U
    builds=json.loads((work/'builds.json').read_text())
    assert len(builds)==6,'one final-room baseline and five UI styles'
    source=builds[0]['source_commit'];assert all(b['source_commit']==source for b in builds)
    shutil.copytree(work/'gallery',out,dirs_exist_ok=True)
    validation=out/'validation';validation.mkdir(exist_ok=True)
    for name in ('builds.json','review-summary.json','audit.json','audit-summary.json','audit.log','build-all.log','default-restore.log'):
        if (work/name).exists():shutil.copy2(work/name,validation/name)
    rows=[]
    for number in range(6):
        src=work/f'captures/v{number}';dst=out/f'actual/v{number}';dst.mkdir(parents=True,exist_ok=True)
        report=json.loads((src/'capture.json').read_text())
        assert report['passed']==report['total'] and not report['failures'],number
        assert report['rom_sha256']==sha(work/f'v{number}/bartgame.gba')
        for row in report['captures']:
            for rel in [row['image'],row['filmstrip'],*row['native_frames']]:
                (dst/rel).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src/rel,dst/rel)
            archive={'all_frames':row.pop('all_frames')}
            if row.get('video'):shutil.copy2(src/row['video'],dst/row['video'])
            if row.get('gif'):
                # The environment is identical in UI1..5. Keep every MP4 and
                # native frame, but publish those duplicated world GIFs once.
                if number==0 or not row['name'].startswith('drain-'):
                    shutil.copy2(src/row['gif'],dst/row['gif'])
                else:archive['gif']=row.pop('gif')
            row['archival_formats']=archive
        report['publication']={'source_report_sha256':sha(src/'capture.json'),
            'note':'Native frames, filmstrips, retained GIFs and videos are unchanged. Raw all-frame PNGs and duplicated world GIFs are retained locally as archival formats.'}
        (dst/'capture.json').write_text(json.dumps(report,indent=2)+'\n')
        rows.append(report)
    composites={}
    for name in ('hud-sewer-max','dialogue-wizard','shop','reward-chest'):
        composites[name]=comparison(work,out,name,U.STYLE_NAMES)
    # UI showcase preserves full-rate footage, selected screen changes become
    # distinct segments rather than pretending they are one uninterrupted run.
    screens=('hud-sewer-max','hud-healthy','menu-items','menu-key-items','menu-map','shop','dialogue-wizard')
    video=out/'five-ui-studies-mgba.mp4'
    process=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1200x190',
        '-r',str(FPS),'-i','-','-an','-c:v','libx264','-threads','2','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],stdin=subprocess.PIPE)
    video_frames=0
    try:
        for screen in screens:
            captures=[next(r for r in rows[n]['captures'] if r['name']==screen) for n in range(1,6)]
            count=min(r['frames'] for r in captures)
            for tick in range(count):
                frame=Image.new('RGB',(1200,190),'#101820');draw=ImageDraw.Draw(frame);draw.fontmode='1'
                for n in range(1,6):
                    im=Image.open(work/f'captures/v{n}/all-frames/{screen}/frame-{tick:03}.png').convert('RGB')
                    draw.text(((n-1)*240+6,6),f'{n}. {U.STYLE_NAMES[n]} / {screen}',font=FONT,fill='#e8c878')
                    frame.paste(im,((n-1)*240,30))
                process.stdin.write(frame.tobytes());video_frames+=1
        process.stdin.close();assert process.wait()==0
    except BaseException:
        process.kill();process.wait();raise
    roms={}
    for number in range(6):
        title='final-drain-quiet-brass' if not number else f'ui-{number}-'+re.sub('[^a-z0-9]+','-',U.STYLE_NAMES[number].lower()).strip('-')
        name=f'{number:02}-{title}.gba';shutil.copy2(work/f'v{number}/bartgame.gba',release/name)
        assert sha(release/name)==rows[number]['rom_sha256'];roms[number]=name
    (release/'builds.json').write_text(json.dumps(builds,indent=2)+'\n')
    (release/'ROM-SHA256.txt').write_text(''.join(f'{sha(release/name)}  {name}\n' for name in roms.values()))
    (release/'README.txt').write_text(f'''BARTGAME final Drain and five interface studies

00 is the final Drain with the neutral compact HUD.01..05 keep that same
room and game while varying the native HUD, menu, dialogue and shop design.
HUDs show equipped items, hearts and gilt, plus the small maze and ammunition
only when seeds or the bow are equipped. The center remains transparent.
No commercial base ROM is needed. Open a .gba in mGBA.

Game/art source: {source}
Build: make -j4 BART_SEWER=9 BART_UI=N
Controls: D-pad move; A assigned item/talk; B assigned item/sword;
L assigned item/shield; R roll/lift/throw; Start inventory; R/L turn tabs.

Full review gallery:
https://github.com/natertott/bartgame/blob/{args.branch}/{out.relative_to(REPO)}/README.md
''')
    archive='final-drain-and-five-ui-studies.zip'
    with zipfile.ZipFile(release/archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name in [*roms.values(),'README.txt','ROM-SHA256.txt','builds.json']:z.write(release/name,name)
    with zipfile.ZipFile(release/archive) as z:assert z.testzip() is None
    (release/'SHA256SUMS.txt').write_text(''.join(f'{sha(release/name)}  {name}\n' for name in [*roms.values(),archive]))
    summary={'source_commit':source,'ui_names':U.STYLE_NAMES,'captures':sum(r['capture_count'] for r in rows),
             'runtime_passed':sum(r['passed'] for r in rows),'runtime_total':sum(r['total'] for r in rows),
             'composite_gifs':composites,'video':{'path':video.name,'frames':video_frames,'fps':FPS,'lossy':True},
             'rom_files':roms,'zip':archive,'source_assemblies_are_not_screenshots':True}
    (validation/'publication-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
