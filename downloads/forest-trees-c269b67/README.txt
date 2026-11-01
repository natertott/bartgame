Compact forest tree art pack

Source: c269b67b9f0652902a5295906f4d0c4d07e2710c
Two forms each at 32x32 pixels (2x2 tiles) and 16x32 (1x2 tiles),
each healthy/sick/dead: 12 pieces. All states share one 16-ink RGB555 bank.

indexed/: canonical P16 PNG art, transparent index 0.
rgba/: exact RGB555-expanded viewing previews.
4bpp/: GBA 8x8 tile data, row-major; left pixel is in the low nibble.
palette.rgb555: 16 little-endian u16 colors (32 bytes).
palette.json and tree-contract.json: colors, ordering, anchors and layout.

Root anchor is [width/2,30]. Canvas and visible bounds are NOT colliders.
There are no animation frames in this static state-design pass.

The guide-led study sets canopy work aside. Regular forest art and procedural
placement are unchanged. Actual mGBA screenshots use deliberately planted
test groves, not natural generated maze rooms. This art pack does not claim
to provide a player-ready review ROM; the developer harness invokes its scene.

Indexed PNG authoring channels are multiples of 8; RGBA previews expand
RGB555 to 8-bit for display. Import canonical indices plus the RGB555 palette.
