# Source 4: Adafruit pixel-art fundamentals — complete reading notes

Original uploaded file: `Pixel Art Fundamentals _ How To Homebrew Game Boy Games _ Adafruit Learning System.pdf`.

- Author shown in PDF: John Park.
- Page URL: <https://learn.adafruit.com/homebrew-game-boy-games/pixel-art-fundamentals>.
- PDF length: 39 printed pages.
- SHA256: `ddac0ea777c0da51998d3d35b8b8b0dd20fda37d653a29ac838b7b77a2994cab`.
- Actual article: PDF pp. 6–19. Pages 1–5 contain navigation/title and pages 20–39 are unrelated guide recommendations/footer/social content. These pages were checked, not silently counted as 39 pages of instruction.
- Method: read extracted text in full; render all 39 pages, inspect contact sheets; inspect article examples at full-page size on pp. 7, 8, 12–14, 17–19. Extract the embedded MiniBoss chart on p. 7 at its original 512×512 pixels with `pdfimages` to read its small image text.

All page numbers below mean PDF pages of this exact file, not website section numbers. Website text, screenshot examples and linked outside tutorials are distinguished below. No outside link was read as part of this source reading.

## All applicable advice and evidence

| ID | Pages | What the source actually says/shows | Native-GBA application / limits |
| --- | --- | --- | --- |
| ADF-01 | 6 | A pixel is a single picture element; the article's working definition of game pixel art emphasizes small graphics authored one pixel at a time, as opposed to complex pre-rendered/real-time 3D imagery. | Keep native indexed drawings. Do not generate a detailed render and trust a shrink operation to make the Drain assets. Literal hand placement can be implemented in the code painters; the software brand is not the design principle. |
| ADF-02 | 7–9 | Limited palettes are a characteristic of pixel art; the article compares 1-bit, 4-bit and 8-bit graphics, and says contemporary developers may choose restrictions stylistically. The Celeste close-up uses twelve colors including transparency. It recommends looking at palette examples on Lospec. | A 16-ink GBA bank is a ceiling, not a quota. Give small features a few useful values and preserve shared semantic ink roles. Do not force each 16×16 crop to use all fifteen opaque inks or introduce near-duplicate shades just because slots exist. Lospec is a suggested external resource, not a resource read here. |
| ADF-03 | 9–11 | Decide the canvas size early; the examples explicitly contrast 16×16 and 32×32 grids. A grid cell holds one pixel or transparency. | Plan painted silhouette and legal hardware canvas separately. Our 16×16 terrain, 16×16 frog head, 32×32 body/wizard and 8×8 flame remain native. A large room fixture is assembled from native pieces; its impressive scale does not justify higher source resolution. |
| ADF-04 | 11–14 | The comparison moves from NES Mario in a 16×16 canvas with four colors including transparency, to SNES Mario in a 32×32 canvas with sixteen colors, to the more complex rendered-looking DS Mario example. The DS image uses many subtle shades. | More source colors and more shading are not automatic improvements. Do not imitate the DS rendering treatment to make the frog or brass look higher quality. A low-color shape that reads immediately is the appropriate target. These are examples across different systems, not a claim that every platform should use four colors. |
| ADF-05 | 17 | Inspect sprite sheets from existing games to study actual in-game resources; Mario sheets are shown. | Judge a coherent family and its frames together, rather than one ornate portrait in isolation. Our review should show every frog head/body, wizard and flame frame on the same native scale and backgrounds. Studying structure is authorized; copying Nintendo pixels into the game is not part of this recommendation. |
| ADF-06 | 17–18 | The drawing example uses a sixteen-color palette where the first entry represents transparency, then pencil placement on a 16×16 grid. | Preserve transparent index zero; never paint the review checkerboard into sprite margins. Keep the head/body and staff/flame joins connected in actual compositing, not merely in separate source canvases. |
| ADF-07 | 18 | The MiniBoss shovel progression first establishes the object's form, then adds dimension with extra values, then cleans/softens corners with anti-aliasing. | Build each Drain fixture and NPC as readable masses before surface detail. A wall outfall first needs a clear mouth/rim/bars, a bridge first needs connected landings/deck, and a frog first needs jaw/eyes/torso. Use two or three deliberate material values before applying scratches or glints. |
| ADF-08 | 18–19 | Aliasing is stair-stepping on diagonal/curved lines. The demonstrated anti-aliasing adds intermediate-contrast edge pixels; the black/white example adds four gray shades. It may look fuzzy when enlarged, so judge the result at actual scale. | Distinguish selective, hand-placed palette anti-aliasing from filtered scaling. Where a curve has a known dark neighboring material, one existing intermediate gold/stone ink may improve a turn at 1×. Do not apply a soft blur, export fractional alpha, or spend four new gray slots for every sprite. A moving sprite must still separate on every background, so external edge AA needs special care. |

