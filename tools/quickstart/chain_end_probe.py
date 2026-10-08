"""The chain-end probe (Oct 2026, the redesign's P1.4): can a RUN be won?

Boots a plain run per seed (no scenario, the real starting kit), walks it
into its drop region so the chain deals its first step, and then drives
every step the way a player would - with the completion audit's inputs
(chain_audit.py: kills by health 0, walks onto rewards, R on chests and
NPCs, a chase for fairies) and a WARP for the travel between rooms, which
the reach model (sim_validate.py, 402/402) and not this probe vouches for.
When the fourth trial completes it reads the finale the ROM drew, drives
the carrier in the Element's region, picks the Element up and reports WIN.

    EVENT  warp a tile and a half below the site's spot (the testbed's own
           landing), ask the ROM what the site deals (QuickStartContentSiteRoll),
           drive that kind. The pot lottery and the memory pair are the
           audit's undriven kinds: a step on them is reported UNDRIVEN and
           the step is forced so the rest of the chain is still exercised.
    WAVE   warp to the row's entrance and clear waves until the counter
           meets the step's target.
    BOSS   warp to the row, wait for the boss the chain asked for, kill it.
    ITEM   the next prize pays it (QuickStartDrawItem): clear the first wave
           of a region not yet cleared and take the reward where it drops.
    QUEST  the side quests have their own probes (carry_probe, the quest
           scenarios); here the quest flag is set and the step reported
           FORCED.

A seed ends WIN, or FAIL at a named step with what the probe saw. FORCED
and UNDRIVEN steps are listed per seed so a WIN says exactly what it rests
on.

    python3 tools/quickstart/chain_end_probe.py [--rom tmc-d3.gba] [--seeds 1:21]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import warp, here, poison_here, press, entities, r16, w16, KIND_ENEMY, KIND_OBJECT, GENT, STRIDE, PLAYER, ROOM_CONTROLS
import scenario as S
import parse_tables as P
import callrom as C
import chain_audit as A

args = sys.argv[1:]
ROM = args[args.index('--rom') + 1] if '--rom' in args else 'tmc-d3.gba'
VERBOSE = '--verbose' in args
lo, hi = 1, 21
if '--seeds' in args:
    a, b = args[args.index('--seeds') + 1].split(':'); lo, hi = int(a), int(b)
SAVE = 0x02002a40
CHAIN_KIND, CHAIN_WHERE, CHAIN_DETAIL, PROGRESS, ROLLED, HINTED = 0x26, 0x2B, 0x30, 0x35, 0x36, 0x37
KIND_NAMES = ['ITEM', 'EVENT', 'WAVE', 'BOSS', 'QUEST']
CARRIER = ['WAVE', 'BOSS', 'QUEST', 'QUEST']
SCRATCH = 0x02000000
GF_QUEST_DONE = 39
ELEMENT = P.ITEMS['ITEM_EARTH_ELEMENT']
sites = P.content_sites()
pool = P.region_pool()
sym = {}
for n in ('QuickStartDropRegionIndex', 'QuickStartElementRegionIndex', 'QuickStartWinCarrier',
          'QuickStartContentSiteRoll', 'QuickStartChainStepMet', 'QuickStartQuestSetFlag',
          'QuickStartSideQuestDone'):
    sym[n] = C.game_sym(n)
GET_INV = C.map_sym('GetInventoryValue')

def s32(v): return v - (1 << 32) if v >= (1 << 31) else v
def progress(c): return c.memory.u8[SAVE + PROGRESS]
def rolled(c): return c.memory.u8[SAVE + ROLLED]
def step(c, i): return (c.memory.u8[SAVE + CHAIN_KIND + i], c.memory.u8[SAVE + CHAIN_WHERE + i], c.memory.u8[SAVE + CHAIN_DETAIL + i])
HEALTH = 0x45   # Entity.health; the player starts with three hearts (24)

SHELL_CLOCK = 0x02002a40 + 0xA8 + 0x1a   # gSave.stats.shells: the seashell invincibility clock (game.c)

def heal(c):
    """The probe's player is not here to fight: waves respawn around a
    kill-everything cheat and three hearts go in seconds (the first runs
    ended on the title screen). Keep the hearts full, and keep the
    seashell's three seconds running (CalculateDamage refuses the hit)."""
    c.memory.u8[PLAYER + HEALTH] = 24
    w16(c, SHELL_CLOCK, 180)

