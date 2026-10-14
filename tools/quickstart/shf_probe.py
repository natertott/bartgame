"""South Hyrule Field under load: what runs out, and when.

The user's report (Oct 2026): in South Hyrule Field enemies sometimes do
not die properly - the sprite freezes, nothing drops, and a few seconds
later it is gone; the kinstone fusers' sprites glitch; and the frame rate
drops depending on which enemies spawned.

A dying enemy must create a DEATH_FX object (EnemyCreateDeathFX,
enemyUtils.c); the DEATH_FX plays the death and drops the item. If
CreateObject finds no free entity slot it returns NULL, and the enemy
just stands with its 255-frame timer running down, then deletes itself:
exactly the frozen sprite with no drop. So this measures every budget a
busy field can exhaust, frame by frame:

  entities   gEntCount against the table's 72 (GetEmptyEntity refuses at 71)
  gfx        GFX sheet slots in use, of 44
  palettes   OBJ palette slots in use, of 16
  oam        sprite entries drawn, of 128
  rate       the true frame rate (gMain.ticks)

It boots the region (scenario REGION) at a difficulty, plays it for a
while, and kills every live enemy every `--every` frames (health to 0:
the enemy's own death handler runs, as after a sword hit). Each death is
watched: one that never gets its DEATH_FX is counted, with what filled the
table at that moment.

    python3 tools/quickstart/shf_probe.py [--row 2] [--diff 3,5] [--seeds 4] [--frames 3600] [--every 120]
"""
import argparse
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emu
from emu import GENT, STRIDE, MAX_ENT
import scenario as S
import parse_tables as P

GMAIN_TICKS = 0x03001000 + 0x0C
ENT_COUNT = 0x03003dbc
OAM_UPDATED = 0x03000003
GFXBASE, MAX_GFX = 0x02024490, 44
PALETTES = 0x02001a00
KIND = {1: 'PLAYER', 3: 'ENEMY', 4: 'PROJ', 6: 'OBJECT', 7: 'NPC', 8: 'PITEM', 9: 'MANAGER'}
OBJ = {v: k for k, v in P._enum(open(os.path.join(P.ROOT, 'include/object.h')).read()).items()}
ENEMY = {v: k for k, v in P._enum(open(os.path.join(P.ROOT, 'include/enemy.h')).read()).items()}
DEATH_FX = {v: k for k, v in OBJ.items()}['DEATH_FX']


def u16(c, a):
    return c.memory.u8[a] | (c.memory.u8[a + 1] << 8)


def u32(c, a):
    return u16(c, a) | (u16(c, a + 2) << 16)


def gfx_used(c):
    return sum(1 for i in range(MAX_GFX) if (c.memory.u8[GFXBASE + 4 + i * 12] & 0x0F) not in (0, 1, 2))


def palettes_used(c):
    # gPaletteList[16]: _0_0 (low nibble of byte 0) 0 = free, 1 = free slot
    # in a run, 2/3 in use, 4 = fixed
    return sum(1 for s in range(16) if (c.memory.u8[PALETTES + s * 4] & 0x0F) not in (0, 1))


def table(c):
    out = []
    for i in range(MAX_ENT):
        b = GENT + i * STRIDE
        k = c.memory.u8[b + 8]
        if k == 0:
            continue
        ident = c.memory.u8[b + 9]
        name = ENEMY.get(ident, ident) if k == 3 else OBJ.get(ident, ident) if k == 6 else ident
        out.append(dict(i=i, addr=0x02000000 + 0, base=b, kind=k, id=ident, name='%s:%s' % (KIND.get(k, k), name)))
    return out


