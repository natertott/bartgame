"""BARTGAME emulator harness: boot the ROM in mGBA, press keys, read RAM by
symbol, take screenshots.

    import probe
    c = probe.boot()
    probe.hold(c, 'RIGHT', 60)
    probe.snap(c, 'out.png')
    print(probe.sym('gPl'))

Symbols come from build/bartgame.map (the linker map), so a probe never
hard-codes an address.
"""
import os
import re
import sys

import mgba.core
import mgba.image
import mgba.log

mgba.log.silence()

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
ROM = os.path.join(ROOT, 'bartgame.gba')
MAP = os.path.join(ROOT, 'build', 'bartgame.map')

_syms = None


def sym(name):
    global _syms
    if _syms is None:
        _syms = {}
        for line in open(MAP):
            m = re.match(r'\s+0x([0-9a-f]{8,16})\s+(\w+)\s*$', line)
            if m:
                _syms[m.group(2)] = int(m.group(1), 16)
    return _syms[name]


def boot(rom=ROM, frames=30):
    img = mgba.image.Image(240, 160)
    c = mgba.core.load_path(rom)
    c.set_video_buffer(img)
    c.bg_video = img
    c.reset()
    for _ in range(frames):
        c.run_frame()
    return c


def snap(c, path):
    img = c.bg_video
    if hasattr(img, 'to_pil'):
        img.to_pil().convert('RGB').save(path)
    else:
        with open(path, 'wb') as fh:
            img.save_png(fh)


def key(c, name):
    return getattr(c, 'KEY_' + name)


def hold(c, names, frames):
    """Hold keys (a string or list) for N frames, then release. mGBA's
    KEY_* constants are bit indices, passed one per argument."""
    if isinstance(names, str):
        names = [names]
    ks = [key(c, n) for n in names]
    c.set_keys(*ks)
    for _ in range(frames):
        c.run_frame()
    c.clear_keys(*ks)


# Actor field offsets (src/actor.h)
A_STATE, A_TIMER, A_DIR, A_FACING, A_X, A_Y, A_Z, A_SPEED, A_HP, A_IFRAMES, A_COLL = 2, 4, 6, 7, 8, 12, 16, 24, 26, 28, 35
ACTOR_SIZE = 64


def actor(c, i):
    a = sym('gActors') + i * ACTOR_SIZE
    x = r32(c, a + A_X)
    y = r32(c, a + A_Y)
    if x >= 1 << 31:
        x -= 1 << 32
    if y >= 1 << 31:
        y -= 1 << 32
    return {'kind': r8(c, a), 'type': r8(c, a + 1), 'state': r8(c, a + A_STATE), 'timer': r8(c, a + A_TIMER),
            'x': x >> 16, 'y': y >> 16, 'z': r32(c, a + A_Z) >> 16, 'speed': r16(c, a + A_SPEED),
            'hp': r16(c, a + A_HP), 'coll': r8(c, a + A_COLL), 'facing': r8(c, a + A_FACING)}


def press(c, name, hold_frames=2, release_frames=2):
    hold(c, name, hold_frames)
    for _ in range(release_frames):
        c.run_frame()


def run(c, frames):
    for _ in range(frames):
        c.run_frame()


def r8(c, a):
    return c.memory.u8[a]


def r16(c, a):
    v = c.memory.u8[a] | (c.memory.u8[a + 1] << 8)
    return v - 0x10000 if v >= 0x8000 else v


def r32(c, a):
    return (c.memory.u8[a] | (c.memory.u8[a + 1] << 8) | (c.memory.u8[a + 2] << 16) | (c.memory.u8[a + 3] << 24))


def w8(c, a, v):
    c.memory.u8[a] = v & 0xFF


def w16(c, a, v):
    c.memory.u8[a] = v & 0xFF
    c.memory.u8[a + 1] = (v >> 8) & 0xFF


def player_pos(c):
    """The player's feet point in room pixels (Actor 0: x at +8, y at +12)."""
    a = sym('gActors')
    x = r32(c, a + 8)
    y = r32(c, a + 12)
    if x >= 1 << 31:
        x -= 1 << 32
    if y >= 1 << 31:
        y -= 1 << 32
    return x >> 16, y >> 16


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/bart.png'
    c = boot()
    run(c, 60)
    snap(c, out)
    print('player at', player_pos(c), '->', out)
