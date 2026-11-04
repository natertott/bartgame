# Quieter glitter — 2026-11-04

The user explicitly requests 50% fewer on-screen glitter points and half the
blink frequency. This supersedes the earlier roughly 20/24-site ambient budget
and faster ornamental glints. It changes atmosphere, without changing the
native star drawings, colors, sizes, surface attachment or foreground rules.

The ambient selector still considers the same ordered first 24 eligible sites.
It retains alternating members into a 12-site view. Even totals retain half
the sites. With an odd total, the final unpaired point has half the usual
bright duration, so its average visible contribution represents half a
retained point. This also halves average glitter in sparse one-site views.
A cap-only change would leave those views unaffected. The original room
candidate list and spatial shuffle remain unchanged. Each retained point
continues to be attached to its material.

Each site's phase now advances on `gFrame >> 1`, retaining the original
independent phase offsets. A complete cycle takes 128 video frames instead
of 64. Normal retained points are bright for 64 frames and dark for 64;
the unpaired point is bright for 32 frames and dark for 96. Both use every
native drawing stage, including the same peak size. The odd-count adaptation
shortens only that final point's pulse while keeping its onset frequency at
half the old rate. Combined with the alternating site selection, integrated
visible glitter is exactly half in unobstructed views, including one-site and
three-site views. Actor occlusion can change a particular view's visible ratio;
source-site density and temporal cadence are verified separately.

Decorative HUD and minimap border glints also advance at 16-frame steps rather
than 8. The minimap current-room blink remains 32 frames per phase, and physical
A/B/L button illumination keeps its original hold and six-frame release tail.
Those functional feedback signals are separate from atmospheric decoration.

Existing camera/room-revision selection caches and foreground actor bounds
remain intact. The smaller selected-view array saves 48 bytes of persistent
memory. No enemy AI, gameplay timers, collision, RNG, world generation,
material palettes, title image or item drawings change in this adjustment.

`tools/glitter_tuning_review.py` records source/native evidence against the
previous delivered performance ROM. Ordinary simulation supplies timing; its
camera/position/inventory and actor-isolation fixtures are disclosed. Native
PNG/GIF evidence remains separate from decoded OAM/HUD diagnostics. Final
capture provenance is appended by the parent review after the frozen
production build is available.

`tools/glitter_density_host.py` compiles the actual baseline and current
ambient C against deterministic fixture rooms. It covers every source count
from zero through 40 across 16 seeds and alternating foreground/floor
materials: 656 cases, including 192 odd-count cases and 671,744 video-frame
cases. All 4,265,136 checks pass. Integrated draw counts are 2,801,664 before
and 1,400,832 after, exactly half. Every retained point preserves all native
drawing stages and a full 128-frame period. Host fixtures establish algorithm
behavior; separate mGBA evidence establishes native timing and appearance.

Paired mGBA captures cover 512 consecutive frames in the Drain, healthy
forest, deep forest and cave. Mean visible glitter falls from 12 to 6 in
the Drain, healthy forest and cave; the sparse deep-forest view falls from
0.5 to 0.25. Every retained point's full cycle doubles from 64 to 128 frames,
including the fractional point, and every native drawing stage remains
visible. Decorative HUD and map-border updates slow from 8 to 16 frames;
the current-room indicator continues to switch every 32 frames.

The paired private-bundle evidence passes 331/331 baseline checks, 187/187
corrected-candidate checks and 27/27 paired comparisons. Four native asset
comparisons confirm unchanged glitter sheet pixels, sheet dimensions and
background/object palettes. Production-bundle provenance is recorded in the
final delivery manifest after its source commit is frozen.

Final source `ef63b92e` produces ROM
`cc57a1f790740ebcd6fc487e126cb970c41f79bc780e4f6bdd9530fc0d7e0d46`.
The fresh frozen-ROM capture again passes187/187 and27/27 paired checks;
[release evidence](../../../../enemy-prototype-review/README.md) includes
the native recordings and full trace archive.
