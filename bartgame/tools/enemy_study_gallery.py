#!/usr/bin/env python3
"""Build exact native source-art comparisons for all sixty enemy proposals.

These are labelled SOURCE pose boards, not mGBA footage or AI simulations.
Each authored pose is held for the same review duration, independently of
gameplay timing. The real-run gallery and combat traces are separate evidence.
"""
import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'art'))
import enemy_studies as STUDIES
import enemy_studies_palette as ENEMY_PALETTE
import reboot_actors as ACTORS
import reboot_core as CORE

CONTRACT_PATH = ROOT / 'art/reboot_contracts.json'
CONTRACTS = {s['name']: s for s in json.loads(CONTRACT_PATH.read_text())['sheets']}
FAMILIES = STUDIES.FAMILIES
VALID_SIZES = {(8,8),(16,16),(32,32),(64,64),(16,8),(32,8),(32,16),
               (64,32),(8,16),(8,32),(16,32),(32,64)}
MECHANICS = {'beetle':'Ground pursuer', 'bat':'Airborne hunter',
             'spitter':'Directional shooter', 'slime':'Compress-and-hop',
             'knight':'Heavy melee striker', 'boss':'Three-phase boss'}
CANONICAL = {'beetle':'walk_s1','bat':'fly1','spitter':'idle_s','slime':'idle',
             'knight':'idle_s','boss':'pulse1'}
BG = '#101820'
PANEL = '#283838'
FIELD = '#485858'
FG = '#f0d898'
DIM = '#b0c0a0'
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
SHA = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def text(draw, xy, value, fill=FG):
    draw.fontmode = '1'  # Crisp labels, with no new antialiased colors.
    draw.text(xy, value, font=FONT, fill=fill)


def wrap(value, max_width):
    lines = []
    line = ''
    for word in value.split():
        candidate = (line+' '+word).strip()
        if line and FONT.getlength(candidate) > max_width:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines


def canvas_size(family):
    # In particular, the current boss is 32x64, while its historical ID
    # contract still describes 32x32. Actual authoring overrides win.
    size = ACTORS.SIZES.get(family, (CONTRACTS[family]['w'], CONTRACTS[family]['h']))
    declared = getattr(STUDIES.module_for(family), 'SIZES', {}).get(family)
    assert not declared or tuple(declared) == tuple(size), (family, declared, size)
    assert size in VALID_SIZES, (family, size)
    return size


def frame_names(family):
    base = tuple(CONTRACTS[family]['frames'])
    extra = tuple(getattr(STUDIES.module_for(family),'EXTRA_FRAMES',{}).get(family,()))
    assert not set(base).intersection(extra), family
    return base + extra


def palette(family):
    # All gallery alternatives are positive profiles. Runtime gives these
    # three bodies the dedicated items/OBJ10 actor bank; it deliberately
    # preserves shared bugs/foliage for Bloom's cloak and carried bushes.
    if ENEMY_PALETTE.applies_to(family):
        colors=ENEMY_PALETTE.colors()
        assert len(colors)==16
        assert all(all(int(color[i:i+2],16)%8==0 for i in (1,3,5)) for color in colors)
        return 'items', 'enemy_studies_palette.colors()', colors
    slot = CONTRACTS[family]['pal']
    bank = ACTORS.BANK_ALIASES[slot]
    colors = CORE.PALETTES[bank]
    assert len(colors) == 16
    assert all(all(int(color[i:i+2],16)%8 == 0 for i in (1,3,5)) for color in colors)
    return slot, bank, colors


