#!/usr/bin/env python3
"""Capture the selected Contour Folio + Exploded Shelves marker combination.

Uses real mGBA inputs, pinned native ABI observation and existing disclosed
seed/ordinary-loader/hero-navigation fixtures. Original concept4 screenshots
are the pixel reference for adopted icon artwork. No health, inventory, gate,
discovery, terrain, palette, VRAM or framebuffer results are assigned.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

import cream_art_study_capture as A
from cream_dynamic_capture import DynamicCapture, forest_cache, map_redraw
from regional_native_support import sha
import probe as Q

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / 'cream-heights-review'
EVENTS = (64, 32, 8, 2, 4, 16, 128)
EVENT_NAMES = ('boss', 'task', 'heal', 'chest', 'folk', 'cache', 'entry')


def write(path, value):
    A.write_json(path, value)


def snap(live, out, label):
    path = out / (label + '.png')
    im = live.c.bg_video.to_pil().convert('RGB').copy()
    im.save(path)
    im.resize((720, 480), Image.Resampling.NEAREST).save(out / (label + '-3x.png'))
    return dict(file=path.name, sha256=sha(path), size=list(im.size))


def bitmap(live):
    return A.digest(A.raw(live.c, 0x06008000, 19200))


def open_map(live):
    live.advance('START', 2)
    live.advance([], 48)
    live.check('real START opens the pause menu', live.state()['state'] == 4)
    live.advance('R', 2)
    live.advance([], 48)
    timing = map_redraw(live, 'R', 0, 0)
    live.check('real two-page R input opens selected Cream map',
               live.state()['state'] == 4 and Q.r16(live.c, 0x0400000e) == 0x1f08)
    return timing


def close_map(live):
    live.advance('START', 2)
    live.advance([], 600, stop=lambda st: st['state'] == 1 and
                 st['actor']['state'] == 0 and st['actor']['z'] == 0)
    live.advance([], 2)
    live.check('START returns from map to living ordinary gameplay',
               live.state()['state'] == 1 and live.state()['health'][0] > 0)


def icon_reference(live, out, data):
    """Compare displayed stamps to the original actual #4 icon pixels.

    Source stamp positions follow #4's recorded shelf count and regional grid.
    Destination positions follow the unchanged #1 grid. Glyph painting is not
    duplicated in this checker: actual historical native RGB pixels are used.
    """
    reference_png = REFERENCE / 'images/maps/04-overview.png'
    reference_data = REFERENCE / 'validation/maps/04-overview-data.json'
    prior = json.loads(reference_data.read_text())
    live.check('same seeded region has the original concept4 event contents',
               data['events'] == prior['events'],
               dict(current=data['events'], reference=prior['events']))
    reference = Image.open(reference_png).convert('RGB')
    actual = live.c.bg_video.to_pil().convert('RGB')
    stamps, represented = [], set()
    two_events, overflow = 0, 0
    for cell in range(25):
        if not data['known'][cell]:
            continue
        events = [(bit, name) for bit, name in zip(EVENTS, EVENT_NAMES)
                  if data['events'][cell] & bit]
        if not events:
            continue
        col, row = cell % 5, cell // 5
        depth = max(1, min(4, prior['levels'][cell]))
        rx, ry = 12 + col * 44 + 16, 28 + row * 22 + 8 - depth * 2
        dx, dy = 12 + col * 150 // 5 + (150 // 5 - 2) // 2, 28 + row * 108 // 5 + (108 // 5 - 2) // 2
        for index, (_, name) in enumerate(events[:2]):
            offset = 0 if len(events) == 1 else -5 if index == 0 else 5
            source = reference.crop((rx + offset - 4, ry - 4, rx + offset + 5, ry + 5))
            dest = actual.crop((dx + offset - 4, dy - 4, dx + offset + 5, dy + 5))
            exact = source.tobytes() == dest.tobytes()
            live.check('adopted %s stamp in room%d exactly matches actual concept4 pixels' % (name, cell), exact)
            stamps.append(dict(cell=cell, event=name, reference_center=[rx + offset, ry],
                               actual_center=[dx + offset, dy], exact=exact,
                               reference_rgb_sha256=A.digest(source.tobytes()),
                               actual_rgb_sha256=A.digest(dest.tobytes())))
            represented.add(name)
        if len(events) > 1:
            two_events += 1
        if len(events) > 2:
            expected = [reference.getpixel((rx + offset, ry + 6)) for offset in (-2, 0, 2)]
            observed = [actual.getpixel((dx + offset, dy + 6)) for offset in (-2, 0, 2)]
            live.check('room%d retains concept4 overflow pips' % cell,
                       expected == observed, dict(reference=expected, actual=observed))
            overflow += 1
    live.check('overview contains real differently colored chest, heal and folk markers',
               {'chest', 'heal', 'folk'}.issubset(represented), sorted(represented))
    live.check('multi-event rooms show both retained concept4 icons', two_events > 0, two_events)
    report = dict(reference_png=str(reference_png.relative_to(ROOT)),
                  reference_sha256=sha(reference_png),
                  reference_data_sha256=sha(reference_data), stamps=stamps,
                  represented=sorted(represented), two_event_rooms=two_events,
                  overflow_rooms=overflow, complete=all(s['exact'] for s in stamps))
    write(out / 'icon-reference.json', report)
    return report


def run_case(bundle, out, seed, charted):
    out.mkdir(parents=True, exist_ok=True)
    live = DynamicCapture(bundle, out / 'private-core', seed)
    if charted:
        for cell in range(25):
            live.request(cell)
            live.advance([], 2)
        live.request(5)
        live.advance([], 2)
    timings = [open_map(live)]
    snapshot = live.readonly()
    data = live.map_data()
    live.check('selected production layout is Contour Folio', live.run.u8('gCreamMapConcept') == 0)
    images = [snap(live, out, 'overview')]
    write(out / 'overview-data.json', data)
    if charted:
        icon_reference(live, out, data)
    else:
        live.check('fresh map retains undiscovered rooms', 0 < sum(data['known']) < 25, data['known'])
    before = bitmap(live)
    live.advance('L', 2)
    live.advance([], 48)
    live.check('L keeps the selected map presentation and bitmap',
               live.run.u8('gCreamMapConcept') == 0 and bitmap(live) == before)
    live.check('ignored style cycling preserves paused game state', live.readonly() == snapshot)
    timings.append(map_redraw(live, 'A', 0, 1))
    zoom = live.map_data()
    write(out / 'zoom-data.json', zoom)
    images.append(snap(live, out, 'zoom'))
    comparable = lambda d: {k: v for k, v in d.items() if k not in ('zoom', 'concept')}
    live.check('overview and room zoom share the same actual terrain and features', comparable(data) == comparable(zoom))
    live.check('zoom is read-only across all live gameplay state', live.readonly() == snapshot)
    timings.append(map_redraw(live, 'B', 0, 0))
    current = live.run.u8('gCreamMapCell')
    if charted:
        key = 'UP' if current >= 5 else 'DOWN'
        timings.append(map_redraw(live, key, 0, 0))
    else:
        target = next(i for i, k in enumerate(data['known']) if not k)
        while live.run.u8('gCreamMapCell') != target:
            at = live.run.u8('gCreamMapCell')
            if at % 5 != target % 5:
                key = 'LEFT' if at % 5 > target % 5 else 'RIGHT'
            else:
                key = 'UP' if at > target else 'DOWN'
            timings.append(map_redraw(live, key, 0, 0))
    selected = live.map_data()
    live.check('D-pad selects a different room without changing the live room',
               selected['selected'] != current and live.readonly() == snapshot)
    timings.append(map_redraw(live, 'A', 0, 1))
    neighbor = live.map_data()
    images.append(snap(live, out, 'neighbor-zoom'))
    write(out / 'neighbor-zoom-data.json', neighbor)
    live.check('selected-room preview preserves paused gameplay', live.readonly() == snapshot)
    if not charted:
        live.check('unvisited room zoom contains no hidden terrain or markers',
                   not neighbor['known'][neighbor['selected']] and not neighbor['marker_count'] and
                   not any(neighbor['kind']) and not any(neighbor['height']))
    # R opens the real item page and returns; no equipment button is pressed.
    live.advance('R', 2)
    live.advance([], 48)
    live.check('R item page preserves inventory and gameplay', live.readonly() == snapshot)
    timings.append(map_redraw(live, 'R', 0, 0))
    live.check('return from items keeps the chosen map layout', live.run.u8('gCreamMapConcept') == 0)
    close_map(live)
    composites = live.composites(out / 'restored-native-BG2')
    images.append(snap(live, out, 'returned'))
    timings.append(open_map(live))
    live.check('reopened map starts in the selected presentation', live.run.u8('gCreamMapConcept') == 0 and live.run.u8('gCreamMapZoom') == 0)
    # Select returns through the normal pause page rather than choosing a style.
    live.advance('SELECT', 2)
    live.advance([], 120)
    live.check('Select returns to normal pause page', live.state()['state'] == 4 and Q.r16(live.c, 0x0400000e) != 0x1f08)
    close_map(live)
    live.check('selected map interactions complete within the existing48frame budget',
               max(t['hardware_frames'] for t in timings) <= 48, timings)
    report = dict(rom_sha256=sha(bundle / 'bartgame.gba'),
                  source_commit=(bundle / 'source-commit.txt').read_text().strip(),
                  tool_sha256=sha(__file__), seed=seed, charted_fixture=charted,
                  fixture='Pinned title seed, ordinary room-load requests and hero-position/facing navigation. Actual menu inputs; no rewards, discovery, terrain, health, inventory, palette or pixel results assigned.',
                  images=images, redraw_timings=timings, native_world_restored=composites['complete'],
                  checks=live.checks, complete=all(c['passed'] for c in live.checks))
    write(out / 'report.json', report)
    write(out / 'input-trace.json', live.identity())
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--seed', default=0xb4a7, type=lambda n: int(n, 0))
    p.add_argument('--forest-cache', action='store_true')
    a = p.parse_args()
    bundle, out = a.bundle.resolve(), a.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    sections = {label: run_case(bundle, out / label, a.seed, charted)
                for label, charted in (('charted', True), ('fresh', False))}
    if a.forest_cache:
        sections['forest-cache'] = forest_cache(bundle, out / 'forest-cache', a.seed)
    result = dict(rom_sha256=sha(bundle / 'bartgame.gba'),
                  source_commit=(bundle / 'source-commit.txt').read_text().strip(),
                  tool_sha256=sha(__file__), sections=sections,
                  complete=all(s['complete'] for s in sections.values()))
    write(out / 'report.json', result)
    return int(not result['complete'])


if __name__ == '__main__':
    raise SystemExit(main())
