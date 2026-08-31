"""Minimal mgba harness for the invariant checker. Self-contained on purpose:
the checker is a repo fixture and must not depend on session scratchpads."""
import mgba.log
mgba.log.silence()
import mgba.core, mgba.image

ROM = 'tmc.gba'
TRANS_BASE = 0x030010A0
PSTAT = TRANS_BASE + 0xC
ROOM_CONTROLS = 0x03000bf0
PLAYER = 0x03001160
GENT = 0x030015a0
MAX_ENT = 72
STRIDE = 0x88
COLL = 0x02025eb0 + 0x2004
SAVE_FLAGS = 0x02002a40 + 0x25C
FLAG_BANK_12 = 0xA80  # gSave.flags bit of FLAG_BANK_12 offset 0
QS_BIT0 = 3388  # gSave.flags bit of QUICKSTART flag 0 (FLAG_BANK_12 + 700)


def w16(c, a, v):
    v &= 0xFFFF
    c.memory.u8[a] = v & 0xFF
    c.memory.u8[a + 1] = (v >> 8) & 0xFF


def r16(c, a):
    v = c.memory.u8[a] | (c.memory.u8[a + 1] << 8)
    return v - 0x10000 if v >= 0x8000 else v


def press(c, k, h=3, r=3):
    c.set_keys(k)
    for _ in range(h):
        c.run_frame()
    c.clear_keys(k)
    for _ in range(r):
        c.run_frame()


def boot(rom=ROM, seed=None):
    """Boot to the start of a run.

    `seed` pins the run's RNG (roadmap A3) - see seed.py, which owns the
    mechanism. Worth knowing when reading results: a boot with no .sav
    behind it always derives the SAME seed, because the seed is mixed from
    save state and a blank save has none. So an unpinned harness run is not
    a random sample of the game, it is one specific run, and anything that
    only breaks on other seeds will not show up until someone passes one.
    """
    if seed is not None:
        import seed as seedmod
        return seedmod.boot_pinned(rom, seed)
    img = mgba.image.Image(240, 160)
    c = mgba.core.load_path(rom)
    c.set_video_buffer(img)
    c.qs_video = img  # kept reachable so callers can screenshot (see snap())
    c.reset()
    for _ in range(120):
        c.run_frame()
    for _ in range(300):
        press(c, c.KEY_A, 3, 3)
        press(c, c.KEY_START, 3, 3)
        if c.memory.u8[ROOM_CONTROLS + 4] != 0:
            break
    for _ in range(180):
        c.run_frame()
    return c


def warp(c, area, room, x, y, frames=300):
    c.memory.u8[PSTAT + 0] = area
    c.memory.u8[PSTAT + 1] = room
    c.memory.u8[PSTAT + 2] = 0
    c.memory.u8[PSTAT + 3] = 0
    w16(c, PSTAT + 4, x)
    w16(c, PSTAT + 6, y)
    c.memory.u8[PSTAT + 8] = 1
    c.memory.u8[TRANS_BASE + 9] = 4
    c.memory.u8[TRANS_BASE + 8] = 1
    for _ in range(frames):
        c.run_frame()


def here(c):
    return (c.memory.u8[ROOM_CONTROLS + 4], c.memory.u8[ROOM_CONTROLS + 5])


def poison_here(c):
    """Make here() impossible to confuse with a real room, before a warp.

    The idiom this replaces zeroed the AREA byte as a "did the warp take"
    sentinel. Area 0 is AREA_MINISH_WOODS - a real area - so the moment
    containment learned about Minish Woods, every probe that used the
    sentinel was warping FROM a room the engine believed in, and 19 checks
    failed for a reason that had nothing to do with the code under test.
    Poison the ROOM byte instead: 0xff is not a room in any area.
    """
    c.memory.u8[ROOM_CONTROLS + 5] = 0xff


def qs_set(c, n, v=1):
    _flag_set(c, QS_BIT0 + n, v)


