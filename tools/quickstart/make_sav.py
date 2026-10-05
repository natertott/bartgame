"""Build a complete .sav around a scenario, with no save to start from.

scenario.py writes a scenario INTO an existing save. This makes the save:
it boots the ROM once (no file attached), takes the game's own freshly
started SaveFile and SaveHeader out of EWRAM, writes the scenario bytes
into the file, and lays the two out the way src/save.c lays them out in
EEPROM - signature at 0 and 0x1000, the header at 0x70/0x1070 with its
status at 0x20/0x1020, file 0 at 0x80/0x1080 with its status at
0x30/0x1030, files 1 and 2 and the index-5 block marked INIT, every status
checksummed with CalculateChecksum. The image is then stored 8-byte-block
reversed, which is how mGBA (and VBA before it) keep this game's EEPROM.

    python3 tools/quickstart/make_sav.py OUT.sav KIND [a b c d] [--kit all] [--diff N] [--rom tmc-d3.gba]
    python3 tools/quickstart/make_sav.py OUT.sav boss 0 2 --kit all     # Big Octorok in Castle Garden

KIND and the parameters are scenario.py's words (site/boss/quest/chain/
region/fuser/room; names resolve the same way), or the raw kind number.

Honesty: the harness's mgba cannot attach a save file (it crashes), so the
layout was never loaded back by the game here. It is transcribed from
src/save.c and the one header mGBA wrote in this environment. If the file
select shows no file, the first thing to try is the un-reversed layout
(`--plain`).
"""
import os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import scenario as S

SAVE_BASE = 0x02002a40
HEADER_BASE = 0x02000000   # gSaveHeader (include/save.h)
FILE_SIZE = 0x500
HEADER_SIZE = 0x10
SIGNATURE = b'AGBZELDA:THE MINISH CAP:ZELDA 3\x00'  # sSignatureLong (USA), src/save.c
STATUS_FILE = 0x4D435A33   # 'MCZ3'
STATUS_INIT = 0x54494E49   # 'TINI'
# (size, checksum1, checksum2, address1, address2) - gSaveFileEEPROMAddresses
SLOTS = {0: (0x500, 0x30, 0x1030, 0x80, 0x1080), 1: (0x500, 0x40, 0x1040, 0x580, 0x1580),
         2: (0x500, 0x50, 0x1050, 0xa80, 0x1a80), 3: (0x10, 0x20, 0x1020, 0x70, 0x1070),
         4: (0x20, 0, 0, 0, 0x1000), 5: (0x20, 0x60, 0x1060, 0xf80, 0x1f80)}


def _checksum(words):
    total, size = 0, len(words) * 2
    for w in words:
        total += (w ^ size) & 0xFFFF
        size -= 2
    return total & 0xFFFF


def status_for(data):
    words = struct.unpack('<%dH' % (len(data) // 2), data)
    ck = (_checksum(struct.unpack('<2H', struct.pack('<I', STATUS_FILE))) + _checksum(words)) & 0xFFFF
    return struct.pack('<HHI', ck, (-ck) & 0xFFFF, STATUS_FILE)


def build_image(save_file, header, scn):
    img = bytearray(b'\xff' * 0x2000)
    data = bytearray(save_file)
    data[S.SCN_OFF:S.SCN_OFF + 6] = bytes(scn)
    data[0x3e] = 0  # carry_item
    data[0x3f] = 0  # carry_want
    init = struct.pack('<HHI', 0xffff, 0xffff, STATUS_INIT)
    for idx, (size, c1, c2, a1, a2) in SLOTS.items():
        if idx == 4:
            img[a1:a1 + size] = SIGNATURE[:size]
            img[a2:a2 + size] = SIGNATURE[:size]
            continue
        if idx == 0:
            blob, st = bytes(data), status_for(bytes(data))
        elif idx == 3:
            blob, st = bytes(header), status_for(bytes(header))
        else:
            blob, st = None, init
        for coff, aoff in ((c1, a1), (c2, a2)):
            img[coff:coff + 8] = st
            if blob is not None:
                img[aoff:aoff + size] = blob
    return bytes(img)


def swap8(data):
    out = bytearray(len(data))
    for i in range(0, len(data), 8):
        out[i:i + 8] = data[i:i + 8][::-1]
    return bytes(out)


def snapshot(rom):
    """A freshly started run's SaveFile and SaveHeader, out of EWRAM."""
    from emu import boot
    c = boot(rom)
    save = bytes(c.memory.u8[SAVE_BASE + i] for i in range(FILE_SIZE))
    header = bytes(c.memory.u8[HEADER_BASE + i] for i in range(HEADER_SIZE))
    return save, header


def make(out, scn, rom='tmc-d3.gba', plain=False, snap=None):
    save, header = snap if snap is not None else snapshot(rom)
    img = build_image(save, header, scn)
    open(out, 'wb').write(img if plain else swap8(img))
    return out


def parse_args(argv):
    rom, plain, kit, diff, land = 'tmc-d3.gba', False, 0, 0, 0
    rest = []
    it = iter(argv)
    for x in it:
        if x == '--rom': rom = next(it)
        elif x == '--plain': plain = True
        elif x == '--kit': kit = S.KITS[next(it)]
        elif x == '--diff': diff = int(next(it))
        elif x == '--land': land = S.resolve_row(next(it))
        else: rest.append(x)
    return rom, plain, kit, diff, land, rest


def scenario_bytes(cmd, rest, kit, diff, land):
    if cmd == 'clear':
        return S.pack(0)
    if cmd == 'site':
        return S.pack(1, S.resolve_site(rest[0]), S.resolve_enum(rest[1], S.EVENTS, 'event kind'),
                      int(rest[2], 0) if len(rest) > 2 else 0, (land + 1) if land else 0, kit, diff)
    if cmd == 'boss':
        return S.pack(2, S.resolve_row(rest[0]), S.resolve_enum(rest[1], S.BOSSES, 'boss form') if len(rest) > 1 else 0, 0, 0, kit, diff)
    if cmd == 'quest':
        return S.pack(3, S.resolve_enum(rest[0], S.QUESTS, 'quest kind'), S.resolve_row(rest[1]), 0, 0, kit, diff)
    if cmd == 'chain':
        k = S.resolve_enum(rest[0], S.CHAIN, 'chain kind')
        where = rest[1] if len(rest) > 1 else '0'
        where = S.resolve_site(where) if k == 1 else (S.resolve_row(where) if k in (2, 3) else int(where, 0))
        return S.pack(4, k, where, int(rest[2], 0) if len(rest) > 2 else 0, land, kit, diff)
    if cmd == 'region':
        return S.pack(5, S.resolve_row(rest[0]), int(rest[1]) if len(rest) > 1 else 0, 0, 0, kit, diff)
    if cmd == 'fuser':
        return S.pack(6, int(rest[0]), S.resolve_face(rest[1]), 0, 0, kit, diff)
    if cmd == 'room':
        import parse_tables as T
        return S.pack(7, T.AREAS[rest[0]] if not rest[0].isdigit() else int(rest[0]),
                      T.ROOMS[rest[1]] if not rest[1].isdigit() else int(rest[1]), int(rest[2]), int(rest[3]), kit, diff)
    raise SystemExit('unknown kind %r' % cmd)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(2)
    out, cmd = sys.argv[1], sys.argv[2]
    rom, plain, kit, diff, land, rest = parse_args(sys.argv[3:])
    scn = scenario_bytes(cmd, rest, kit, diff, land)
    make(out, scn, rom, plain)
    print('%s <- %s' % (out, S.describe(scn)))