def settle(c, n=90):
    for _ in range(0, n, 30):
        heal(c); A.run(c, 30)
    A.dismiss(c); heal(c)

# the audit's drivers run frames without healing; wrap their frame runner
_audit_run = A.run
def _healing_run(c, n):
    for _ in range(0, n, 30):
        heal(c); _audit_run(c, min(30, n))
    heal(c)
A.run = _healing_run

META_XP = SAVE + 0x4ac   # gSave.meta_xp: the win adds the run's score to it before the reset

def meta_xp(c):
    return r16(c, META_XP) | (r16(c, META_XP + 2) << 16)

def dead(c):
    return here(c) == (0, 0) and c.memory.u8[PLAYER + 0x0c] == 0 and r16(c, PLAYER + 0x2e) == 0
def step_met(c, i): return C.call_keep(c, sym['QuickStartChainStepMet'], (i,)) != 0

VIA = [None]   # the run's drop row: a warp an interior refuses goes through it

def travel(c, a, r, x, y):
    """Warp and wait until the room is really the one asked for: a textbox
    or an Ezlo line pending at departure holds the transition up, and a
    warp out of some interiors straight to a field room is refused (seed
    3: Percy's treehouse to the Western Wood, four attempts) while the
    same warp from a field room goes through - so the second attempt hops
    through the drop row first."""
    for attempt in range(4):
        if attempt == 1 and VIA[0] is not None and (a, r) != VIA[0][:2]:
            poison_here(c)
            warp(c, VIA[0][0], VIA[0][1], VIA[0][2], VIA[0][3], frames=300)
            settle(c, 60)
        poison_here(c)
        warp(c, a, r, x, y, frames=300)
        for _ in range(4):
            if here(c) == (a, r):
                break
            A.run(c, 60)
        if VERBOSE:
            print('      travel to %s attempt %d: here %s msg %d action %#x' % ((a, r), attempt, here(c), c.memory.u8[0x02000050], c.memory.u8[PLAYER + 0x0c]), flush=True)
        if here(c) == (a, r):
            break
        # the request was lost (an item-get or a cutscene owned the frame
        # it was made on): ask again
        A.run(c, 120)
    settle(c, 60)
    return here(c) == (a, r)

def goto_row(c, row):
    return travel(c, pool[row]['area'], pool[row]['room'], pool[row]['entrance'][0], pool[row]['entrance'][1])

def goto_site(c, site):
    an, rn, a, r, x, y = sites[site]
    return travel(c, a, r, x, y + 24)

def site_kind(c, site):
    C.call_keep(c, sym['QuickStartContentSiteRoll'], (site, SCRATCH, SCRATCH + 4))
    return c.memory.u8[SCRATCH], c.memory.u8[SCRATCH + 4]

def teleport_onto(c, x, y):
    w16(c, PLAYER + 0x2e, x); w16(c, PLAYER + 0x32, y)
    A.run(c, 20)

def take_ground_items(c, limit=6):
    """Walk onto every ground item in the room (a prize the probe earned)."""
    for _ in range(limit):
        items = entities(c, KIND_OBJECT, 0)
        if not items:
            return
        teleport_onto(c, items[0][4], items[0][5]); settle(c, 30)

def drive_wave(c, row, i, budget=40):
    goto_row(c, row)
    killed = 0
    for _ in range(budget):
        heal(c); killed += A.kill_all(c); settle(c, 90)
        if step_met(c, i):
            return True, 'waves cleared (killed %d)' % killed
    return False, 'wave target not met after %d kills' % killed

