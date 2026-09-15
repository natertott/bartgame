"""Does the trophy-case ledger survive a power cycle?

The one persistence question the earlier probe left open: gSave.figurines
survived a death-and-return, but nobody had watched it cross a real save
write, a core reset, and a reload through the file-select flow.

Shape: boot, set one ledger bit nothing else sets, call the game's own
WriteSaveFile (the exact call the run-start and win paths make), hard-reset
the core (EWRAM wiped, SRAM kept - a power cycle), walk the boot flow
again so InitSaveData/file-select reload the file, read the bit back.

Controls, so silence can't lie:
  * a NEIGHBOR byte in figurines stays 0 through the whole trip (the read
    isn't just seeing 0xff garbage),
  * the bit is confirmed GONE from gSave right after reset and BACK only
    after the boot flow ran (so it came from EEPROM, not from surviving
    RAM).
"""
import sys
sys.path.insert(0, '/home/user/bartgame/tools/quickstart')
from emu import boot, here, press, ROOM_CONTROLS
from callrom import call

ROM = '/home/user/bartgame/tmc.gba'
GSAVE = 0x02002a40
FIGURINES = GSAVE + 0xD0        # u8[36]
WRITE_SAVE_FILE = 0x08086c7c    # tmc.map
SAVE_HEADER = 0x02000000 + 4    # gSaveHeader->saveFileId (after the int signature)
TEST_BYTE = FIGURINES + 7       # catalog rows 56..63
TEST_MASK = 0x24                # two bits, an arbitrary non-trivial pattern
NEIGHBOR = FIGURINES + 8

c = boot(ROM)
print('booted into', here(c))
c.memory.u8[TEST_BYTE] = c.memory.u8[TEST_BYTE] | TEST_MASK
before = c.memory.u8[TEST_BYTE]
file_id = c.memory.u8[SAVE_HEADER]
print(f'file id {file_id}, ledger byte set to {before:#04x}, neighbor {c.memory.u8[NEIGHBOR]:#04x}')

r = call(c, WRITE_SAVE_FILE, file_id, GSAVE, budget=30_000_000)
print(f'WriteSaveFile returned {r}')

c.reset()  # power cycle: CPU+RAM reset, SRAM (EEPROM) kept
for _ in range(30):
    c.run_frame()
after_reset = c.memory.u8[TEST_BYTE]
print(f'after reset, before reload: ledger byte {after_reset:#04x} (want 0x00 - EWRAM cleared)')

for _ in range(120):
    c.run_frame()
for _ in range(300):
    press(c, c.KEY_A, 3, 3)
    press(c, c.KEY_START, 3, 3)
    if c.memory.u8[ROOM_CONTROLS + 4] != 0:
        break
for _ in range(180):
    c.run_frame()
print('rebooted into', here(c))
final = c.memory.u8[TEST_BYTE]
neigh = c.memory.u8[NEIGHBOR]
print(f'ledger byte {final:#04x} (want {TEST_MASK:#04x} set), neighbor {neigh:#04x} (want 0x00)')
ok = (final & TEST_MASK) == TEST_MASK and neigh == 0 and (after_reset & TEST_MASK) != TEST_MASK
print('PASS: the ledger round-trips a power cycle' if ok else 'FAIL')
sys.exit(0 if ok else 1)
