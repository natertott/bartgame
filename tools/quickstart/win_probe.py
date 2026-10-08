"""The finale, end to end (Oct 2026, P1.4's other half): with the four
trials forced done the Element is drawn, the carrier is driven in the
Element's region and the Element is picked up - the win.

Per seed: force the four pre-steps (finale_probe's way), land in the drop
row so the chain monitor draws the finale, read the carrier, warp to the
Element row and drive the carrier - WAVE: clear waves until the Element
appears at the row's reward spot; BOSS: kill the boss the row deals (each
kill cycle waits for the drops to blink out, the boss is deferred while
they hold the sprite table); QUEST: the quest flag (the quests have their
own probes). Then stand on the Element and read ITEM_EARTH_ELEMENT back.
The win's reset must also empty the dungeon key bag (a small key and a big
key are planted first, and the probe follows the reset back into the next
run's hub, where the run-start wipe runs; Oct 2026, P3).

    python3 tools/quickstart/win_probe.py [--rom tmc-d3.gba] [--seeds 1:7]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import warp, here, poison_here, entities, r16, w16, KIND_ENEMY, KIND_OBJECT, PLAYER, ROOM_CONTROLS
import scenario as S
import parse_tables as P
import callrom as C
import chain_audit as A
import chain_end_probe as E
args = sys.argv[1:]
ROM = args[args.index('--rom') + 1] if '--rom' in args else 'tmc-d3.gba'
lo, hi = 1, 7
if '--seeds' in args:
    a, b = args[args.index('--seeds') + 1].split(':'); lo, hi = int(a), int(b)
SAVE = 0x02002a40
pool = P.region_pool()
wins = 0; fails = []
for sd in range(lo, hi):
    c = S.boot(ROM, 0, seed=sd, frames=300)
    c.memory.u8[SAVE + 0x3C] = 0x51
    drop = C.call_keep(c, E.sym['QuickStartDropRegionIndex'], ())
    E.VIA[0] = (pool[drop]['area'], pool[drop]['room'], pool[drop]['entrance'][0], pool[drop]['entrance'][1])
    for i in range(4):
        c.memory.u8[SAVE + E.CHAIN_KIND + i] = 0
        c.memory.u8[SAVE + E.CHAIN_WHERE + i] = 0
        c.memory.u8[SAVE + E.CHAIN_DETAIL + i] = 0
    c.memory.u8[SAVE + E.PROGRESS] = 3
    c.memory.u8[SAVE + E.ROLLED] = 4
    c.memory.u8[SAVE + E.HINTED] = 0x0f
    E.goto_row(c, drop); E.settle(c, 180)
    elem = E.s32(C.call_keep(c, E.sym['QuickStartElementRegionIndex'], ()))
    if elem < 0:
        print('FAIL seed %3d  no element drawn (progress %d rolled %d)' % (sd, E.progress(c), E.rolled(c)), flush=True); fails.append(sd); continue
    carrier = E.CARRIER[C.call_keep(c, E.sym['QuickStartWinCarrier'], ()) & 3]
    forced = []
    if carrier == 'QUEST':
        C.call_keep(c, E.sym['QuickStartQuestSetFlag'], (E.GF_QUEST_DONE,)); forced.append('quest')
    # read the score BEFORE landing: a forced QUEST carrier can hand the
    # Element over on the landing itself (seed 2 after Hyrule Town joined
    # the ring), and a score read after that sees the win as the baseline
    xp0 = E.meta_xp(c)
    # a small key in the bag (gSave.dungeonKeys[1], the Cave of Flames') and
    # a big key bit: the run reset must take both (Oct 2026, P3)
    c.memory.u8[SAVE + 0x45C + 1] = 3
    c.memory.u8[SAVE + 0x46C + 1] = 2
    landed = E.goto_row(c, elem)
    got = E.meta_xp(c) > xp0; killed = 0
    for n in range(0 if got else (40 if carrier != 'BOSS' else 30)):
        E.heal(c); killed += A.kill_all(c); E.settle(c, 90 if carrier != 'BOSS' else 700)
        # the win is a reset (gSave.meta_xp grows); see chain_end_probe
        if E.meta_xp(c) > xp0:
            got = True; break
        if E.dead(c):
            break
        elems = [e for e in entities(c, KIND_OBJECT, 0) if e[3] == E.ELEMENT]
        if elems:
            E.teleport_onto(c, elems[0][4], elems[0][5]); E.settle(c, 60)
            if E.meta_xp(c) > xp0:
                got = True; break
    keys = None
    if got:
        # follow the win's DoSoftReset through the title into the next run:
        # the run-start wipe (GameTask_Transition) runs on that way back in,
        # not at the win itself
        from emu import press, ROOM_CONTROLS
        for _ in range(400):
            if c.memory.u8[ROOM_CONTROLS + 4] == 48:   # AREA_WIND_TRIBE_TOWER, the hub
                break
            press(c, c.KEY_A, 3, 3); press(c, c.KEY_START, 3, 3)
        keys = (c.memory.u8[SAVE + 0x45C + 1], c.memory.u8[SAVE + 0x46C + 1], c.memory.u8[ROOM_CONTROLS + 4])
    if got and keys[:2] != (0, 0):
        got = False
        forced.append('dungeon keys kept across the reset: %s' % (keys,))
    note = 'row %d (%s) carrier %s, landed %s, killed %d, meta_xp %d -> %d, key bag after the reset %s%s' % (elem, pool[elem]['roomName'], carrier, landed, killed, xp0, E.meta_xp(c), keys[:2] if keys else '-', (' [forced: %s]' % ', '.join(forced)) if forced else '')
    print('%-4s seed %3d  %s' % ('WIN' if got else 'FAIL', sd, note), flush=True)
    if got: wins += 1
    else: fails.append(sd)
print('\nRESULT %s %d/%d' % ('PASS' if not fails else 'FAIL', wins, hi - lo))
sys.exit(1 if fails else 0)
