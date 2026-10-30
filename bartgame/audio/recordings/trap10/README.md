# Trap Circuit — ten GBA soundtracks

Ten new instrumental trap-style tracks at **164–184 BPM**, each **48 bars** (about 63–70 seconds). Custom sliding 808 bass, syncopated kick locks, sharp half-time claps/snares, selective triplet/32nd hats, and distinct melodic palettes keep the collection varied.

- `mp3/`: 192 kbps listening copies; `flac/`: lossless emulator captures.
- [MP3 playlist](mp3.m3u) · [FLAC playlist](flac.m3u)
- `provenance/`: per-track ROM/ELF/audio hashes, exact durations and observed loops.
- `soundtrack_manifest.json`: source instruments, six custom 808 models, glide design, PCM hashes and metadata.
- `SHA256SUMS`: checksums for all twenty audio files. Run `sha256sum -c SHA256SUMS` here.

Captured from the compiled GBA music-player ROM in mGBA 0.10.5. Each file contains a full arranged pass plus three seconds after its loop restart. FLAC is bit-exact to captured WAV; MP3 is the listening encoding. Physical handheld audio has not been recorded. Frame-scheduled loop restarts may have a brief boundary dip.

The custom 808 pitch curves, harmonic shaping, saturation, filters and kick ducking are computed offline and baked into stereo signed 8-bit/16,384 Hz cartridge PCM. DMA1 and DMA2 feed the GBA Direct Sound FIFOs through shared Timer0; no runtime oscillator or sample mixer is needed. Music state is 20 bytes. See `capture_metrics.json` for measured CPU scope and final ROM hash. This is a separate audition bank; prior game assignments and recordings remain unchanged.

GM instrument samples use MIT-licensed FluidR3 (Frank Wen and contributors); notices are included. The custom bass uses the supplied oscillator design. No uploaded reference-song audio was sampled.

| Code | Track | BPM | First pass | Style | Recordings |
| --- | --- | ---: | ---: | --- | --- |
| T01 | Razorwire Run | 172 | 1:07 | Bell-led trap / syncopated warm 808 | [MP3](mp3/01_razorwire-run.mp3) · [FLAC](flac/01_razorwire-run.flac) |
| T02 | Chrome Pressure | 178 | 1:05 | Orchestral trap / grit 808 | [MP3](mp3/02_chrome-pressure.mp3) · [FLAC](flac/02_chrome-pressure.flac) |
| T03 | Jade Circuit | 166 | 1:09 | Melodic flute trap / clean legato 808 | [MP3](mp3/03_jade-circuit.mp3) · [FLAC](flac/03_jade-circuit.flac) |
| T04 | Neon Kickback | 174 | 1:06 | Bright bounce trap / rubber 808 | [MP3](mp3/04_neon-kickback.mp3) · [FLAC](flac/04_neon-kickback.flac) |
| T05 | Voltage Thorns | 182 | 1:03 | Rage trap / charang and buzz 808 | [MP3](mp3/05_voltage-thorns.mp3) · [FLAC](flac/05_voltage-thorns.flac) |
| T06 | Glassfang Sprint | 176 | 1:05 | Glassy dark-crystal melodic trap with gritty 808 locks | [MP3](mp3/06_glassfang-sprint.mp3) · [FLAC](flac/06_glassfang-sprint.flac) |
| T07 | Emerald Heat | 168 | 1:09 | Warm marimba and steel-pan melodic trap with clean 808 bounce | [MP3](mp3/07_emerald-heat.mp3) · [FLAC](flac/07_emerald-heat.flac) |
| T08 | Ghost Rail | 180 | 1:04 | Drill-influenced trap with darting pizzicato, low brass and rubber 808 | [MP3](mp3/08_ghost-rail.mp3) · [FLAC](flac/08_ghost-rail.flac) |
| T09 | Pocket Comet | 164 | 1:10 | Bright electric-piano future trap with celesta and harmonic-guitar replies | [MP3](mp3/09_pocket-comet.mp3) · [FLAC](flac/09_pocket-comet.flac) |
| T10 | Boss Rush Protocol | 184 | 1:03 | Horn-and-guitar boss-anthem trap with Reese 808 and huge half-time claps | [MP3](mp3/10_boss-rush-protocol.mp3) · [FLAC](flac/10_boss-rush-protocol.flac) |
