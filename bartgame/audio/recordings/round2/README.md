# Round 2 — faster grooves, wider instrument palette

Twenty new pieces: **A01–A10** develop the strongest first-round themes; **B01–B10** explore different genres and instrument families. All new pieces are **160–190 BPM** and 32 bars, starting with active hooks and rhythms.

The original Razor Bloom remains unchanged in [the first-round MP3](../mp3/09_razor-bloom.mp3) and [FLAC](../flac/09_razor-bloom.flac). Compare it with A01 Overdrive and A07 Switchblade below.

- `mp3/`: 192 kbps listening copies; `flac/`: lossless emulator captures.
- [MP3 playlist](mp3.m3u) · [FLAC playlist](flac.m3u)
- `provenance/`: 20 capture sidecars with ROM/ELF/audio hashes and loop markers.
- `soundtrack_manifest.json`: score roles, actual instrument programs, tempo, length, PCM metadata and reference entry.
- `SHA256SUMS`: checksums for all 40 new audio files; run `sha256sum -c SHA256SUMS` here.

These recordings come from the compiled GBA stereo review ROM running in mGBA 0.10.5. Each includes a full first pass and 3 seconds after the loop restart. New instrument voices are precombined into separate signed 8-bit 16,384 Hz ROM PCM streams and played through DMA1/FIFO_A left + DMA2/FIFO_B right. The new music does not use a common PSG lead. FLAC is bit-exact to captured WAV; MP3 is the only lossy encoding step after capture. Physical handheld audio has not been recorded; frame-scheduled loop boundaries may have a brief dip.

The stereo prototype bank is separate from the prior 30-track bank and existing gameplay assignments. Its player contains all 20 new tracks and the original Razor reference. Music RAM state is 20 bytes; final-bank update calls average 0.070% of a frame in mGBA, with DMA bus traffic measured separately. See `capture_metrics.json` for scope and exact ROM hash.

Instrument samples use the **MIT-licensed FluidR3 GM** bank (Frank Wen and contributors); copyright and license notices are included here. No uploaded source-song audio was sampled. Traditional instrument names describe General MIDI approximations rather than authentic acoustic ensembles/tuning.

| Code | Track | BPM | First pass | Style | Recordings |
| --- | --- | ---: | ---: | --- | --- |
| A01 | Razor Bloom - Overdrive | 174 | 0:44 | Neurofunk / guitar drum and bass | [MP3](mp3/01_a01-razor-bloom-overdrive.mp3) · [FLAC](flac/01_a01-razor-bloom-overdrive.flac) |
| A02 | Verdant Velocity | 164 | 0:47 | Mallet-driven jungle / bright Latin pop | [MP3](mp3/02_a02-verdant-velocity.mp3) · [FLAC](flac/02_a02-verdant-velocity.flac) |
| A03 | Chrome Heartbeat | 182 | 0:42 | Industrial power-rock / brass chase | [MP3](mp3/03_a03-chrome-heartbeat.mp3) · [FLAC](flac/03_a03-chrome-heartbeat.flac) |
| A04 | Glass Causeway - Prism Sprint | 168 | 0:46 | Speed garage / crystalline guitar pop | [MP3](mp3/04_a04-glass-causeway-prism-sprint.mp3) · [FLAC](flac/04_a04-glass-causeway-prism-sprint.flac) |
| A05 | Neon Market - Flash Sale | 160 | 0:48 | Uptempo disco-funk / clavinet chase | [MP3](mp3/05_a05-neon-market-flash-sale.mp3) · [FLAC](flac/05_a05-neon-market-flash-sale.flac) |
| A06 | Signal Garden - Sunburst | 166 | 0:46 | Lydian piano-funk sprint with flute and alto-sax call and response | [MP3](mp3/06_signal-garden-sunburst.mp3) · [FLAC](flac/06_signal-garden-sunburst.flac) |
| A07 | Razor Bloom - Switchblade | 180 | 0:43 | Brash synth-brass and FM-key trance/acid sprint | [MP3](mp3/07_razor-bloom-switchblade.mp3) · [FLAC](flac/07_razor-bloom-switchblade.flac) |
| A08 | Chromatic Slipstream | 176 | 0:44 | Fast orchestral-rock traversal with violin/cello ostinato and answering trumpet | [MP3](mp3/08_chromatic-slipstream.mp3) · [FLAC](flac/08_chromatic-slipstream.flac) |
| A09 | Rooftop Rally | 170 | 0:45 | Fast rooftop funk with clean-guitar hook, clavinet and trombone breaks | [MP3](mp3/09_rooftop-rally.mp3) · [FLAC](flac/09_rooftop-rally.flac) |
| A10 | Bloom Circuit Finale | 188 | 0:41 | Immediate orchestral-rock anthem with horns, racing strings and bright major release | [MP3](mp3/10_bloom-circuit-finale.mp3) · [FLAC](flac/10_bloom-circuit-finale.flac) |
| B01 | Brass Knuckle Parade | 176 | 0:44 | Big-band swing / brass chase | [MP3](mp3/11_brass-knuckle-parade.mp3) · [FLAC](flac/11_brass-knuckle-parade.flac) |
| B02 | Cactus Rocket | 186 | 0:41 | Bluegrass / country chase | [MP3](mp3/12_cactus-rocket.mp3) · [FLAC](flac/12_cactus-rocket.flac) |
| B03 | Papaya Panic | 172 | 0:45 | Samba / batucada-inspired arcade sprint | [MP3](mp3/13_papaya-panic.mp3) · [FLAC](flac/13_papaya-panic.flac) |
| B04 | Midnight Klezmer Express | 184 | 0:42 | Klezmer / polka-inspired chase | [MP3](mp3/14_midnight-klezmer-express.mp3) · [FLAC](flac/14_midnight-klezmer-express.flac) |
| B05 | Circuit Raga | 180 | 0:43 | South Asian raga-inspired fast dance | [MP3](mp3/15_circuit-raga.mp3) · [FLAC](flac/15_circuit-raga.flac) |
| B06 | Clockwork Gamelan | 162 | 0:47 | Interlocking metallic chamber percussion | [MP3](mp3/16_clockwork-gamelan.mp3) · [FLAC](flac/16_clockwork-gamelan.flac) |
| B07 | Cathedral Pinball | 178 | 0:43 | Baroque counterpoint / orchestral arcade | [MP3](mp3/17_cathedral-pinball.mp3) · [FLAC](flac/17_cathedral-pinball.flac) |
| B08 | Skank Engine | 190 | 0:40 | Brass-led ska-punk | [MP3](mp3/18_skank-engine.mp3) · [FLAC](flac/18_skank-engine.flac) |
| B09 | Tin Toy Stampede | 180 | 0:43 | Odd-accent circus ragtime | [MP3](mp3/19_tin-toy-stampede.mp3) · [FLAC](flac/19_tin-toy-stampede.flac) |
| B10 | Pixel Highlands | 188 | 0:41 | Celtic-reel-inspired folk metal | [MP3](mp3/20_pixel-highlands.mp3) · [FLAC](flac/20_pixel-highlands.flac) |
