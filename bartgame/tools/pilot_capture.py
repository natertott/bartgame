"""Capture the Drain art pilot from the real ROM and hold it against the
artist's frame (art/ref/drain_pilot/master_240x160.png).

    cd bartgame && make pilot && python3 tools/pilot_capture.py OUTDIR

Boots bartgame_drainpilot.gba in mGBA and writes, all raw 240x160 (no
scaling, no filter):

    engine_capture_240x160.png          the whole frame: BG1, BG2, OBJ
    engine_capture_bg_240x160.png       BG2 and BG1 only
    engine_capture_ground_240x160.png   BG2 only
    master_hw_240x160.png               the master with each colour expanded
                                        from 5 bits the way mGBA shows it
    bg_hw_240x160.png, ground_hw_240x160.png   the same for the pack's
                                        ground and ground+overlay PNGs
    diff_*.png, compare_*.json          tools/compare_frames.py's output
    readback.json                       the hardware state read back from
        VRAM, palette RAM, OAM and the IO registers, each checked byte for
        byte against the delivered files
    sheet_3x.png                        master | capture | diff against the
                                        mGBA-expanded master, at 3x
    engine_capture_again_240x160.png    the pilot again, after Start to the
                                        title and Select back
    after_pilot_hall_240x160.png        a run begun from the title after it

The artist's verifier expands a 5-bit channel c to round(c*255/31) and
mGBA to (c<<3)|(c>>2); the two differ by 1 at c = 3, 7, 24 and 28, so the
master as delivered is compared at tolerance 0 and 1, and the master
brought through mGBA's expansion at tolerance 0.
"""
import json
import os
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import probe as P  # noqa: E402

PILOT = os.path.normpath(os.path.join(ROOT, 'art', 'ref', 'drain_pilot'))
ROM = os.path.join(ROOT, 'bartgame_drainpilot.gba')
P.MAP = os.path.join(ROOT, 'build_pl', 'bartgame_drainpilot.map')
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
DISPCNT = 0x04000000
MODE0_OBJ1D = 0x0040
BG1, BG2, OBJ = 0x0200, 0x0400, 0x1000
layout = json.load(open(os.path.join(PILOT, 'layout.json')))


def u16(c, a):
    return P.r16(c, a) & 0xFFFF


def read(c, addr, n):
    return bytes(P.r8(c, addr + i) & 0xFF for i in range(n))


def hw(v):
    return ((v >> 3) << 3) | ((v >> 3) >> 2)


def hw_image(im):
    return im.convert('RGB').point(hw)


def delivered(rel):
    return open(os.path.join(PILOT, rel), 'rb').read()


c = P.boot(rom=ROM, frames=90, start=False)
state = P.r8(c, P.sym('gGame'))
fade = P.r8(c, P.sym('gFadeLevel'))
P.snap(c, os.path.join(OUT, 'engine_capture_240x160.png'))
full = u16(c, DISPCNT)
for tag, bits in (('bg', BG1 | BG2), ('ground', BG2)):
    # the layers are set only on a state change, so a write here holds
    P.w16(c, DISPCNT, MODE0_OBJ1D | bits)
    c.run_frame()
    P.snap(c, os.path.join(OUT, 'engine_capture_%s_240x160.png' % tag))
P.w16(c, DISPCNT, full)
c.run_frame()

# ---- the hardware state, against the files as delivered
checks = {}


def check(name, got, want):
    checks[name] = {'match': got == want, 'bytes': len(want)}
    if got != want:
        first = next(i for i in range(min(len(got), len(want))) if got[i] != want[i]) if len(got) == len(want) else None
        checks[name]['first_difference_at'] = first


