"""Enemy-only material bank proposal and source-composite readability proof.

This module does NOT alter palettes or sheets on import. Integration must give
only beetle/bat/slime their own bank: the existing bugs bank also colors the
Petal Cloak and carried bushes. Backgrounds and protected items stay exact.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont
import reboot_core as C

FAMILIES = ('beetle', 'bat', 'slime')
ORIGINAL = tuple(C.PALETTES['foliage'])
# 0 transparent;1 moving contour;2..7 green ramp;8..12 warm organic/wood;
# 13 cool recess;14 cool body plane;15 ivory material/eye/specular.
BUGS_STUDY_PALETTE = (
    '#000000', '#101820', '#182830', '#204840',
    '#386858', '#508870', '#78a080', '#b0c898',
    '#302828', '#584030', '#886040', '#c09058',
    '#e8c880', '#284850', '#80a8a8', '#f0e8c8',
)
assert len(BUGS_STUDY_PALETTE) == 16
assert all(int(color[i:i+2],16)%8==0 for color in BUGS_STUDY_PALETTE for i in (1,3,5))


def colors():
    """Copy of the dedicated16-ink bank. No global palette mutation."""
    return list(BUGS_STUDY_PALETTE)


def applies_to(family):
    return family in FAMILIES


def _painter(family):
    if family=='slime':
        import enemy_studies_soft
        return enemy_studies_soft
    import enemy_studies_small
    return enemy_studies_small


def _image(family, variant, pose, palette):
    return C.rgba(_painter(family).frame(family,variant,pose),palette)


def _font(size=11):
    return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',size)


def write_review(out, repo=None):
    """Source sprites on immutable actual native background crops, not a run.

    Both sides use exactly the same current indexed sprite; only its proposed
    input bank differs. Background crops are exact ungraded mGBA pixels.
    """
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    repo=Path(repo) if repo else Path(__file__).resolve().parents[2]
    actual=repo/'art-review/ui-menu-exploration/actual/v1'
    scenes={
        'forest': ('hud-healthy.png',(144,36,192,76)),
        'blight': ('hud-blighted.png',(94,104,142,144)),
        'Drain': ('hud-sewer-max.png',(126,100,174,140)),
        'cave': ('hud-cave.png',(144,96,192,136)),
    }
    font=_font();caption=_font(10);records=[]
    # Primary boards: all30 concepts,2x crop plus a separate native1x pair.
    for scene,(name,bounds) in scenes.items():
        source=actual/name;captured=Image.open(source).convert('RGBA')
        assert captured.size==(240,160)
        crop=captured.crop(bounds);assert crop.size==(48,40)
        cw,ch=208,139
        board=Image.new('RGB',(cw*5,44+ch*6),'#101820');d=ImageDraw.Draw(board);d.fontmode='1'
        d.text((7,6),f'{scene}: all 30 enemy forms / original bank LEFT, actor-only proposal RIGHT',font=font,fill='#f0d898')
        d.text((7,23),'SOURCE COMPOSITES on actual mGBA background crops; 1x + 2x nearest-neighbour. NOT new emulator output.',font=caption,fill='#b0c0a0')
        for fi,family in enumerate(FAMILIES):
            pose={'beetle':'walk_s1','bat':'fly1','slime':'idle'}[family]
            module=_painter(family)
            for variant in range(1,11):
                col=(variant-1)%5;row=fi*2+(variant-1)//5;x=col*cw;y=44+row*ch
                d.text((x+4,y+2),f'{family} {variant}: {module.CONCEPTS[family][variant-1]}',font=caption,fill='#f0d898')
                rendered=[]
                for side,palette in enumerate((ORIGINAL,BUGS_STUDY_PALETTE)):
                    composite=crop.copy();a=_image(family,variant,pose,palette)
                    composite.alpha_composite(a,(16,14))
                    board.paste(composite.resize((96,80),Image.Resampling.NEAREST),(x+4+side*100,y+18))
                    board.paste(composite,(x+28+side*100,y+99))
                    rendered.append(composite)
                # Regions outside the authored sprite are exact captured pixels.
                old,new=rendered;mask=module.frame(family,variant,pose)
                for py in range(40):
                    for px in range(48):
                        occupied=16<=px<32 and 14<=py<30 and mask.getpixel((px-16,py-14))
                        if not occupied:assert old.getpixel((px,py))==new.getpixel((px,py))==crop.getpixel((px,py))
                records.append({'scene':scene,'source':str(source.relative_to(repo)),
                    'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                    'crop':list(bounds),'family':family,'variant':variant,'pose':pose,
                    'source_composite':True,'actual_run':False})
        board.save(out/f'all30-{scene}-palette-comparison-source.png')
    # Every frame is reviewed in each material context, not only an idle.
    for family in FAMILIES:
        module=_painter(family)
        names={'beetle':('walk_s1','walk_s2','walk_e1','walk_e2'),
               'bat':('rest','fly1','fly2'),'slime':('idle','squash','jump')}[family]
        bw=150+len(names)*2*38;bh=44+10*52
        atlas=Image.new('RGB',(bw,bh),'#101820');ad=ImageDraw.Draw(atlas);ad.fontmode='1'
        ad.text((6,5),f'{family}: every pose old / new / native2x inspection, SOURCE',font=caption,fill='#f0d898')
        for v in range(1,11):
            y=44+(v-1)*52;ad.text((5,y+13),f'{v}. {module.CONCEPTS[family][v-1]}',font=caption,fill='#f0d898')
            for i,pose in enumerate(names):
                for side,palette in enumerate((ORIGINAL,BUGS_STUDY_PALETTE)):
                    im=_image(family,v,pose,palette).resize((32,32),Image.Resampling.NEAREST)
                    atlas.paste(im,(150+(i*2+side)*38,y),im)
                if v==1:ad.text((150+i*76,25),pose,font=caption,fill='#b0c0a0')
        atlas.save(out/f'{family}-all-pose-palette-source.png')
    # All palette swatches are native quantized inputs, not graded screenshots.
    swatch=Image.new('RGB',(16*44,116),'#101820');sd=ImageDraw.Draw(swatch);sd.fontmode='1'
    for row,(name,palette) in enumerate((('Current shared foliage',ORIGINAL),('Proposed actor material',BUGS_STUDY_PALETTE))):
        y=row*55;sd.text((4,y+1),name,font=font,fill='#f0d898')
        for i,color in enumerate(palette):
            sd.rectangle((i*44,y+18,i*44+42,y+44),fill=color)
            sd.text((i*44+3,y+29),format(i,'x'),font=font,fill='#000000' if i>=6 else '#f0d898')
    swatch.save(out/'enemy-palette-swatches-source.png')
    (out/'source-composite-provenance.json').write_text(json.dumps({
        'method':'Exact captured240x160 background crops with source indexed sprites overlaid at native16px. This is source comparison, NOT new emulator evidence. Only actor input palette changes between sides.',
        'palette':list(BUGS_STUDY_PALETTE),'old_palette':list(ORIGINAL),
        'family_count':3,'concept_count':30,'scene_comparisons':120,
        'records':records,'shared_bank_hazard':'Original bugs also colors PetalCloak/HUD/carriedbush. Give enemy bodies an independent bank; do not replace shared foliage/bugs globally.',
        'limits':'Static foreground separation and allsourceposes inspected; parent real-run capture still needed. No numerical contrast metric is an aesthetic score.'},indent=2)+'\n')


if __name__=='__main__':
    write_review('/workspace/setup/appearance-enemy-studies/palette-review')
