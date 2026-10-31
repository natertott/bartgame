#!/usr/bin/env python3
"""Native source gallery for the five selected enemies and the Broken Heart.

These are SOURCE pose catalogs, not mGBA recordings or a combat simulation.
Each body pose has the same review hold. Actual state timing and movement
belong to the separately captured running ROM.
"""
import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import enemy_study_gallery as G

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'art'))
import enemy_studies as S
import reboot_core as C

PROFILE = 11
FAMILIES = tuple(S.FAMILIES)
SELECTED = {'beetle': ('Coin Toad', 9), 'bat': ('Quill Moth', 9),
            'spitter': ('Trumpet Bellflower', 5), 'slime': ('Pear Bladder', 9),
            'knight': ('Moth Confessor', 6), 'boss': ('Broken Heart', None)}
BG, FIELD, DIM = G.BG, G.FIELD, G.DIM
SHA = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def refs(family):
    """Body IDs retain the historical order; companions are explicit."""
    return tuple(G.frame_names(family))


def graphic(family, name):
    im = S.frame(family, PROFILE, name)
    assert im.mode == 'P' and im.size == G.canvas_size(family), (family, name)
    assert set(im.tobytes()) <= set(range(16)), (family, name)
    assert im.getbbox(), (family, name, 'blank')
    return im, C.rgba(im, G.palette(family)[2])


def overview(poses=None):
    """Common foot baseline, with 1x/3x and silhouette copies separated."""
    board = Image.new('RGB', (1140, 328), BG)
    d = ImageDraw.Draw(board)
    G.text(d, (8, 5), 'USER-SELECTED ENEMIES / native SOURCE art, not emulator output')
    G.text(d, (8, 23), '1x + 3x nearest-neighbour and silhouettes; shared foot baseline. Body poses have review holds, not AI timing.', DIM)
    for index, family in enumerate(FAMILIES):
        x = index * 190
        label, old = SELECTED[family]
        pose = (poses or {}).get(family, G.CANONICAL[family])
        G.text(d, (x + 7, 51), label)
        G.text(d, (x + 7, 67), G.MECHANICS[family], DIM)
        G.text(d, (x + 7, 83), 'New Heart' if old is None else f'Selected study #{old}', DIM)
        im, rgba = graphic(family, pose)
        w, h = im.size
        baseline = 296
        by = baseline - h * 3
        d.rectangle((x + 7, by - 1, x + 9 + w * 3, baseline + 1), fill=FIELD)
        G.paste_sprite(board, rgba, (x + 8, by), 3)
        G.paste_sprite(board, rgba, (x + 118, baseline - h))
        G.paste_sprite(board, G.silhouette(im), (x + 154, baseline - h))
        G.text(d, (x + 7, 306), pose, DIM)
    return board


def family_pose(family, name, hold):
    im, rgba = graphic(family, name)
    w, h = im.size
    height = max(216, h * 3 + 92)
    board = Image.new('RGB', (368, height), BG)
    d = ImageDraw.Draw(board)
    G.text(d, (8, 6), f'{SELECTED[family][0]} / SOURCE body pose {name}')
    G.text(d, (8, 24), f'{hold}ms review hold; not movement or attack timing', DIM)
    G.text(d, (8, 40), f'Native {w}x{h}, 4bpp indices, RGB555 palette', DIM)
    base = height - 28
    d.rectangle((12, base - h * 3 - 2, 15 + w * 3, base + 1), fill=FIELD)
    G.paste_sprite(board, rgba, (14, base - h * 3), 3)
    G.paste_sprite(board, rgba, (174, base - h))
    G.paste_sprite(board, G.silhouette(im), (240, base - h))
    G.text(d, (12, base + 7), '3x', DIM)
    G.text(d, (172, base + 7), 'native 1x', DIM)
    G.text(d, (238, base + 7), 'silhouette', DIM)
    return board


def atlas(family):
    entries = [(family, name) for name in refs(family)]
    if family == 'knight': entries.extend(('ksword', name) for name in refs('ksword'))
    if family == 'spitter': entries.append(('proj', 'seed'))
    w, h = G.canvas_size(family)
    cw, ch, cols = max(176, w * 3 + w + 34), h * 3 + 48, 4
    board = Image.new('RGB', (cw * cols, 56 + math.ceil(len(entries) / cols) * ch), BG)
    d = ImageDraw.Draw(board)
    G.text(d, (8, 5), f'{SELECTED[family][0]} / COMPLETE native SOURCE frames, not mGBA')
    G.text(d, (8, 23), 'Body plus separately labelled weapon/seed companions; native 1x and integer 3x.', DIM)
    for n, (sheet, name) in enumerate(entries):
        x, y = n % cols * cw, 56 + n // cols * ch
        im, rgba = graphic(sheet, name)
        G.text(d, (x + 5, y + 3), (sheet + ' / ' if sheet != family else '') + name)
        G.paste_sprite(board, rgba, (x + 7, y + 23 + (h - im.height) * 3), 3)
        G.paste_sprite(board, rgba, (x + w * 3 + 20, y + 23 + h * 3 - im.height))
        G.text(d, (x + 5, y + ch - 16), '3x / native 1x', DIM)
    return board


