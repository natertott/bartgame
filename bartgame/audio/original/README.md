# Original BARTGAME soundtrack in the main ROM

These five tracks are original game compositions published on `forest-art`,
pinned at `cad41afcc9041b0a346fe052aba54f2caa19043a`:

| Game context | Catalog ID | Original piece |
| --- | ---: | --- |
| Drain / sewer | 1 | Undertow Circuit |
| Blighted Forest | 2 | Verdant Afterimage |
| Heart battle | 3 | Heart of Chrome |
| Title | 26 | Crown of the Afterlight — Dawn Overture |
| Victory | 25 | Aurora Unbound |

The branch stores lossless captures of its compiled music-player ROM in mGBA,
with exact first-pass and loop metadata. Its thirty-piece original composer
and generated player source/PCM were not committed. The later `recreations/`
folder contains different uploaded-song material and is not used here.

The main game therefore imports the original lossless native mixes, preserving
their compositions, instruments and timing, rather than inventing replacement
scores. `manifest.json` records the pinned source FLAC and manifest hashes,
first-pass/loop times, hardware sample rate, quantization error and ROM hashes.
No MP3 is decoded and no foreign-source recording is included.
`source-catalogue.json`, `source-SHA256SUMS.txt` and `source-captures/` retain
the original small metadata verbatim; each imported FLAC is checked against
its published SHA256 before conversion.

Re-import from the pinned Git objects, from `bartgame/`:

```sh
python3 tools/import_original_music.py
```

Re-import needs the pinned commit locally, `ffmpeg` and `numpy`. Ordinary builds
need none of those audio tools: they assemble the checked-in ROM streams.

The streams are signed8-bit mono at32768Hz, unity gain, rounded once from the
polyphase-resampled native mix. The GBA uses its synchronous32768Hz PWM mode.
DMA1 streams FIFO_A directly from cartridge ROM to both speakers. No decoder,
mixer, heap or sample buffer runs in gameplay. Pulse1 and noise retain the
existing gameplay effects. Timer0 clocks samples; Timer1 counts them. The
existing VBlank-hook chain maintains loop timing even if room construction or
menu drawing spans multiple video frames. Video keeps DMA3 and profiling keeps
timers2/3.

Each stream ends with8192 samples of the next loop's musical continuation,
plus alignment padding. This is safe FIFO prefetch and a continuous boundary,
not silence. At the next physical VBlank the driver repositions DMA at the
loop position corresponding to samples already consumed, with at most three
samples of backward word alignment. Title playback keeps its original intro
and loops from frame531 rather than replaying the introduction.

The five payloads total8,855,184 cartridge bytes. They do not occupy EWRAM or
IWRAM sample memory. `src/original_music_data.c` binds the existing five BGM IDs
to these original catalog entries. `src/sound.c` maintains the stream and
read-only diagnostics used by native emulator qualification.
