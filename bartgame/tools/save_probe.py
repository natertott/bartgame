"""Continue a legacy save in the actual ROM, then reload its v2 record.

    python tools/save_probe.py [--legacy-rom OLD.gba --legacy-map OLD.map]

With a legacy ROM, the fixture is written by that ROM's normal death/save
path. Without one, the same serialized v1 layout is constructed from the
current death/save record. No save files outside this process are touched.
"""
import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))
import probe as P
import critical_path as CP
import mgba.core
import mgba.image

SRAM = 0x0E000000
MAGIC = 0x54524142
CELLS = 25
MYST = 4 + CELLS * 13 + 2 + 3 + 3 + 3 + CELLS + 1 + 1
MYST_FLAGS = MYST + CELLS
WORLD_SIZE = (MYST_FLAGS + CELLS + CELLS * 10 + 3) & ~3


def checksum(data):
    value = 0x9E3779B9
    for byte in data:
        value = ((value ^ byte) * 16777619) & 0xFFFFFFFF
    return value


def ram(c, base, size):
    return bytes(P.r8(c, base+i) for i in range(size))


def record(c):
    magic, version, size = struct.unpack('<IHH', ram(c, SRAM, 8))
    assert magic == MAGIC, ('save magic', hex(magic))
    assert 8 + WORLD_SIZE < size < 4096, ('record size', size)
    data = ram(c, SRAM, size)
    assert struct.unpack('<I',data[-4:])[0] == checksum(data[:-4]), 'checksum'
    return version, data


def save_on_death(c):
    CP.dismiss(c)
    P.w8(c, P.sym('gActors')+2, 7)  # PS_DEAD, the normal save path
    P.w8(c, P.sym('gPl')+24, 121)   # dead_timer expires
    P.run(c, 6)
    return record(c)


def continue_record(data, rom):
    c = mgba.core.load_path(rom)
    c.bg_video = mgba.image.Image(240,160)
    c.set_video_buffer(c.bg_video)
    c.reset()
    for i,byte in enumerate(data):
        P.w8(c, SRAM+i, byte)
    P.run(c, 45)
    P.press(c, 'START', 2, 80)  # Continue is the first title choice
    CP.dismiss(c)
    assert CP.area(c)==0 and CP.gstate(c)==1, 'continued run must wake in Drain'
    return c


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--legacy-rom')
    parser.add_argument('--legacy-map')
    args=parser.parse_args()
    assert bool(args.legacy_rom)==bool(args.legacy_map), 'supply both legacy paths'
    current_rom, current_map = P.ROM, P.MAP
    if args.legacy_rom:
        P.MAP=args.legacy_map
        P._syms=None
    c=P.boot(rom=args.legacy_rom or current_rom, seed=0xB4A7)
    CP.dismiss(c)
    w=CP.world(c)
    world=P.sym('gWorld'); pl=P.sym('gPl')
    P.w8(c,pl+8,1|2|64)  # sword, bombs, shield; lamp and cloak unowned
    P.w8(c,pl+6,3); P.w8(c,pl+7,5); P.w16(c,pl+4,27)
    # Old unrelated optional mysteries may already have paid a prize.
    for i,cell in enumerate(w['key_cell']):
        P.w8(c,world+MYST+cell,0 if i==2 else 2|(1<<6))
        P.w8(c,world+MYST_FLAGS+cell,1|2)
        flags=world+4+cell*13+11
        P.w8(c,flags,P.r8(c,flags)|(0x08|0x02 if i==1 else 0))
    unrelated=next(i for i in range(CELLS) if i not in w['key_cell'])
    P.w8(c,world+4+unrelated*13+4,0x11)
    version, raw=save_on_death(c)
    if args.legacy_rom:
        assert version==1, ('legacy fixture version',version)
    else:
        data=bytearray(raw)
        struct.pack_into('<H',data,4,1)
        struct.pack_into('<I',data,len(data)-4,checksum(data[:-4]))
        raw=bytes(data)
    expected=bytearray(raw[8:8+WORLD_SIZE])
    seed=struct.unpack_from('<I',expected)[0]
    for i,cell in enumerate(w['key_cell']):
        expected[MYST+cell]=(8,5,7)[i]|(1<<4)|(((seed+cell)%3)<<6)
        flags=4+cell*13+11
        if i==0:
            expected[flags]|=0x08|0x02
            expected[MYST_FLAGS+cell]|=1|4
        else:
            expected[flags]&=~(0x08|0x02)
            expected[MYST_FLAGS+cell]=0
    P.MAP=current_map; P._syms=None
    c=continue_record(raw,current_rom)
    assert ram(c,P.sym('gWorld'),WORLD_SIZE)==bytes(expected), 'migration changed unrelated world data or failed task flags'
    for off,size in ((4,2),(6,1),(7,1),(8,1),(9,3),(30,1),(35,2)):
        saved=raw[8+WORLD_SIZE+off:8+WORLD_SIZE+off+size]
        assert ram(c,P.sym('gPl')+off,size)==saved, ('inventory preservation',off)
    version,migrated=record(c)
    assert version==2, ('upgraded version',version)
    assert migrated[8:8+WORLD_SIZE]==expected
    print('PASS legacy inventory, gates, loot and unrelated state preserved')
    print('PASS owned reward retained; unrelated old mystery completion cannot consume missing items')
    print('PASS migrated record written as v2 with valid checksum')
    # A v2 record is loaded without running migration a second time.
    c=continue_record(migrated,current_rom)
    assert ram(c,P.sym('gWorld'),WORLD_SIZE)==expected, 'v2 round trip'
    # Winning a trial and claiming its prize are distinct persistent states.
    lamp=w['key_cell'][1]
    P.w8(c,P.sym('gWorld')+MYST_FLAGS+lamp,4)
    expected[MYST_FLAGS+lamp]=4
    pocket=4+unrelated*13+4
    P.w8(c,P.sym('gWorld')+pocket,expected[pocket]|0x20)
    expected[pocket]|=0x20
    version,roundtrip=save_on_death(c)
    assert version==2 and roundtrip[8:8+WORLD_SIZE]==expected
    print('PASS v2 continue/death/save round trip')
    c=continue_record(roundtrip,current_rom)
    assert ram(c,P.sym('gWorld'),WORLD_SIZE)==expected
    assert not (P.r8(c,P.sym('gPl')+8)&4), 'unclaimed candle granted during reload'
    print('PASS unclaimed trial victory and opened pocket persist without auto-claim')
    # Bad checksum: the title must not silently continue a damaged record.
    corrupt=bytearray(migrated); corrupt[20]^=1
    c=mgba.core.load_path(current_rom); c.bg_video=mgba.image.Image(240,160)
    c.set_video_buffer(c.bg_video); c.reset()
    for i,byte in enumerate(corrupt): P.w8(c,SRAM+i,byte)
    P.run(c,45)
    P.w16(c,P.sym('gSeedOverride'),0xCC55); P.w16(c,P.sym('gSeedOverride')+2,0)
    P.press(c,'START',2,80); CP.dismiss(c)
    assert P.r32(c,P.sym('gWorld'))==0xCC55, 'corrupt record accepted instead of starting a fresh run'
    print('PASS corrupted checksum rejected')
    print('RESULT PASS 6/6')


if __name__=='__main__': main()
