#!/usr/bin/env python3
"""Publish selected interfaces and sixty enemy studies from immutable evidence.

Native PNGs and full-rate MP4 viewing copies are copied byte-for-byte. Real
comparison boards only concatenate/crop actual captured frames; source pose
art is published separately. Only exact-palette GIFs are retained. The local
all-frames archives and superseded pilots are deliberately not published.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile

from PIL import Image, ImageDraw, ImageFont, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
FPS = 16777216 / 280896
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
BG = '#101820'
FG = '#e8c878'
FAMILIES = ('beetle','bat','spitter','slime','knight','boss')
NATIVE = (240,160)


def gif_durations(count, step=2):
    ticks=list(range(0,count,step))
    return [round(b/FPS*100)*10-round(a/FPS*100)*10
            for a,b in zip(ticks,ticks[1:]+[count])]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value,indent=2)+'\n')


def text(draw, xy, value):
    draw.fontmode='1'
    draw.text(xy,value,font=FONT,fill=FG)


def safe_path(base, rel):
    path=(Path(base)/rel).resolve()
    assert path.is_relative_to(Path(base).resolve()),('path escapes evidence folder',rel)
    return path


def exact_copy(src, dst):
    src,dst=Path(src),Path(dst)
    assert src.is_file(),src
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)
    assert sha(src)==sha(dst),(src,dst)


def copy_capture_report(source, destination, filename, approved_hashes):
    source,destination=Path(source),Path(destination)
    original=read(source/filename)
    assert original['passed']==original['total'],source
    assert not original.get('failures'),source
    assert original['rom_sha256'] in approved_hashes,('capture uses unfrozen ROM',source)
    result=copy.deepcopy(original);omitted=[];copied=set()
    for row in result['captures']:
        active=[row['image'],*row.get('native_frames',[])]
        if row.get('filmstrip'):active.append(row['filmstrip'])
        if row.get('video'):active.append(row['video'])
        archive={}
        if row.get('all_frames'):
            archive['all_frames']=row.pop('all_frames')
            archive['all_frames_note']='Local archival source only; not an active publication path.'
        if row.get('gif'):
            if row.get('gif_metadata',{}).get('exact_palette'):
                active.append(row['gif'])
            else:
                archive['gif']=row.pop('gif')
                archive['gif_note']='Omitted: complete sequence exceeds GIF palette; native PNG/MP4 remain.'
                omitted.append({'source':str(source),'capture':row['name'],
                                'colors':row.get('gif_metadata',{}).get('colour_count')})
        elif row.get('gif_metadata') and not row['gif_metadata'].get('exact_palette'):
            omitted.append({'source':str(source),'capture':row['name'],
                            'colors':row['gif_metadata'].get('colour_count')})
        for rel in active:
            src=safe_path(source,rel);dst=safe_path(destination,rel)
            exact_copy(src,dst);copied.add(rel)
        for rel in [row['image'],*row.get('native_frames',[])]:
            with Image.open(destination/rel) as image:
                assert image.size==NATIVE,('not native framebuffer',destination/rel,image.size)
        if archive:row['archival_formats']=archive
    result['publication']={
        'source_report_sha256':sha(source/filename),
        'source_commit':approved_hashes[original['rom_sha256']]['source_commit'],
        'variant':approved_hashes[original['rom_sha256']]['variant'],
        'method':'Active media are unchanged copies of approved frozen-ROM mGBA output. Local raw all-frame directories and inexact GIFs are archival only.',
    }
    destination.mkdir(parents=True,exist_ok=True)
    write(destination/filename,result)
    return {'path':str(destination),'report':filename,'captures':len(result['captures']),
            'passed':result['passed'],'total':result['total'],'files_copied':len(copied),
            'rom_sha256':result['rom_sha256'],'omitted_gifs':omitted}


def copy_source_gallery(work, out, builds):
    source=work/'source-gallery';manifest=read(source/'source-manifest.json')
    assert manifest.get('source_only') and manifest['concept_count']==60
    assert manifest['frame_count']>=640,('stale pre-north source gallery',manifest['frame_count'])
    for rel,expected in manifest['files'].items():
        expected=expected['sha256'] if isinstance(expected,dict) else expected
        assert sha(safe_path(source,rel))==expected,('source gallery file hash',rel)
    frozen=builds[0].get('source_file_sha256',{})
    for rel,expected in manifest['source_sha256'].items():
        assert sha(ROOT/rel)==expected,('stale source painter gallery',rel)
        if rel in frozen:assert frozen[rel]==expected,('gallery differs from ROM source',rel)
    for family,row in manifest['animations'].items():
        assert row['exact_palette'] and row['decoded_rgb_verified'],family
    # The generator supplies its own exact source-GIF decoder proof. Copy
    # every source-native atlas/frame/README/manifest without re-encoding it.
    for path in source.rglob('*'):
        if path.is_file():exact_copy(path,out/'source'/path.relative_to(source))
    paths=[out/'source/ordinary-summary-source.png',out/'source/heavy-summary-source.png']
    images=[Image.open(p).convert('RGB') for p in paths]
    width=max(im.width for im in images)
    combined=Image.new('RGB',(width,sum(im.height for im in images)),BG)
    y=0;parts=[]
    for path,image in zip(paths,images):
        combined.paste(image,(0,y))
        assert combined.crop((0,y,image.width,y+image.height)).tobytes()==image.tobytes()
        parts.append({'source':str(path.relative_to(out)),'sha256':sha(path),
                      'rectangle':[0,y,image.width,y+image.height]})
        y+=image.height
    combined.save(out/'sixty-concepts-source.png')
    return {'source_manifest':'source/source-manifest.json','concept_count':60,
            'native_frame_count':manifest['frame_count'],
            'complete_source_cycles':{family:'source/'+row['path'] for family,row in manifest['animations'].items()},
            'combined_source_overview':{'path':'sixty-concepts-source.png','parts':parts,
                                        'note':'Unchanged concatenated SOURCE boards; not emulator images.'}}


def raw_frame(source, row, tick):
    path=safe_path(source,row['all_frames'])/f'frame-{tick:03}.png'
    with Image.open(path) as image:
        assert image.size==NATIVE,(path,image.size)
        return image.convert('RGB').copy()


def crop_bounds(row, tick):
    trace=row['trace'];state=trace[tick]
    target=state.get('target')
    if target is None:
        # Follow the last recorded physical location after defeat. This
        # changes only the viewing crop; never paint a missing actor.
        target=next((t['target'] for t in reversed(trace[:tick+1]) if t.get('target')),None)
    if target is None:return (72,40,168,120)
    x=(target['x_q16']>>16)-state['camera'][0]
    y=(target['y_q16']>>16)-(target.get('z_q16',0)>>16)-state['camera'][1]
    height=64 if row['kind']==5 else 32 if row['kind']==4 else 16
    left=max(0,min(144,x-48));top=max(0,min(80,y-(height+80)//2))
    return left,top,left+96,top+80


def concept_label(manifest,row,variant):
    kind=row['kind']
    if not 0<=kind<len(FAMILIES):return f'v{variant:02}'
    family=FAMILIES[kind]
    data=manifest['families'][family]
    if isinstance(data,dict):
        concepts=data.get('concepts')
        if concepts:return f"v{variant:02} / {concepts[variant-1]}"
    return f'v{variant:02} / '+family


def board_frame(cases, manifest, tick, cropped=False):
    width=1000 if cropped else 1200
    board=Image.new('RGB',(width,392),BG);draw=ImageDraw.Draw(board)
    clip=cases[0][2]['name'];mode='actual96x80 crops, 2x NN' if cropped else 'actual240x160 frames, unchanged'
    text(draw,(5,5),f'{clip} / {mode} / video tick {tick}')
    for i,(variant,source,row) in enumerate(cases):
        image=raw_frame(source,row,tick)
        if cropped:image=image.crop(crop_bounds(row,tick)).resize((192,160),Image.Resampling.NEAREST)
        x=i%5*(200 if cropped else 240);y=24+i//5*184
        label=concept_label(manifest,row,variant)
        # Truncate only the external review caption; native content is exact.
        while FONT.getlength(label)>(194 if cropped else 234):label=label[:-1]
        text(draw,(x+4,y+3),label)
        board.paste(image,(x+(4 if cropped else 0),y+20))
    return board


def exact_comparison_gif(cases, manifest, total, path, cropped=False, step=2):
    """One literal shared palette, preserved cadence, no quantized fallback.

    Make indexed frames lazily so long real boss recordings do not require
    retaining hundreds of RGB contact sheets at once. Pillow may hold the
    smaller indexed frames while encoding; each converted frame is verified.
    """
    ticks=list(range(0,total,step));colors=set()
    for tick in ticks:
        im=board_frame(cases,manifest,tick,cropped)
        colors.update(rgb for _,rgb in im.getcolors(im.width*im.height))
        if len(colors)>256:return {'published':False,'exact_palette':False,'colour_count_at_least':len(colors),
                                   'reason':'Union exceeds256. Native boardPNG and per-option MP4 are retained.'}
    palette=Image.new('P',(1,1));values=[v for rgb in sorted(colors) for v in rgb];palette.putpalette(values+[0]*(768-len(values)))
    lookup={rgb:i for i,rgb in enumerate(sorted(colors))}
    def indexed(tick):
        im=board_frame(cases,manifest,tick,cropped)
        converted=im.quantize(palette=palette,dither=Image.Dither.NONE)
        if converted.convert('RGB').tobytes()!=im.tobytes():
            # Explicit lookup avoids a lossy nearest-color cache collision.
            raw=im.tobytes();converted=Image.new('P',im.size);converted.putpalette(palette.getpalette())
            converted.putdata([lookup[rgb] for rgb in zip(raw[0::3],raw[1::3],raw[2::3])])
        assert converted.convert('RGB').tobytes()==im.tobytes(),(path,tick)
        return converted
    durations=gif_durations(total,step)
    first=indexed(ticks[0]);first.save(path,save_all=True,append_images=(indexed(t) for t in ticks[1:]),
                                     duration=durations,loop=0,optimize=False,disposal=2)
    # Tick captions guarantee unique review frames; verify all decoded game
    # pixels and exact displayed durations after GIF encoding.
    with Image.open(path) as gif:
        assert gif.n_frames==len(ticks),(path,gif.n_frames,len(ticks))
        for tick,duration,decoded in zip(ticks,durations,ImageSequence.Iterator(gif)):
            expected=board_frame(cases,manifest,tick,cropped)
            assert decoded.convert('RGB').tobytes()==expected.tobytes(),(path,tick,'GIF pixels')
            assert decoded.info['duration']==duration,(path,tick,'GIF duration')
    return {'published':True,'path':path.name,'exact_palette':True,'colour_count':len(colors),
            'timeline_frames':len(ticks),'video_frames':total,'sample_step':step,
            'duration_ms':sum(durations),'source_fps':FPS,'decoded_rgb_verified':True}


def enemy_comparisons(work, out, sources=None, minimum_cases=12, case_prefix='actual/enemies'):
    manifest=read(work/'source-gallery/source-manifest.json')
    sources=sources or [work/f'enemy-reviews/v{variant}' for variant in range(1,11)]
    reports=[read(s/'capture.json') for s in sources]
    by=[{row['name']:row for row in r['captures']} for r in reports]
    names=list(by[0]);assert len(names)>=minimum_cases,'Incomplete final enemy suite'
    assert all(set(rows)==set(names) for rows in by),'different enemy case sets'
    dest=out/'comparisons';dest.mkdir(exist_ok=True);comparisons={}
    for name in names:
        rows=[b[name] for b in by]
        total=rows[0]['frames'];assert all(r['frames']==total for r in rows),(name,'durations')
        # Presentation can differ; the final audit owns comparisons against
        # baseline. The positive study bodies must share their actual AI trace.
        mechanics={r['mechanics_trace_sha256'] for r in rows}
        assert len(mechanics)==1,(name,'positive profile mechanics differ')
        cases=[(i+1,source,row) for i,(source,row) in enumerate(zip(sources,rows))]
        representative=min(total-1,rows[0].get('representative_tick',total//2))
        item={'frames':total,'fps':FPS,'representative_tick':representative,
              'mechanics_trace_sha256':rows[0]['mechanics_trace_sha256'],
              'source_case':case_prefix+'/v1/capture.json',
              'method':'Only unchanged real captured frames, with captions outside game pixels. No sprite was painted or posed by this publisher.'}
        for cropped,suffix in ((False,'ten-way'),(True,'ten-way-context-2x')):
            stem=f'{name}-{suffix}';png=dest/(stem+'.png')
            image=board_frame(cases,manifest,representative,cropped);image.save(png)
            # Independently ensure every pasted screenshot/crop has its exact
            # original RGB bytes rather than trusting composition alone.
            rectangles=[]
            for i,(_,source,row) in enumerate(cases):
                original=raw_frame(source,row,representative)
                bounds=crop_bounds(row,representative) if cropped else None
                if bounds:original=original.crop(bounds).resize((192,160),Image.Resampling.NEAREST)
                x=i%5*(200 if cropped else 240)+(4 if cropped else 0);y=44+i//5*184
                assert image.crop((x,y,x+original.width,y+160)).tobytes()==original.tobytes()
                rectangles.append({'variant':i+1,'local_archival_frame':str((source/row['all_frames']/f'frame-{representative:03}.png').relative_to(work)),
                                   'archival_frame_sha256':sha(source/row['all_frames']/f'frame-{representative:03}.png'),
                                   'archival_frame_published':False,
                                   'crop':bounds,'destination':[x,y,x+original.width,y+160]})
            animation=exact_comparison_gif(cases,manifest,total,dest/(stem+'.gif'),cropped)
            if animation['published']:animation['path']='comparisons/'+animation['path']
            item['context' if cropped else 'native']={'image':'comparisons/'+png.name,'sha256':sha(png),
                                                     'rectangles':rectangles,'animation':animation}
        comparisons[name]=item
        print('COMPARISON',name,flush=True)
    return comparisons


def copy_other_reviews(work, out, approved):
    result=[]
    appearance=work/'appearance-review'
    assert (appearance/'appearance-review.json').is_file(),'Final appearance-review missing'
    result.append(copy_capture_report(appearance,out/'actual/appearance','appearance-review.json',approved))
    assert result[-1]['captures']==56,'Incomplete final nine-combination appearance review'
    for path in appearance.glob('nine-*.png'):exact_copy(path,out/'actual/appearance'/path.name)
    for name in ('README.md','legacy-save-review.json','legacy-save-review.log'):
        exact_copy(appearance/name,out/'actual/appearance'/name)
    legacy=read(appearance/'legacy-save-review.json')
    assert legacy['passed']==legacy['total'] and legacy['rom_sha256'] in approved
    result.append({'path':str(out/'actual/appearance'),'report':'legacy-save-review.json',
                   'captures':0,'passed':legacy['passed'],'total':legacy['total'],
                   'files_copied':2,'rom_sha256':legacy['rom_sha256'],'omitted_gifs':[]})
    maps=work/'map-review'
    reports=list(maps.rglob('capture.json'))
    assert reports,'Final map-review missing'
    for path in reports:
        parent=path.parent;relative=parent.relative_to(maps)
        result.append(copy_capture_report(parent,out/'actual/maps'/relative,'capture.json',approved))
    for name in ('map-feature-comparison.png','map-feature-comparison-2x.png'):
        exact_copy(maps/name,out/'actual/maps'/name)
    return result



def write_browse_pages(out):
    """Human-readable GitHub paths for every real case, without GIF reruns."""
    out=Path(out);pages=[]
    labels={
        'pursuer-behavior':'Ground pursuit with bridge depth', 'pursuer-clearing':'Unobstructed ground pursuit',
        'flyer-behavior':'Airborne hunt',
        'shooter-behavior':'Directional seed shot', 'hopper-behavior':'Squash and hop',
        'melee-behavior':'Heavy wind-up and strike', 'melee-after-menu':'Heavy after menu restoration',
        'melee-real-combat':'Real heavy combat, hurt and defeat', 'boss-ring':'Boss radial burst',
        'boss-fan-and-adds':'Boss aimed fan and summons', 'boss-lunge':'Boss lunge',
        'boss-real-defeat':'Real boss combat and defeat', 'cave-natural-group':'Natural cave encounter',
    }
    directories=[path for category in ('enemies','pursuer-clearing') for path in (out/'actual'/category).glob('v*')]
    for directory in sorted(directories,key=lambda p:(p.parent.name,int(p.name[1:]))):
        report=read(directory/'capture.json');variant=report['enemy_variant']
        title='Selected interface with existing enemies' if variant==0 else f'Enemy alternatives {variant:02}'
        if directory.parent.name=='pursuer-clearing':title=f'Unobstructed ground pursuit / alternative {variant:02}'
        lines=[f'# {title}', '', '[Main gallery](../../../README.md) · [Full capture report](capture.json)', '',
            'These are actual mGBA recordings from the frozen ROM, not source pose animations. '
            'Safe player position, inventory, health and boss-phase HP fixtures are disclosed in the report. '
            'Enemy AI state, timer, height and pose are never assigned to fabricate an action.', '',
            'Native PNGs and chronology frames retain exact game pixels. MP4 is the full-rate, lossy viewing copy. '
            'GIF links are included only when the complete sequence has an exact palette.', '',
            '| Actual action | Preview | Watch / inspect |', '| --- | --- | --- |']
        for row in report['captures']:
            name=row['name'];links=[]
            if row.get('gif'):links.append(f"[Exact GIF]({row['gif']})")
            if row.get('video'):links.append(f"[Full-rate MP4]({row['video']})")
            if row.get('filmstrip'):links.append(f"[Chronology]({row['filmstrip']})")
            lines.append(f"| {labels.get(name,name)} | [Native PNG]({row['image']}) | "+' · '.join(links)+' |')
        for row in report['captures']:
            name=row['name'];lines+=['',f'## {labels.get(name,name)}','',f"![Actual {name}]({row['image']})",'']
            links=[]
            if row.get('gif'):links.append(f"[Exact-palette animation]({row['gif']})")
            if row.get('video'):links.append(f"[Full-rate MP4]({row['video']})")
            links.append(f"[Chronology filmstrip]({row['filmstrip']})")
            lines+=[' · '.join(links),'',row.get('note','')]
            if row.get('gif_metadata') and not row['gif_metadata'].get('exact_palette'):
                lines+=['','An exact GIF is unavailable because the complete sequence exceeds 256 colors; PNG and MP4 retain the evidence.']
        path=directory/'README.md';path.write_text('\n'.join(lines)+'\n');pages.append(str(path.relative_to(out)))
    for path in sorted((out/'actual/maps').rglob('capture.json')):
        directory=path.parent;report=read(path)
        depth=len(directory.relative_to(out).parts)
        back='../'*depth+'README.md'
        lines=['# Actual map and location-marker review','',f'[Main gallery]({back}) · [Full capture report](capture.json)','',
            'Native frames show the adopted graph overview and chamber zoom, with real generated event positions. '
            'Map ownership, completion and safe-player fixtures are stated in each case. No unknown event position is invented.','']
        if (directory/'map-feature-comparison.png').exists():
            lines+=['![Overview, room and event-location comparisons](map-feature-comparison.png)','',
                    '[Integer 2× comparison](map-feature-comparison-2x.png)','']
        lines+=['| Case | Actual pixels |','| --- | --- |']
        for row in report['captures']:
            links=[f"[Native PNG]({row['image']})"]
            if row.get('filmstrip'):links.append(f"[Chronology]({row['filmstrip']})")
            if row.get('video'):links.append(f"[MP4]({row['video']})")
            if row.get('gif'):links.append(f"[Exact GIF]({row['gif']})")
            lines.append(f"| {row['name']} | "+' · '.join(links)+' |')
        target=directory/'README.md';target.write_text('\n'.join(lines)+'\n');pages.append(str(target.relative_to(out)))
    summary=out/'validation/publication-summary.json'
    if summary.exists():
        value=read(summary);value['browse_pages']=pages;write(summary,value)
    return pages



def publish_supplement(work,out):
    """Add an unobstructed natural pursuer case without touching main media.

    The original132 cases remain immutable depth/behavior evidence. This adds
    ten separately recorded clearing encounters so legs and contact can also
    be inspected without bridge-rail occlusion.
    """
    builds=read(work/'builds.json');assert len(builds)==11
    approved={b['rom_sha256']:b for b in builds}
    source_commit=builds[0]['source_commit']
    destination=out/'validation/publication-summary.json'
    summary=read(destination);assert summary['source_commit']==source_commit
    reviews=[];sources=[]
    for variant in range(1,11):
        src=work/f'pursuer-clearing/v{variant}'
        report=read(src/'capture.json')
        assert len(report['captures'])==1 and report['captures'][0]['name']=='pursuer-clearing'
        assert report['enemy_variant']==variant
        samples=report['captures'][0].get('unobstructed_terrain_samples',[])
        assert len(samples)==report['captures'][0]['frames'] and all(samples),('clearing terrain sample failure',variant)
        row=copy_capture_report(src,out/f'actual/pursuer-clearing/v{variant}','capture.json',approved)
        row['path']=str(Path(row['path']).relative_to(out));row['supplement']='pursuer-clearing'
        reviews.append(row);sources.append(src)
    comparison=enemy_comparisons(work,out,sources,minimum_cases=1,case_prefix='actual/pursuer-clearing')
    primary=[r for r in summary['actual_reviews'] if not r.get('supplement')]
    summary['primary_counts']={'captures':sum(r['captures'] for r in primary),
                               'passed':sum(r['passed'] for r in primary),
                               'total':sum(r['total'] for r in primary)}
    summary['actual_reviews']=[r for r in summary['actual_reviews'] if r.get('supplement')!='pursuer-clearing']+reviews
    summary['comparisons'].update(comparison)
    summary.setdefault('supplemental_counts',{})['pursuer-clearing']={
        'captures':sum(r['captures'] for r in reviews),'passed':sum(r['passed'] for r in reviews),
        'total':sum(r['total'] for r in reviews),
        'note':'Natural clearing encounter; original bridge-depth cases remain unchanged.',
        'trace_parity':'All ten positive-profile mechanics trace hashes equal for this case.',
    }
    summary['captures']=sum(r['captures'] for r in summary['actual_reviews'])
    summary['runtime_passed']=sum(r['passed'] for r in summary['actual_reviews'])
    summary['runtime_total']=sum(r['total'] for r in summary['actual_reviews'])
    summary['quantized_gifs_omitted']=sum((r['omitted_gifs'] for r in summary['actual_reviews']),[])
    write(destination,summary);write_browse_pages(out)
    for name in ('pursuer-clearing-summary.json','pursuer-clearing-status.json','pursuer-clearing-batch.log',
                 'pursuer-clearing-mechanics.json','enemy-runtime-review.md'):
        if (work/name).is_file():exact_copy(work/name,out/'validation'/name)
    return {'supplemental_counts':summary['supplemental_counts'],'overall_captures':summary['captures'],
            'overall_passed':summary['runtime_passed'],'overall_total':summary['runtime_total'],
            'comparison_cases':list(comparison)}


def release_roms(work, release, builds, branch, gallery):
    release.mkdir(parents=True,exist_ok=True);names={}
    for build in builds:
        variant=build['variant'];filename='00-selected-ui-existing-enemies.gba' if variant==0 else f'enemy-study-{variant:02}.gba'
        source=work/f'v{variant}/bartgame.gba'
        assert sha(source)==build['rom_sha256'],source
        exact_copy(source,release/filename);names[variant]=filename
    write(release/'builds.json',builds)
    (release/'ROM-SHA256.txt').write_text(''.join(f'{sha(release/name)}  {name}\n' for name in names.values()))
    (release/'README.txt').write_text(f'''BARTGAME - selected interface and ten enemy-art comparison builds

00 uses the selected HUD, item layout1, map layout2 and title Options, with
existing enemy art. enemy-study01..10 each select one alternative per current
six enemy mechanics: sixty alternatives in ten playable comparison ROMs.
Enemy forms remain proposals; names do not change mechanics. No commercial ROM
is needed. Source: {builds[0]['source_commit']}

Title: select Options; Up/Down chooses Style or Colors; Left/Right cycles;
A/B/Start keeps the choice and returns. Settings survive reset independently
of run saves. Menu/dialogue shapes and colors are independent; HUD is fixed.
Start opens/closes inventory; R cycles pages; A/B/L assign tools. Map A zooms,
B returns. D-pad browses. The minimap and equipped-item ammo stay on the HUD.

Normal build: make -j4 (BART_UI=6 BART_MENU=1 BART_ENEMY=0).
Study build: make -j4 BART_ENEMY=1..10 BUILD=build_enemy_N.
Gallery: https://github.com/natertott/bartgame/blob/{branch}/{gallery}/README.md
''')
    archive=release/'selected-ui-and-ten-enemy-studies.zip'
    contents=[*names.values(),'README.txt','ROM-SHA256.txt','builds.json']
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for rel in contents:z.write(release/rel,rel)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and len([f for f in z.namelist() if f.endswith('.gba')])==11
        assert all(hashlib.sha256(z.read(f)).hexdigest()==sha(release/f) for f in z.namelist())
    (release/'SHA256SUMS.txt').write_text(''.join(f'{sha(release/name)}  {name}\n' for name in [*names.values(),archive.name]))
    return names,archive.name


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('work','out','release'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--branch',required=True);p.add_argument('--browse-only',action='store_true',help='Write per-ROM/map GitHub browse pages without copying or encoding media.');p.add_argument('--supplement-only',action='store_true',help='Add the ten unobstructed pursuer-clearing reports and comparisons; retain existing source/main media/ROMs.');a=p.parse_args()
    work,out,release=a.work.resolve(),a.out.resolve(),a.release.resolve()
    assert not(a.browse_only and a.supplement_only),'Choose one postprocessing mode'
    if a.browse_only:
        print(json.dumps({'browse_pages':write_browse_pages(out)},indent=2));return 0
    if a.supplement_only:
        print(json.dumps(publish_supplement(work,out),indent=2));return 0
    builds=read(work/'builds.json');assert len(builds)==11
    assert sorted(b['variant'] for b in builds)==list(range(11))
    builds.sort(key=lambda b:b['variant']);source=builds[0]['source_commit']
    assert all(b['source_commit']==source for b in builds),'Mixed source freeze'
    audit=read(work/'audit-summary.json');assert audit['passed']==audit['total']
    capture_summary=read(work/'enemy-review-summary.json')
    assert capture_summary['source_commit']==source and capture_summary['all_passed']
    assert capture_summary['captures']==132 and capture_summary['passed']==capture_summary['total']
    approved={b['rom_sha256']:b for b in builds};out.mkdir(parents=True,exist_ok=True)
    validation=out/'validation';validation.mkdir(exist_ok=True)
    for name in ('builds.json','build-all.log','default-restore.log','enemy-audit.json','enemy-audit-summary.json',
                 'audit.json','audit-summary.json','enemy-mechanics.json','enemy-mechanics.md',
                 'final-runtime-verification.json','review-summary.json','runtime-review.md',
                 'enemy-review-summary.json','map-review-summary.json','baseline-vs-positive-mechanics.json'):
        if (work/name).is_file():exact_copy(work/name,validation/name)
    # These native palette diagnostics are explicitly SOURCE composites on
    # old immutable mGBA backgrounds. Exclude temporary seed reviews/pilots.
    palette_proofs=work/'palette-review'
    for pattern in ('all30-*-palette-comparison-source.png','*-all-pose-palette-source.png',
                    'enemy-palette-swatches-source.png','source-composite-provenance.json'):
        for path in palette_proofs.glob(pattern):
            exact_copy(path,validation/'palette-review'/path.name)
    for variant in range(11):
        frozen=read(work/f'v{variant}/freeze.json')
        assert frozen['rom_sha256']==builds[variant]['rom_sha256']
        exact_copy(work/f'v{variant}/freeze.json',validation/f'freezes/v{variant}.json')
    source_summary=copy_source_gallery(work,out,builds)
    reviews=[]
    for variant in range(11):
        reviews.append(copy_capture_report(work/f'enemy-reviews/v{variant}',out/f'actual/enemies/v{variant}','capture.json',approved))
    reviews+=copy_other_reviews(work,out,approved)
    for review in reviews:review['path']=str(Path(review['path']).relative_to(out))
    comparisons=enemy_comparisons(work,out)
    names,archive=release_roms(work,release,builds,a.branch,str(out.relative_to(REPO)))
    summary={'source_commit':source,'variants':builds,'rom_files':names,'zip':archive,
             'source_art':source_summary,'actual_reviews':reviews,'comparisons':comparisons,
             'captures':sum(r['captures'] for r in reviews),'runtime_passed':sum(r['passed'] for r in reviews),
             'runtime_total':sum(r['total'] for r in reviews),'quantized_gifs_omitted':sum((r['omitted_gifs'] for r in reviews),[]),
             'format_policy':'PNG/frame/filmstrip copies exact; MP4 full-rate lossy viewing copies; GIF exact-only with recorded cadence. Local raw all-frame archives are not active published paths. Source art is separate from actual mGBA output.'}
    write(validation/'publication-summary.json',summary)
    write_browse_pages(out)
    # Main README is editorial and parent-owned. Hash every current artifact
    # and ROM; rerun this final manifest after any parent README additions.
    files={}
    for base in (out,release):
        for path in sorted(base.rglob('*')):
            if path.is_file() and path!=validation/'publication-manifest.json':
                files[str(path.relative_to(REPO))]={'sha256':sha(path),'bytes':path.stat().st_size}
    write(validation/'publication-manifest.json',{'source_commit':source,'files':files,
          'note':'Exact file hashes excluding this manifest. Parent may regenerate after editorial documentation.'})
    print(json.dumps({'source':source,'captures':summary['captures'],'runtime':f"{summary['runtime_passed']}/{summary['runtime_total']}",
                      'roms':len(names),'zip':archive,'comparison_cases':len(comparisons),'files':len(files)},indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