def drive_boss(c, row, i, budget=30):
    """The chain's boss is dealt by the region wave loop and DEFERRED while
    the kills' drops hold the sprite table (QuickStartSpawnRegionWave's
    owed latch), so each kill cycle waits for the drops to blink out."""
    goto_row(c, row)
    killed = 0
    for _ in range(budget):
        heal(c); killed += A.kill_all(c); settle(c, 700)
        if step_met(c, i) or c.memory.u8[SAVE + HINTED] & 0x80:
            return True, 'boss down (killed %d)' % killed
    return False, 'no boss latch after %d kills' % killed

def drive_item(c, detail, drop, i):
    """The next prize pays the item: clear the first wave of a region not
    yet cleared this run and take the reward where it drops (the row's
    reward spot, and whatever else the clear put on the floor)."""
    rows = [drop] + [r for r in range(len(pool)) if r != drop]
    tried = 0
    for row in rows:
        goto_row(c, row)
        if not entities(c, KIND_ENEMY):
            settle(c, 120)
        if not entities(c, KIND_ENEMY):
            continue
        tried += 1
        for _ in range(6):
            A.kill_all(c); settle(c, 120)
        rx, ry = pool[row]['reward']
        ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
        spots = [(ox + rx, oy + ry)] + [(e[4], e[5]) for e in entities(c, KIND_OBJECT, 0)]
        for sx, sy in spots:
            if A.coll_at(c, (sx - ox) >> 4, (sy - oy) >> 4) != 0:
                continue
            teleport_onto(c, sx, sy); settle(c, 40)
            if C.call_keep(c, GET_INV, (detail,)):
                # let the item-get sequence play out before any warp: a
                # transition asked for during it was never honoured
                settle(c, 300); A.dismiss(c); settle(c, 60)
                return True, 'paid by row %d' % row
        if tried >= 3:
            break
    return C.call_keep(c, GET_INV, (detail,)) != 0, 'no region clear paid it (%d rows tried)' % tried

def drive_event(c, site, forced):
    if not goto_site(c, site):
        return False, 'could not land at site %d' % site
    kind, extra = site_kind(c, site)
    kname = S.EVENTS[kind] if kind < len(S.EVENTS) else str(kind)
    if kname in A.DRIVEN:
        if not A.spawned(c, kname):
            settle(c, 120)
        ok, note = A.drive(c, kname, site, extra)
        return ok, '%s: %s' % (kname, note)
    forced.append('site %d %s' % (site, kname))
    b = A.FLAG_BANK_12 + A.SITE_ORIGIN + site
    c.memory.u8[A.SAVE_FLAGS + (b >> 3)] |= 1 << (b & 7)
    return True, '%s: UNDRIVEN, forced' % kname

progress_moved = [None]

