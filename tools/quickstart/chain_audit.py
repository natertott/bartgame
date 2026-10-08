"""The completion audit (Oct 2026, the redesign's P0.3): does every ? room
event, in every site that can host it, FINISH and set GF_CONTENT_SITE_DONE -
the bit a chain EVENT step waits on? And does a region clear raise the
wave counter a WAVE step waits on?

Every kind is booted through the testbed (scenario SITE i KIND, full kit),
driven to its end with the inputs a player would use - or the cheat a
probe can use (an enemy's health written to 0 is how memory_probe clears
a wave) - and the DONE bit is read back. A cell is PASS, FAIL (the kind
ran but DONE never set), NOSPAWN (the kind put nothing in the room: the
testbed forced a kind the site's class never deals, which is fine) or
UNDRIVEN (a kind this probe has no inputs for: the pot lottery, whose pots
want a lift-and-throw walk, and the memory pair, which memory_probe.py
covers 9/9).

    python3 tools/quickstart/chain_audit.py [--rom tmc-d3.gba] [--sites A:B] [--kinds WAVES,NPC,...] [--regions]
    python3 tools/quickstart/chain_audit.py --only 4:WAVES,85:CHEST_LOTTERY   # re-run named cells
"""
import os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import warp, here, poison_here, press, entities, r16, coll_at, act_at, KIND_ENEMY, KIND_OBJECT, KIND_NPC, GENT, STRIDE, PLAYER, ROOM_CONTROLS, SAVE_FLAGS, FLAG_BANK_12
import scenario as S
import parse_tables as P
import callrom as C
args = sys.argv[1:]
ROM = args[args.index('--rom') + 1] if '--rom' in args else 'tmc-d3.gba'
SITE_ORIGIN = 1
MSG = 0x02000050
EVENTS = S.EVENTS  # ['ITEM_DROP','MINIBOSS','NPC','WAVES','POT_LOTTERY','CHEST_LOTTERY','FAIRY','MEMORY']
DRIVEN = ['WAVES', 'MINIBOSS', 'NPC', 'ITEM_DROP', 'CHEST_LOTTERY', 'FAIRY']
kinds = args[args.index('--kinds') + 1].split(',') if '--kinds' in args else DRIVEN
sites = P.content_sites()
full = P.content_sites_full()   # ... plus the gate kinstone id in [6]
lo, hi = 0, len(sites)
if '--sites' in args:
    a, b = args[args.index('--sites') + 1].split(':'); lo, hi = int(a), int(b)

def site_done(c, n):
    b = FLAG_BANK_12 + SITE_ORIGIN + n
    return (c.memory.u8[SAVE_FLAGS + (b >> 3)] >> (b & 7)) & 1

def dismiss(c, limit=600):
    """Close textboxes. A is pressed only while a box is up; in Ezlo's talk
    state with no box (0x16) B backs out instead - mashing A there walked
    into Ezlo's SAVE option and quit the run to the title (the chain-end
    probe's "title screen" endings and a freeze inside EEPROMWrite,
    measured)."""
    quiet = 0
    for _ in range(limit):
        msg = c.memory.u8[MSG]; action = c.memory.u8[PLAYER + 0x0c]
        if msg == 0 and action not in (0x16, 0x7):
            c.run_frame(); quiet += 1
            if quiet >= 30:
                return
            continue
        if msg == 0 and action == 0x16:
            press(c, c.KEY_B, 3, 17); quiet = 0
            continue
        press(c, c.KEY_A, 3, 17); quiet = 0

def kill_all(c):
    n = 0
    for e in entities(c, KIND_ENEMY):
        c.memory.u8[GENT + e[0] * STRIDE + 0x45] = 0; n += 1
    return n

def run(c, n):
    for _ in range(n):
        c.run_frame()