def run(rom, row, diff, seed, frames, every, one=True, collect=True):
    c = S.boot(rom, S.KINDS['REGION'], row, 0, kit=2, diff=diff, seed=seed, frames=300)
    for _ in range(600):
        if c.memory.u8[0x02000050]:
            emu.press(c, c.KEY_A, 3, 17)
        else:
            c.run_frame()
    hist, worst, worst_at, msg = [], 60.0, None, []
    peak = dict(ents=0, gfx=0, pal=0, oam=0)
    peak_census = None
    dying = {}            # entity address -> frames since its death began
    lost, deaths = [], 0
    pal_full = 0          # frames with every dynamic palette slot (6-14) held
    npc_pal0 = collections.Counter()   # NPCs drawn in palette 0: a failed load
    pal_owners = None
    stale = collections.Counter()      # drawn with a GFX slot no longer theirs
    for f in range(frames):
        c.memory.u8[emu.PLAYER + 0x45] = 24    # the player cannot lose
        c.memory.u8[emu.PLAYER + 0x3d] = 30
        if c.memory.u8[0x02000050]:
            emu.press(c, c.KEY_A, 3, 3)
        c.run_frame()
        hist.append(u16(c, GMAIN_TICKS))
        # gMain.ticks stands still while a text box is up: a window with a
        # message in it reads as a dip that is not one.
        msg.append(1 if c.memory.u8[0x02000050] else 0)
        if len(hist) > 30 and not any(msg[-31:]):
            rate = 60.0 * ((hist[-1] - hist[-31]) & 0xffff) / 30
            if rate < worst:
                if os.environ.get('SHF_SNAP') and rate < 40:
                    emu.snap(c, os.path.join(os.environ['SHF_SNAP'], 'worst_%04d.png' % f))
                worst = rate
                worst_at = (f, collections.Counter(e['name'] for e in table(c)).most_common(6))
        ents = c.memory.u8[ENT_COUNT]
        g, p, o = gfx_used(c), palettes_used(c), c.memory.u8[OAM_UPDATED]
        if ents > peak['ents']:
            peak_census = collections.Counter(e['name'] for e in table(c))
        for k, v in (('ents', ents), ('gfx', g), ('pal', p), ('oam', o)):
            peak[k] = max(peak[k], v)
        tab = table(c)
        if all((c.memory.u8[PALETTES + s * 4] & 0x0F) in (2, 3) for s in range(6, 15)):
            pal_full += 1
            if pal_owners is None:
                pal_owners = ['%04x:%s' % (u16(c, PALETTES + s * 4 + 2),
                              ','.join(sorted({e['name'] for e in tab if c.memory.u8[e['base'] + 0x1a] & 0xf == s}))[:60])
                              for s in range(6, 15)]
        for e in tab:
            sl = c.memory.u8[e['base'] + 0x26]          # spriteAnimation[0]: its GFX slot
            if sl and c.memory.u8[e['base'] + 0x18] & 3 and e['kind'] in (3, 6, 7):
                st = c.memory.u8[GFXBASE + 4 + sl * 12] & 0x0F
                if st not in (3, 4, 5) or c.memory.u8[GFXBASE + 4 + sl * 12 + 2] == 0:
                    stale[e['name']] += 1
            if e['kind'] == 7 and c.memory.u8[e['base'] + 0x1a] & 0xf == 0 and c.memory.u8[e['base'] + 0x18] & 3:
                npc_pal0[e['id']] += 1
        fx_parents = {u32(c, e['base'] + 0x50) for e in tab if e['kind'] == 6 and e['id'] == DEATH_FX}
        live = set()
        for e in tab:
            if e['kind'] != 3:
                continue
            addr = e['base']
            live.add(addr)
            if c.memory.u8[addr + 0x3a] & 2:      # gustJarState: its death has begun
                if addr not in dying:
                    dying[addr] = 0
                    deaths += 1
                dying[addr] += 1
                if dying[addr] == 3 and addr not in fx_parents:
                    lost.append(dict(frame=f, enemy=e['name'], ents=ents,
                                     census=collections.Counter(x['name'] for x in tab).most_common(6)))
        for addr in list(dying):
            if addr not in live:
                del dying[addr]
        if every and f % every == every - 1:
            # one enemy at a time, as a player fights (or all at once: --all)
            for e in tab:
                if e['kind'] == 3 and c.memory.u8[e['base'] + 0x45] > 0 and not c.memory.u8[e['base'] + 0x3a] & 2:
                    c.memory.u8[e['base'] + 0x45] = 0
                    if one:
                        break
        if collect and f % 20 == 0:
            # the player picks up what dropped (drops move to the player's
            # tile, where the pickup takes them)
            px, py = u16(c, emu.PLAYER + 0x2e), u16(c, emu.PLAYER + 0x32)
            for e in tab:
                if e['kind'] == 6 and OBJ.get(e['id']) == 'GROUND_ITEM':
                    c.memory.u8[e['base'] + 0x2e] = px & 0xff
                    c.memory.u8[e['base'] + 0x2f] = px >> 8
                    c.memory.u8[e['base'] + 0x32] = py & 0xff
                    c.memory.u8[e['base'] + 0x33] = py >> 8
        enemies = sum(1 for e in tab if e['kind'] == 3)
        peak['enemies'] = max(peak.get('enemies', 0), enemies)
        peak['kinds'] = max(peak.get('kinds', 0), len({e['id'] for e in tab if e['kind'] == 3}))
    del c
    return dict(worst=worst, peak=peak, census=peak_census, deaths=deaths, lost=lost,
                pal_full=pal_full, npc_pal0=npc_pal0, pal_owners=pal_owners, stale=stale, worst_at=worst_at)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rom', default=os.path.join(P.ROOT, 'tmc-d3.gba'))
    ap.add_argument('--row', type=int, default=2)
    ap.add_argument('--diff', default='3,5')
    ap.add_argument('--seeds', type=int, default=4)
    ap.add_argument('--seed-base', type=int, default=0, help='first seed index')
    ap.add_argument('--frames', type=int, default=3600)
    ap.add_argument('--every', type=int, default=40)
    ap.add_argument('--all', action='store_true', help='kill every enemy at once')
    ap.add_argument('--no-collect', action='store_true', help='leave the drops on the floor')
    a = ap.parse_args()
    for d in [int(x) for x in a.diff.split(',')]:
        for s in range(a.seed_base, a.seed_base + a.seeds):
            seed = 0x5F0 + s * 7919
            r = run(a.rom, a.row, d, seed, a.frames, a.every, one=not a.all, collect=not a.no_collect)
            pk = r['peak']
            print('row %d diff %d seed %06x: worst %.0f fps; peak enemies %d, entities %d/72, gfx %d/44, palettes %d/16, '
                  'oam %d/128, enemy kinds %d; deaths %d, without DEATH_FX %d' % (a.row, d, seed, r['worst'], pk.get('enemies', 0),
                                                                  pk['ents'], pk['gfx'], pk['pal'], pk['oam'], pk.get('kinds', 0),
                                                                  r['deaths'], len(r['lost'])), flush=True)
            if r['worst_at'] and r['worst'] < 50:
                print('   worst window ends frame %d: %s' % (r['worst_at'][0], ', '.join('%s %d' % kv for kv in r['worst_at'][1])))
            print('   at the entity peak: %s' % ', '.join('%s %d' % kv for kv in r['census'].most_common(8)))
            print('   palettes: all nine dynamic slots held on %d of %d frames; NPCs drawn in palette 0 (a failed load): %s'
                  % (r['pal_full'], a.frames, dict(r['npc_pal0']) or 'none'))
            print('   drawn from a GFX slot not (or no longer) loaded: %s' % (dict(r['stale'].most_common(6)) or 'none'))
            if r['pal_owners']:
                print('   first full palette table: %s' % ' | '.join(r['pal_owners']))
            for l in r['lost'][:3]:
                print('   lost death frame %d %s, %d entities: %s' % (l['frame'], l['enemy'], l['ents'],
                                                                     ', '.join('%s %d' % kv for kv in l['census'])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