# The room-keyed content sites are the one QUICKSTART block that does NOT
# live in the +700 window - they are raw FLAG_BANK_12 offsets, based at 1
# (offset 0 is unwritable; SetLocalFlagByBank drops it). See the bank map at
# the top of src/game.c.
#
# EXTENSION sites (index 61+) route their bits elsewhere - this mirrors the
# game's own QsSetSiteFlag router (QuickStartSiteExtTarget, src/game.c)
# byte for byte, because a harness that writes the raw location for an
# extension bit is poking window flags that belong to something else.
SITE_ORIGIN = 1
SITE_RAW_BITS = 793  # 61 sites * 13 bits
FLAG_BANK_11 = 0x9C0


def _site_bit(n):
    if n < SITE_RAW_BITS:
        return FLAG_BANK_12 + SITE_ORIGIN + n
    e = n - SITE_RAW_BITS
    if e < 21:
        return FLAG_BANK_12 + 700 + 208 + e
    if e < 34:
        return FLAG_BANK_12 + 700 + 496 + (e - 21)
    if e < 73:
        return FLAG_BANK_12 + 700 + 617 + (e - 34)
    if e < 105:
        return FLAG_BANK_12 + 700 + 658 + (e - 73)
    if e < 112:
        return FLAG_BANK_12 + 700 + 94 + (e - 105)
    if e < 143:
        return FLAG_BANK_11 + 143 + (e - 112)
    if e < 150:
        return FLAG_BANK_11 + 124 + (e - 143)
    return FLAG_BANK_11 + 133 + (e - 150)


def qs_site_set(c, n, v=1):
    _flag_set(c, _site_bit(n), v)


def _flag_set(c, b, v):
    a = SAVE_FLAGS + (b >> 3)
    m = 1 << (b & 7)
    c.memory.u8[a] = (c.memory.u8[a] | m) if v else (c.memory.u8[a] & ~m)


def room_dims(c):
    return r16(c, ROOM_CONTROLS + 0x1e), r16(c, ROOM_CONTROLS + 0x20)


# Entity field offsets. kind is at +8 and id at +9 - NOT +0/+1, which is a
# mistake worth naming here because it was made repeatedly: reading +0 returns
# a field whose values are multiples of 8, so a scan looks plausible, finds
# nothing, and reads as "the room is empty" rather than as a broken probe.
ENT_KIND = 8
ENT_ID = 9
ENT_TYPE = 10
ENT_X = 0x2e
ENT_Y = 0x32
KIND_PLAYER, KIND_ENEMY, KIND_PROJECTILE, KIND_OBJECT, KIND_NPC = 1, 3, 4, 6, 7
GROUND_ITEM_ID = 0


def entities(c, kind=None, ident=None):
    """(index, kind, id, type, worldX, worldY) for every live entity."""
    out = []
    for i in range(MAX_ENT):
        b = GENT + i * STRIDE
        k = c.memory.u8[b + ENT_KIND]
        if k == 0 or (kind is not None and k != kind):
            continue
        if ident is not None and c.memory.u8[b + ENT_ID] != ident:
            continue
        out.append((i, k, c.memory.u8[b + ENT_ID], c.memory.u8[b + ENT_TYPE],
                    r16(c, b + ENT_X), r16(c, b + ENT_Y)))
    return out


def coll_at(c, tx, ty):
    return c.memory.u8[COLL + tx + (ty << 6)]


def snap(c, path):
    """Save the current frame as a PNG (rendering ground truth - the one way
    to catch the sprites-never-render VRAM failure class).

    mgba's python Image exposes different APIs depending on how the
    bindings were built: a source build gives to_pil(), the pip wheel
    (0.10.2) gives save_png(file). Try both so a probe written against one
    machine still runs on the other."""
    img = c.qs_video
    if hasattr(img, 'to_pil'):
        img.to_pil().convert('RGB').save(path)
        return
    with open(path, 'wb') as fh:
        img.save_png(fh)
