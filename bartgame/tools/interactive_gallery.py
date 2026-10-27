"""Publish actual mGBA interactive-scenery captures and comparisons.

python tools/interactive_gallery.py BEFORE_CAPTURES AFTER_CAPTURES OUT

Native framebuffers are copied unchanged. Captions, nearest-neighbour
scaling and adjacent before/after panels are the only changes to images.
Same seed/cell/feature cases may have relocated targets after entrance
clearance changes; the capture reports retain those differences explicitly.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from PIL import Image,ImageDraw,ImageFont
import bloom_suite_gallery as G

PAIRS=('forest-wood-chest','forest-brass-chest','blight-relic-chest','blight-wood-chest',
       'forest-cave-door','forest-hollow-door','blight-thicket-door','cave-exit',
       'cave-floor-switch','thicket-censer','forest-shrine',
       'blight-bomb-wall','blight-cobweb','blight-cape-hole')
OVERVIEW=('forest-wood-chest','forest-brass-chest','forest-relic-chest','blight-relic-chest',
          'forest-cave-door','forest-hollow-door','forest-thicket-door','blight-thicket-door',
          'cave-floor-switch','hollow-floor-switch','thicket-censer','forest-shrine',
          'forest-bomb-wall','blight-bomb-wall','blight-cobweb','blight-cape-hole')
REEL=('forest-wood-chest','forest-brass-chest','forest-relic-chest','blight-wood-chest','blight-relic-chest',
      'forest-cave-door','mixed-cave-door','forest-hollow-door','blight-hollow-door','forest-thicket-door','blight-thicket-door',
      'cave-exit','hollow-exit','thicket-exit','cave-floor-switch','hollow-floor-switch','thicket-floor-switch','thicket-censer',
      'forest-bomb-wall','blight-bomb-wall','forest-cobweb','blight-cobweb','forest-cape-hole','blight-cape-hole','forest-shrine')
FONT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)


def overview(root,out):
    board=Image.new('RGB',(4*480,4*350+36),G.BG);d=ImageDraw.Draw(board)
    d.text((12,10),'FINAL INTERACTIVE SCENERY / actual mGBA frames, 2x nearest neighbour',font=FONT,fill=G.FG)
    for i,name in enumerate(OVERVIEW):
        image=Image.open(root/'after'/f'{name}.png').convert('RGB').resize((480,320),Image.Resampling.NEAREST)
        x=i%4*480;y=36+i//4*350;board.paste(image,(x,y));d.text((x+8,y+324),name,font=FONT,fill=G.FG)
    board.save(out/'overview.png')
    names=PAIRS[:8]+('cave-floor-switch','forest-shrine','blight-bomb-wall','blight-cobweb')
    board=Image.new('RGB',(1920,6*350+36),G.BG);d=ImageDraw.Draw(board)
    d.text((12,10),'BEFORE / AFTER / same seed, cell and feature; generated entrance anchors can move',font=FONT,fill=G.FG)
    for i,name in enumerate(names):
        x=i%2*960;y=36+i//2*350
        for j,side in enumerate(('before','after')):
            im=Image.open(root/side/f'{name}.png').convert('RGB').resize((480,320),Image.Resampling.NEAREST)
            board.paste(im,(x+j*480,y));d.text((x+j*480+8,y+324),side.upper()+' | '+name,font=FONT,fill=G.FG)
    board.save(out/'before-after.png')


def video(root,out):
    path=out/'interactive-scenery-reel.mp4'
    proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','480x342','-r','30','-i','-','-an','-c:v','libx264','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(path)],stdin=subprocess.PIPE)
    count=0
    try:
        for name in REEL:
            frames,durations=G.load_gif(root/'after'/f'{name}.gif');pos=end=0
            for tick in range(round(sum(durations)*30/1000)):
                target=tick*1000/30
                while pos<len(frames)-1 and target>=end+durations[pos]:end+=durations[pos];pos+=1
                proc.stdin.write(G.label(frames[pos],'mGBA FINAL | '+name).tobytes());count+=1
        proc.stdin.close()
        if proc.wait():raise RuntimeError('ffmpeg did not finish successfully')
    except BaseException:proc.kill();proc.wait();raise
    return {'path':path.name,'frames':count,'fps':30,'seconds':count/30,'clips':list(REEL),'note':'Lossy H.264 review convenience; original GIFs and native PNGs retained.'}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('before',type=Path);ap.add_argument('after',type=Path);ap.add_argument('out',type=Path);ap.add_argument('--no-video',action='store_true');args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    reports={};counts={}
    # Regeneration must not retain files from an earlier candidate ROM.
    # Only the generator-owned evidence directories are replaced.
    for family in ('before','after','comparisons'):
        if (args.out/family).exists():shutil.rmtree(args.out/family)
    for side,source in [('before',args.before),('after',args.after)]:
        report=json.loads((source/'capture.json').read_text());assert report['count']==40 and not report['missing'];assert report['activation_checks']=={'passed':32,'total':32}
        reports[side]=report;dest=args.out/side;dest.mkdir(exist_ok=True);shutil.copyfile(source/'capture.json',dest/'capture.json')
        for row in report['captures']:
            name=row['name']
            for relative in [row['image'],row['filmstrip'],name+'.gif',*row['native_frames']]:
                a=source/relative;b=dest/relative;b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b)
        counts[side]={'captures':len(report['captures']),'exact_palette_gifs':sum(r['gif']['exact_palette'] for r in report['captures']),'activation_checks':report['activation_checks']}
    pairs=args.out/'comparisons';pairs.mkdir(exist_ok=True);comparisons=[]
    for name in PAIRS:
        info=G.compare(args.out/'before'/f'{name}.gif',args.out/'after'/f'{name}.gif',pairs/f'{name}.gif',name)
        row=next(r for r in reports['after']['captures'] if r['name']==name)
        comparisons.append({'name':name,'gif':f'comparisons/{name}.gif','matched_case':row['matched_case'],**info})
        print('COMPARISON',name,flush=True)
    overview(args.out,args.out)
    manifest={'method':__doc__.strip(),'before_rom_sha256':reports['before']['rom_sha256'],'after_rom_sha256':reports['after']['rom_sha256'],'counts':counts,'comparisons':comparisons,
              'fixture_note':'Same seed/cell/feature cases; entrance headroom intentionally relocates some generated targets and subsequent placements. Original positions, cameras and physical contracts are in capture.json.',
              'same_target_cases':sum(r['matched_case']['same_target'] for r in reports['after']['captures']),
              'same_camera_cases':sum(r['matched_case']['same_initial_camera'] for r in reports['after']['captures']),
              'palette_note':'Native PNGs preserve exact framebuffer pixels. GIFs exceeding 256 union colours are quantized; exact_palette metadata records precision.'}
    if not args.no_video:manifest['video']=video(args.out,args.out)
    manifest['files']=[{'path':str(p.relative_to(args.out)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(args.out.rglob('*')) if p.is_file() and (p.relative_to(args.out).parts[0]in('before','after','comparisons') or p.name in ('overview.png','before-after.png','interactive-scenery-reel.mp4'))]
    for file in manifest['files']:
        p=args.out/file['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==file['sha256']
        if p.suffix=='.png' and len(p.relative_to(args.out).parts)==3 and p.relative_to(args.out).parts[0] in ('before','after'):
            assert Image.open(p).size==(240,160),(str(p),Image.open(p).size)
    (args.out/'gallery-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k in ['counts','same_target_cases','same_camera_cases','video']},indent=2));print('FILES',len(manifest['files']),'BYTES',sum(v['bytes']for v in manifest['files']))


if __name__=='__main__':main()
