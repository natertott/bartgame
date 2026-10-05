"""A region boss fought free-roam with the sword alone, measured for stalls.

Boots a BOSS testbed scenario (the family deals from wave 0 in the named
pool row), then drives the player at the nearest piece and swings every 14
frames, logging every piece's action/subAction/health/hitType and the
chuchu body's Helper (intro stage, peel counter). A "stall" is 600+ frames
in which no piece changed state while the player kept swinging.

    python3 tools/quickstart/boss_fight.py FORM [ROW] [FRAMES] [--rom tmc-d3.gba]
      FORM 0 green chuchu, 1 blue chuchu, 2 big octorok

The driver teleports beside the body when it has been stuck against a
piece or a wall for 40 frames - this measures the DAMAGE PATH (does the
sword hurt it, does the fight complete, does any phase hang), not
pathfinding. Textboxes are dismissed; the player is healed every frame.

PASS: "no boss pieces left" before the frame budget and an empty STALLS
list. The Oct 2026 batch measured: green chuchu dead at ~5300 frames, blue
likewise, big octorok at ~2000, no stalls; before it, the Four Sword never
moved the peel counter and the chuchu sat 3586 frames in its walk-home
state.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import here, entities, KIND_ENEMY, ROOM_CONTROLS, PLAYER, GENT, r16
import scenario as S
GSAVE = 0x02002a40; MSG = 0x02000050; STRIDE = 0x88
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
ROM = sys.argv[sys.argv.index('--rom') + 1] if '--rom' in sys.argv else 'tmc-d3.gba'
FORM = int(ARGS[0]) if ARGS else 0; ROW = int(ARGS[1]) if len(ARGS) > 1 else 0
FRAMES = int(ARGS[2]) if len(ARGS) > 2 else 12000
BOSS_IDS = (0x13, 0x39)
def pieces(c):
    out = []
    for (i, k, ident, t, x, y) in entities(c, KIND_ENEMY):
        if ident in BOSS_IDS:
            b = GENT + i * STRIDE
            out.append(dict(i=i, id=ident, type=c.memory.u8[b+0x0a], type2=c.memory.u8[b+0x0b], act=c.memory.u8[b+0x0c],
                            sub=c.memory.u8[b+0x0d], hp=c.memory.u8[b+0x45], hit=c.memory.u8[b+0x3f], ifr=c.memory.u8[b+0x3d],
                            x=x, y=y, base=b))
    return out
def helper(c, b):
    p = c.memory.u8[b+0x84] | c.memory.u8[b+0x85]<<8 | c.memory.u8[b+0x86]<<16 | c.memory.u8[b+0x87]<<24
    if 0x02000000 <= p < 0x02040000:
        return (c.memory.u8[p+3], c.memory.u8[p+6], c.memory.u8[p+4])  # intro stage, peel counter, unk_04
    return None
c = S.boot(ROM, S.KINDS['BOSS'], ROW, FORM, kit=1, frames=300)
print('here', here(c), 'form', FORM, flush=True)
sig_last = None; sig_since = 0; stalls = []; swung = 0; hits_seen = 0
last_hp = {}
for f in range(FRAMES):
    c.memory.u8[GSAVE + 0xA8 + 2] = 40
    ps = pieces(c)
    keys = []
    if (c.memory.u8[MSG] & 0x7f) and f % 10 == 0:
        keys.append(c.KEY_A)
    if ps:
        px, py = r16(c, PLAYER + 0x2e), r16(c, PLAYER + 0x32)
        # chase the nearest piece
        tgt = min(ps, key=lambda p: abs(p['x'] - px) + abs(p['y'] - py))
        dx, dy = tgt['x'] - px, tgt['y'] - py
        d = abs(dx) + abs(dy)
        # stuck against a piece or a wall: sidestep for a while
        if 'last_pos' not in globals(): last_pos, stuck, side = (px, py), 0, 0
        if abs(px - last_pos[0]) + abs(py - last_pos[1]) < 2 and d > 18: stuck += 1
        else: stuck = 0
        last_pos = (px, py)
        if stuck > 40:
            # unstick by teleporting beside the body: the damage path is what is measured, not pathfinding
            from emu import w16
            body = [p for p in ps if p['type'] == 0] or ps
            w16(c, PLAYER + 0x2e, body[0]['x']); w16(c, PLAYER + 0x32, body[0]['y'] + 24)
            stuck = 0
        if side > 0:
            side -= 1
            keys.append((c.KEY_UP if dy > 0 else c.KEY_DOWN) if abs(dx) >= abs(dy) else (c.KEY_LEFT if dx > 0 else c.KEY_RIGHT))
        elif d > 18:
            if abs(dx) >= abs(dy):
                keys.append(c.KEY_RIGHT if dx > 0 else c.KEY_LEFT)
            else:
                keys.append(c.KEY_DOWN if dy > 0 else c.KEY_UP)
        if d < 40 and f % 14 < 2:
            keys.append(c.KEY_B); swung += 1
    if keys: c.set_keys(*keys)
    c.run_frame()
    c.clear_keys(*keys) if keys else None
    sig = tuple((p['id'], p['type'], p['act'], p['sub'], p['hp'], p['hit']) for p in ps)
    if sig != sig_last:
        # the intro (every piece in subAction 0) is vanilla's own slow
        # entrance, ~1300 frames with Ezlo's hint dismissed - not a stall
        if sig_since >= 600 and not all(p[3] == 0 for p in sig_last):
            stalls.append((f - sig_since, sig_since, sig_last))
        sig_last = sig; sig_since = 0
    else:
        sig_since += 1
    if f % 120 == 0:
        px, py = r16(c, PLAYER + 0x2e), r16(c, PLAYER + 0x32)
        desc = ' '.join('%x:t%d/%d a%d s%d hp%d ht%x if%d d%d' % (p['id'], p['type'], p['type2'], p['act'], p['sub'], p['hp'], p['hit'], p['ifr'] if p['ifr'] < 128 else p['ifr']-256, abs(p['x']-px)+abs(p['y']-py)) for p in ps)
        hs = [helper(c, p['base']) for p in ps if p['type'] == 0 and p['id'] == 0x13]
        print(f, 'msg', c.memory.u8[MSG] & 0x7f, 'pl', (px, py), 'helper', hs, '|', desc, flush=True)
    if not ps and f > 600:
        print('no boss pieces left at frame', f, flush=True); break
if sig_since >= 600 and sig_last and not all(p[3] == 0 for p in sig_last): stalls.append((FRAMES - sig_since, sig_since, sig_last))
print('swings', swung)
print('STALLS (start, length, signature):')
for s in stalls: print('  ', s)
alive = bool(pieces(c))
print('RESULT', 'PASS' if (not alive and not stalls) else 'FAIL')
sys.exit(0 if (not alive and not stalls) else 1)
