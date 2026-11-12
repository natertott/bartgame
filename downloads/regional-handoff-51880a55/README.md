# Regional handoff release — 51880a55

[Download ROM](https://raw.githubusercontent.com/natertott/bartgame/handoff-restoration-curdled-cream/downloads/regional-handoff-51880a55/bartgame-51880a55.gba) · [Download ZIP](https://raw.githubusercontent.com/natertott/bartgame/handoff-restoration-curdled-cream/downloads/regional-handoff-51880a55/bartgame-51880a55.zip)

[Actual mGBA gallery, controls and verification](../../regional-handoff-review/README.md).
The restored features now belong to Forest/Cream; Cream uses a second matching
wall ladder. The ordinary build retains existing art, music and boss wins.

Source: `51880a55e6ecf86728f3a0923e5547e7bdeed5a0`. ROM SHA256: `0dd8554384b53e618140f8c61590fc7e6a7ff0888f296ece034a95f357b34fdd`.
No commercial base ROM is required. This is the normal production game.

To continue an earlier run, copy its `.sav` beside the new ROM and use the same
filename stem. Won runs start fresh. Published extension-v2 checkpoints migrate
to the new position-aware extension without discarding inventory/profile data.

`native-evidence.zip` contains the exact frozen ROM/ELF/linker map/assets header,
source identity, unchanged native captures, input/fixture reports, separate
host proofs and a snapshot of the qualification tools. Native report hashes
must match this ROM. Camera mosaics remain labelled separately from untouched
240×160 gallery frames. Private SRAM and emulator state files are excluded.
`evidence-manifest.json` inventories the archive; `SHA256SUMS` covers the files.

The native quest/chain review earns its outcomes through real inputs with
explicit navigation fixtures. Isolated mechanisms use declared loadouts and
protection. Host sweeps, native asset decoding and actual gameplay inputs have
separate scopes in the [verification](../../bartgame/docs/regional-integration/VERIFICATION.md).
