# Compact HUD and interface runtime

Status: final source is ready for the parent freeze. The latest user steering
explicitly keeps the minimap and requests ammunition counts for equipped
blightseeds and bow. This supersedes the first pilot's no-map/no-ammo design.
The previous 24-pixel full-width bar is replaced with local compact groups.
The existing menu/shop/dialogue controls and semantic hierarchy stay intact;
the five studies supply distinct frame, panel, marker and palette families.

## Final native HUD layout

The gameplay HUD displays current/max hearts, gilt, equipped items, ammunition
only for equipped blightseeds/bow, and a small minimap. A/B/L letters identify
the equipped pictograms. Empty slots are transparent. Keys and the R-action
hand/prompt are absent. The pause menu retains its larger detailed maze map.

- Health starts at screen (2,2), with up to ten 8×8 native heart drawings in
  one row. Full/half/empty shapes use the selected HUD tile bank.
- Gilt uses a coin at x84..91 and native 3×5 outlined figures beginning at
  x94,y3. The full 16-bit amount65,535 fits before x115 without truncation.
- The central top interval x116..147 stays transparent. Northern entrances
  and the ladder's above-arch arrow remain visible through that opening.
- Equipment slot anchors are x148/178/208. Each uses a separately authored
  ten-pixel icon in a 16×16 hardware canvas, at slotx+4,y0. Existing frame
  ordering and per-item palette/material identity remain stable.
- Relevant ammunition is drawn at slotx+17,y3 with native 3×5 figures. Counts
 0..255 are exact. Ordinary gameplay caps are smaller, but no value is silently
  clipped to two digits. Only EQ_BOMBS and EQ_BOW show a count.
- Backplates adapt to content:20px without ammunition,22/26/30px for one/two/
  three-digit ammunition. No empty30px boxes are left around non-ammo items.
- Every painted top-HUD pixel stays within twelve rows. Its physical BG
  canvas is 240×16 because GBA tiles are8×8; rows12..15 are transparent.
- The minimap is a native16×16 drawing at (222,142), covering only x222..237,
  y142..157. A dark border and local backing keep the tiny five-by-five maze
  readable without expanding the top strip. Visited cells, fog, goal and the
  current forest cell/Drain entry marker use the existing semantic map inks.
  Map generation occurs on room-entry updates, as in the original engine.

## Implementation and performance

`src/text.c` uses a reserved transparent60-tile canvas. Its dirty cache only
repaints when health, gilt, capacity, equipment or relevant ammunition changes;
only changed heart cells are redrawn. Source item tiles upload only when their
equipped frame changes. Full-screen menus may borrow this canvas, then its
cache is invalidated on return. Unrelated hidden ammo/key changes do not force
a HUD upload. No full-width background or per-frame full canvas repaint occurs.

Currency uses an unsigned rendering path and five figures. Cached currency is
s32 with -1 invalidation, so65,535 does not alias the invalid marker. Gameplay
currency remains the existingu16; shop prices and purchase/equipment rules are
unchanged. `sHudCount[SLOT_COUNT]` tracks only conditional equipped ammunition.

HUD source/hardware ranges remain identifiable: item tiles start at
OBJ_TILE_HUD_ICONS876, sixteen reserved tiles per slot; each streamed16×16
frame uses four tiles. The compact map uses four existing reserved tiles at
OBJ_TILE_MINIMAP1008..1011. The old ammunition OBJ count range is not painted;
new ammo figures are in the transparent BG canvas. Other actor, portrait and
menu allocations are unaffected.

`src/text.h` and generated assets export HUD_HEIGHT_PIXELS12, describing the
TOP information strip, not the separate bottom-right minimap. Ambient glitter's
existing top exclusion follows that smaller height while preserving its native
source, budget and surface grammar. Makefile BART_UI0..5 validation, profile
stamp and dependencies prevent stale themes from leaking between builds.
Zero keeps the existing interface theme with the new compact HUD; five other
themes are opt-in studies.

## Floating text contrast

The light parchment theme deliberately uses dark body ink on backed panels.
Those semantic body colors cannot be used for unbacked title/win prompts on
a dark bitmap. `src/game.c` now uses invariant light UI_INK_PALE with a dark
outline for PressStart, Continue, NewGame and the victory PressStart prompt.
The animated picker identifies the title choice. Backed body text and input
behavior retain their existing roles.

## Pilot evidence and limits

Isolated source/build checks use:

    source /workspace/setup/activate.sh
    make -j4 BART_SEWER=0 BART_UI=0 \
      BUILD=/workspace/setup/drain-ui-final/ui-runtime-pilot \
      TARGET=ui-runtime-pilot

The current `ui-hud-pilot/` PNGs show normal/ten-heart states, gilt0/999/65,535,
three equipped items with conditional ammo, empty slots and the lower-right
map. They are actual native mGBA framebuffer captures, with an explicitly
old-sewer fixture to isolate the interface before final-art integration.

The initial no-map/no-ammo pilot passed23 independent runtime checks, including
HP/gilt/equipment/menu restoration and one-frame replacement OAM after sword
contact at both24 and80 maxHP. Those old scope assertions are superseded by
the user's later steering. Updated validation now checks the top-strip/map
region whitelist, conditional ammunition and live room-map tracking. The parent
publishes final all-profile results only after its corrected source freeze.

No final capture or performance result is inferred from source legality alone.