def diagnostics():
    fields = [('Drain', C.PALETTES['drain'][4]),
              ('Healthy', C.PALETTES['ground'][4]),
              ('Blight', C.PALETTES['blight'][4]),
              ('Cave', C.PALETTES['stone'][3])]
    board = Image.new('RGB', (960, 48 + 6 * 110), BG)
    d = ImageDraw.Draw(board)
    G.text(d, (8, 5), 'SELECTED SOURCE diagnostics / value and native scene-material swatches')
    G.text(d, (8, 23), 'Quiet authored fields, not actual game screenshots. Every native copy remains unscaled.', DIM)
    for n, family in enumerate(FAMILIES):
        y = 48 + n * 110
        im, rgba = graphic(family, G.CANONICAL[family])
        G.text(d, (8, y + 3), SELECTED[family][0])
        G.paste_sprite(board, G.gray(rgba), (176, y + 22))
        G.paste_sprite(board, G.silhouette(im), (228, y + 22))
        for i, (label, color) in enumerate(fields):
            x = 304 + i * 158
            G.text(d, (x, y + 3), label, DIM)
            d.rectangle((x, y + 20, x + 64, y + 88), fill=color)
            G.paste_sprite(board, rgba, (x + (64 - im.width) // 2, y + 87 - im.height))
    return board


def write_readme(out, report):
    lines = ['# Selected enemy native source art', '',
             'These are **SOURCE pose catalogs**, not mGBA recordings or gameplay-timing simulations.', '',
             'The user selected Coin Toad, Quill Moth, Trumpet Bellflower, Pear Bladder and Moth Confessor. '
             'The final boss is a new purplish Broken Heart with a jagged split down the middle. '
             'All art starts on its actual GBA canvas with sixteen RGB555 inks including transparent zero.', '',
             '![Selected source overview](selected-overview-source.png)', '',
             '[Animate the selected pose catalog](selected-all-poses-source.gif) · '
             '[Native value/silhouette diagnostics](selected-diagnostics-source.png) · '
             '[Exact native coverage and hashes](source-manifest.json)', '',
             '## Complete body pose cycles', '',
             f'Every body pose is shown with a fixed {report["pose_duration_ms"]}ms inspection hold. '
             'Source cycles do not reproduce actual windup duration, live damage windows, gravity, movement, '
             'hurt blinking or AI decisions. Actual mGBA footage is separate. '
             'The six body cycles cover all 61 body frame instances; two weapon orientations and one seed '
             'complete the 64-frame native set and are included in the labelled atlases.', '',
             '| Selected form / mechanic | Native canvas | Body frames | Source cycle | Complete atlas |',
             '| --- | --- | ---: | --- | --- |']
    for family in FAMILIES:
        w, h = G.canvas_size(family)
        lines.append(f'| {SELECTED[family][0]} / {G.MECHANICS[family]} | {w}×{h} | {len(refs(family))} | '
                     f'[GIF]({family}-all-poses-source.gif) | [PNG](atlases/{family}-all-frames-source.png) |')
    lines += ['', 'The original `atk` frames deliberately alias the newer `strike` images. '
              'West-facing views use the existing horizontal mirror. The boss uses its actual 32×64 '
              'canvas; transparent padding is not its damage footprint. The body split remains visible '
              'through pulse, charge, release, spawn, lunge, hurt and collapse.', '',
              '## Native files and validation', '',
              'Every frame has an indexed PNG with its literal hardware palette and an exact RGBA PNG. '
              'The manifest records original/appended IDs, raw index and RGBA hashes, native canvas, '
              'palette, source hashes and each output hash. No filtered reduction, fractional alpha or '
              'automatic screenshot recoloring is used. Every GIF is decoded back and compared with '
              'its source RGB boards; there is no quantized fallback.', '',
              'The small enemy bank remains separate from the shared cloak/carried-bush colors. '
              'Moth Confessor and the shooter/Heart use the existing stone/blight banks. '
              'Validation establishes native completeness and encoding, not a claim of gameplay '
              'balance or a new damage/vulnerability rule.']
    (out / 'README.md').write_text('\n'.join(lines) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--pose-ms', type=int, default=150)
    args = parser.parse_args()
    assert args.pose_ms >= 50 and args.pose_ms % 10 == 0
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=True)
    (out / 'atlases').mkdir(exist_ok=True)
    source_names = ['art/enemy_studies.py', 'art/enemy_studies_small.py',
                    'art/enemy_studies_soft.py', 'art/enemy_studies_heavy.py',
                    'art/enemy_studies_palette.py', 'art/enemy_heart.py',
                    'art/reboot_core.py', 'art/reboot_actors.py',
                    'art/reboot_contracts.json', 'tools/enemy_study_gallery.py',
                    'tools/selected_enemy_gallery.py']
    hashes = {name: SHA(ROOT / name) for name in source_names}
    report = {'method': __doc__, 'profile': PROFILE, 'source_only': True,
              'git_base_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'source_sha256': hashes, 'pose_duration_ms': args.pose_ms,
              'families': {}, 'animations': {}, 'frames': [], 'files': {}}
    for family in FAMILIES:
        name, choice = SELECTED[family]
        slot, source, colors = G.palette(family)
        seq = G.pose_sequence(family)
        assert set(seq) == set(refs(family)), family
        report['families'][family] = {'name': name, 'selected_study': choice,
                                     'canvas': G.canvas_size(family),
                                     'palette_slot': slot, 'palette_source': source,
                                     'colors_rgb555': colors,
                                     'frame_names': list(refs(family)), 'review_sequence': seq}
        atlas(family).save(out / 'atlases' / f'{family}-all-frames-source.png')
        path = out / f'{family}-all-poses-source.gif'
        frames = [family_pose(family, pose, args.pose_ms) for pose in seq]
        report['animations'][family] = {'path': path.name, 'pose_names': seq,
                                       **G.exact_gif(frames, args.pose_ms, path)}
    entries = [(family, name) for family in FAMILIES for name in refs(family)]
    entries += [('ksword', name) for name in refs('ksword')] + [('proj', 'seed')]
    for family, name in entries:
        im, rgba = graphic(family, name)
        slot, source, colors = G.palette(family)
        dest = out / 'native' / family; dest.mkdir(parents=True, exist_ok=True)
        indexed_path, rgba_path = dest / f'{name}-indexed.png', dest / f'{name}.png'
        pal = [value for color in colors for value in C.rgb(color)]
        indexed = im.copy(); indexed.putpalette(pal + [0] * (768 - len(pal)))
        indexed.save(indexed_path, transparency=0); rgba.save(rgba_path)
        assert Image.open(indexed_path).convert('RGBA').tobytes() == rgba.tobytes()
        assert Image.open(rgba_path).convert('RGBA').tobytes() == rgba.tobytes()
        report['frames'].append({'family': family, 'name': name, 'canvas': list(im.size),
                                 'palette_slot': slot, 'palette_source': source,
                                 'index_sha256': hashlib.sha256(im.tobytes()).hexdigest(),
                                 'rgba_sha256': hashlib.sha256(rgba.tobytes()).hexdigest(),
                                 'native_indexed_png': str(indexed_path.relative_to(out)),
                                 'native_rgba_png': str(rgba_path.relative_to(out)),
                                 'bounds': im.getbbox(), 'indices': sorted(set(im.tobytes())),
                                 'rgba_roundtrip_verified': True})
    assert len(report['frames']) == 64, len(report['frames'])
    report['frame_count'], report['body_frame_count'] = 64, 61
    overview().save(out / 'selected-overview-source.png')
    diagnostics().save(out / 'selected-diagnostics-source.png')
    seqs = {family: G.pose_sequence(family) for family in FAMILIES}
    count = max(map(len, seqs.values()))
    combined = [overview({family: seqs[family][tick % len(seqs[family])] for family in FAMILIES})
                for tick in range(count)]
    path = out / 'selected-all-poses-source.gif'
    report['combined_animation'] = {'path': path.name,
                                    **G.exact_gif(combined, args.pose_ms, path),
                                    'note': 'Each body cycles through its complete labelled source poses; not one shared AI clock.'}
    for name, expected in hashes.items(): assert SHA(ROOT / name) == expected, ('source changed', name)
    write_readme(out, report)
    report['files'] = {str(p.relative_to(out)): {'sha256': SHA(p), 'bytes': p.stat().st_size}
                       for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'source-manifest.json'}
    (out / 'source-manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'source_only': True, 'frame_count': 64, 'body_frame_count': 61,
                      'body_cycles': len(report['animations']), 'files': len(report['files']),
                      'out': str(out)}))


if __name__ == '__main__':
    main()
