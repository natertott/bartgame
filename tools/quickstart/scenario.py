"""The feature testbed's front door: write a scenario into a save.

A scenario is eight bytes in the QUICKSTART save (SaveFile.scenario_*,
include/save.h) that the run-start code reads once (QuickStartScenarioRunStart,
src/game.c) and the four dealers consult when they roll. With one set, the
run skips the hub, hands out the kit asked for, pins the difficulty, and lands
the player in the scenario's room with the dice loaded for exactly one
feature. No rebuild - which is the whole point.

    python3 tools/quickstart/scenario.py list                 # the catalogue
    python3 tools/quickstart/scenario.py site  27 WAVES 5     # site 27 deals a 3-wave gauntlet, draw seed 5
    python3 tools/quickstart/scenario.py site  ROOM_CAVES_BOOMERANG MINIBOSS 2
    python3 tools/quickstart/scenario.py boss  TRILBY OCTOROK
    python3 tools/quickstart/scenario.py quest CARRY LLR
    python3 tools/quickstart/scenario.py chain EVENT 27 0 --land NHF
    python3 tools/quickstart/scenario.py region NHF 3          # arrive with 3 waves already cleared
    python3 tools/quickstart/scenario.py fuser 1 REM
    python3 tools/quickstart/scenario.py room  AREA_ROYAL_VALLEY ROOM_ROYAL_VALLEY_MAIN 20 30
    python3 tools/quickstart/scenario.py clear
    python3 tools/quickstart/scenario.py show --sav tmc-d3.sav

Every writing command takes `--sav FILE` (default tmc-d3.sav), `--kit none|test|all`
and `--diff N`. Regions may be named by pool row number, by a short name
(CG LLR SHF NHF TRIL EH EHC EHN WW WWC WWN RV CW WR WRN MW LH CREN VF) or by
ROOM_* name. Sites by index or ROOM_* name (the first site in that room).

The .sav is an EEPROM image: three 0x500-byte slots, each written twice, each
with a status block (checksum over 'MCZ3' plus the slot). Only slots whose
status says they hold a file are touched, and the checksums are redone so
the game keeps trusting them. Two byte layouts are in use among emulators
for EEPROM saves (as written, and 8-byte-block reversed - mGBA's, measured
from its own header); this picks the one under which the file's checksums
verify (or, with no file yet, the one showing the header) and refuses when
neither fits rather than guess.

CAVEAT: the slot write has not been driven end to end here. The harness's
mgba binding crashes with any save file attached, so the checksum
arithmetic is transcribed from src/save.c (CalculateChecksum,
DataDoubleWriteWithStatus) and untested against the game's own reading of
it. First real use: `show` the save afterwards, and if the game reports the
file corrupt, the arithmetic is the suspect.

For the harness there is `boot(rom, **scenario)`: same bytes, written into
EWRAM on every title frame (seed.py's trick) so no .sav is needed.
"""
import sys, os, struct

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parse_tables as T

SAVE_BASE = 0x02002a40
SCN_OFF = 0x38           # scenario_kind .. scenario_kitdiff = 0x38..0x3d
SLOT_SIZE = 0x500
# (checksum1, checksum2, address1, address2) per slot - gSaveFileEEPROMAddresses
SLOTS = ((0x30, 0x1030, 0x80, 0x1080), (0x40, 0x1040, 0x580, 0x1580), (0x50, 0x1050, 0xa80, 0x1a80))
STATUS_FILE = 0x4D435A33  # 'MCZ3' as agbcc evaluates the multichar constant

KINDS = {'NONE': 0, 'SITE': 1, 'BOSS': 2, 'QUEST': 3, 'CHAIN': 4, 'REGION': 5, 'FUSER': 6, 'ROOM': 7}
KIND_NAMES = {v: k for k, v in KINDS.items()}
EVENTS = ['ITEM_DROP', 'MINIBOSS', 'NPC', 'WAVES', 'POT_LOTTERY', 'CHEST_LOTTERY', 'FAIRY', 'MEMORY']
CHAIN = ['ITEM', 'EVENT', 'WAVE', 'BOSS', 'QUEST']
QUESTS = ['POT', 'HUNT', 'SCAV', 'STEALTH', 'CARRY']
BOSSES = {'GREEN': 0, 'CHUCHU': 0, 'BLUE': 1, 'ELECTRIC': 1, 'OCTOROK': 2}
KITS = {'none': 0, 'test': 1, 'all': 2}
# Pool rows by position - the pool's own order (QuickStartRegionOfPoolIndex).
SHORT = ['CG', 'LLR', 'SHF', 'NHF', 'TRIL', 'EH', 'EHC', 'EHN', 'WW', 'WWC', 'WWN',
         'RV', 'CW', 'WR', 'WRN', 'MW', 'LH', 'CREN', 'VF', 'HT']
