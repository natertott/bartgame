# Final Drain and interface studies

The [current review gallery](../../art-review/drain-final-ui/README.md) contains
one final Drain room and five optional interface skins. Normal `make` now uses
Drain profile 9 and the neutral compact interface, UI0. UI1–5 remain choices
for feedback. [The direction log](art-reboot/ART_DIRECTION_LOG.md) records the
user's selections, follow-up HUD requirements and actual-screen corrections.

The newer [five remixed interfaces and ten interactive menu layouts](../../art-review/ui-menu-exploration/README.md)
extend this comparison using the preferred structures and requested wine,
green and ivory palettes. They retain the final room and compact HUD/minimap/
conditional ammo. UI6–10 and MENU1–10 are optional; UI0/MENU0 stays the default.

## Final room

The final art combines v3 floor/debris #1/#5, north-wall language #1/#3, market
#1/#3, wizard corner #2, crossing/rail #2/#5, storage #2/#3 and lower rail #4.
The larger ladder has a taller arch and rungs, with the up-arrow above it.
Both brass arches have a continuous face, connected upper-left highlight and
narrow depth return. The enlarged severed wall pipe visibly leaks. A side-view
outlet projects from the left edge and pours rightward into the channel.
Left/right walls have their own capped inward-facing perspective.

The room remains 30×20 cells, 480×320 pixels. Its bridge, channel, market,
ladder trigger, wizard, spawn and NPC anchors keep their physical arrangement.
All 657 ground/foreground placements retain their resolved collision, type,
prop and glitter flags. Bloom, Step-and-cut, other areas and save formats stay
intact. Art is authored in native 16×16 cells and 8×8 hardware subtiles, with
one RGB555 4bpp area palette. Source room assemblies omit runtime glitter and
are explicitly distinguished from 240×160 actual mGBA output.

Previous pictures were reused between north/side walls and unrelated floors,
which prevented independent perspective and erased fixtures. The final pack
appends 657 placement-specific picture IDs while keeping original IDs 0–912
stable. All 1,554 native frame drawings survive ROM encoding. Exact complete
animation sequences may share a resident allocation only when every frame,
orientation, palette and timing agree. This preserves motion while fitting
822/1024 BG subtiles and 69 animation allocations. It applies only to final
Drain packing; forest/interior packing stays unchanged.

[Art decisions](art-reboot/references/DRAIN_FINAL.md) ·
[Integration and save compatibility](art-reboot/references/DRAIN_FINAL_INTEGRATION.md)

## Compact HUD and five interface choices

The HUD shows hearts, gilt, equipped items, the minimap, and ammunition only
for equipped blightseeds or the bow. Its top paint stays within 12 rows; the
16×16 explored/current-room minimap sits separately at screen (222,142).
Equipment occupies fixed x148/178/208 anchors with smaller backplates when
no ammo count is needed. Counts include zero and can display all 0–255 values.
Keys, unrelated ammo, the R prompt and the old full-width bar remain absent.
The center at x116–147 stays transparent, exposing northern game content.

| UI profile | Direction |
| --- | --- |
| 0 | Quiet Brass: neutral established theme with the new compact HUD. |
| 1 | Ivory Wire: thin relic linework and restrained gilt fragments. |
| 2 | Moulded Vellum: light stained paper, torn contours and dark body type. |
| 3 | Black Glass: clipped angular panels and controlled metallic steps. |
| 4 | Wine Reliquary: dark wine fields and ornate worn embroidery. |
| 5 | Salvage Ledger: repaired green ledger material, seams and rivets. |

All skins preserve the native font and input hierarchy. Their panels, tabs,
selections, markers and cursors change geometry as well as material/color.
Menus, key items, maps/zoom, shops, dialogue, rewards, title choices, death and
victory are reviewed in actual runs. Selected tabs use semantic contrast;
backed paper prose avoids dark title outlines. Floating prompts use pale ink.

[Interface art](art-reboot/references/UI_STUDIES.md) ·
[HUD layout/cache/runtime](art-reboot/references/UI_RUNTIME.md) ·
[Shared art bible](art-reboot/ART_BIBLE.md)

## Build choices

```sh
# Final room, neutral compact UI and selected Step-and-cut sword.
make -j4

# Final room with a proposed interface skin.
make -j4 BART_UI=2 BUILD=build_vellum

# New preferred-structure/palette skin, existing menu arrangement.
make -j4 BART_UI=6 BART_MENU=0 BUILD=build_winebound

# Optional Twin Atlas menu layout in the same skin.
make -j4 BART_UI=6 BART_MENU=6 BUILD=build_twin_atlas

# Historical room art with the current compact interface/runtime.
make -j4 BART_SEWER=3 BART_UI=0 BUILD=build_old_room
```

`BART_SEWER=0` retains original room art, 1–5 the third-pass concepts, 6–8 the
mixed concepts, and 9 the final room. Historical profiles do not revert current
HUD/runtime code. `BART_SWING=3` remains Step-and-cut. Profile stamps and all
painter dependencies prevent stale asset reuse.

## Earlier studies

The [first five concepts](../../art-review/sewer-concepts/README.md),
[reference-led second pass](../../art-review/sewer-concepts-v2/README.md), and
[feedback-led third pass](../../art-review/sewer-concepts-v3/README.md) remain
immutable review evidence on their original branches. Their ROMs keep their
own recorded source/runtime versions. They are not the final production room.
