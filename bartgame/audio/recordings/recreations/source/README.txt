GBA ORIGINALS — SOURCE / SCORES

Sixteen full-length GBA ROMs are supplied separately: eight original-mix PCM
conversions (R01–R08) and eight automatic instrument reconstructions (I01–I08).
This source archive omits the large PCM planes, original uploads and model
weights. The original mixes keep performance and vocals; instrument covers
use symbolic notes/onsets only. Automatic transcription is approximate.

PLAY
Use the separate ROM archive or individual ROM links. A play/stop; START
restart; B stop. Each cartridge holds one complete source/version. Tested in
mGBA 0.10.5; no physical handheld recording was made.

RECREATE NATIVE PCM FROM YOUR MP3 UPLOADS
Requires Python 3, numpy/scipy per requirements-synthesis.txt and ffmpeg with
soxr resampling. Put your eight original filenames in one input directory:
    python3 tools/rebuild_native.py --inputs /path/to/mp3s --output generated
This verifies filenames and regenerates signed 8-bit PCM at synchronized 65,536 Hz,
except complete Timeless at 32,768 Hz to fit 32 MiB. A common documented linear gain
avoids clipping while preserving relative source levels; no time stretch/cuts.
Source hash identities are recorded in source_manifest.json.

RE-SYNTHESIZE / EDIT AN INSTRUMENTAL SCORE
Install libfluidsynth (tested 2.4.4) and Python requirements. Fetch the MIT bank:
    bash tools/fetch_soundfont.sh
Or set GBA_SOUNDFONT to a local FluidR3_GM.sf2. The bank is not bundled.
Scores and editable MIDI are in scores/ and midi/. Example:
    python3 tools/rebuild_cover.py --score scores/01_iloveuihateu.cover.json --output generated/covers/01_iloveuihateu.npy
That renderer accepts symbolic note/drum events only, not source waveforms.
The score uses beat units at 120 BPM (one beat = .5 seconds) to preserve the original
absolute timestamps; this is a timing representation, not a new musical tempo.
Convert resulting floats to Ixx ROM planes with export_pcm.export_planes at
32768Hz, preserving source duration/guards, as documented in its source.
The provided MIDI preserves inferred notes and bass wheel curves with 12-semitone
range; it cannot reproduce the source singer, articulation or timbre exactly.

BUILD GENERATED PCM INTO A ROM
Install arm-none-eabi GCC/binutils and Python 3. Example after native generation:
    DATA_DIR="$PWD/generated/assets/R01/src" ASSET_ROOT="$PWD/generated/assets/R01" BUILD_DIR="$PWD/generated/builds/R01" bash player_template/tools/build_player.sh
The matching standalone template, header contract and bitrate/PWM fields are in
player_template/. Example C/ASM descriptors are in data_descriptors/. Actual
PCM assets are intentionally omitted because your source recordings regenerate
them; the complete playable ROMs are supplied in the separate archive.

HARDWARE / ACCURACY
Two DMA channels stream stereo directly from cartridge ROM into GBA FIFOs.
No runtime mixer, decoder or sample RAM buffer is used. The rate/PWM choices
were measured, including rejection of asynchronous clocks that add sidebands.
Direct native captures have authentic emulator bass high-pass/DAC coloration.
The strongest full-performance reference is the native PCM version; instrument
rebuilds can miss or mislabel notes, chords, octaves, bends and drum attacks.
The note candidates came from full mixed audio via Basic Pitch+harmonic/bass
views and independent low-band YIN; no official stems/MIDI or note-perfect
human score were available. Source timings and complete file lengths remain.

The recording derivatives and editable source are published at your request; compiled ROMs remain separate chat-download artifacts.
Soundbank copyright/license notices accompany the downloads. The diagnostic
neural separation pilot was not used as a full-track isolated stem and is not
represented as one. See the listening report and JSON provenance for methods.