def pose_sequence(family):
    """Review order covers every authored body pose; not an AI timeline."""
    if family == 'spitter':
        seq = [f'{action}_{face}' for face in ('s','e','n')
               for action in ('idle','walk','charge','spit')]
    elif family == 'knight':
        seq = []
        for face in ('s','e','n'):
            seq += [f'idle_{face}',f'walk_{face}1',f'walk_{face}2',
                    f'windup_{face}',f'atk_{face}',f'strike_{face}',
                    f'recover_{face}',f'hurt_{face}']
    elif family == 'boss':
        seq = ['pulse1','pulse2','charge1','charge2','release1','release2',
               'spawn1','spawn2','lunge1','lunge2','hurt','dying1','dying2']
    elif family == 'bat':
        seq = ['rest','fly1','fly2']
    elif family == 'slime':
        seq = ['idle','squash','jump']
    else:
        seq = list(frame_names(family))
    assert set(seq) == set(frame_names(family)), (family,set(seq)^set(frame_names(family)))
    return seq


def exact_gif(frames, pose_ms, path):
    """Literal RGB union palette: fail rather than publish a quantized GIF."""
    colors = sorted(set(rgb for frame in frames for _,rgb in frame.getcolors(frame.width*frame.height)))
    assert len(colors) <= 256, (path, len(colors))
    lookup = {rgb:i for i,rgb in enumerate(colors)}
    raw_palette = [channel for rgb in colors for channel in rgb]
    raw_palette += [0]*(768-len(raw_palette))
    converted = []
    for frame in frames:
        p = Image.new('P',frame.size)
        p.putpalette(raw_palette)
        pixels=frame.tobytes()
        p.putdata([lookup[rgb] for rgb in zip(pixels[0::3],pixels[1::3],pixels[2::3])])
        converted.append(p)
    converted[0].save(path,save_all=True,append_images=converted[1:],
                      duration=pose_ms,loop=0,optimize=False,disposal=2)
    with Image.open(path) as gif:
        decoded = [(im.convert('RGB').copy(),im.info['duration']) for im in ImageSequence.Iterator(gif)]
    # The phase caption changes even for intentional old/new pose aliases.
    assert len(decoded) == len(frames), (path,len(decoded),len(frames))
    assert all(a.tobytes() == b.tobytes() and duration == pose_ms
               for (a,duration),b in zip(decoded,frames)), path
    return {'exact_palette':True,'colors':len(colors),'frames':len(frames),
            'pose_duration_ms':pose_ms,'duration_ms':pose_ms*len(frames),
            'decoded_rgb_verified':True}


def render_pose(family,variant,name):
    image = STUDIES.frame(family,variant,name)
    assert image.mode == 'P' and image.size == canvas_size(family), (family,variant,name,image.mode,image.size)
    assert set(image.tobytes()) <= set(range(16)), (family,variant,name)
    assert image.getbbox(), (family,variant,name,'empty')
    return image


def rgba(image,family):
    return CORE.rgba(image,palette(family)[2])


def paste_sprite(board,image,xy,scale=1):
    if scale != 1:
        image=image.resize((image.width*scale,image.height*scale),Image.Resampling.NEAREST)
    board.paste(image,xy,image)


def silhouette(image):
    result = Image.new('RGBA',image.size,(0,0,0,0))
    result.putdata([(240,232,192,255) if value else (0,0,0,0) for value in image.tobytes()])
    return result


def gray(image):
    result = image.convert('L').convert('RGBA')
    result.putalpha(image.getchannel('A'))
    return result


def tile_height(family):
    return canvas_size(family)[1]*3+68


def draw_concept(board,x,y,family,variant,name,metadata):
    d=ImageDraw.Draw(board)
    w,h=canvas_size(family)
    image=render_pose(family,variant,name)
    graphic=rgba(image,family)
    text(d,(x+7,y+2),f'v{variant:02} / {name}')
    # Explanatory text remains outside both native and enlarged art rectangles.
    for i,line in enumerate(wrap(metadata['concepts'][variant-1],186)):
        text(d,(x+7,y+17+i*13),line,DIM)
    top=y+48
    d.rectangle((x+7,top-1,x+9+w*3,top+h*3+1),fill=FIELD)
    paste_sprite(board,graphic,(x+8,top),3)
    native_x=x+126 if w<=16 else x+118
    d.rectangle((native_x-2,top+h*3-h-2,native_x+w+1,top+h*3+1),fill=FIELD)
    paste_sprite(board,graphic,(native_x,top+h*3-h))
    paste_sprite(board,silhouette(image),(x+166,top+h*3-h))
    text(d,(x+8,top+h*3+4),'3x',DIM)
    text(d,(native_x,top+h*3+4),'1x',DIM)
    text(d,(x+164,top+h*3+4),'sil',DIM)


