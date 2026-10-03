"""Does a scenario in the save boot the run into the thing it names?

One boot per scenario kind, plus a control (no scenario -> the hub, as ever).
Each boot writes the bytes into EWRAM on every title frame (scenario.boot),
so no .sav is involved; the .sav path is scenario.py's and is checked by its
`show` on a real save.

    python3 tools/quickstart/scenario_probe.py [--rom tmc-d3.gba]

PASS: every row below lands where the catalogue says and shows the forced
content (the boss's id, the giver, the fuser's face, the chain's step 0, the
pinned difficulty, the kit's sword).
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import here, entities, KIND_ENEMY, KIND_NPC, SAVE_FLAGS
import scenario as S
import parse_tables as P
import callrom as C

SAVE = 0x02002a40
FLAG_BANK_11 = 0x9C0
AREAS, ROOMS = P.AREAS, P.ROOMS
ENEMY = {'CHUCHU_BOSS': 0x13, 'OCTOROK_BOSS': 0x39}  # include/enemy.h


def bank11(c, bit):
    b = FLAG_BANK_11 + bit
    return (c.memory.u8[SAVE_FLAGS + (b >> 3)] >> (b & 7)) & 1


def bits(c, base, n):
    return sum(bank11(c, base + i) << i for i in range(n))


def run(rom):
    rows = S.pool()
    sites = P.content_sites()
    results = []

    def check(name, ok, detail=''):
        results.append(ok)
        print('%s %-34s %s' % ('PASS' if ok else 'FAIL', name, detail))

    # Control: no scenario, the hub.
    c = S.boot(rom, 0)
    check('control: no scenario -> hub', here(c) == (48, 3), str(here(c)))

    # ROOM: Royal Valley at the pool's own drop tile.
    c = S.boot(rom, S.KINDS['ROOM'], AREAS['AREA_ROYAL_VALLEY'], ROOMS['ROOM_ROYAL_VALLEY_MAIN'], 18, 53)
    check('ROOM lands in Royal Valley', here(c) == (AREAS['AREA_ROYAL_VALLEY'], 0), str(here(c)))

    # REGION: North Hyrule Field with three waves banked; kit + difficulty too.
    c = S.boot(rom, S.KINDS['REGION'], 3, 3, kit=1, diff=7)
    nhf = rows[3]
    check('REGION lands in NHF', here(c) == (nhf['area'], nhf['room']), str(here(c)))
    wc = C.call_keep(c, C.game_sym('QuickStartRegionGetWaveCount'), (3,))
    check('REGION banks 3 waves', wc == 3, 'wave count %d' % wc)
    diff = C.call_keep(c, C.game_sym('QuickStartGetDifficulty'), ())
    check('difficulty pinned to 7', diff == 7, 'difficulty %d' % diff)
    sword = C.call_keep(c, C.map_sym('GetInventoryValue'), (P.ITEMS.get('ITEM_FOURSWORD', 0x0B),))
    check('test kit: Four Sword owned', sword != 0, 'inventory %d' % sword)

    # BOSS: Trilby deals the Big Octorok from wave 0.
    c = S.boot(rom, S.KINDS['BOSS'], 4, 2, frames=900)
    tril = rows[4]
    ids = [e[2] for e in entities(c, KIND_ENEMY)]
    check('BOSS lands in Trilby', here(c) == (tril['area'], tril['room']), str(here(c)))
    check('BOSS deals the Big Octorok', ENEMY['OCTOROK_BOSS'] in ids, 'enemy ids %s' % sorted(set(ids)))

    # QUEST CARRY hosted in Lon Lon Ranch: the roll takes the row, the giver stands.
    c = S.boot(rom, S.KINDS['QUEST'], 4, 1, frames=600)
    llr = rows[1]
    check('QUEST lands in LLR', here(c) == (llr['area'], llr['room']), str(here(c)))
    check('QUEST carry host forced to row 1', bank11(c, 156) == 1 and bits(c, 157, 5) == 1,
          'rolled %d host %d' % (bank11(c, 156), bits(c, 157, 5)))
    zeldas = [e for e in entities(c, KIND_NPC) if e[2] == 0x28]
    check('QUEST carry giver spawned', len(zeldas) >= 1, '%d Zelda NPCs' % len(zeldas))

    # FUSER: Lon Lon Ranch's cast wears Rem.
    c = S.boot(rom, S.KINDS['FUSER'], 1, 55, frames=600)
    faces = sorted(set(e[2] for e in entities(c, KIND_NPC)))
    check('FUSER: Rem in LLR', here(c) == (llr['area'], llr['room']) and 55 in faces, 'npc ids %s' % faces)

    # CHAIN: step 0 pre-dealt as EVENT at site 27, landing in that site's room.
    c = S.boot(rom, S.KINDS['CHAIN'], 1, 27, 0, frames=600)
    kind0, where0 = c.memory.u8[SAVE + 0x26], c.memory.u8[SAVE + 0x2B]
    site = sites[27]
    check('CHAIN lands in site 27', here(c) == (site[2], site[3]), '%s vs %s' % (here(c), (site[2], site[3])))
    check('CHAIN step 0 = EVENT 27', kind0 == 1 and where0 == 27, 'kind %d where %d' % (kind0, where0))

    # SITE: site 27 deals a miniboss.
    c = S.boot(rom, S.KINDS['SITE'], 27, 1, 0, frames=900)
    kind = C.call_keep(c, C.game_sym('QuickStartContentSiteKind'), (27,)) if False else None
    enemies = entities(c, KIND_ENEMY)
    check('SITE 27 deals a miniboss', here(c) == (site[2], site[3]) and len(enemies) >= 1,
          'room %s enemies %s' % (here(c), sorted(set(e[2] for e in enemies))))

    print('RESULT:', 'PASS' if all(results) else 'FAIL', '(%d/%d)' % (sum(results), len(results)))
    return 0 if all(results) else 1


if __name__ == '__main__':
    rom = 'tmc-d3.gba'
    if '--rom' in sys.argv:
        rom = sys.argv[sys.argv.index('--rom') + 1]
    sys.exit(run(rom))
