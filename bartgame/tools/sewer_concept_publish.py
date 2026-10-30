"""Publish a frozen Drain study without altering its game framebuffers.

Run after source galleries, all nine ROM freezes, the independent audit and
all eight real-mGBA reviews exist under --work. Source/actual presentations
remain separate. The main editorial README is maintained with the art pass.
"""
import argparse
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from PIL import Image, ImageDraw, ImageFont

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--work',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--release',type=Path,required=True)
parser.add_argument('--branch',required=True)
args=parser.parse_args()
repo=Path(__file__).resolve().parents[2]
game=repo/'bartgame'
local=args.work.resolve()
out=args.out.resolve()
out.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(game/'tools'))
from bloom_suite_gallery import write_gif
sys.path.insert(0,str(game/'art'))
import sewer_concepts as S

sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
builds=json.loads((local/'builds.json').read_text())
assert len(builds)==9 and [b['variant'] for b in builds]==list(range(9))
source=builds[0]['source_commit']
assert all(b['source_commit']==source for b in builds)
assert sha(game/'bartgame.gba')==builds[0]['rom_sha256']
shutil.copytree(local/'gallery-source',out/'source',dirs_exist_ok=True)
validation=out/'validation'
validation.mkdir(exist_ok=True)
for name in ['audit-scope.json','audit-scope-summary.json','audit-scope.log','review-summary.json','builds.json','build-0.log','default-restore.log']:
    shutil.copy2(local/name,validation/name)
for name,destination in (('terrain/terrain-validation.json','terrain-validation.json'),
                         ('terrain/validation.json','terrain-validation.json'),
                         ('npcs/native-review.json','native-review.json')):
    if (local/name).exists():shutil.copy2(local/name,validation/destination)

reports={}
for n in range(1,9):
    src=local/f'captures/v{n}'
    dst=out/f'actual/v{n}'
    dst.mkdir(parents=True,exist_ok=True)
    report=json.loads((src/'capture.json').read_text())
    assert report['rom_sha256']==builds[n]['rom_sha256']
    assert report['passed']==report['total'] and len(report['captures'])==10
    for row in report['captures']:
        for name in [*row['native_frames'],row['preview_png'],row['filmstrip'],row['video']]:
            (dst/name).parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src/name,dst/name)
        archived={'full_frames':row.pop('full_frames')}
        if row['name']=='bridge' or n<=5 and row['name'] in ('market','wizard'):
            shutil.copy2(src/row['gif'],dst/row['gif'])
        else:
            if (dst/row['gif']).exists():(dst/row['gif']).unlink()
            archived['gif']=row.pop('gif')
        row['archival_formats']=archived
    report['publication']={'source_report_sha256':sha(src/'capture.json'),
        'note':'Native selected PNGs, videos, filmstrips and traces are unchanged. Bridge GIFs are published for all recipes, plus market/wizard GIFs for1..5; all-frame local archives and other GIFs are listed under archival_formats.'}
    (dst/'capture.json').write_text(json.dumps(report,indent=2)+'\n')
    reports[n]=report
    shutil.copy2(local/f'build-{n}.log',validation/f'build-{n}.log')
    shutil.copy2(local/f'review-v{n}.log',validation/f'review-v{n}.log')

print('Copied source gallery and80actual cases',flush=True)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
FPS=16777216/280896
views=('market','wizard','bridge','ladder')
video=out/'five-concepts-mgba.mp4'
proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24',
    '-video_size','1200x190','-framerate',str(FPS),'-i','-','-an','-c:v','libx264','-crf','17',
    '-pix_fmt','yuv420p','-movflags','+faststart',str(video)],stdin=subprocess.PIPE)