def drive(c, kind, site, extra=0):
    """Finish the event the way a player (or a cheat) would; return (done, note)."""
    if kind in ('WAVES', 'MINIBOSS'):
        # kill every wave (health 0, as memory_probe does), then WALK ONTO
        # the content spot: both kinds latch DONE only when the reward they
        # drop there has been picked up (QuickStartSetupWaveRoomContent,
        # the miniboss branch of QuickStartSetupEventContent)
        killed = 0; quiet = 0
        for _ in range(40):
            k = kill_all(c)
            killed += k
            run(c, 90); dismiss(c)
            if site_done(c, site):
                return True, 'killed %d' % killed
            quiet = quiet + 1 if k == 0 else 0
            if quiet >= 3:
                break
        for _ in range(3):
            walk_to_spot(c, site); run(c, 30); dismiss(c)
            if site_done(c, site):
                return True, 'killed %d, reward taken' % killed
        # the reward is where it dropped; stand on it
        for e in entities(c, KIND_OBJECT, 0):
            teleport_to(c, e[4], e[5]); run(c, 30); dismiss(c)
            if site_done(c, site):
                return True, 'killed %d, reward taken (teleported)' % killed
        return site_done(c, site), 'killed %d, enemies left %d, player %s' % (killed, len(entities(c, KIND_ENEMY)), local(c))
    if kind == 'FAIRY':
        # two fairies hover about the spot and wander; walk at the nearest
        # one (it heals and leaves when touched)
        if not [e for e in entities(c, KIND_OBJECT) if e[2] == FAIRY_ID]:
            return site_done(c, site), 'no fairies were placed'
        for _ in range(40):
            fs = [e for e in entities(c, KIND_OBJECT) if e[2] == FAIRY_ID]
            if site_done(c, site):
                return True, 'fairy taken'
            if not fs:
                break
            px, py = r16(c, PLAYER + 0x2e), r16(c, PLAYER + 0x32)
            f = min(fs, key=lambda e: abs(e[4] - px) + abs(e[5] - py))
            dx, dy = f[4] - px, f[5] - py
            if abs(dx) > 2:
                press(c, c.KEY_LEFT if dx < 0 else c.KEY_RIGHT, min(8, abs(dx)), 1)
            if abs(dy) > 2:
                press(c, c.KEY_UP if dy < 0 else c.KEY_DOWN, min(8, abs(dy)), 1)
            run(c, 4)
        run(c, 30)
        sx, sy = spot_world(c, site)
        ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
        floor = act_at(c, (sx - ox) >> 4, (sy - oy) >> 4)
        for _ in range(30):
            fs = [e for e in entities(c, KIND_OBJECT) if e[2] == FAIRY_ID]
            if site_done(c, site) or not fs:
                break
            # a fairy flies over walls, pits, ladders and doors; only stand
            # where the floor is the spot's own kind of floor (a door tile
            # took the player out of the room), and only on OURS (type2 1,
            # QUICKSTART_FAIRY_EVENT_TYPE2) - a room's own fairies do not count
            fs = [e for e in fs if c.memory.u8[GENT + e[0] * STRIDE + 11] == FAIRY_TYPE2
                  and coll_at(c, (e[4] - ox) >> 4, (e[5] - oy) >> 4) == 0
                  and act_at(c, (e[4] - ox) >> 4, (e[5] - oy) >> 4) == floor
                  and (e[5] - oy) < sites[site][5] + 40]   # not down by the door row
            if not fs:
                run(c, 40); continue
            teleport_to(c, fs[0][4], fs[0][5]); run(c, 30)
        if site_done(c, site):
            return True, 'fairy taken (teleported)'
        # the last resort: a fairy that will not come back over the floor
        # (the Boomerang chamber's pits) is brought to the player instead
        from emu import w16
        ours = [e for e in entities(c, KIND_OBJECT) if e[2] == FAIRY_ID and c.memory.u8[GENT + e[0] * STRIDE + 11] == FAIRY_TYPE2]
        for e in ours[:2]:
            b = GENT + e[0] * STRIDE
            w16(c, b + 0x2e, r16(c, PLAYER + 0x2e)); w16(c, b + 0x32, r16(c, PLAYER + 0x32))
            run(c, 30)
            if site_done(c, site):
                return True, 'fairy taken (brought to the player)'
        return site_done(c, site), 'player %s fairies %d' % (local(c), len([e for e in entities(c, KIND_OBJECT) if e[2] == FAIRY_ID]))
    if kind == 'CHEST_LOTTERY':
        # three chests at x-16, x, x+16 on the spot's row; the player is a
        # tile below the middle one. The round ends on the FIRST chest opened
        # (specialChest.c), and only the winner - slot extra & 3, which the
        # testbed sets - latches DONE: so go straight to it, face it, R.
        slot = extra & 3
        # The row can sit up to three tiles from the table spot
        # (QuickStartFindChestRowNear), so take the winner's place from the
        # chest object itself (local flag 250 + slot) and stand below it.
        win = [e for e in entities(c, KIND_OBJECT, CHEST_ID) if e[3] == 250 + min(slot, 2)]
        if not win:
            if not entities(c, KIND_OBJECT, CHEST_ID) and entities(c, KIND_OBJECT, 0):
                # no row fits within three tiles of the spot, so the kind
                # fell back to the item drop (QuickStartFindChestRowNear)
                ok, note = drive(c, 'ITEM_DROP', site, extra)
                return ok, 'no chest row fits; item drop instead: ' + note
            return site_done(c, site), 'no chest for slot %d' % slot
        tx, ty = win[0][4], win[0][5] + 16
        for _ in range(24):
            dx = tx - r16(c, PLAYER + 0x2e); dy = ty - r16(c, PLAYER + 0x32)
            if abs(dx) <= 2 and abs(dy) <= 3:
                break
            if abs(dy) > 3:
                press(c, c.KEY_UP if dy < 0 else c.KEY_DOWN, min(8, abs(dy)), 2)
            if abs(dx) > 2:
                press(c, c.KEY_LEFT if dx < 0 else c.KEY_RIGHT, min(8, abs(dx)), 2)
        how = 'walked'
        if abs(tx - r16(c, PLAYER + 0x2e)) > 2 or abs(ty - r16(c, PLAYER + 0x32)) > 3:
            # not below the winner: R here would open the wrong chest, and
            # the first chest opened ends the round
            teleport_to(c, tx, ty); how = 'teleported'
        press(c, c.KEY_UP, 4, 2)
        for n in range(3):
            press(c, c.KEY_R, 4, 8); dismiss(c); run(c, 30); dismiss(c)
            if site_done(c, site):
                return True, 'winning chest (slot %d) opened (%s)' % (slot, how)
        return site_done(c, site), 'player %s, chests left %d' % (local(c), len(entities(c, KIND_OBJECT, CHEST_ID)))
    if kind == 'NPC':
        # a second Zelda in a room that allows one, or no slot for her, deals
        # the item drop instead (QuickStartSetupEventContent, flag 5)
        sx, sy = spot_world(c, site)
        near = [e for e in entities(c, KIND_NPC) if abs(e[4] - sx) <= 64 and abs(e[5] - sy) <= 64]
        if not near and entities(c, KIND_OBJECT, 0):
            ok, note = drive(c, 'ITEM_DROP', site, extra)
            return ok, 'no Zelda for this site; item drop instead: ' + note
    if kind in ('NPC', 'ITEM_DROP'):
        # the testbed parks the player a tile below the spot: walk into it
        # (an item is taken on contact), talk/open with R, take every textbox
        walk_to_spot(c, site, 12 if kind == 'NPC' else 2)
        how = 'walked'
        for n in range(6):
            if n == 3:
                sx, sy = spot_world(c, site)
                if kind == 'NPC':
                    # the NPC may have wandered off the spot: stand below
                    # wherever it is now
                    npcs = entities(c, KIND_NPC)
                    if npcs:
                        e = min(npcs, key=lambda e: abs(e[4] - sx) + abs(e[5] - sy))
                        sx, sy = e[4], e[5]
                teleport_to(c, sx, sy + (14 if kind == 'NPC' else 0)); press(c, c.KEY_UP, 4, 2); how = 'teleported'
            press(c, c.KEY_R, 4, 8); dismiss(c)
            press(c, c.KEY_A, 4, 8); dismiss(c)
            if site_done(c, site):
                break
        run(c, 60); dismiss(c)
        return site_done(c, site), 'player at %s (%s)' % (local(c), how)
    return site_done(c, site), 'undriven'

