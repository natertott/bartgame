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


def boot(rom=ROM):
    img = mgba.image.Image(240, 160)
    c = mgba.core.load_path(rom)
    c.set_video_buffer(img)
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


def qs_set(c, n, v=1):
    b = QS_BIT0 + n
    a = SAVE_FLAGS + (b >> 3)
    m = 1 << (b & 7)
    c.memory.u8[a] = (c.memory.u8[a] | m) if v else (c.memory.u8[a] & ~m)


def room_dims(c):
    return r16(c, ROOM_CONTROLS + 0x1e), r16(c, ROOM_CONTROLS + 0x20)


def coll_at(c, tx, ty):
    return c.memory.u8[COLL + tx + (ty << 6)]
