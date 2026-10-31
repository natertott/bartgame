Source mixes and instrument remakes on GBA: local review template

This template plays one complete stereo PCM recording per cartridge. R01-R08
identify direct conversions of the original mixes, with source instruments
and vocals intact. I01-I08 identify separately reconstructed instrument
arrangements. The UI labels these versions separately. No source recordings
are included in this code template. Keep source-derived audio and ROMs local
unless the user separately authorizes sharing them.

The driver streams ROM to DMA1/FIFO A (left) and DMA2/FIFO B (right). Timer0
sets the exact source descriptor rate; SOUNDBIAS sets DAC PWM resolution/rate.
There is no runtime decoder, sample mixer, floating-point DSP, per-sample IRQ
or software sample RAM buffer. Source intros and tails remain present.

Quality must use synchronized or integer-related sample/PWM clocks. The
preferred mode in the mGBA probe is Timer0 divider 256/reload 0xFF00 at
65,536 Hz with SOUNDBIAS 0x4200 (8-bit PWM at 65,536 Hz). Divider 512/reload
0xFE00 with bias 0x0200 gives 32,768 Hz sample/PWM clocks for smaller ROMs.
The current instrument versions use 32,768 Hz / bias 0x0200. The longest
direct source, Timeless, uses that same mode to fit the complete stereo
file within the cartridge limit. An arbitrary rate such as 44,150.568 Hz with 65,536 Hz
PWM introduces phase jitter and audible distortion; do not use it merely to
fit a song. Select final per-file rates after checking the 32 MiB ROM limit.
Resample source audio offline to the exact selected hardware clock, without
time stretching, and quantize to signed8-bit. Do not normalize or reconstruct
the original mix. Instrument versions are rendered separately. All optional
PSG event fields remain zero.

src/soundtrack_data.h is the exporter contract. Its final two fields are
u16 timer_reload and u16 sound_bias. Slot0 is silent; slot1 is the source.
Prefix title with its ID, for example "R01 - Artist - Song" or "I01 - Song". The UI
shows that ID and title; A plays/stops, START restarts and B stops.

Set total_frames=ceil(source_duration*16777216/280896). Zero pad each PCM
plane from the true source ending to that video-frame boundary, then add at
least 8,192 zero guard samples. Both planes are aligned to 16 bytes. This covers FIFO
prefetch and short main-loop delays, not arbitrary stalls. The hardware
gFrame VBlank counter anchors the loop schedule. Capture only the original
source duration for review; a loop and its padded silence are not appended.

Build with ARM bare-metal GCC in PATH and Python 3:
    bash tools/build_player.sh
Defaults read src/soundtrack_data.c and src/soundtrack_pcm.s and write
build/soundtest/soundtrack.gba. To reuse one code tree for eight separate
source assets, set DATA_DIR, ASSET_ROOT and BUILD_DIR. GAME_DIR selects this
code/header root. ROM_TITLE and ROM_CODE optionally set cartridge metadata.
DATA_DIR must contain soundtrack_data.c and soundtrack_pcm.s; relative
.incbin paths resolve against ASSET_ROOT. Example:
    DATA_DIR=/path/to/R01/src ASSET_ROOT=/path/to/R01 \
        BUILD_DIR=/path/to/R01/build ROM_TITLE=R01SOURCE ROM_CODE=R001 \
        bash tools/build_player.sh

Recording requires mGBA 0.10.x Python bindings and NumPy:
    python tools/capture.py --rom build/soundtest/soundtrack.gba \
        --elf build/soundtest/soundtrack.elf --song 1 --seconds 180.0 \
        --output recording.wav
The recorder captures actual compiled GBA playback without gain, EQ, fades
or normalization. Startup latency of up to one video frame and the emulator
resampler's delay are retained; compare_source.py measures alignment rather
than editing the capture. Native 8-bit conversion and the GBA DAC mean the
result cannot be bit-identical to a modern source recording.

validate.py reports source silence without rejecting it by default, so a
video-source intro or silent ending remains valid. Its optional --max-silence
sets a stricter policy. compare_source.py measures source/capture correlation,
gain and timing drift. These tools record emulation, not a physical speaker
or headphone jack. CPU profiling excludes DMA bus use outside driver calls.
