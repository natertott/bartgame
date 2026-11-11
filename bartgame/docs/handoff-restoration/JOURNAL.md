# Discovery catalogue extension

The Drain cabinet retains its existing layout, native preview sizes, 24 item
entries and nine enemy entries. The restored item vocabulary appends 118 stable
IDs and four original golden fusion-half entries; the restored bestiary appends 75 enemies. Original names, notes and preview
frames remain intact, except that Blightseeds now explain charged throws and
explosion on ground impact. New entries show the same native sprite, palette,
mechanical description and HP/contact damage used by the corresponding actor.
Unknown visible entries remain unnamed until encountered. Seven hidden source
helpers/reference slots are omitted from the visible index and its progress
count, including the excluded Wallet. The original24 entries retain their order;
139 item entries and84 enemy entries are browseable. All146 raw item IDs remain
stable in storage/API metadata; no visible ordinal is serialized.

The complete catalogue uses 20 item-bit bytes and 12 enemy-bit bytes. Its two
64-byte JRN2 records occupy SRAM `0x7E40..0x7EBF`. Loading an earlier build's
JRN1 records at `0x7EC0..0x7EFF` copies all original discoveries and publishes a
new generation without modifying either source slot. Alternate slots, an
explicit size/version, checksums, bounds validation and magic written last
reject incomplete records. Appearance preferences begin at `0x7F00` and retain
their original bytes. A run reset never clears catalogue discoveries.

Extended metadata is copied into caller-owned `JournalEntry` storage. This is
intentional: rendering six list rows cannot replace the selected entry's name,
stats or preview. The legacy pointer getters remain stable for original IDs;
the complete catalogue uses `journal_entry(page,id,out)`. The diagnostic low
32/16-bit masks remain available alongside the full arrays.

`tools/journal_host_review.py` compiles the actual journal C with real production
item/enemy metadata and a private Linux SRAM mapping. Production coverage passes
1,951 functional checks plus 97,600 protected-byte checks; LAB coverage passes
1,868 functional checks. Coverage includes all 146 item and 84 enemy metadata
entries, high discovery bits, migration, generation wrap, interrupted record
publication, invalid bounds, duplicate discovery and caller-storage stability.
LAB discovery remains RAM-only, including migration. This evidence establishes
storage/metadata behavior; native preview artwork and UI timing require ROM
and emulator review separately.

## Additive run/profile isolation

The independent run extension keeps two1,404-byte checksummed records within
reserved4KB slots at `0x4000` and `0x5000`, keyed to the unchanged base save's
checksum. A separate versioned32-byte profile prefix uses two128-byte slots at
`0x7D00` and `0x7D80`. Compile-time guards keep both ranges below the journal.
Loading an older complete run retains newer profile deaths, score, difficulty
and entitlement choices. If both profile records are lost, a valid run can
recover its profile prefix. Missing or invalid extension data seeds only the
new systems; the existing base Forest/inventory save layout remains intact.

`tools/run_extension_host_review.py` compiles the actual extension C with
production serialization types and graph generation. Its1,479 production
checks plus48,640 protected-byte checks cover every incomplete write prefix,
checksum/generation selection, malformed bounds, profile precedence/recovery,
seed matching and erasure isolation. LAB checks confirm no extension/profile
writes. Runtime-only initialization is explicitly stubbed; old base-save
migration and native hardware behavior still require integration evidence.
