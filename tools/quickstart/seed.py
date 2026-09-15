"""Roadmap A3: the fixed-seed playtest switch.

Every QUICKSTART run derives an RNG seed at run start and records it in
`gSave.run_seed`. Setting the pin flag makes the next run reuse that value
verbatim instead of deriving a fresh one, so a run can be replayed turn for
turn - same region chain, same shop stock and prices, same "? room"
contents, same fuser scatter.

Two things follow from the seed being RECORDED unconditionally, not only
when someone remembered to turn recording on:

  - A player's bug report is reproducible from their save file alone. The
    seed is in the .sav; `read_sav()` pulls it out.
  - The invariant checker can print the seed it happened to run on, so a
    failure that only shows up on some seeds can be re-run exactly.

Usage:
    python3 tools/quickstart/seed.py show [--rom tmc.gba]
    python3 tools/quickstart/seed.py show --sav tmc.sav
    python3 tools/quickstart/seed.py pin  0xDEADBEEF [--rom tmc.gba]
    python3 tools/quickstart/seed.py check [--rom tmc.gba]

`check` is the self-test: it pins one seed, boots twice, and reports whether
the two runs agree - and then boots on a different seed and reports whether
that one differs.
"""
import sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# gSave lives at 0x02002a40; run_seed is the QUICKSTART u32 at +0x4C (the old
# filler4c, see include/save.h). In a .sav the same struct is written from
# offset 0 of the slot, so the field sits at 0x4C there too.
SAVE_BASE = 0x02002a40
RUN_SEED_OFF = 0x4C
RUN_SEED = SAVE_BASE + RUN_SEED_OFF

# FLAG_BANK_11 (0x9C0) offset 174 - GF_SEED_PINNED in game.c.
SAVE_FLAGS_OFF = 0x25C
FLAG_BANK_11 = 0x9C0
SEED_PINNED_BIT = FLAG_BANK_11 + 174


def read_seed(c):
    return int.from_bytes(bytes(c.memory.u8[RUN_SEED + i] for i in range(4)), 'little')


def write_seed(c, seed):
    for i in range(4):
        c.memory.u8[RUN_SEED + i] = (seed >> (8 * i)) & 0xFF


def set_pin(c, on=True):
    a = SAVE_BASE + SAVE_FLAGS_OFF + (SEED_PINNED_BIT >> 3)
    m = 1 << (SEED_PINNED_BIT & 7)
    c.memory.u8[a] = (c.memory.u8[a] | m) if on else (c.memory.u8[a] & ~m)


def is_pinned(c):
    a = SAVE_BASE + SAVE_FLAGS_OFF + (SEED_PINNED_BIT >> 3)
    return bool(c.memory.u8[a] & (1 << (SEED_PINNED_BIT & 7)))


def boot_pinned(rom, seed, frames=240):
    """Boot `rom` with the run pinned to `seed`.

    Timing is the whole trick. Within one boot the order is: AgbMain sets
    gRand to its literal, InitSaveData loads gSave from SRAM, then
    GameTask_Transition runs the run-start block that reads the pin. So the
    pin only has to be in EWRAM between the load and the block - it does NOT
    have to reach SRAM, and a soft reset would actively destroy it, because
    the reset reloads gSave from SRAM and throws the in-RAM copy away. (That
    is the same trap the run counter hit; see the reseed comment in game.c.)

    Rather than guess which frame InitSaveData lands on, this rewrites the
    pin and seed on EVERY frame of the title sequence. Whichever frame the
    load happens on, a later write still precedes the run-start block.
    """
    import mgba.core, mgba.image
    from emu import ROOM_CONTROLS
    img = mgba.image.Image(240, 160)
    c = mgba.core.load_path(rom)
    c.set_video_buffer(img)
    c.qs_video = img
    c.reset()

    def hammer():
        write_seed(c, seed)
        set_pin(c, True)

    for _ in range(120):
        hammer()
        c.run_frame()
    for _ in range(300):
        for keys, hold in ((c.KEY_A, 3), (c.KEY_START, 3)):
            c.set_keys(keys)
            for _ in range(hold):
                hammer()
                c.run_frame()
            c.clear_keys(keys)
            for _ in range(3):
                hammer()
                c.run_frame()
        if c.memory.u8[ROOM_CONTROLS + 4] != 0:
            break
    for _ in range(frames):
        c.run_frame()
    return c


def soft_reset(c):
    """A+B+START+SELECT, then back through the title into a fresh run."""
    from emu import press, ROOM_CONTROLS
    for _ in range(20):
        c.set_keys(c.KEY_A, c.KEY_B, c.KEY_START, c.KEY_SELECT)
        c.run_frame()
    c.clear_keys(c.KEY_A, c.KEY_B, c.KEY_START, c.KEY_SELECT)
    for _ in range(60):
        c.run_frame()
    for _ in range(120):
        c.run_frame()
    for _ in range(300):
        press(c, c.KEY_A, 3, 3)
        press(c, c.KEY_START, 3, 3)
        if c.memory.u8[ROOM_CONTROLS + 4] != 0:
            break
    for _ in range(180):
        c.run_frame()


