# Five UI remixes: preferred structures and reusable palettes

Status: five exploratory visual skins. No new skin is selected for production.
The user's current feedback is the direct source. They prefer structures2,4,5
and explicitly request palettes1,4,5 for this new set, despite favoring4/5 most.
Accordingly there is one ivory-palette proposal and four wine/green proposals;
no new proposal keeps the light parchment palette2 or black-glass structure3.

The shared art bible, direction log, reference register and established PDF
application rules were read. The existing G01/G04/G08/G09/G11/G12/G18 principles
remain applicable: native silhouette/structure, useful material values, clean
pixel runs, selective edge strength, controlled texture and pixel-preserving
review. This art subtask did not access a new article or claim new game research;
the menu-research task records those separate sources and observations.

## Five choices

| User-facing choice | Build profile | Structure and refinement | Exact palette source |
| --- | --- | --- | --- |
| 1 Winebound Folio | BART_UI=6 | Rounded folio derived from2; a rolled/turned corner, quieter double ink rule and folded selected corners. |4 Wine Reliquary |
| 2 Mossbound Fieldbook | BART_UI=7 | Folio2 plus repaired ledger5; lapped corners, interrupted stitches, short seams and small clasp-like markers. |5 Salvage Ledger |
| 3 Ivory Reliquary | BART_UI=8 | Brocade4 refined into clustered corner leaves and a quiet single wire along long edges. |1 Ivory Wire |
| 4 Burgundy Archivist | BART_UI=9 | Brocade4/ledger5 hybrid; square reinforcement, rivets, broken double rails and archival tab plates. |4 Wine Reliquary |
| 5 Verdigris Devotional | BART_UI=10 | Rounded folio2 with attached4-style paired leaves and5-style repairs; cusp corners and inset seams. |5 Salvage Ledger |

All five have newly authored frame, tab, badge, rule, divider, continuation
marker, right-pointing selection marker and inventory cursor geometry. Their
51 C-facing tile identifiers, marker meanings and cursor allocation remain
stable. Empty fields stay subordinate; richer material detail is attached to
corners/joins, leaving interior text fields open. The five indexed kit hashes
differ from one another and from every historical0–5 kit.

## Structure versus color

`STYLE_RECIPES` records geometry, preferred design sources and palette source
independently. `palette_profile()` returns the reusable palette identity;
`geometry_recipe()` names the structure. The three requested semantic palettes
are copied exactly at RGB555 precision. Geometry can later be reused with an
area palette, but this pass does not invent or activate automatic regional
color switching. A future palette must preserve foreground/background roles,
map-state meanings and readable selected/disabled/body/floating text.

For new6–10 only, neutral HUD backplate, text, outline and gilt roles follow
the chosen material palette. Health reds and actual equipment-material
palettes remain stable; a healing heart or bow does not change meaning by skin.
The mini-map's green traversability/current-state roles remain stable while
its neutral field coordinates with the chosen interface palette. All current
HUD content rules remain in force: compact12px top, isolated bottom-corner
minimap, equipped item icons and their relevant ammunition, hearts and gilt.
The runtime agent supplies the corresponding five small pod-corner shapes.

All chosen new palettes have dark main fields, so selected-tab HIGH and body
CREAM remain light; invariant PALE floating text keeps its dark contour.
Shop speech bubbles retain the existing semantic pairing between their field
and DARK role: the ivory/green light bubble uses dark type, while wine's dark
bubble uses light type. Contrast must still be checked in actual screenshots.

## Scope and preservation

Only `art/ui_studies.py` changes in this art subtask. `art/reboot_ui.py`, native
font metrics, the title bitmap, room artwork and the material item glyphs are
not edited. Profiles0–5 retain exact exported pixels and palettes for every
kit tile, HUD tile, marker, cursor and group. Every one of the17 separately
authored equipment glyphs also matches its old source bytes. No arbitrary
pixels were added to retained material symbols.

Native canvases are8×8 kit/marker tiles,32×32 inventory cursors (painted over
the existing24px cell height), and16×16 hardware equipment canvases containing
the existing10px glyphs. Indices stay0–15; palettes remain sixteen RGB555 inks
including transparent zero. No high-resolution image, filtered resampling,
extra font, imported game graphic or fractional alpha is introduced.

## Evidence and tradeoffs

- `native-validation.json`:1,221/1,221 native checks across profiles0–10.
- `remix-source-review.json`:40/40 historical-preservation, exact-palette,
  identifier and new-structure checks, with source/export hashes.
- `five-remixed-ui-source.png`: five native source menu/dialogue assemblies,
  explicitly not emulator screenshots. Control examples correctly say
  A/B/L assign, R page and Start close.
- `five-new-kit-atlas.png`: every new kit tile at3× nearest-neighbor.
- `compact-hud-icons.png`: retained native item glyphs at1×/3×.
- Source preview files and validation scripts are beside these artifacts.
  The parent captures actual menus, dialogue and HUD state from real mGBA.

The Winebound option is softer/rounded, Mossbound more repaired, Ivory the
quiet ornamental option, Burgundy more rigid and reinforced, and Verdigris
more foliate. Long rails remain deliberately restrained so even the more
ornate proposals do not fill text fields with texture. These are exploratory
tradeoffs, not a ranking or a claim that hash counts measure artistic quality.

Frozen source SHA256:
`5f924a43aa53fb0403cf6f1e77fe6912263b3ca7d210f614a081c3839f577b5b`.

## Tiny runtime HUD backing follow-up

`src/text.c` now has five explicit `hud_pod` branches for profiles6–10: rolled
folio, lapped stitches, restrained corner beads, compact riveted reinforcement
and an attached paired-leaf form. All backgrounds remain under the figures and
item pictograms. Every coordinate stays inside its local20–30px width and rows
0–11; counts, labels, slots, caches, map allocation and navigation are untouched.
Profiles0–5 produce exactly the same preprocessed function as their previous
source. Each new branch also passes a standalone C syntax compile. These source
checks do not substitute for the parent's actual mGBA HUD/state review.

`hud-pod-source-check.json` records that narrow verification. Text source SHA:
`a68bd4a74e7490335e7289013707f7aa35143444e3dd25ce2c6f18842a63b5b0`.