## Embedded MiniBoss chart on PDF p. 7

The page links the MiniBoss tutorials and includes an actual readable chart titled **Resizing Pixel Art**. The following advice is visibly in that embedded chart, not invented from the link title. Cite it as “Adafruit PDF p. 7, embedded MiniBoss chart.”

| ID | Explicit embedded advice | GBA translation / application |
| --- | --- | --- |
| ADF-M1 | Avoid scaling and rotating pixel art when possible; imperfect lines are easy to produce and need redrawing. If automatic resize is used, choose the nearest-neighbor form. | Generate our assets at their final size. Enlarge review images only with nearest neighbor. An artist may use a rough transform as a construction aid, but must redraw the final outline and pixel groups; a transformed preview is not a finished GBA frame. |
| ADF-M2 | Concept-to-pixel work is a translation rather than a rescaling operation. Begin with the large masses. | User references inform silhouette, material and emphasis; do not attempt to retain every high-resolution feature. For the five Drain directions, choose different primary masonry/arch/market/NPC masses first, then author their native details. |
| ADF-M3 | Select a few strong identifying details and place detail/contrast there, keeping other regions cleaner. The diagram mentions the shoulder guard and large coat fold as examples. | Put the frog's emphasis on bulging or sleepy eyes, a broad mouth and apron/cap; put the wizard's emphasis on hood/robe mass and flaming staff. Avoid equally strong outlines on every vest seam, robe fold, stone crack and rivet. This also supports quieter floors around the ladder and market approach. |
| ADF-M4 | As resolution falls, choose which details matter; some details, including facial features, may need to be discarded. Larger resolution allows more realistic sizes and rounder shapes. | Do not preserve portrait-level facial anatomy in a 16×16 frog head. A few connected eye/mouth pixels are enough. The wizard's shadowed hood is useful because it avoids forcing a tiny face into too little space. Separately authored 48×48 portraits can retain more form while using the same identity. |
| ADF-M5 | The adjustment workflow repairs outlines/silhouettes, redraws missing information, chooses details to omit, fixes broken shading, and when enlarging redraws squares/rounds shapes and broken lines without dithering before finding places for added details. | A changed shape requires rebuilding its pixel clusters and shading, not just stretching the old frame. Do not add noise to conceal a poor resize. Keep the fixed gameplay anchors and frame canvases while redrawing geometry within them. The chart's prohibition on dithering is specifically in the resizing workflow; it is not a universal article ban on all intentional dithering. |

## Direct image observations (our analysis, not extra author commands)

1. **Celeste scene, p. 7:** the house reads as large dark/brown-violet structural masses, with local strong window/snow highlights. The snow's bright top and blue lower clusters define a continuous ledge; there is not an equally strong grid around every background pixel. Applied to the Drain, preserve broad gray floor masses and clear bank faces while reserving high contrast for the ladder, gold outfall, frog face and flame.
2. **Celeste character close-up, p. 8:** hair, face, clothing and backpack are coherent groups using a small ramp. The close-up is enlarged without inventing fine new details. Our frog/wizard source boards should similarly expose clean intentional groups rather than a scattering of isolated material pixels.
3. **Mario comparisons, pp. 12–14:** low-color original forms remain clear even with large flat masses; the rendered-looking example has numerous small intermediate shades. This is a useful warning against treating extra shading as synonymous with a stronger GBA character.
4. **Shovel sequence, p. 18:** every stage keeps a recognizable handle/shaft/blade silhouette. The shaded version adds plane information, and the final edge treatment refines the same shape. It does not rescue an unclear shape by applying a texture overlay. A pipe needs a legible barrel/flange/opening before corrosion, and a floor grate needs clear bars before glints.
5. **Anti-aliasing comparison, p. 19:** the huge close-up deliberately reveals gray border pixels; the two actual-size versions beneath are needed to assess the intended result. This does not authorize automatic high-resolution downsampling of game art.