def family_board(family,name,metadata,pose_ms=None):
    header=50
    height=tile_height(family)
    board=Image.new('RGB',(1000,header+height*2),BG)
    d=ImageDraw.Draw(board)
    text(d,(8,5),f'{MECHANICS[family]} / internal ID {family} / TEN SOURCE alternatives / not emulator output')
    subtitle=f'POSE {name} / '+(f'{pose_ms} ms per pose for review, NOT AI timing' if pose_ms else 'Native 1x + 3x nearest-neighbour + silhouette')
    text(d,(8,23),subtitle,DIM)
    for variant in range(1,11):
        x=(variant-1)%5*200;y=header+(variant-1)//5*height
        draw_concept(board,x,y,family,variant,name,metadata)
    return board


def summary_board(families,metadata):
    heights=[36+tile_height(f)*2 for f in families]
    board=Image.new('RGB',(1000,48+sum(heights)),BG)
    d=ImageDraw.Draw(board)
    text(d,(8,6),'SOURCE ART / 1x + 3x and silhouettes / native GBA proposals, not mGBA output')
    text(d,(8,24),'Compare v01-v10 within each mechanic. The concept labels are working descriptions, not enemy names.',DIM)
    top=48
    for family,height in zip(families,heights):
        d.rectangle((0,top,999,top+28),fill=PANEL)
        text(d,(8,top+6),f'{MECHANICS[family]} / {family} / {canvas_size(family)[0]}x{canvas_size(family)[1]} canvas')
        for variant in range(1,11):
            x=(variant-1)%5*200;y=top+36+(variant-1)//5*tile_height(family)
            draw_concept(board,x,y,family,variant,CANONICAL[family],metadata[family])
        top += height
    return board


def all_frames_atlas(family,variant,metadata):
    refs=[(family,name) for name in frame_names(family)]
    if family=='knight':refs.extend(('ksword',name) for name in frame_names('ksword'))
    if family=='spitter':refs.append(('proj','seed'))
    w,h=canvas_size(family)
    cellw=max(148,w*3+w+22)
    cellh=h*3+46
    cols=6
    rows=math.ceil(len(refs)/cols)
    board=Image.new('RGB',(cols*cellw,52+rows*cellh),BG);d=ImageDraw.Draw(board)
    text(d,(8,5),f'SOURCE ALL FRAMES / {MECHANICS[family]} v{variant:02} / {metadata["concepts"][variant-1]}')
    text(d,(8,23),'Complete body contract + appended poses; 1x and 3x. Separate weapon/projectile companions are labelled.',DIM)
    for n,(sheet,name) in enumerate(refs):
        x=n%cols*cellw;y=52+n//cols*cellh
        image=render_pose(sheet,variant,name);graphic=rgba(image,sheet)
        text(d,(x+5,y+3),(sheet+' / ' if sheet!=family else '')+name)
        by=y+22+(h-image.height)*3
        paste_sprite(board,graphic,(x+6,by),3)
        paste_sprite(board,graphic,(x+image.width*3+16,y+22+h*3-image.height))
        text(d,(x+6,y+25+h*3),'3x / 1x',DIM)
    return board


