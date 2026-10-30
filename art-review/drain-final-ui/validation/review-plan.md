# Final Drain and UI review plan

Actual mGBA framebuffers, native 240×160. Recordings use normal buttons and
real item pickup, purchase, enemy contact death, save reset and Heart fight.
Inventory, seed, safe position and room navigation are disclosed fixtures.
No picture, canvas, animation pose or game completion state is assigned.

Final suite: 39 captures per build, six builds UI0–5, 234 total captures.
Ten final Drain viewpoints plus a walk; 10 HUD states/contexts including conditional
ammo 0/9/99/255;paginated wizard dialogue,shop selection/purchase/unaffordable
states,inventory/equip/key/map/zoom, real bow-chest reward, death-return, title
Continue/NewGame selection, and actual victory after the Heart fight.

The initial final9/UI0 pilot (before the user's minimap/ammo steering) passed
119/119 checks and 34 captures. Its screenshots proved the above-ladder arrow
remained visible under the compact HUD and the left-edge profile outlet survived
actual map assembly. It is pilot evidence, not relabelled final media.

Final HUD checks decode actual BG0/OBJ alpha. Only top 12px and isolated 16×16
minimap(x222..237,y142..157)may paint;central gap x116..147 stays transparent.
Keys do not affect the HUD; ammo changes appear only with corresponding equipment.
Map VRAM must change for different generated current rooms. Every ordinary idle sample
compares actual game updates and VBlanks. Palette-preserving GIFs and native PNGs
are primary colour evidence; full-rate MP4s are lossy convenience copies.

Existing engine has real shop Buy/Leave and title Continue/NewGame choices.
There is no independent yes/no primitive; none is fabricated for the gallery.

Final functional checks are149 per UI profile (894 total); image review remains
necessary and caught selected-tab and paper-victory contrast defects in the
first full pilot, despite all functional checks passing. Those captures are
archived as pilot-443e7aa, never relabelled final. The C fixes preserve all
frozen art and use correct semantic text ink/outline by placement.

Root owns independent packed-ROM and physical-layout auditing. Source gallery
uses 657 final placement IDs and per-cell animation clocks to avoid prior alias
errors. Source assemblies are always distinguished from actual framebuffers.