def teleport_to(c, x, y):
    """A probe's cheat for the travel INSIDE a room, used only after the
    walk failed: the question here is whether the event FINISHES, and a
    reward the walk could not reach is reported as such (the PASS note says
    'teleported')."""
    from emu import w16
    w16(c, PLAYER + 0x2e, x); w16(c, PLAYER + 0x32, y)
    run(c, 10)

def spot_world(c, site):
    return (r16(c, ROOM_CONTROLS + 6) + sites[site][4], r16(c, ROOM_CONTROLS + 8) + sites[site][5])

def walk_to_spot(c, site, margin=2):
    """The testbed parks the player a tile below the content spot (two in a
    few rooms). Walk up until standing on it (or `margin` pixels short of
    it: an NPC is talked to from the tile below, and some are not solid)
    or stalled: the Boomerang cave's spots sit at the top of a ladder, and
    a climb is slow."""
    ty = r16(c, ROOM_CONTROLS + 8) + sites[site][5]
    stall = 0; last = None
    for _ in range(60):
        y = r16(c, PLAYER + 0x32)
        if y - ty <= margin:
            return
        press(c, c.KEY_UP, 6, 1)
        stall = stall + 1 if y == last else 0
        last = y
        if stall >= 4:
            return

def local(c):
    return (r16(c, PLAYER + 0x2e) - r16(c, ROOM_CONTROLS + 6), r16(c, PLAYER + 0x32) - r16(c, ROOM_CONTROLS + 8))

def spawned(c, kind):
    if kind in ('WAVES', 'MINIBOSS'):
        return len(entities(c, KIND_ENEMY)) > 0
    if kind in ('NPC', 'FAIRY'):
        return len(entities(c, KIND_NPC)) > 0 or len(entities(c, KIND_OBJECT)) > 0
    return len(entities(c, KIND_OBJECT)) > 0

