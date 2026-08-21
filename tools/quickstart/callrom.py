"""Call a function inside the running ROM and read what it returns.

A Python re-implementation of a C rule is a claim about the C, never a
measurement of it. This runs the shipped code: warp the game into the state
you want to ask about, then hand the CPU the function's address and read r0.

Two details make it work rather than crash:

  * mgba's binding refuses to write r15, so PC is set the way the hardware
    sets it - park the target in r3 and have ARMRunFake execute a `bx r3`,
    which reloads the prefetch pipeline. The `bx` encoding depends on the
    mode the CPU happens to be in when you interrupt it, and after a warp
    that is usually ARM (the BIOS IRQ wait), not Thumb.
  * IME is cleared for the duration. Without that an interrupt fires
    mid-call and the CPU vanishes into the BIOS handler with your LR.

The call clobbers the interrupted context, so treat a core as spent
afterwards: one question per boot.
"""
from mgba._pylib import ffi, lib

TRAP = 0x08000000     # ROM start; we stop before ever executing it
SCRATCH_SP = 0x0203F000
THUMB_BX_R3 = 0x4718
ARM_BX_R3 = 0xE12FFF13
def _game_text_base(mapfile='build/USA/tmc.map'):
    """src/game.o's .text base, read from the CURRENT map - never hardcode
    it: every edit to game.c can move it, and a stale base resolves every
    symbol to some other function whose behavior is plausible enough to
    debug for an hour."""
    import re
    for line in open(mapfile):
        m = re.match(r'\s*\.text\s+(0x[0-9a-f]+)\s+0x[0-9a-f]+\s+src/game\.o', line)
        if m:
            return int(m.group(1), 16)
    raise KeyError('src/game.o .text base not in ' + mapfile)


def game_sym(name, obj='build/USA/src/game.o', text=None):
    """Address of a static function in game.c. They are absent from tmc.map -
    static symbols only survive in the object file's own symbol table."""
    import subprocess
    if text is None:
        text = _game_text_base()
    out = subprocess.run(['arm-none-eabi-nm', obj], capture_output=True, text=True).stdout
    for line in out.split('\n'):
        p = line.split()
        if len(p) == 3 and p[2] == name:
            return text + int(p[0], 16)
    raise KeyError(name)


def call(core, addr, r0=0, r1=0, budget=500000):
    cpu = core.cpu._native
    native = core._core
    # The CPU is usually parked in the BIOS IntrWait halt loop between
    # frames. Injecting there loses the jump: with IME forced off the loop
    # never wakes, and with it on, IntrWait's own return swallows the
    # hijack. So first step - interrupts still live - until the CPU is in
    # ordinary game code (out of the BIOS, not in IRQ mode), then hijack.
    for _ in range(2_000_000):
        pc = cpu.gprs[15]
        if pc >= 0x08000000 and (core.cpu.cpsr.packed & 0x1f) in (0x10, 0x1f):
            break
        lib.ARMRun(cpu)
    else:
        raise RuntimeError('CPU never reached game code')
    native.busWrite16(native, 0x04000208, 0)  # IME off
    cpsr = core.cpu.cpsr.packed
    cpu.gprs[0] = r0
    cpu.gprs[1] = r1
    cpu.gprs[3] = addr | 1
    cpu.gprs[13] = SCRATCH_SP
    cpu.gprs[14] = TRAP | 1
    lib.ARMRunFake(cpu, THUMB_BX_R3 if (cpsr & 0x20) else ARM_BX_R3)
    for _ in range(budget):
        pc = cpu.gprs[15]
        if pc - 4 == TRAP or pc - 8 == TRAP:
            return cpu.gprs[0]
        lib.ARMRun(cpu)
    raise RuntimeError('call did not return within %d instructions' % budget)
