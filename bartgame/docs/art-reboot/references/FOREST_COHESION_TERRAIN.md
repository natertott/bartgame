# Forest material and edge refinement

This local pass responds to the user's review of the generated rooms: water
and crossings looked pasted in, debris was too evenly scattered, and material
edges did not form a coherent forest. It retains the twelve approved compact
tree drawings exactly. The previous uploaded-guide application remains the
reference; this pass claims no newly read external source.

All pictures are authored as native indexed 16×16 cells, with 8×8 hardware
subtiles, transparent index zero where a separate floor really exists, and
RGB555 colors in the existing world banks. The actual GBA budget and room
behavior remain review gates; source illustrations alone cannot qualify them.

The ground stays quiet. A few connected horizontal leaf/soil marks replace
repeated dark upright strokes. Tall grass and ferns form low connected leaf
rosettes. Small flower/fungus groups have a common stem/ground contact and
material rather than resembling individual shiny dropped items.

Paths have quarter-local uneven grass lips, shared soil colors at every
corruption stage, and 47 side/concave-corner combinations per healthy/sick
context. The two contexts share the same indexed picture data and differ only
in their ground/decay_mix bank. Soil roles 7–11 match across those banks;
gray diseased grass remains the accepted local floor direction.

Six ground-detail families also have healthy/sick render aliases sharing their
exact indexed pixels: flowers, alternate flowers, tall grass, ferns, litter and
shade. Their exterior index4 must use the actual local floor's bank. This
avoids a healthy-green sixteen-pixel square beneath a plant on gray sick turf.
Aliases retain the original logical IDs and physical metadata.

Water is blue-green with short horizontal reflections. The exterior of each
bank is transparent, with a narrow wet-soil lip and deep near-water contact;
the renderer must supply actual grass, earth or sick ground beneath it.
Single isolated cells use an intentionally shallow puddle instead of four
complete riverbanks squeezed around a tiny square. Falls are connected sheets
with local moving crests. Bridges expose a clear plank deck, attached side
beams and open travel ends. The generator must provide real dry landings and
a destination; the source picture cannot make an arbitrary bridge useful.

The retained ledge kit has a continuous grassy lip, exposed earth/root face,
lower cast shadow and explicit end caps. It does not promise an inaccessible
upper route. Holes keep a genuinely dark recess below an irregular soil lip,
without a luminous purple fill that competes with interactions.

Final art/atlas limits, native room renders, motion and any source-only families
are recorded by the coordinated integration review after the real build exists.