FACES = ['ZELDA', 'POSTMAN', 'WHEATON', 'PITA', 'REM', 'ANJU', 'KID']


def npc_ids():
    import re
    src = open(os.path.join(T.ROOT, 'include/npc.h')).read()
    i = src.find('enum')
    body = src[i:src.find('}', i)]
    out, n = {}, 0
    for m in re.finditer(r'^\s*([A-Z_0-9]+)\s*(?:=\s*(0x[0-9a-fA-F]+|\d+))?\s*,', body, re.M):
        if m.group(2):
            n = int(m.group(2), 0)
        out[m.group(1)] = n
        n += 1
    return out


def pool():
    return T.region_pool()


def resolve_row(name):
    rows = pool()
    if name.isdigit():
        return int(name) % len(rows)
    u = name.upper()
    if u in SHORT:
        return SHORT.index(u)
    for i, r in enumerate(rows):
        if r['roomName'] == u or r['roomName'].endswith('_' + u):
            return i
    raise SystemExit('unknown region %r (use a pool row, %s, or a ROOM_* name)' % (name, ' '.join(SHORT)))


def resolve_site(name):
    sites = T.content_sites()
    if name.isdigit():
        return int(name)
    u = name.upper()
    for i, s in enumerate(sites):
        if s[1] == u:
            return i
    raise SystemExit('unknown site %r' % name)


def resolve_enum(name, table, what):
    if name.isdigit():
        return int(name)
    u = name.upper()
    if u in table:
        return table.index(u) if isinstance(table, list) else table[u]
    raise SystemExit('unknown %s %r (one of %s)' % (what, name, ' '.join(table)))


def resolve_face(name):
    if name.isdigit():
        return int(name)
    ids = npc_ids()
    if name.upper() in ids:
        return ids[name.upper()]
    raise SystemExit('unknown NPC %r' % name)


# ---------------------------------------------------------------- the .sav
def _checksum(words):
    """CalculateChecksum (src/save.c): sum of (word ^ remaining size), u16."""
    total, size = 0, len(words) * 2
    for w in words:
        total += (w ^ size) & 0xFFFF
        size -= 2
    return total & 0xFFFF