comparisons={}
video_count=0
try:
    for view in views:
        rows=[next(r for r in reports[n]['captures'] if r['name']==view) for n in range(1,6)]
        count=rows[0]['video_frames']
        for row in rows:
            assert row['video_frames']==count and row['position_fixture']==rows[0]['position_fixture'] and row['camera']==rows[0]['camera']
        for row in rows[1:]:
            assert [(r['frame'],r['game_updates'],r['position'],r['camera']) for r in row['trace']]==[(r['frame'],r['game_updates'],r['position'],r['camera']) for r in rows[0]['trace']]
        gifs=[]
        for tick in range(count):
            board=Image.new('RGB',(1200,190),'#10171e')
            d=ImageDraw.Draw(board)
            d.fontmode='1'
            for index,n in enumerate(range(1,6)):
                im=Image.open(local/f'captures/v{n}/all-frames/{view}/frame-{tick:03}.png').convert('RGB')
                board.paste(im,(index*240,30))
                d.text((index*240+5,3),f'{n}. {S.STYLE_NAMES[n]}',font=font,fill='#eee7c8')
                d.text((index*240+5,17),view+' / real mGBA / normal speed',font=font,fill='#a0b8a8')
            proc.stdin.write(board.tobytes())
            video_count+=1
            if tick%2==0:gifs.append(board)
            if tick==count//2:board.save(out/f'actual-{view}-comparison.png')
        durations=[round(min(count,t+2)/FPS*100)*10-round(t/FPS*100)*10 for t in range(0,count,2)]
        comparisons[view]=write_gif(gifs,durations,out/f'actual-{view}-comparison.gif')
        if view!='bridge':(out/f'actual-{view}-comparison.gif').unlink()
        print('COMPARISON',view,comparisons[view],flush=True)
    proc.stdin.close()
    assert proc.wait()==0
except BaseException:
    proc.kill();proc.wait();raise

release=args.release.resolve()
release.mkdir(exist_ok=True)
names={}
for n in range(1,9):
    recipe=S.recipe(n)
    name=f'{n:02}-'+re.sub('[^a-z0-9]+','-',recipe['name'].lower()).strip('-')+'.gba'
    shutil.copy2(local/f'v{n}/bartgame.gba',release/name)
    assert sha(release/name)==builds[n]['rom_sha256']
    names[n]=name
(release/'builds.json').write_text(json.dumps(builds,indent=2)+'\n')
(release/'ROM-SHA256.txt').write_text(''.join(f'{sha(release/name)}  {name}\n' for name in names.values()))
(release/'README.txt').write_text(f'''BARTGAME - eight native Drain art comparison builds

Open a .gba in mGBA. No commercial base ROM is needed.
01..05 are complete concepts;06..08 are mixed-component room designs.
All use the same physical room, Bloom and glitter. The merchant is a cartoon
frog and the wizard wears purple with a flame-tipped staff. These are optional
studies for feedback. The released art-reboot branch remains unchanged.

Source game/art: {source}
Build: make -j4 BART_SEWER=N (default0 keeps the released room).
The selected Step-and-cut sword remains the default in every comparison ROM.

D-pad walk. A talk/use assigned item. B sword. L shield.
R roll while moving; lift while still; throw when carrying.
Start inventory, key items and map.

All asset choices, room maps, real mGBA videos and full inventory:
https://github.com/natertott/bartgame/blob/{args.branch}/{out.relative_to(repo)}/README.md
''')
zip_name='all-eight-sewer-concepts.zip'
with zipfile.ZipFile(release/zip_name,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for name in [*names.values(),'README.txt','builds.json','ROM-SHA256.txt']:z.write(release/name,name)
with zipfile.ZipFile(release/zip_name) as z:assert z.testzip() is None
(release/'SHA256SUMS.txt').write_text(''.join(f'{sha(release/name)}  {name}\n' for name in [*names.values(),zip_name]))

audit=json.loads((local/'audit-scope-summary.json').read_text())
runtime_total=sum(r['total'] for r in reports.values())
summary={'source_commit':source,'default_rom_sha256':builds[0]['rom_sha256'],
         'default_release_unchanged':True,'static_audit':{'passed':audit['passed'],'total':audit['total']},
         'runtime_checks':{'passed':runtime_total,'total':runtime_total,'cases':sum(r['capture_count'] for r in reports.values())},
         'combined_checks':{'passed':audit['passed']+runtime_total,'total':audit['total']+runtime_total},
         'comparisons':comparisons,'video':{'path':video.name,'frames':video_count,'fps':FPS,'seconds':video_count/FPS,'lossy':True},
         'rom_files':names,'source_assembly_world_size':[480,320],'native_game_screen':[240,160],
         'limits':'Source assemblies omit ambient glitter and are not screenshots. Actual video frames are real mGBA output; captions are outside gameplay. Static art coverage exceeds the idle NPC poses activated in the runtime clips.'}
(validation/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'source_files':len(list((out/'source').rglob('*'))),'publication_bytes_so_far':sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),'video_frames':video_count,'zip_bytes':(release/zip_name).stat().st_size,'rom_files':names},indent=2),flush=True)
