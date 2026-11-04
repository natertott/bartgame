# Paired action and build checks

The [previous build](action-performance-before.json) and
[frozen HUD build](action-performance-after.json) each pass29/29 representative
mGBA action/render checks. Each of Drain, healthy forest, blighted forest and
cave has192 game updates per192 video frames while actual sword, shield
and cape inputs run. Recorded OAM and glitter remain within their limits.
Inventory, safe positioning and cleared unrelated actors are explicit fixtures.
These samples isolate action/render cost; they are not a worst-case combat
performance guarantee.

The tool is the committed `bartgame/tools/art_reboot_performance.py`; the
full raw per-frame data and ROM hashes are in the linked reports. The final
HUD source is4747b6788f18fe32da7d3304f34ce94c22468d5b.

[HUD0 preservation](legacy-preservation.json) confirms a fresh historical
comparison build equals the prior ROM byte-for-byte. [Default make](default-build.json)
emits the exact frozen HUD1 ROM.