def diagnostic_board(family,metadata):
    # Native context copies sit below3x art. Tall bosses must reserve their
    # complete64px height there rather than clipping the second review row.
    w,h=canvas_size(family);ch=max(h*3+66,h*4+40);cw=220
    board=Image.new('RGB',(cw*5,42+ch*2),BG);d=ImageDraw.Draw(board)
    text(d,(8,5),f'SOURCE value / silhouette / {MECHANICS[family]} / native 1x and 3x, not a game scene')
    text(d,(8,23),'Diagnostic fields: Drain, healthy ground, blight and cave values. No screenshot grading.',DIM)
    fields=[CORE.PALETTES[bank][ink] for bank,ink in [('drain',4),('ground',4),('blight',4),('stone',3)]]
    for v in range(1,11):
        x=(v-1)%5*cw;y=42+(v-1)//5*ch
        image=render_pose(family,v,CANONICAL[family]);graphic=rgba(image,family)
        text(d,(x+5,y+3),f'v{v:02} / {family}')
        paste_sprite(board,gray(graphic),(x+6,y+21),3)
        paste_sprite(board,silhouette(image),(x+108,y+21),1)
        # Four unscaled native copies on deliberately plain diagnostic fields.
        for i,color in enumerate(fields):
            bx=x+4+i*(w+5)
            by=y+25+h*3
            d.rectangle((bx,by,bx+w+3,by+h+3),fill=color)
            paste_sprite(board,graphic,(bx+2,by+2))
    return board


def companions_board(metadata):
    board=Image.new('RGB',(1000,310),BG);d=ImageDraw.Draw(board)
    text(d,(8,5),'SOURCE companion sprites / native 1x + 3x / not a combat/weapon positioning simulation')
    text(d,(8,23),'Melee weapons (both orientations) and directional-shooter seed. Shared boss spores/hurt/death FX stay existing art.',DIM)
    for v in range(1,11):
        x=(v-1)%5*200;y=48+(v-1)//5*130
        text(d,(x+6,y+3),f'v{v:02} / weapon + seed')
        for col,(family,name) in enumerate([('ksword','blade_e'),('ksword','blade_s'),('proj','seed')]):
            im=render_pose(family,v,name);graphic=rgba(im,family)
            paste_sprite(board,graphic,(x+7+col*63,y+23),3)
            paste_sprite(board,graphic,(x+7+col*63,y+78))
            text(d,(x+5+col*63,y+99),name,DIM)
    return board


