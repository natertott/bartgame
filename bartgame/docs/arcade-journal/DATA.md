# Arcade journal: discoveries and content

2026-11-05. The user's brief adds a retro cabinet in the Drain that remembers
items and enemies the player has encountered. This note describes data and
persistence; actual cabinet art and emulator UI evidence are separate.

## What can be discovered

`journal.h` defines24 stable item IDs and9 stable enemy IDs. Entries cover
all equipped tools, both shield drawings, passive/key items, heart pieces and
containers, every pickup/ammunition bundle, the Grail and the frog's Healing
Petal. The petal restores two hearts, while a loose Heart restores one; they
are separate entries despite sharing a heart-shaped icon. A lit bomb and an
ambient sparkle are states/effects rather than additional collectible items.

Each entry supplies its actual native sheet/frame/material bank, a concise
name and factual description. Enemy entries also supply HP/contact damage.
The shared unit is **8 player HP per heart**; ordinary sword and arrow damage
is2 enemy HP. The lamp burns supported terrain and does not secretly acquire
enemy fire damage through its journal description. Original enemy behavior
and new enemy counters are described without inventing weaknesses.

The user interface must gate names, pictures and descriptions with the
`*_seen` accessors. Unknown entries may occupy `???` slots, but must not reveal
their identity or hints. Accessor bounds are checked and invalid IDs do
nothing. Persistent IDs are append-only; never reorder existing entries.

Discovery hooks belong to actual visibility/acquisition, not procedural room
creation or enemy-spawn allocation. `journal_note_pickup` maps real `PK_*`
values; `journal_note_icon` maps `F_ICON32_*` item-get icons; the distinct
`journal_note_shop_icon` maps the frog's old `F_ITEMS_*` stock icons. All writes
are suppressed after a bit has already been seen. `journal_note_owned` seeds
facts available in a continued legacy inventory. It does not infer a Heart
Container from increased maximum HP, because that increase might have come
from four quarters. Nor does a general arrow count invent encounters with
five-arrow or ten-arrow bundles.

## Persistence without changing a run save

The existing run-save versions1/2 remain byte-for-byte unchanged. Discoveries
are independent profile knowledge, surviving New Game, death, a lost run or
run-save erasure. The separate appearance record remains at SRAM offset
`0x7F00`. Journal storage occupies only `0x7EC0..0x7EFF`: two32-byte slots.
The parent integration must assert that `sizeof(SaveFile)` ends before
`JOURNAL_SRAM_OFFSET`, as well as its existing preference boundary assertion.

Each slot contains magic/version/size, a32-bit generation,24 item bits,9 enemy
bits, reserved zeros and an FNV-1a checksum. The newer valid serial generation
wins; generation wrap is handled. An update invalidates the inactive slot,
writes its payload/checksum and publishes magic last. A torn or corrupt newest
slot falls back to the preceding valid generation. Two invalid slots produce
an empty journal without touching a run save or preferences. A power loss can
lose the newest discovery, but cannot replace an intact prior record with a
partial one. No empty record is written merely by opening the journal.

The optional mechanics lab can exercise discovery in RAM but does not persist
its granted inventory or test encounters into the profile journal.

## Source-level qualification

An actual-C host harness includes the implemented `journal.c` and maps a
private32KB SRAM buffer at the GBA address. It verifies first discovery,
duplicate/invalid ID no-ops, every item/enemy bit, exact icon/pickup/stock
mappings, inventory seeding, reload, generation wrap, damaged-latest fallback,
torn-target fallback and both-invalid reset. Byte guards verify every address
outside the journal's64-byte reservation remains untouched. The completed
host run passes65,540 assertions, most of which are those byte guards.

Private harness and log: `/workspace/setup/arcade-journal/host/`.
This establishes data logic and memory boundaries, not actual GBA cartridge
power-loss behavior or a real arcade interaction. Native mGBA save, visibility
and interface tests must qualify the integrated ROM separately.

The storage check is now reproducible without a GBA asset build:

```sh
python3 tools/journal_host_review.py --out /tmp/bartgame-journal-host
```

It requires Linux and a host C compiler (`--cc` selects one). The tool removes
only include directives from the actual journal C/header, supplies fixed-width
host types and the actual PlayerState declaration, and derives stub art IDs
from source contracts. No journal function body is rewritten. Both modes pass:
production132 functional assertions plus65,408 protected-byte checks; optional
lab9 functional assertions, including loading existing profile knowledge while
leaving every SRAM byte unchanged when test encounters add discoveries.
The output records source/tool/compiled-fixture hashes, compiler commands and
logs. Stub art identifiers establish no native palette or rendered-image claim.
