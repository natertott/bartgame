# GBA soundtrack recordings

All 30 pieces were recorded from the compiled GBA music-player ROM running in mGBA 0.10.5. Each recording contains the complete first pass plus three seconds after the loop restarts.

- `mp3/`: 192 kbps listening copies, tracks 01–30.
- `flac/`: lossless copies of the unprocessed 44.1 kHz, 16-bit emulator captures, tracks 01–30.
- `provenance/`: per-track capture metadata and ROM/audio hashes.
- `soundtrack_manifest.json`: track names, roles, tempos, durations, loop positions and asset metadata.
- [`mp3.m3u`](mp3.m3u) and [`flac.m3u`](flac.m3u): ordered playlists.
- `SHA256SUMS`: checksums of all 60 audio files, relative to this directory.

Tracks 01–25 are gameplay pieces; tracks 26–30 are variations on the title theme. These identifiers refer to the generated soundtrack catalog.

The mix is mono in a two-channel container. These are emulator captures; physical GBA speaker/headphone recordings are not included. Playback loop restarts are frame scheduled and may have a brief boundary dip or jitter. MP3 is the only lossy encoding step; FLAC decodes bit-for-bit to the original captured WAV.

Only the newly generated game soundtrack is included. The uploaded reference recordings are not included, and their audio was not sampled into these pieces.

Verify the audio files from this directory with `sha256sum -c SHA256SUMS`.

## Track index

| ID | Track | BPM | First pass | Recordings |
| --- | --- | ---: | ---: | --- |
| 01 | Undertow Circuit | 96 | 1:00 | [MP3](mp3/01_undertow-circuit.mp3) · [FLAC](flac/01_undertow-circuit.flac) |
| 02 | Verdant Afterimage | 112 | 0:51 | [MP3](mp3/02_verdant-afterimage.mp3) · [FLAC](flac/02_verdant-afterimage.flac) |
| 03 | Heart of Chrome | 144 | 0:40 | [MP3](mp3/03_heart-of-chrome.mp3) · [FLAC](flac/03_heart-of-chrome.flac) |
| 04 | Glass Causeway | 132 | 0:44 | [MP3](mp3/04_glass-causeway.mp3) · [FLAC](flac/04_glass-causeway.flac) |
| 05 | Neon Market | 118 | 0:49 | [MP3](mp3/05_neon-market.mp3) · [FLAC](flac/05_neon-market.flac) |
| 06 | Static Rain | 130 | 0:44 | [MP3](mp3/06_static-rain.mp3) · [FLAC](flac/06_static-rain.flac) |
| 07 | Hollow Relay | 105 | 0:55 | [MP3](mp3/07_hollow-relay.mp3) · [FLAC](flac/07_hollow-relay.flac) |
| 08 | Low Orbit | 120 | 0:48 | [MP3](mp3/08_low-orbit.mp3) · [FLAC](flac/08_low-orbit.flac) |
| 09 | Razor Bloom | 145 | 0:40 | [MP3](mp3/09_razor-bloom.mp3) · [FLAC](flac/09_razor-bloom.flac) |
| 10 | Midnight Transit | 108 | 0:53 | [MP3](mp3/10_midnight-transit.mp3) · [FLAC](flac/10_midnight-transit.flac) |
| 11 | Mirror Lake | 96 | 1:00 | [MP3](mp3/11_mirror-lake.mp3) · [FLAC](flac/11_mirror-lake.flac) |
| 12 | Velvet Engine | 120 | 0:48 | [MP3](mp3/12_velvet-engine.mp3) · [FLAC](flac/12_velvet-engine.flac) |
| 13 | Blacklight Duel | 136 | 0:42 | [MP3](mp3/13_blacklight-duel.mp3) · [FLAC](flac/13_blacklight-duel.flac) |
| 14 | Signal Garden | 124 | 0:46 | [MP3](mp3/14_signal-garden.mp3) · [FLAC](flac/14_signal-garden.flac) |
| 15 | Blue Hour | 90 | 1:04 | [MP3](mp3/15_blue-hour.mp3) · [FLAC](flac/15_blue-hour.flac) |
| 16 | Gravity Arcade | 138 | 0:42 | [MP3](mp3/16_gravity-arcade.mp3) · [FLAC](flac/16_gravity-arcade.flac) |
| 17 | Fever Corridor | 146 | 0:39 | [MP3](mp3/17_fever-corridor.mp3) · [FLAC](flac/17_fever-corridor.flac) |
| 18 | Afterglow Ruins | 102 | 0:56 | [MP3](mp3/18_afterglow-ruins.mp3) · [FLAC](flac/18_afterglow-ruins.flac) |
| 19 | Magnet Hearts | 116 | 0:50 | [MP3](mp3/19_magnet-hearts.mp3) · [FLAC](flac/19_magnet-hearts.flac) |
| 20 | Moonlit Breakwater | 110 | 0:52 | [MP3](mp3/20_moonlit-breakwater.mp3) · [FLAC](flac/20_moonlit-breakwater.flac) |
| 21 | Glass Cathedral | 100 | 0:58 | [MP3](mp3/21_glass-cathedral.mp3) · [FLAC](flac/21_glass-cathedral.flac) |
| 22 | Phantom Overdrive | 148 | 0:39 | [MP3](mp3/22_phantom-overdrive.mp3) · [FLAC](flac/22_phantom-overdrive.flac) |
| 23 | Last Train Home | 128 | 0:45 | [MP3](mp3/23_last-train-home.mp3) · [FLAC](flac/23_last-train-home.flac) |
| 24 | Dawn Protocol | 132 | 0:44 | [MP3](mp3/24_dawn-protocol.mp3) · [FLAC](flac/24_dawn-protocol.flac) |
| 25 | Aurora Unbound | 124 | 0:46 | [MP3](mp3/25_aurora-unbound.mp3) · [FLAC](flac/25_aurora-unbound.flac) |
| 26 | Crown of the Afterlight - Dawn Overture | 108 | 1:11 | [MP3](mp3/26_title_dawn_overture.mp3) · [FLAC](flac/26_title_dawn_overture.flac) |
| 27 | Crown of the Afterlight - Chrome Procession | 120 | 1:04 | [MP3](mp3/27_title_chrome_procession.mp3) · [FLAC](flac/27_title_chrome_procession.flac) |
| 28 | Crown of the Afterlight - Violet Cathedral | 96 | 1:20 | [MP3](mp3/28_title_violet_cathedral.mp3) · [FLAC](flac/28_title_violet_cathedral.flac) |
| 29 | Crown of the Afterlight - Nightfall Ascendant | 132 | 0:58 | [MP3](mp3/29_title_nightfall_ascendant.mp3) · [FLAC](flac/29_title_nightfall_ascendant.flac) |
| 30 | Crown of the Afterlight - Aurora Apotheosis | 116 | 1:06 | [MP3](mp3/30_title_aurora_apotheosis.mp3) · [FLAC](flac/30_title_aurora_apotheosis.flac) |

## Round 2

[Twenty faster tracks with a wider instrument palette](round2/README.md): ten developments, ten left-field experiments, MP3 and FLAC. Original Razor Bloom remains unchanged.

## Trap Circuit

[Ten new trap-style soundtracks](trap10/README.md): 164–184 BPM, custom sliding 808s, MP3 and FLAC.
