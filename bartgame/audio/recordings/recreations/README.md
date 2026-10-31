# Original uploads — GBA recreations and A/B comparison

Both versions of all eight uploads are here, in full length:

- **R01–R08 / original mix:** the uploaded performance, instruments and vocals played through the GBA’s Direct Sound system.
- **I01–I08 / instrument rebuild:** newly synthesized game-instrument sounds from automatic note and drum analysis. These are approximate; dense chords, octaves, vocal phrasing and drum details can be missed or misidentified.

Each version includes **MP3 and lossless FLAC**, captured from its compiled GBA ROM in **mGBA 0.10.5**. Both sets preserve the complete decoded source durations, with no appended loop. The original-mix versions are the closest performance match. Physical-handheld audio was not recorded.

[Interactive A/B page](index.html) · [Method and limitations](reports/comparison_notes.html) · [Source/build instructions](source/README.txt) · [Editable MIDI](source/midi) · [Inferred scores](source/scores)

GitHub displays HTML as source. To use the interactive page offline, download this folder with its subfolders and open `index.html`. The player switches versions at the current timestamp and optionally matches listening volume without modifying the files.

[Original-mix playlist](native_playlist.m3u) · [Instrument-rebuild playlist](instrument_playlist.m3u)

## Recordings

| Song | Full length | Original mix on GBA | Instrument rebuild |
| --- | ---: | --- | --- |
| Playboi Carti — ILoveUIHateU | 2:15 | [MP3](recordings/native/mp3/R01_iloveuihateu.mp3) · [FLAC](recordings/native/flac/R01_iloveuihateu.flac) | [MP3](recordings/instrument/mp3/I01_iloveuihateu.mp3) · [FLAC](recordings/instrument/flac/I01_iloveuihateu.flac) |
| Desire — Under Your Spell | 3:53 | [MP3](recordings/native/mp3/R02_desire-under-your-spell.mp3) · [FLAC](recordings/native/flac/R02_desire-under-your-spell.flac) | [MP3](recordings/instrument/mp3/I02_desire-under-your-spell.mp3) · [FLAC](recordings/instrument/flac/I02_desire-under-your-spell.flac) |
| The Weeknd with Playboi Carti — Timeless | 4:16 | [MP3](recordings/native/mp3/R03_timeless.mp3) · [FLAC](recordings/native/flac/R03_timeless.flac) | [MP3](recordings/instrument/mp3/I03_timeless.mp3) · [FLAC](recordings/instrument/flac/I03_timeless.flac) |
| Snow Strippers — Under Your Spell | 3:38 | [MP3](recordings/native/mp3/R04_snow-strippers-under-your-spell.mp3) · [FLAC](recordings/native/flac/R04_snow-strippers-under-your-spell.flac) | [MP3](recordings/instrument/mp3/I04_snow-strippers-under-your-spell.mp3) · [FLAC](recordings/instrument/flac/I04_snow-strippers-under-your-spell.flac) |
| Friday Night | 3:58 | [MP3](recordings/native/mp3/R05_friday-night.mp3) · [FLAC](recordings/native/flac/R05_friday-night.flac) | [MP3](recordings/instrument/mp3/I05_friday-night.mp3) · [FLAC](recordings/instrument/flac/I05_friday-night.flac) |
| Daft Punk — Voyager | 3:48 | [MP3](recordings/native/mp3/R06_voyager.mp3) · [FLAC](recordings/native/flac/R06_voyager.flac) | [MP3](recordings/instrument/mp3/I06_voyager.mp3) · [FLAC](recordings/instrument/flac/I06_voyager.flac) |
| Sunday Evening Pain | 3:01 | [MP3](recordings/native/mp3/R07_sunday-evening-pain.mp3) · [FLAC](recordings/native/flac/R07_sunday-evening-pain.flac) | [MP3](recordings/instrument/mp3/I07_sunday-evening-pain.mp3) · [FLAC](recordings/instrument/flac/I07_sunday-evening-pain.flac) |
| Drake — What’s Next | 3:20 | [MP3](recordings/native/mp3/R08_whats-next.mp3) · [FLAC](recordings/native/flac/R08_whats-next.flac) | [MP3](recordings/instrument/mp3/I08_whats-next.mp3) · [FLAC](recordings/instrument/flac/I08_whats-next.flac) |

## Data and playback

- `recordings/native/` and `recordings/instrument/`: all 32 audio files.
- `recordings/provenance/`: 16 capture sidecars with exact durations and ROM/ELF/audio hashes.
- `source/`: converter and player source, inferred note scores, MIDI and regeneration instructions.
- `reports/data/`: duration, fidelity, source-model and playback validation evidence.
- `SHA256SUMS`: all 32 audio-file checksums; verify with `sha256sum -c SHA256SUMS` here.

Seven original-mix ROMs use synchronized 65,536 Hz stereo PCM; complete “Timeless” uses 32,768 Hz to fit the normal 32 MiB cartridge window. Instrument rebuilds use 32,768 Hz stereo. GBA quantization and output-filter coloration remain. The original-mix conversion applies one common linear headroom gain and preserves source pitch/timing/structure.

The player streams cartridge PCM with DMA1/DMA2 and Timer0, with 20 bytes of driver state and no runtime sample mixer. The inferred scores are editable drafts, not official stems or verified note-perfect transcriptions. GM instrument samples use the MIT-licensed FluidR3 bank; credit and license notices are in `licenses/`.

Compiled ROMs and ZIP archives remain excluded under the repository’s existing `.gitignore`. They were supplied in the chat downloads; this folder contains the recordings and editable/rebuildable source. Original uploaded MP3 files are not copied into this repository folder.
