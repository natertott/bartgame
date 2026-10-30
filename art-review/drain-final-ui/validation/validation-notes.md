# Independent final Drain and UI verification

This audit is separate from the asset builder. Expected indexed pixels come
from native art painters; actual ROM data is independently decoded from4bpp
nibbles, hardware flip flags, palette selection and animation allocations.
No build_assets, Tileset deduplicator, parse_art or tile_bytes import is used.

Allowed changes are explicit:657 new picture identities for the same room
placements, final Drain material pixels/animations, selected frog/wizard,
UI kit/marker/inventory-cursor/HUD source pixels and interface palettes. Original IDs remain
stable; every occupied room cell retains resolved collision/type/prop/glitter
metadata and every object anchor. Bloom/Step-and-cut, other actors/enemies/items,
forest/interior art, title bitmap, existing gameplay metadata and timing tables
are compared as exact resolved payloads, not relocated pointer bytes.

Frozen provenance records every art Python/JSON input hash and the exact ROM
hash. All six final profiles must select Drain9 and their own UI number. The
source tree must stay unchanged during the audit. Native palette/canvas and
resident BG/OBJ budgets are checked. Identical complete animation sequences
may share allocations; the independent decoder still checks every clone and
frame separately.

## Updated HUD requirements

The user's later request retains a minimap and currently relevant ammunition.
Earlier pure three-field HUD pilot reports are therefore superseded, not final
proof. Final tests allow only the compact12px top HUD and the native16×16 map
at(222,142), with a clear top-center gap116..147. Keys remain hidden. Ammo is
visible only when the corresponding bomb or bow item is equipped, and each
counter changes independently of the other.

Runtime verification decodes actual BG0 and priority-zero OAM pixels, checks
native miniature uploads and item palettes, cache updates, menu restoration,
and all25 minimap cells against current gWorld visited/goal/current-room state.
Map states are checked in the Drain, after pause navigation, at forest entry
and after another real room transition. Inventory/resource fixtures and a
room-transition fixture are disclosed; no sprite/UI pixels or poses are forced.

An isolated ordinary-enemy contact fixture checks that damage clears the live
sword hit region and removes sword art on the next replacement OAM upload at
both normal24HP and maximum80HP. Pixel source fidelity and these measured cases
are not taste scores or worst-case performance guarantees. The separate gallery
reviews full room contexts and readability visually.

## Pilot results

The pre-freeze final9/UI0 static ROM pilot passed9,842/9,842 checks; its source
provenance was intentionally not treated as final freeze evidence. Drain BG
use was822/1024 in one bank. Every one of1,554 final tile-frame drawings decoded
exactly;119 placement IDs had changing pixels.

The updated legacy-sewer UI0 runtime pilot passed53/53 checks, including map
and conditional ammo behavior. All ordinary contact samples observed replacement
OAM one video frame after hurt. These are early integration findings; final
reports are generated again from the final six frozen builds.

Run from the standalone game directory after freezes exist:

    source /workspace/setup/activate.sh
    python tools/drain_ui_audit.py --frozen /workspace/setup/drain-ui-final \
      --baseline /workspace/setup/sewer-concepts-v3/v0 --runtime \
      --out /workspace/setup/drain-ui-final/audit.json

`audit-summary.json` is the compact result. The full report names every check
and all failures; neither report is a substitute for actual mGBA screenshots.

## Final audit boundary correction

The initial full audit still classified the inventory cursor with protected
world sprites. It reported five exact pixel differences in UI1–5, all matching
the intentionally authored `ui_studies.selection_cursor` family. The boundary
was corrected specifically for the `cursor` sheet; its canvas, frame IDs,
palette slot and every4bpp pixel are now independently checked against source.
No game source, native art or frozen ROM changed to resolve this audit issue.
All six runtime suites had already passed in that run.

## Superseded443e pilot verification

Corrected technical audit on source443e7aabf2a21932dc4e815fd719f1e3b5ee34b0 passes
59,509/59,509 checks across UI0–5 with the same final Drain9. This includes
414 actual-mGBA runtime checks and36 ordinary-enemy contact samples. Every
observed replacement upload removes sword art one video frame after hurt.
All native source, frozen provenance, physical-map and protected-asset
comparisons pass. Every build uses822 Drain subtiles in one palette bank;
forest693 and interior114 remain byte-identical to the baseline art.
The full report is audit.json; compact audit-summary.json and audit-aggregate.json
retain the scope, coverage, measured delays and limitations.

## Selected-tab contrast review

Subsequent native visual review found that Items/Key Items/Map selection text
used the old dark ink on new dark tab materials. The packed source and runtime
state tests had passed because they establish fidelity and behavior, not taste
or contrast. Those443e freezes and reports are therefore pilot evidence.
The UI owner corrects page_frame to use the semantic HIGH ink for study skins
while retaining baseline0's dark-on-gold label. Floating item counts use pale
text with a dark outline. No arbitrary pixel ratio is used to declare the
result beautiful or readable: all five actual selected-tab contexts are
reviewed visually after the replacement freeze. Full technical/runtime
verification is rerun on those new exact ROMs.

## Corrected final freeze

Source `87abc1b4aa90d8f993896669a4bbebec8dd2112e` passes **59,509/59,509** checks across all six final ROMs:
59,095 static/native/provenance checks plus414 actual-mGBA runtime checks.
All36 ordinary-enemy contact samples still replace sword OAM exactly1 frame
after hurt. Conditional equipped ammunition, hidden keys, compact HUD/map
bounds, all25 minimap cells and menu restoration pass. Every final native
source/ROM match and protected-art/physical-map comparison remains exact.

Separate code-provenance-check.json independently matches all recorded code
input hashes to current files and the recorded git commit for all six freezes.
The art source hash guard passed throughout the audit.

For the contrast correction, selection-contrast-review contains15 exact native
mGBA screenshots reached through normal Start/R inputs, covering Items, Key
Items and Map as the selected tab in every study skin. The comparison board
uses unchanged top-of-screen crops; captions are outside game pixels. Manual
1x inspection finds the selected and unselected labels clear in all15 contexts.
No palette, text ink, UI canvas or pixel data was assigned by the capture
fixture. This visual review supplies the contrast evidence the earlier byte
checks could not establish. The superseded443e result is retained as history
and must not be labelled as final.
