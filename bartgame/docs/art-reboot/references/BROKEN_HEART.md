# Selected boss: the broken purple Heart

Status: native production drawing selected by the user's latest brief; the
parent integrates it into the selected enemy profile and verifies actual ROM
playback. The source previews below do not claim to be mGBA recordings.

The user selected Coin Toad, Quill Moth, Trumpet Bellflower, Pear Bladder and
Moth Confessor for the other five behaviors, then specified that the final
boss must still be **a purplish heart broken down the middle**. That direct
instruction supersedes the earlier bell, chalice, maw and other boss proposals.
Those historical concepts remain available but are not adopted boss anatomy.

## Shape, scale and material

`art/enemy_heart.py` authors the new drawing directly inside the existing
32×64 indexed hardware canvas. The main organ occupies approximately the
32×40 collision-bearing region, with short attached upper arteries. Two
asymmetric upper lobes and a long lower point establish a Heart silhouette.
The central split is an irregular, continuous transparent wound from the
upper cleft through the lower point, with a dark cut rim and sparse reflective
tissue edges. It is a broken object, rather than an intact heart with a
decorative line. There are no eyes, face, central maw or separate particles.

The existing sixteen-color `blight` bank is used without modification.
Dark violet/purple tissue dominates the silhouette, with warmer mauve wet
upper planes and a few rose/ivory speculars. Other enemies, world materials,
Bloom, UI and shared palettes are not changed by this module. Broad upper-left
light-facing planes and darker lower/right folds describe volume. Vessels are
attached and sparse; the brightest colors follow torn tissue and wet lobe
surfaces instead of forming a uniform glowing perimeter.

The native outline, limited material groups, clean pixel runs, stable anchors,
silhouette checks and restrained local reflections apply the already-read
G01–G18 reference guidance and the shared art bible. No new external article,
missing illustration or high-resolution reference is claimed as inspected.
The user brief and the existing source rule documents are the direct sources
for this local design.

## Complete presentation set

The native frame order is the existing boss's three original IDs followed by
its ten appended phase poses:

| Frames | Visible behavior |
| --- | --- |
| `pulse1`, `pulse2` | Upper lobes expand and relax around a fixed lower point. The engine already supplies world-space hovering. |
| `charge1`, `charge2` | Lobes swell and the jagged split widens in preparation for the existing volley. |
| `release1`, `release2` | Torn halves recoil and relax around the open wound after emission. |
| `spawn1`, `spawn2` | Lower vessels swell alternately as solid tissue; paired black holes are avoided so the organ never acquires a face. |
| `lunge1`, `lunge2` | The upper and middle masses compress/strain within the fixed native anchor. |
| `hurt` | Local stress and wet tissue reflections brighten while the split remains visible. |
| `dying1`, `dying2` | Both halves fold toward the lower point, widen apart and lose highlights. No unconnected dust pixels appear. |

The artwork does not add a shield, directional immunity, exclusive wound
weak point, bonus-damage phase or attack. The boss's source timers, movement,
projectiles, hitbox, health and 120-update defeat sequence remain the parent's
existing mechanics. The broken center is an identity and motion cue, not a
new targeting restriction.

## Source evidence and limits

`python art/enemy_heart.py --out PATH` generates:

- `broken-heart-all-poses-source.png`: all thirteen native poses at 1×/3×.
- `broken-heart-all-poses-source.gif`: exact-palette pose catalog, each held
  for 150ms for inspection; this does not simulate engine attack timing.
- `broken-heart-context-source.png`: source assemblies over four solid
  material-color backgrounds, explicitly not generated rooms or emulator
  screenshots.
- Native transparent RGBA and indexed PNGs for every pose.
- `native-validation.json`: legal canvas/index checks, distinct authored pose
  hashes, continuous transparent split checks and decoded GIF RGB proof.

All thirteen poses pass those source checks and were visually examined at
native size and integer zoom. The upper arteries can resemble short curled
horns in silhouette; their attachment to the organ and lack of a face keep the
body readable as a Heart. Mauve highlights are an intentional use of the
existing blight material bank, not a new palette policy. Actual arena contrast,
phase playback, hurt/death and streamed-frame encoding are verified separately
by the parent against a frozen game build.
