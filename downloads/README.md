# BARTGAME downloads

## Latest: readable interactive scenery

Larger wooden, brass and relic chests, full-tile switches, tall cave/hollow/
thicket entrances, clear pits and barriers, larger censers/pots, and explicit
healing shrine markers now stand out against the forest and blight. Intact
barriers stay in front of hidden hoards. A pre-existing unreachable-censer
placement bug is fixed. Existing rewards, progression and saves are retained.

- [Download the final GBA ROM](https://github.com/natertott/bartgame/raw/refs/heads/forest-art/downloads/interactive-scenery-3d3f8aa/bartgame-interactive-scenery-3d3f8aa.gba)
- [Download the ZIP](https://github.com/natertott/bartgame/raw/refs/heads/forest-art/downloads/interactive-scenery-3d3f8aa/bartgame-interactive-scenery-3d3f8aa.zip)
- [SHA256 checksums](interactive-scenery-3d3f8aa/SHA256SUMS.txt)
- [40 actual mGBA cases, comparisons and video](../forest-review/interactive-scenery/README.md)

Open the `.gba` in mGBA. Built from game source commit
[`3d3f8aa`](https://github.com/natertott/bartgame/commit/3d3f8aa970a163959655463dc52efd75c15597e1).
All 625 sampled generated rooms pass traversal checks, and all 549 interaction
checks pass. Previous forest, blight, Bloom, item and title updates are included.

ROM SHA256:

```text
bbd08678b1e10fb110e562a6374b0242cb8e73affbdd747f033fd0ce99619eee
```

## Previous: complete Bloom animation polish

Bloom now has direction-correct equipment depth, cleaner sword and item
motions, continuous lifting/throwing, guard walking, phased jumps with ground
shadows, and polished roll, hurt, drowning and death poses. Airborne damage
and wall bounces now recover to a proper landing. All previous forest, item
and title updates are included.

- [Download the final GBA ROM](https://github.com/natertott/bartgame/raw/refs/heads/forest-art/downloads/bloom-suite-c518ba9/bartgame-bloom-suite-c518ba9.gba)
- [Download the ZIP](https://github.com/natertott/bartgame/raw/refs/heads/forest-art/downloads/bloom-suite-c518ba9/bartgame-bloom-suite-c518ba9.zip)
- [SHA256 checksums](bloom-suite-c518ba9/SHA256SUMS.txt)
- [99 actual mGBA before/after recordings and video reel](../forest-review/bloom-suite/README.md)

Open the `.gba` in mGBA. Built from game source commit
[`c518ba9`](https://github.com/natertott/bartgame/commit/c518ba9fbdc4efdee5b43330dcbd5105c329eaa6).
The 97 ordinary action clips retain their gameplay traces; two recovery
clips demonstrate intentional hovering fixes. Save data remains compatible.

ROM SHA256:

```text
d5f9eda0647c0b197011656cd9fd758f2438df6c4e7e212dd100d31fc3f130ac
```

## Previous: regular forest material polish

The regular forest now uses clustered cool-green foliage, clearer oak,
birch and fir sprites, warm roots, quiet ground, mossy banks and subtle
water reflections. Shared woodland materials connect it to the updated
blighted forest. All previous item, title and Bloom updates are included.

- [Download the updated GBA ROM](https://github.com/natertott/bartgame/raw/refs/heads/forest-art/downloads/healthy-reference-fe25dc1/bartgame-healthy-reference-fe25dc1.gba)
- [Download the updated ZIP](https://github.com/natertott/bartgame/raw/refs/heads/forest-art/downloads/healthy-reference-fe25dc1/bartgame-healthy-reference-fe25dc1.zip)
- [SHA256 checksums](healthy-reference-fe25dc1/SHA256SUMS.txt)
- [Actual mGBA comparisons, screenshots and animation](../forest-review/healthy-reference/README.md)

Open the `.gba` in mGBA. Built from source commit
[`fe25dc1`](https://github.com/natertott/bartgame/commit/fe25dc1f38dd2d6894f53c3130785235d2b4db70).
All 75 sampled room layouts and spawn records match the previous build;
progression, surface and rendering checks pass.

ROM SHA256:

```text
d346f72866060e452f8751efc51dc0b074d8cb240ceba159784b97939da78f59
```

## Previous: Blighted Forest atlas artwork

The forest now uses blue-violet canopy, luminous mossy ruins, quieter purple
earth, softer decay edges, twisted trees, crystals, pools and mist inspired
by the supplied atlas. This build retains the previous item, title and
Bloom animation updates.

- [Download the updated GBA ROM](https://github.com/natertott/bartgame/raw/refs/heads/forest-art/downloads/blight-reference-cdb99b8/bartgame-blight-reference-cdb99b8.gba)
- [Download the updated ZIP](https://github.com/natertott/bartgame/raw/refs/heads/forest-art/downloads/blight-reference-cdb99b8/bartgame-blight-reference-cdb99b8.zip)
- [SHA256 checksums](blight-reference-cdb99b8/SHA256SUMS.txt)
- [Actual mGBA screenshots, comparisons and animation](../forest-review/blight-reference/README.md)

Open the `.gba` in mGBA. Built from source commit
[`cdb99b8`](https://github.com/natertott/bartgame/commit/cdb99b8ff213cd4328083b750acb9513237704b1).
All 75 sampled generated rooms preserve their collision and spawn records;
all three required rewards and the Heart remain completable.

ROM SHA256:

```text
d3b9049cdcc48f43aa6415838d28fa8f2efc15cdeb6341b2660dbe244b95bd76
```

## Previous: supplied item and shield artwork

This build includes the supplied item and shield designs, richer inventory
palettes, matching held-item art, the imported title and Bloom animation polish.

- [Download the updated GBA ROM](https://github.com/natertott/bartgame/raw/refs/heads/forest-art/downloads/items-reference-ac29db7/bartgame-items-reference-ac29db7.gba)
- [Download the updated ZIP](https://github.com/natertott/bartgame/raw/refs/heads/forest-art/downloads/items-reference-ac29db7/bartgame-items-reference-ac29db7.zip)
- [SHA256 checksums](items-reference-ac29db7/SHA256SUMS.txt)
- [Actual mGBA item comparisons](../forest-review/items-reference/README.md)

Open the `.gba` in mGBA. Built from source commit
[`ac29db7`](https://github.com/natertott/bartgame/commit/ac29db7) on `forest-art`.
All 2,920 rendering, palette, gameplay and title checks passed.
The wooden shield starts owned. Green-and-gold upgrade art is supported;
the upgrade has not been assigned to a new loot reward.

ROM SHA256:

```text
22655879ab59d8c93a80e7dfcbaecec98465bb5f723086233c25516e0efd3d45
```

## Previous: imported title artwork

The opening screen now imports the supplied screenshot at 240×160, using
2,070 colours in the GBA's direct-colour display.

- [Download the updated GBA ROM](https://github.com/natertott/bartgame/raw/refs/heads/forest-art/downloads/title-reference-66422bc/bartgame-title-reference-66422bc.gba)
- [Download the updated ZIP](https://github.com/natertott/bartgame/raw/refs/heads/forest-art/downloads/title-reference-66422bc/bartgame-title-reference-66422bc.zip)
- [SHA256 checksums](title-reference-66422bc/SHA256SUMS.txt)
- [Actual mGBA title comparison](../forest-review/title-reference/README.md)

Open the `.gba` in mGBA. The ZIP contains the same ROM and a short README.
Built from source commit [`66422bc`](https://github.com/natertott/bartgame/commit/66422bc)
on `forest-art`. The real ROM passed 79/79 title checks, 21/21 menu checks,
and 274/274 Bloom animation checks.

ROM SHA256:

```text
629b27d29cbffbfee63a8b70c450cdbd95a28da5bae78a43aa4401d081d7a211
```

## Previous: Bloom animation polish

The final Bloom animation build is ready to play in mGBA.

- [Download the GBA ROM](https://github.com/natertott/bartgame/raw/refs/heads/forest-art/downloads/bloom-polish-f42e91e/bartgame-bloom-polish-f42e91e.gba)
- [Download the ZIP](https://github.com/natertott/bartgame/raw/refs/heads/forest-art/downloads/bloom-polish-f42e91e/bartgame-bloom-polish-f42e91e.zip)
- [SHA256 checksums](bloom-polish-f42e91e/SHA256SUMS.txt)

Open the `.gba` in mGBA. The ZIP contains the same ROM and a short README.

Built from source commit [`f42e91e`](https://github.com/natertott/bartgame/commit/f42e91e60c026416d78d7bd9ce86e9f8c9aad673)
on `forest-art`. This is the tested ROM used by the
[actual mGBA animation gallery](../forest-review/bloom-animation/README.md).
All 1,812 animation, gameplay and sprite-memory checks passed.

ROM SHA256:

```text
b8d76c00875361f14c308fcf591f12903870c063ddd749780d29dca5142ef7d5
```
