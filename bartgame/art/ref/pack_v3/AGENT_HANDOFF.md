# BARTGAME environment art — redesigned pack (V3)

This package is the regenerated BARTGAME environment art pack rebuilt from the tile-spec pipeline and repackaged as a downloadable drop-in asset set.

## What this pack contains

- `assets/`: individual PNG files grouped by palette family. These are the primary integration assets.
- `atlases/`: grouped atlas sheets plus atlas metadata.
- `gba_4bpp/`: per-asset 4bpp exports.
- `gba_palettes/`: BGR555 palette files.
- `manifest.json`: exact dimensions, frame counts, file paths, and metadata for each entry.
- `previews/`: room mockups and zoom previews.
- `source/`: build scripts, the spec markdown, and the style-board references used by the builder.

## Integration

1. Copy the contents of `assets/` into the game art directory, preserving all subfolders and filenames.
2. Do not rename files. The engine or importer should continue using the same key-to-file mapping.
3. Variants are arranged left-to-right in 16px columns.
4. Animation frames are stacked top-to-bottom in rows.
5. Multi-tile scenic images should be sliced by the importer at 16×16 boundaries.
6. Overlay entries must continue rendering above sprites; ground entries render below sprites.
7. Collision and gameplay logic should remain unchanged.

## Style intent

This V3 pack was regenerated to align more closely with the approved dark “grime and glamour” direction:

- living wood: deeper blue-green foliage, warmer amber lighting, cooler stone
- blighted forest: higher-magenta corruption and darker violet fields
- drain: darker masonry, brighter teal water glow, warm prop lighting

## Validation

The included build verification was rerun after regeneration. The validator reported 117 assets and no issues.