chr_ = delivered(layout['character_file'])
check('BG characters, VRAM 0x06000000 vs ' + layout['character_file'], read(c, 0x06000000, len(chr_)), chr_)
check('BG1 map, screenblock 24 vs ' + layout['BG1']['map_file'], read(c, 0x06000000 + 24 * 0x800, 2048), delivered(layout['BG1']['map_file']))
check('BG2 map, screenblock 28 vs ' + layout['BG2']['map_file'], read(c, 0x06000000 + 28 * 0x800, 2048), delivered(layout['BG2']['map_file']))
check('BG palette RAM banks 0-12 vs ' + layout['BG_palette_file'], read(c, 0x05000000, 13 * 32), delivered(layout['BG_palette_file']))
objpal = delivered(layout['OBJ_palette_file'])
check('OBJ palette RAM banks 13-15 vs banks 0-2 of ' + layout['OBJ_palette_file'], read(c, 0x05000200 + 13 * 32, 3 * 32), objpal[:3 * 32])
bgcnt = {n: u16(c, 0x04000000 + off) for n, off in (('BG1CNT', 0x0A), ('BG2CNT', 0x0C))}
oam = []
for i in range(128):
    a0, a1, a2 = (u16(c, 0x07000000 + i * 8 + k) for k in (0, 2, 4))
    if (a0 & 0x0300) == 0x0200:
        continue
    shape, size = a0 >> 14, a1 >> 14
    w, h = [[(8, 8), (16, 16), (32, 32), (64, 64)], [(16, 8), (32, 8), (32, 16), (64, 32)], [(8, 16), (8, 32), (16, 32), (32, 64)]][shape][size]
    oam.append({'slot': i, 'x': a1 & 0x1FF, 'y': a0 & 0xFF, 'w': w, 'h': h, 'tile': a2 & 0x3FF,
                'priority': (a2 >> 10) & 3, 'palette': a2 >> 12, 'hflip': bool(a1 & 0x1000), 'vflip': bool(a1 & 0x2000)})
for sp, o in zip(layout['sprite_placement'], oam):
    b = delivered('gba/obj_%s_4bpp.bin' % sp['name'])
    check('OBJ %s tiles, OBJ VRAM tile %d vs gba/obj_%s_4bpp.bin' % (sp['name'], o['tile'], sp['name']), read(c, 0x06010000 + o['tile'] * 32, len(b)), b)
    checks['OAM %s' % sp['name']] = {'match': (o['x'], o['y'], o['w'], o['h'], o['priority'], o['palette'], o['hflip'], o['vflip']) == (sp['x'], sp['y'], sp['size'][0], sp['size'][1], 2, 13 + sp['palette_bank_obj'], False, False),
                                     'want': {'x': sp['x'], 'y': sp['y'], 'size': sp['size'], 'priority': 2, 'palette': 13 + sp['palette_bank_obj']}, 'got': o}
regs_ok = (full == MODE0_OBJ1D | BG1 | BG2 | OBJ and bgcnt['BG1CNT'] == (1 | 24 << 8) and bgcnt['BG2CNT'] == (2 | 28 << 8))
checks['registers'] = {'match': regs_ok, 'DISPCNT': '0x%04x' % full, 'BG1CNT': '0x%04x' % bgcnt['BG1CNT'], 'BG2CNT': '0x%04x' % bgcnt['BG2CNT'],
                       'want': 'DISPCNT 0x1640 (mode 0, OBJ 1D, BG1, BG2, OBJ); BG1CNT 0x1801 (priority 1, characters 0, screenblock 24, 32x32); BG2CNT 0x1c02 (priority 2, screenblock 28)'}
scroll = P.sym('gBgScroll')
checks['scroll'] = {'match': all(u16(c, scroll + k) == 0 for k in (4, 6, 8, 10)), 'BG1': [u16(c, scroll + 4), u16(c, scroll + 6)], 'BG2': [u16(c, scroll + 8), u16(c, scroll + 10)]}
checks['visible sprites'] = {'match': len(oam) == len(layout['sprite_placement']), 'count': len(oam)}
checks['fade'] = {'match': fade == 0, 'level': fade}
checks['state'] = {'match': state == 7, 'gGame.state': state, 'want': 'GS_PILOT (7)'}