def run_seed(sd):
    c = S.boot(ROM, 0, seed=sd, frames=300)
    # tell the containments this run's transitions are a probe's warps
    # (QuickStartProbeWarpsFree): scenario_d, unused on a plain run
    c.memory.u8[SAVE + 0x3C] = 0x51
    drop = C.call_keep(c, sym['QuickStartDropRegionIndex'], ())
    VIA[0] = (pool[drop]['area'], pool[drop]['room'], pool[drop]['entrance'][0], pool[drop]['entrance'][1])
    xp0 = meta_xp(c)
    forced = []
    log = []
    goto_row(c, drop)
    settle(c, 120)
    if rolled(c) == 0:
        return 'FAIL', 'no step rolled in the drop row %d' % drop, log, forced
    for i in range(4):
        if progress(c) > i:
            continue
        kind, where, detail = step(c, i)
        kname = KIND_NAMES[kind] if kind < 5 else str(kind)
        before = progress(c)
        progress_moved[0] = lambda c, b=before: progress(c) > b
        if kname == 'EVENT':
            ok, note = drive_event(c, where, forced)
        elif kname == 'WAVE':
            ok, note = drive_wave(c, where, i)
        elif kname == 'BOSS':
            ok, note = drive_boss(c, where, i)
        elif kname == 'ITEM':
            ok, note = drive_item(c, detail, drop, i) if detail else (True, 'wants nothing')
        elif kname == 'QUEST':
            C.call_keep(c, sym['QuickStartQuestSetFlag'], (GF_QUEST_DONE,))
            forced.append('quest'); ok, note = True, 'FORCED'
        else:
            ok, note = False, 'unknown kind'
        # the monitor advances the step in a region room
        if here(c)[0:2] != (pool[drop]['area'], pool[drop]['room']) and progress(c) <= i:
            goto_row(c, drop)
        settle(c, 120)
        # the next step is dealt by the monitor in a region room once this
        # one is met; give it the frames
        for _ in range(6):
            if rolled(c) > i + 1 or progress(c) <= i:
                break
            settle(c, 60)
        log.append('step %d %s where %d detail %d: %s -> progress %d rolled %d' % (i, kname, where, detail, note, progress(c), rolled(c)))
        if dead(c):
            if VERBOSE:
                from emu import snap
                snap(c, 'dead_seed%d_step%d.png' % (sd, i))
            return 'FAIL', 'the run ended (title screen) during step %d %s' % (i, kname), log, forced
        if progress(c) <= i:
            return 'FAIL', 'stuck at step %d %s (%s)' % (i, kname, note), log, forced
    settle(c, 120)
    elem = s32(C.call_keep(c, sym['QuickStartElementRegionIndex'], ()))
    if elem < 0:
        return 'FAIL', 'four trials done, no element drawn', log, forced
    carrier = C.call_keep(c, sym['QuickStartWinCarrier'], ())
    cname = CARRIER[carrier & 3]
    log.append('finale: element row %d (%s) carrier %s' % (elem, pool[elem]['roomName'], cname))
    if cname == 'QUEST' and not C.call_keep(c, sym['QuickStartSideQuestDone'], ()):
        C.call_keep(c, sym['QuickStartQuestSetFlag'], (GF_QUEST_DONE,)); forced.append('carrier quest')
    goto_row(c, elem)
    for _ in range(60 if cname != 'BOSS' else 30):
        heal(c); A.kill_all(c); settle(c, 90 if cname != 'BOSS' else 700)
        # the win is a RESET: QuickStartCheckWinCondition adds the run's
        # score to gSave.meta_xp and starts the next run, so the Element is
        # never seen in the inventory from here. meta_xp going up is the win.
        if meta_xp(c) > xp0:
            return 'WIN', 'the Element was taken in row %d and the run reset (meta_xp %d -> %d)' % (elem, xp0, meta_xp(c)), log, forced
        if dead(c):
            return 'FAIL', 'the run ended without a win in row %d' % elem, log, forced
        elems = [e for e in entities(c, KIND_OBJECT, 0) if e[3] == ELEMENT]
        if elems:
            teleport_onto(c, elems[0][4], elems[0][5]); settle(c, 60)
            if meta_xp(c) > xp0:
                return 'WIN', 'the Element was taken in row %d and the run reset (meta_xp %d -> %d)' % (elem, xp0, meta_xp(c)), log, forced
    return 'FAIL', 'carrier %s never put the element down in row %d' % (cname, elem), log, forced

def main():
    wins = 0; fails = []
    for sd in range(lo, hi):
        res, why, log, forced = run_seed(sd)
        for l in log:
            print('    ' + l, flush=True)
        print('%-4s seed %3d  %s%s' % (res, sd, why, ('  [forced: %s]' % ', '.join(forced)) if forced else ''), flush=True)
        if res == 'WIN':
            wins += 1
        else:
            fails.append((sd, why))
    print('\nRESULT %s %d/%d' % ('PASS' if not fails else 'FAIL', wins, hi - lo))
    for sd, why in fails:
        print('  seed %d: %s' % (sd, why))
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