# Where each save slot's SaveFile starts in the EEPROM image, straight out
# of gSaveFileEEPROMAddresses (src/save.c): three slots of 0x500 bytes, each
# written twice - the second copy is the backup the game falls back on.
# TMC saves to EEPROM, not SRAM, which is why a .sav is 8KB and why
# mgba's memory.sram holds none of this.
SAV_SLOT_BASES = (0x080, 0x580, 0xA80)
SAV_MIRROR = 0x1000


def read_sav(path):
    """The run seed out of a .sav, without booting anything.

    CAVEAT, because it matters before you trust an answer from this: the
    offsets are derived from the game's own EEPROM address table, but they
    have NOT been checked against a real QUICKSTART save. Producing one
    inside this harness needs mgba to flush its save file, and mgba
    segfaults on core teardown here before it does. A save from actual play
    would settle it in seconds - until then treat a plausible-looking
    number as plausible, not confirmed, and cross-check it by pinning the
    value and seeing whether the run matches what was reported.
    """
    data = open(path, 'rb').read()
    out = []
    for i, base in enumerate(SAV_SLOT_BASES):
        for mirror in (0, SAV_MIRROR):
            off = base + mirror + RUN_SEED_OFF
            if off + 4 > len(data):
                continue
            seed = int.from_bytes(data[off:off + 4], 'little')
            if seed not in (0, 0xFFFFFFFF):
                out.append((i, base + mirror, seed))
    return out


def _fingerprint(c):
    """A cheap signature of what this run rolled.

    The shop's drawn stock plus Lon Lon Ranch's fuser scatter: two
    independent per-run draws, in two different rooms, so agreement is
    unlikely to be coincidence.
    """
    from emu import warp, here, entities, ROOM_CONTROLS, r16
    sig = []
    warp(c, 48, 1, 120, 104, frames=300)
    if here(c) == (48, 1):
        ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
        sig.append(tuple(sorted((e[3], e[4] - ox, e[5] - oy)
                                for e in entities(c) if e[1] == 6)))
    warp(c, 3, 5, 344, 870, frames=320)
    if here(c) == (3, 5):
        ox, oy = r16(c, ROOM_CONTROLS + 6), r16(c, ROOM_CONTROLS + 8)
        sig.append(tuple(sorted((e[4] - ox, e[5] - oy)
                                for e in entities(c) if e[1] == 7 and e[2] == 0x28)))
    return tuple(sig)


def main(argv):
    cmd = argv[0] if argv else 'show'
    rom = 'tmc.gba'
    if '--rom' in argv:
        rom = argv[argv.index('--rom') + 1]

    if cmd == 'show' and '--sav' in argv:
        rows = read_sav(argv[argv.index('--sav') + 1])
        if not rows:
            print('no run seed found - an empty save, or one written before '
                  'gSave.run_seed existed')
        for i, off, seed in rows:
            print(f'save {i} @0x{off:04x}: seed 0x{seed:08x}')
        print('(offsets from src/save.c; not yet cross-checked against a '
              'save from real play - see read_sav)')
        return 0

    from emu import boot
    if cmd == 'show':
        c = boot(rom)
        print(f'seed 0x{read_seed(c):08x}   pinned={is_pinned(c)}')
        return 0

    if cmd == 'pin':
        seed = int(argv[1], 0)
        c = boot_pinned(rom, seed)
        got = read_seed(c)
        print(f'pinned 0x{seed:08x} -> run is on 0x{got:08x}   '
              f'{"OK" if got == seed else "MISMATCH"}')
        return 0 if got == seed else 1

    if cmd == 'check':
        want = 0x0BADC0DE
        a = boot_pinned(rom, want)
        sa = read_seed(a)
        fa = _fingerprint(a)
        b = boot_pinned(rom, want)
        sb = read_seed(b)
        fb = _fingerprint(b)
        d = boot_pinned(rom, 0x12345678)
        sd = read_seed(d)
        fd = _fingerprint(d)
        print(f'run A pinned 0x{want:08x} -> seed 0x{sa:08x}')
        print(f'run B pinned 0x{want:08x} -> seed 0x{sb:08x}')
        print(f'run C pinned 0x12345678 -> seed 0x{sd:08x}')
        same = (sa == sb == want) and fa == fb
        differs = fd != fa
        print()
        print(f'same seed reproduces the run: {same}')
        print(f'a different seed changes it:  {differs}')
        print('RESULT:', 'PASS' if (same and differs) else 'FAIL')
        return 0 if (same and differs) else 1

    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