## Explicit hardware distinction

The article's title places it in a Game Boy homebrew guide, but **this supplied page does not teach DMG sprite dimensions, an 8×8 tile rule, 8×16 sprites, Game Boy tile allocation or a mandatory four-color hardware prescription**. The four-color claim in the text belongs to its NES Mario example. Likewise, this article is not the source for RGB555 or GBA palette-bank capacities.

Our platform adaptation uses the independently established project specification: 240×160 GBA screen, 8×8 hardware subtiles, 16×16 gameplay cells, 16 indexed entries per 4bpp bank including transparent zero, RGB555 colors and the project's legal OBJ canvases. Do not replace those facts with the constraints of another console.

## Topics absent or limited in this particular source

- It does **not** provide a tile-seam/autotiling method, bridge placement algorithm, perspective formula, material-specific stone/water recipe, hue-shifting rule or numerical contrast target.
- It links tutorials including animation, but gives **no specific animation timing, squash/stretch, keyframe or walk-cycle rules in its own prose**. Sprite-sheet inspection is the applicable explicit advice.
- Dithering appears only as an exclusion in the embedded enlargement-repair workflow; do not attribute a universal anti-dither law to the whole source.
- The mention of pre-rendered 3D is a definition/comparison, not an instruction to install a 3D package.
- Piskel, Aseprite and Pixilart are suggested tools, not required production dependencies. Python-native painters can follow the same design workflow.
- Related guides after p. 19, site navigation and social links are not pixel-art recommendations to incorporate into the game.

## Concrete five-style redesign recommendations

These are **our applications** of ADF-01–08 and ADF-M1–M5 after inspecting the current first-pass `room-overview.png` and `characters.png`. They are not claimed as literal Adafruit instructions.

| Style | Current issue seen in first study | Reference-led correction |
| --- | --- | --- |
| 1 Crown of Sludge | Every brick joint is similarly explicit; gold framing and small trim all receive nearly equal emphasis. | Establish broad heavy gray planes, dark mortar mainly where it reinforces construction, a single strong gold rim and grouped upper-left highlight. Keep smaller pipe joints/subordinate trim below the ladder/outfall emphasis. Form and plane before scratches. |
| 2 Crooked Brassworks | The rounded floor-cobble pattern repeats with strong contrast across most walkable ground. The market and frog can compete with that pattern. | Keep round cartoon masses but reduce interior floor contrast and use fewer lit edges. Concentrate the frog's identifying detail on big eyes and broad mouth/paunch; reserve the crowded detail for the small market cluster. |
| 3 Moonlit Cistern | The quiet palette works, but some very long perfect contour lines flatten fixtures into diagrams. | Use broad cool stone masses plus a small deliberate shade plane; refine selected arch turns with existing intermediate brass/stone pixels at native size. Keep water separated by its bank shape rather than filling it with many little shades. |
| 4 Rotten Reliquary | Cracks/bones repeat over broad floor regions, making grime a texture grid and small bone clusters potential false pickups. | Translate filth into a few larger, connected, low-contrast deposits. Keep bright small object-like details rare. Let the toad's low wide jaw and the wizard's ragged hood provide readable identity without adding random surface pixels. |
| 5 Royal Drains | Gold embroidery, market glints, pipe edges and grate trim all compete; a polished ornamental object can appear interactive merely because it is bright. | Choose the functional ladder and main sewer as primary gold masses; simplify the other gilt detail. Give the capped frog and tall wizard a few strong details, leaving cloak/apron panels clean enough to read in motion. |

Across all five, first make plain native silhouettes/masses, then shade, then clean only necessary edges, and inspect the finished result at 1× in actual mGBA backgrounds. The user's desired abundance of existing surface glitter remains a fixed requirement; reduce competing static pixel noise rather than suppressing that glitter.
