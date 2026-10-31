# Selected enemies and broken purple Heart

- [Download the GBA ROM](https://raw.githubusercontent.com/natertott/bartgame/selected-enemies-heart/downloads/selected-enemies-770b542/selected-enemies-770b542.gba)
- [Download the ZIP](https://raw.githubusercontent.com/natertott/bartgame/selected-enemies-heart/downloads/selected-enemies-770b542/selected-enemies-770b542.zip)
- [Actual mGBA gallery and videos](../../art-review/selected-enemies-heart/README.md)
- [SHA256 checksums](SHA256SUMS.txt)

Coin Toad, Quill Moth, Trumpet Bellflower, Pear Bladder and Moth Confessor are
adopted as the normal enemy set. The new final boss is a purple Heart broken
down the middle, with thirteen coordinated poses. The selected interfaces,
Options, Step-and-cut sword and final Drain remain included.

Open the `.gba` in mGBA. The ZIP contains the same ROM, instructions, checksum
and frozen input manifest. No commercial base ROM is needed. Existing saves
remain compatible. Build: ordinary `make -j4` (`BART_ENEMY=11`), game/art source
[`770b542`](https://github.com/natertott/bartgame/commit/770b5422715fd108fc5b2607ab0978702b96e46f).

All 88 runtime checks over thirteen actual mGBA cases and all 12,919 independent
source/ROM/preservation checks pass. The gallery documents review fixtures and
separates source pose catalogs from actual gameplay timing.

ROM: **594,124 bytes**. SHA256:

```text
9330a44a4e27d99606a757134aa41a62adb122a74315c400e1ad3427048c8661
```