def write_readme(out,report,metadata):
    lines=['# Sixty native enemy source-art proposals','','These are **SOURCE pose studies**, not emulator footage or AI simulations. Each of six current enemy mechanics has ten alternatives. Working concept labels are secondary to the existing mechanic; no body form or enemy name is adopted here.','','Every drawing starts at its actual legal GBA canvas size, with indices 0–15 and sixteen RGB555 inks including transparent zero. Native indexed and RGBA PNGs are retained. Enlargements are integer 3× nearest-neighbor; labels stay outside game art.','','**Final comparison palette:** the ground pursuer, airborne hunter and compress-and-hop bodies use the approved actor-only `enemy_studies_palette.colors()` bank, compiled as the existing `items` / OBJ10 alias for positive enemy profiles. That bank was chosen after 120 source comparisons on actual background crops. The original shared bugs/foliage bank stays intact for the cloak and carried bushes; the other three enemy material banks and companion palettes remain unchanged. Earlier painter-specific foliage boards are historical authoring diagnostics, not the final colors shown here. The source manifest records the exact palette API hash and every frame’s input bank.','','[Forty ordinary concepts](ordinary-summary-source.png) · [Twenty heavy/boss concepts](heavy-summary-source.png) · [Companion weapons/projectile](companions-source.png) · [Native coverage and hashes](source-manifest.json)','','## Complete source pose cycles','','Every animated board shows all authored body frames, including appended anticipation, melee recovery and boss phases. Each pose has a fixed '+str(report['pose_duration_ms'])+' ms review hold. This deliberately does **not** claim to reproduce AI state duration, actual attack damage windows, real movement, hurt blinking or physics. The separate mGBA gallery provides runtime evidence.','','| Mechanic / internal sheet ID | Native canvas | Body frames per option | Ten alternatives | Complete pose cycle | Value/silhouette check |','| --- | --- | ---: | --- | --- | --- |']
    for family in FAMILIES:
        w,h=canvas_size(family)
        lines.append(f'| {MECHANICS[family]} / `{family}` | {w}×{h} | {len(frame_names(family))} | [PNG]({family}-ten-source.png) | [GIF]({family}-all-poses-source.gif) | [PNG]({family}-diagnostic-source.png) |')
    lines += ['','The boss is drawn on its **actual 32×64 current canvas**, not the obsolete 32×32 dimensions recorded with its historical sheet ID. Shared damage/death effects are existing engine art; body suites do not invent ordinary death poses or weaknesses. The knight retains intentional old `atk` / new `strike` pose aliases.','','## Full per-option frame atlases','','Atlases include native and 3× body poses, plus separately labelled weapon/seed companions where applicable. Each native folder also contains indexed PNGs and exact RGBA PNGs for every pose.','','| Mechanic | Full authored suites |','| --- | --- |']
    for family in FAMILIES:
        links=' · '.join(f'[v{v:02}](atlases/{family}-v{v:02}-all-frames-source.png)' for v in range(1,11))
        lines.append(f'| {MECHANICS[family]} | {links} |')
    lines += ['','## Form choices by mechanic','','These notes explain the intended visual analogy; they are not claims about new mechanics or exclusive weak points.']
    for family in FAMILIES:
        lines += ['',f'### {MECHANICS[family]} / `{family}`','','| Option | Working form | Animation/recognition intent |','| --- | --- | --- |']
        for v,(name,note) in enumerate(zip(metadata[family]['concepts'],metadata[family]['notes']),1):
            lines.append(f'| v{v:02} | {name} | {note} |')
    lines += ['','## Validation scope','','All '+str(report['frame_count'])+' authored body/companion frame instances are validated for legal geometry, index range, existing palette roles and exact native PNG decoding. All six GIFs round-trip to their source RGB boards with exact union palettes; no GIF is color-quantized. Source code hashes, per-frame index/RGBA hashes, PNG hashes, original/appended frame lists and full coverage are in the manifest.','','Native silhouette/value diagnostics use quiet swatches, not fabricated game screenshots. These checks establish encoding and source completeness, **not** human recognition, balanced mechanics or a winning art choice. Actual terrain/combat/input evidence and final adoption status belong to the parent review.']
    (out/'README.md').write_text('\n'.join(lines)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--pose-ms',type=int,default=150)
    args=parser.parse_args()
    assert args.pose_ms>=50 and args.pose_ms%10==0, 'GIF hold must be a multiple of10ms, at least50ms'
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    (out/'atlases').mkdir(exist_ok=True)
    source_paths=[ROOT/'art'/name for name in ('enemy_studies.py','enemy_studies_small.py','enemy_studies_soft.py','enemy_studies_heavy.py','enemy_studies_palette.py','reboot_actors.py','reboot_core.py','reboot_contracts.json')]
    source_paths.append(Path(__file__).resolve())
    source_hashes={str(p.relative_to(ROOT)):SHA(p) for p in source_paths}
    metadata=STUDIES.concepts()
    report={'method':__doc__,'git_base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'provenance_note':'Actual source inputs are pinned by SHA256 below. The git base can predate uncommitted authoring files; ROM freeze/capture provenance is separate.',
            'source_sha256':source_hashes,'pose_duration_ms':args.pose_ms,'source_only':True,
            'palette_policy':{'approved_for_positive_profiles':True,'families':list(ENEMY_PALETTE.FAMILIES),
                'api':'enemy_studies_palette.colors()','source_sha256':source_hashes['art/enemy_studies_palette.py'],
                'physical_obj_alias':'items','physical_obj_slot':10,
                'protected_shared_bank':'Original bugs/foliage remains unchanged for cloak and carried bushes.',
                'basis':'120 source comparisons on actual background crops; distinct from new actual mGBA evidence.'},
            'concept_count':60,'families':{},'frames':[],'animations':{},'files':{}}
    refs=[(family,name) for family in FAMILIES for name in frame_names(family)]
    refs += [('ksword',name) for name in frame_names('ksword')] + [('proj','seed')]
    for family in FAMILIES:
        base=list(CONTRACTS[family]['frames']);extra=list(getattr(STUDIES.module_for(family),'EXTRA_FRAMES',{}).get(family,()))
        slot,bank,colors=palette(family)
        report['families'][family]={'mechanic':MECHANICS[family],'canvas':canvas_size(family),
                                     'palette_slot':slot,'palette_source':bank,'palette_rgb555':colors,
                                     'original_frames':base,'appended_frames':extra,'review_sequence':pose_sequence(family),
                                     **metadata[family]}
        canonical_hashes=[hashlib.sha256(render_pose(family,v,CANONICAL[family]).tobytes()).hexdigest() for v in range(1,11)]
        assert len(set(canonical_hashes))==10,(family,'duplicate concepts')
        family_board(family,CANONICAL[family],metadata[family]).save(out/f'{family}-ten-source.png')
        frames=[family_board(family,name,metadata[family],args.pose_ms) for name in pose_sequence(family)]
        p=out/f'{family}-all-poses-source.gif'
        report['animations'][family]={'path':p.name,'pose_names':pose_sequence(family),**exact_gif(frames,args.pose_ms,p)}
        diagnostic_board(family,metadata[family]).save(out/f'{family}-diagnostic-source.png')
        for variant in range(1,11):
            all_frames_atlas(family,variant,metadata[family]).save(out/'atlases'/f'{family}-v{variant:02}-all-frames-source.png')
    for family,name in refs:
        slot,bank,colors=palette(family)
        raw_palette=[channel for color in colors for channel in CORE.rgb(color)]
        raw_palette += [0]*(768-len(raw_palette))
        for variant in range(1,11):
            image=render_pose(family,variant,name);graphic=rgba(image,family)
            dst=out/'native'/family/f'v{variant:02}';dst.mkdir(parents=True,exist_ok=True)
            pi=dst/f'{name}-indexed.png';pr=dst/f'{name}.png'
            indexed=image.copy();indexed.putpalette(raw_palette);indexed.save(pi,transparency=0)
            graphic.save(pr)
            assert Image.open(pi).convert('RGBA').tobytes()==graphic.tobytes(), pi
            assert Image.open(pr).convert('RGBA').tobytes()==graphic.tobytes(), pr
            report['frames'].append({'family':family,'variant':variant,'name':name,'canvas':image.size,
                'palette_slot':slot,'palette_source':bank,'palette_sha256':hashlib.sha256(json.dumps(colors).encode()).hexdigest(),
                'indexed_sha256':hashlib.sha256(image.tobytes()).hexdigest(),'rgba_sha256':hashlib.sha256(graphic.tobytes()).hexdigest(),
                'native_indexed_png':str(pi.relative_to(out)),'native_rgba_png':str(pr.relative_to(out)),
                'opaque_pixels':sum(bool(v) for v in image.tobytes()),'indices':sorted(set(image.tobytes())),
                'bounds':image.getbbox(),'rgba_roundtrip_verified':True})
    summary_board(FAMILIES[:4],metadata).save(out/'ordinary-summary-source.png')
    summary_board(FAMILIES[4:],metadata).save(out/'heavy-summary-source.png')
    companions_board(metadata).save(out/'companions-source.png')
    report['frame_count']=len(report['frames'])
    expected=10*len(refs)
    assert report['frame_count']==expected
    for rel,digest in source_hashes.items():assert SHA(ROOT/rel)==digest,('source changed during gallery',rel)
    write_readme(out,report,metadata)
    report['files']={str(p.relative_to(out)):{'sha256':SHA(p),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file() and p.name!='source-manifest.json'}
    (out/'source-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'concepts':report['concept_count'],'native_frame_instances':report['frame_count'],
                      'gifs':len(report['animations']),'files':len(report['files']),
                      'source_only':True,'out':str(out)}))


if __name__=='__main__':
    main()
