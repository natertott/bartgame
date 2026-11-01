# Independent tree-study review

Reviewed source: `c269b67b9f0652902a5295906f4d0c4d07e2710c`.
Scope: twelve tree studies, not a replacement forest or canopy. The requested sizes are interpreted as two-by-two and one-by-two **16-pixel tiles**: 32×32 and 16×32 pixels. Each size has two forms, each drawn in healthy, sick and dead states.

## Reference and visual assessment

I read the complete supplied 14-page GBA Sprite Art Guide, inspected its illustrated pages, and recorded page-specific applications in `docs/art-reboot/references/TREE_GUIDE_APPLICATION.md`. The PDF's advice is a reference; the user's tree-only scope controls this pass. In particular, these studies apply broad connected value masses before texture, meaningful silhouette changes between states, fixed ground anchors, and local contact shadows without a baked background fringe (guide pp. 5–10).

The first prototype's healthy trees were too uniformly domed. The revised drawings break the broad crowns into unequal connected lobes and give the narrow forms uneven lateral branches. At native size the final healthy forms read as compact stylized trees. Sick forms lose foliage and expose wood rather than relying on a recolor; dead forms have bare broken forks. The smaller forms remain deliberately simpler than the broad ones. Green, olive and wood shades stay related to the existing forest palette; violet is a small injury/light accent rather than a background fill.

I inspected all six final native mGBA catalog/grove images on grass, path and sick-grass floors, and both broad/narrow walk-around filmstrips. The root shadows and transparent branch gaps expose the underlying floor correctly on all three backgrounds. There is no dark rectangular backdrop or light edge halo. Trees remain compact beside Bloom. The walk strips show Bloom behind, beside and in front of the selected trees, with the contact point controlling overlap; the character remains identifiable. The repeated-grove arrangement has an open middle corridor and is explicitly a diagnostic planting, not a generated forest composition.

The remaining visual tradeoff is that bare 16×32 trees are slender and quieter than full crowns. They read as dead trees in the side-by-side study, but their visibility in a dense future forest still needs composition review. This pass does not establish recognition by new players or settle the user's choice of form. Adding texture everywhere would undermine the current native readability.

## Independent verification

`final-audit.json`: **599/599 checks passed**, zero failures. The separate capture report passed 104/104 checks. The independent audit decodes the frozen native 4bpp atlas and palette, reconstructs each source image, checks the source export and all twelve ground anchors, and recomputes the actual BG maps, root footprints, floor pixels, tree pixels and Bloom overlap from raw runtime data. It does not take the capture tool's expected-pixel assertions as proof.

The eight final contexts contain 352 recorded observations. The two movement sequences use ordinary game updates and input after the initial placement. Exact sampled GIFs are inspection aids with sampled timing; they are not full-rate animation measurements. The checks cover these fixtures, not all game rooms, all actions or performance on physical hardware.

All previously shipped profiles 0–29 rebuilt byte-identically to the preceding frozen controls. Existing normal forest/canopy payloads and animation maps, other region art, UI and character sprites remain unchanged. Profile 30 holds the separate tree-study atlas and review entry point; these screenshots are real mGBA renders of that diagnostic ROM mode, not a claim that the normal procedural forest already uses the new trees.

Audit tool SHA-256: `6d2a10a23f93dcc4e510b2811f228b2d66e3087d57460b4277cb67f5f1ca2323`.