objs = P._enum(open(os.path.join(P.ROOT, 'include/object.h')).read())
FAIRY_ID = objs['FAIRY']
CHEST_ID = objs['SPECIAL_CHEST']
FAIRY_TYPE2 = 0x51   # QUICKSTART_FAIRY_EVENT_TYPE2: the event's own fairies
def main():
    global lo, hi
    retired = None
    results = collections.Counter(); fails = []
    if '--regions' in args:
        # every pool row: arrive with 0 waves cleared, kill the region wave, read the counter
        cnt = None
        for row in range(len(P.region_pool())):
            c = S.boot(ROM, S.KINDS['REGION'], row, 0, kit=2, frames=400); dismiss(c)
            fn = C.game_sym('QuickStartRegionGetWaveCount')
            before = C.call_keep(c, fn, (row,))
            killed = 0
            for _ in range(30):
                killed += kill_all(c); run(c, 90); dismiss(c)
                after = C.call_keep(c, fn, (row,))
                if after > before:
                    break
            after = C.call_keep(c, fn, (row,))
            ok = after > before
            results['REGION ' + ('PASS' if ok else 'FAIL')] += 1
            print('%s region row %2d %-40s waves %d -> %d (killed %d)' % ('PASS' if ok else 'FAIL', row, P.region_pool()[row]['roomName'], before, after, killed), flush=True)
            if not ok:
                fails.append(('region', row, P.region_pool()[row]['roomName']))
    else:
        c0 = S.boot(ROM, 0, frames=60)
        ret_fn = C.game_sym('QuickStartSiteRetired')
        roll_fn = C.game_sym('QuickStartContentSiteRoll')
        only = None
        if '--only' in args:
            only = [(int(t.split(':')[0]), t.split(':')[1]) for t in args[args.index('--only') + 1].split(',')]
            lo, hi = 0, len(sites)
        for i in range(lo, hi):
            an, rn, a, r, x, y = sites[i]
            if only is not None and not any(o[0] == i for o in only):
                continue
            if C.call_keep(c0, ret_fn, (i,)):
                print('skip site %3d %-46s retired' % (i, rn), flush=True); continue
            if an == 'AREA_GREAT_FAIRIES':
                # the three Great Fairy rooms keep their vanilla content on
                # purpose (the honesty test, the Fountain of Sacrifice);
                # the site dispatch skips them and their own scripts set
                # DONE (QuickStartFairyHonestyReward). Not this probe's.
                print('VANILLA  site %3d %-46s the fairy\'s own script resolves it' % (i, rn), flush=True)
                results['VANILLA'] += 1; continue
            if full[i][6] != 0:
                # behind a kinstone fusion (the Goron cave's chambers): the
                # testbed's kit does not fuse, and the chain never deals a
                # gated site before its fusion (QuickStartChainEventOk)
                print('GATED    site %3d %-46s kinstone %d' % (i, rn, full[i][6]), flush=True)
                results['GATED'] += 1; continue
            for kind in (kinds if only is None else [o[1] for o in only if o[0] == i]):
                kidx = EVENTS.index(kind)
                c = S.boot(ROM, S.KINDS['SITE'], i, kidx, 0, kit=2, frames=240)
                if here(c) != (a, r):
                    # the testbed could not land here (a spot the landing code refuses)
                    res = 'NOLAND'
                else:
                    dismiss(c)
                    C.call_keep(c, roll_fn, (i, 0x02000000, 0x02000004))
                    if site_done(c, i):
                        res = 'PRE-DONE'
                    elif c.memory.u8[0x02000000] != kidx:
                        # this run's memory pair sits here (QuickStartMemorySite,
                        # decided before the testbed's override): the site deals
                        # the lesson or the recital whatever is asked, and
                        # memory_probe.py covers that kind
                        res = 'MEMORY'
                    elif not spawned(c, kind):
                        res = 'NOSPAWN'
                    else:
                        ok, note = drive(c, kind, i, 0)
                        res = 'PASS' if ok else 'FAIL'
                        if not ok and here(c) != (a, r):
                            # the landing put the player on something that
                            # took them out of the room (site 8: the cave's
                            # exit stairs are a tile and a half below its spot)
                            res = 'LEFT'; note = 'now in %s' % (here(c),)
                results[res] += 1
                print('%-8s site %3d %-46s %-13s %s' % (res, i, rn, kind, note if res in ('PASS', 'FAIL') else ''), flush=True)
                if res in ('FAIL', 'LEFT'):
                    fails.append((i, rn, kind))
    print('\nSUMMARY', dict(results))
    if fails:
        print('FAILS:')
        for f in fails:
            print('  ', f)
    print('RESULT', 'FAIL' if fails else 'PASS')
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
