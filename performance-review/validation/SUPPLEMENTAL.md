# Additional native and workload checks

[Native menu comparison](menu/comparison.json) matches all 45 actual RGB images
and page/cursor/map/zoom/state records. The [before](menu/before/report.json)
and [after](menu/after/report.json) captures each pass 99/99 checks, including
all nine Wine/Moss/Ivory style and palette combinations selected through
ordinary Options input. The 90 untouched 240×160 PNGs accompany their reports.
No artwork, palette, frame clock or framebuffer was injected.

[Scenario validation](scenario-validation.json) checks raw media hashes,
90 exact GIF samples and retained enemy counts in all 30 no-offense fixtures.

[Previous extended Heart data](heart-before.json.gz) and
[optimized extended Heart data](heart-after.json.gz) retain the complete
900-video-frame bow/Heart pressure samples as lossless gzip JSON. They
measure 898/900 and 899/900 updates respectively. Projectiles and enemy
behavior remain live; final projectile counts differ because the simulation
advances and shots collide. This measures pressure during part of the fight.
It does not compare identical end states or cover a complete boss fight.

[Supplemental file manifest](supplemental-files.json) records native image
hashes and exact decompression hashes.