def _file_checksum(slot_bytes):
    status_words = struct.unpack('<2H', struct.pack('<I', STATUS_FILE))
    data_words = struct.unpack('<%dH' % (len(slot_bytes) // 2), slot_bytes)
    return (_checksum(status_words) + _checksum(data_words)) & 0xFFFF


def _swap8(data):
    out = bytearray(len(data))
    for i in range(0, len(data) - 7, 8):
        out[i:i + 8] = data[i:i + 8][::-1]
    return bytes(out)


HEADER_MAGIC = b'AGBZELDA:THE MINISH CAP:'  # the EEPROM header the title screen writes


def _layout(data):
    """'plain' or 'swapped': whichever makes a slot's status verify, or,
    failing a slot, whichever shows the game's own header at offset 0.

    The header rule is measured, not assumed: an mGBA .sav of this ROM with
    no file in it yet reads "ADLEZBGANIM EHT:..." - the header in 8-byte
    blocks each stored back to front - so that emulator's layout is
    'swapped'. A slot that verifies still wins, because it proves the
    checksum arithmetic along with the layout.
    """
    for name, view in (('plain', data), ('swapped', _swap8(data))):
        for c1, c2, a1, a2 in SLOTS:
            for coff, aoff in ((c1, a1), (c2, a2)):
                ck1, ck2, status = struct.unpack_from('<HHI', view, coff)
                if status == STATUS_FILE and ck1 == _file_checksum(view[aoff:aoff + SLOT_SIZE]):
                    return name
    for name, view in (('plain', data), ('swapped', _swap8(data))):
        if view[:len(HEADER_MAGIC)] == HEADER_MAGIC:
            return name
    return None


def read_sav(path):
    data = open(path, 'rb').read()
    layout = _layout(data)
    if layout is None:
        return None, []
    view = data if layout == 'plain' else _swap8(data)
    out = []
    for i, (c1, c2, a1, a2) in enumerate(SLOTS):
        for coff, aoff in ((c1, a1), (c2, a2)):
            ck1, ck2, status = struct.unpack_from('<HHI', view, coff)
            if status != STATUS_FILE:
                continue
            out.append((i, aoff, view[aoff + SCN_OFF:aoff + SCN_OFF + 6]))
    return layout, out


def write_sav(path, scn):
    data = open(path, 'rb').read()
    layout = _layout(data)
    if layout is None:
        raise SystemExit('%s: no save slot verifies under either EEPROM layout - '
                         'is this a save the game has written?' % path)
    view = bytearray(data if layout == 'plain' else _swap8(data))
    touched = 0
    for c1, c2, a1, a2 in SLOTS:
        for coff, aoff in ((c1, a1), (c2, a2)):
            ck1, ck2, status = struct.unpack_from('<HHI', view, coff)
            if status != STATUS_FILE:
                continue
            view[aoff + SCN_OFF:aoff + SCN_OFF + 6] = bytes(scn)
            ck = _file_checksum(bytes(view[aoff:aoff + SLOT_SIZE]))
            struct.pack_into('<HHI', view, coff, ck, (-ck) & 0xFFFF, STATUS_FILE)
            touched += 1
    out = bytes(view) if layout == 'plain' else _swap8(bytes(view))
    open(path, 'wb').write(out)
    return layout, touched


# ---------------------------------------------------------------- the harness
def boot(rom, kind, a=0, b=0, c=0, d=0, kit=0, diff=0, seed=None, frames=240):
    """Boot `rom` into the scenario, hammering the bytes into gSave on every
    title frame (seed.boot_pinned's timing argument applies verbatim)."""
    import mgba.core, mgba.image
    from emu import ROOM_CONTROLS
    import seed as seedmod
    scn = pack(kind, a, b, c, d, kit, diff)
    img = mgba.image.Image(240, 160)
    core = mgba.core.load_path(rom)
    core.set_video_buffer(img)
    core.qs_video = img
    core.reset()

    def hammer():
        for i, v in enumerate(scn):
            core.memory.u8[SAVE_BASE + SCN_OFF + i] = v
        if seed is not None:
            seedmod.write_seed(core, seed)
            seedmod.set_pin(core, True)

    for _ in range(120):
        hammer()
        core.run_frame()
    for _ in range(300):
        for keys, hold in ((core.KEY_A, 3), (core.KEY_START, 3)):
            core.set_keys(keys)
            for _ in range(hold):
                hammer()
                core.run_frame()
            core.clear_keys(keys)
            for _ in range(3):
                hammer()
                core.run_frame()
        if core.memory.u8[ROOM_CONTROLS + 4] != 0:
            break
    for _ in range(frames):
        core.run_frame()
    return core


def pack(kind, a=0, b=0, c=0, d=0, kit=0, diff=0):
    return bytes([kind & 0xFF, a & 0xFF, b & 0xFF, c & 0xFF, d & 0xFF, ((kit & 3) << 4) | (diff & 0xF)])


def describe(scn):
    kind, a, b, c, d, kd = scn[:6]
    name = KIND_NAMES.get(kind, '?%d' % kind)
    kit, diff = (kd >> 4) & 3, kd & 0xF
    tail = '  kit=%s diff=%s' % ({0: 'none', 1: 'test', 2: 'all', 3: 'all'}[kit], diff or 'build')
    rows = pool()
    rn = lambda i: rows[i % len(rows)]['roomName'] if rows else str(i)
    if kind == 0:
        return 'NONE (a normal run)'
    if kind == 1:
        s = T.content_sites()
        where = s[a][1] if a < len(s) else '?'
        return 'SITE %d (%s) deals %s extra %d, opens row %s%s' % (
            a, where, EVENTS[b] if b < len(EVENTS) else b, c, (d - 1) if d else '-', tail)
    if kind == 2:
        return 'BOSS row %d (%s) form %s%s' % (a, rn(a), {0: 'green', 1: 'blue', 2: 'octorok', 3: 'octorok'}[b & 3], tail)
    if kind == 3:
        return 'QUEST %s hosted in row %d (%s)%s' % (QUESTS[a] if a < len(QUESTS) else a, b, rn(b), tail)
    if kind == 4:
        return 'CHAIN step 0 = %s where %d detail %d, land row %d (%s)%s' % (
            CHAIN[a] if a < len(CHAIN) else a, b, c, d, rn(d), tail)
    if kind == 5:
        return 'REGION row %d (%s) with %d waves cleared%s' % (a, rn(a), b, tail)
    if kind == 6:
        ids = {v: k for k, v in npc_ids().items()}
        return 'FUSER spot room %d wears %s%s' % (a, ids.get(b, b), tail)
    if kind == 7:
        return 'ROOM area %d room %d at tile (%d, %d)%s' % (a, b, c, d, tail)
    return name + tail


def catalogue():
    rows = pool()
    print('== pool rows (regions) ==')
    for i, r in enumerate(rows):
        print('  %2d %-5s %s / %s  drop %s' % (i, SHORT[i] if i < len(SHORT) else '', r['areaName'], r['roomName'], r['entrance']))
    print('== content sites ==')
    for i, s in enumerate(T.content_sites_full()):
        gate = ('  gate kinstone %d' % s[6]) if s[6] else ''
        print('  %3d %s / %s  content (%d, %d)%s' % (i, s[0], s[1], s[4], s[5], gate))
    print('== event kinds ==   ' + ' '.join('%d=%s' % (i, k) for i, k in enumerate(EVENTS)))
    print('== chain kinds ==   ' + ' '.join('%d=%s' % (i, k) for i, k in enumerate(CHAIN)))
    print('== quest kinds ==   ' + ' '.join('%d=%s' % (i, k) for i, k in enumerate(QUESTS)))
    print('== boss forms ==    0=green chuchu 1=blue chuchu 2=octorok')
    print('== fuser spot rooms ==')
    for i, f in enumerate(T.fuser_spots()):
        print('  %2d %s / %s' % (i, f['areaName'], f['roomName']))
    print('== fuser faces ==   ' + ' '.join(FACES))


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    sav = 'tmc-d3.sav'
    kit = diff = 0
    land = 0
    rest = []
    it = iter(argv[1:])
    for x in it:
        if x == '--sav':
            sav = next(it)
        elif x == '--kit':
            kit = KITS[next(it)]
        elif x == '--diff':
            diff = int(next(it))
        elif x == '--land':
            land = resolve_row(next(it))
        else:
            rest.append(x)
    if cmd == 'list':
        catalogue()
        return 0
    if cmd == 'show':
        layout, rows = read_sav(sav)
        if layout is None:
            print('%s: no verifying save slot' % sav)
            return 1
        print('%s (%s layout)' % (sav, layout))
        for i, off, scn in rows:
            print('  slot %d @0x%04x: %s' % (i, off, describe(scn)))
        return 0
    if cmd == 'clear':
        scn = pack(0)
    elif cmd == 'site':
        scn = pack(1, resolve_site(rest[0]), resolve_enum(rest[1], EVENTS, 'event kind'),
                   int(rest[2], 0) if len(rest) > 2 else 0, (land + 1) if land else 0, kit, diff)
    elif cmd == 'boss':
        scn = pack(2, resolve_row(rest[0]), resolve_enum(rest[1], BOSSES, 'boss form') if len(rest) > 1 else 0,
                   0, 0, kit, diff)
    elif cmd == 'quest':
        scn = pack(3, resolve_enum(rest[0], QUESTS, 'quest kind'), resolve_row(rest[1]), 0, 0, kit, diff)
    elif cmd == 'chain':
        k = resolve_enum(rest[0], CHAIN, 'chain kind')
        where = rest[1] if len(rest) > 1 else '0'
        where = resolve_site(where) if k == 1 else (resolve_row(where) if k in (2, 3) else int(where, 0))
        scn = pack(4, k, where, int(rest[2], 0) if len(rest) > 2 else 0, land, kit, diff)
    elif cmd == 'region':
        scn = pack(5, resolve_row(rest[0]), int(rest[1]) if len(rest) > 1 else 0, 0, 0, kit, diff)
    elif cmd == 'fuser':
        scn = pack(6, int(rest[0]), resolve_face(rest[1]), 0, 0, kit, diff)
    elif cmd == 'room':
        scn = pack(7, T.AREAS[rest[0]] if not rest[0].isdigit() else int(rest[0]),
                   T.ROOMS[rest[1]] if not rest[1].isdigit() else int(rest[1]),
                   int(rest[2]), int(rest[3]), kit, diff)
    else:
        print(__doc__)
        return 2
    print('scenario:', describe(scn), ' bytes', scn.hex())
    if not os.path.exists(sav):
        print('%s does not exist - start the game once so it writes a save, then rerun' % sav)
        return 1
    layout, touched = write_sav(sav, scn)
    print('wrote %d slot copies in %s (%s layout)' % (touched, sav, layout))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