# ---- the frames
Image.open(os.path.join(PILOT, 'master_240x160.png')).convert('RGB').point(hw).save(os.path.join(OUT, 'master_hw_240x160.png'))
ground = Image.open(os.path.join(PILOT, 'assets/bg/ground_240x160.png')).convert('RGBA')
bg = ground.copy()
bg.alpha_composite(Image.open(os.path.join(PILOT, 'assets/bg/overlay_240x160.png')).convert('RGBA'))
hw_image(ground).save(os.path.join(OUT, 'ground_hw_240x160.png'))
hw_image(bg).save(os.path.join(OUT, 'bg_hw_240x160.png'))
master = os.path.join(PILOT, 'master_240x160.png')
pairs = [
    ('master_tol0', master, 'engine_capture_240x160.png', 0),
    ('master_tol1', master, 'engine_capture_240x160.png', 1),
    ('master_tol8', master, 'engine_capture_240x160.png', 8),
    ('master_hw_tol0', os.path.join(OUT, 'master_hw_240x160.png'), 'engine_capture_240x160.png', 0),
    ('bg_hw_tol0', os.path.join(OUT, 'bg_hw_240x160.png'), 'engine_capture_bg_240x160.png', 0),
    ('ground_hw_tol0', os.path.join(OUT, 'ground_hw_240x160.png'), 'engine_capture_ground_240x160.png', 0),
]
compares = {}
for tag, a, b, tol in pairs:
    r = subprocess.run([sys.executable, os.path.join(HERE, 'compare_frames.py'), a, os.path.join(OUT, b), '--tolerance', str(tol),
                        '--output', os.path.join(OUT, 'diff_%s.png' % tag), '--report', os.path.join(OUT, 'compare_%s.json' % tag)],
                       capture_output=True, text=True)
    rp = os.path.join(OUT, 'compare_%s.json' % tag)
    rep = json.load(open(rp))
    rep['a'] = os.path.relpath(a, ROOT) if a.startswith(PILOT) else os.path.basename(a)
    rep['b'] = b
    json.dump(rep, open(rp, 'w'), indent=1)
    compares[tag] = {k: rep[k] for k in ('a', 'b', 'tolerance', 'mismatched', 'worst_channel_difference', 'pass')}
    print('%-15s %s' % (tag, r.stdout.strip().split(': ', 1)[-1]))

# ---- a sheet to look at: master | capture | diff (mGBA-expanded master, tolerance 0)
sheet = Image.new('RGB', (240 * 3 + 16, 160), (40, 40, 40))
for i, p in enumerate((master, os.path.join(OUT, 'engine_capture_240x160.png'), os.path.join(OUT, 'diff_master_hw_tol0.png'))):
    sheet.paste(Image.open(p).convert('RGB'), (i * 248, 0))
sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(os.path.join(OUT, 'sheet_3x.png'))

# ---- out and back: Start leaves for the title, Select on the title comes
# back to the same frame, and a run begun after it has the game's own VRAM
P.press(c, 'START', 2, 40)
checks['Start leaves for the title'] = {'match': P.r8(c, P.sym('gGame')) == 0, 'gGame.state': P.r8(c, P.sym('gGame'))}
P.press(c, 'SELECT', 2, 60)
P.snap(c, os.path.join(OUT, 'engine_capture_again_240x160.png'))
again = Image.open(os.path.join(OUT, 'engine_capture_again_240x160.png')).tobytes() == Image.open(os.path.join(OUT, 'engine_capture_240x160.png')).tobytes()
checks['Select on the title shows the same frame again'] = {'match': P.r8(c, P.sym('gGame')) == 7 and again, 'gGame.state': P.r8(c, P.sym('gGame')), 'identical': again}
P.press(c, 'START', 2, 40)
P.press(c, 'START', 2, 60)
P.press(c, 'A', 2, 20)
P.press(c, 'A', 2, 40)
P.snap(c, os.path.join(OUT, 'after_pilot_hall_240x160.png'))
folk = P.sym('pal_obj') + 13 * 32
after = {'gGame.state': P.r8(c, P.sym('gGame')), 'gAnimTiles': P.r8(c, P.sym('gAnimTiles')),
         'BG1CNT': '0x%04x' % u16(c, 0x0400000A), 'BG2CNT': '0x%04x' % u16(c, 0x0400000C),
         'OBJ bank 13 is the folk\'s again': read(c, 0x05000200 + 13 * 32, 32) == read(c, folk, 32)}
after['match'] = (after['gGame.state'] in (1, 3) and after['gAnimTiles'] == 1 and after['BG1CNT'] == '0xd801' and after['BG2CNT'] == '0xdc02'
                  and after['OBJ bank 13 is the folk\'s again'])
checks['a run begun after the pilot has the game\'s VRAM'] = after

ok = all(v['match'] for v in checks.values())
json.dump({'rom': os.path.basename(ROM), 'frames_run_before_capture': 90, 'readback_all_match': ok, 'readback': checks, 'compare': compares},
          open(os.path.join(OUT, 'readback.json'), 'w'), indent=1)
for k, v in checks.items():
    print('%-5s %s' % ('ok' if v['match'] else 'FAIL', k))
print('readback: %s' % ('all match' if ok else 'MISMATCH'))
sys.exit(0 if ok and compares['master_hw_tol0']['pass'] and compares['master_tol1']['pass'] else 1)
