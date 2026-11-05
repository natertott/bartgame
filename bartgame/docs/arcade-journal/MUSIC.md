# Original music restoration — 2026-11-05

The user directs the main ROM to use the original songs on `forest-art`.
The fetched branch tip is `cad41afcc9041b0a346fe052aba54f2caa19043a`; the old local
branch name pointed to `1e66780c`, before the music commits. The implementation
uses the fetched object explicitly.

## Source availability and selection

The first music commit, `1ace6e74`, publishes thirty original BARTGAME pieces
in `bartgame/audio/recordings/flac/`, with a manifest and capture provenance.
Subsequent commits add twenty variations, ten trap pieces and eight unrelated
uploaded-song comparisons. The thirty original tracks' composer, hardware
note events and generated player ROM/PCM are absent from the committed tree
and relevant history. Only the unrelated recreation player template is
published; none of its source music is imported into the game.

The selected catalog entries are the original designated exploration/boss
roles:1 Undertow Circuit (sewer),2 Verdant Afterimage (forest),3 Heart of Chrome
(boss), plus26 Dawn Overture (first title-theme option) and25 Aurora Unbound
(victory). This is a documented context mapping, not a claim that the user
selected one of the five title variants in an earlier review.

The source recordings are lossless mGBA captures of the native GBA compositions.
The implementation imports their first passes and original loop starts,
using `audio/original/manifest.json` as the exact path/revision/hash record.
It preserves the original music rather than claiming recovery of missing PSG
score sources. No MP3, commercial reference clip or later uploaded-song
recreation is used.

## Native playback

`tools/import_original_music.py` performs the offline import: lossless source,
mono32768Hz polyphase resampling, nearest signed8-bit quantization at unity
gain. The main game streams these ROM bytes through DMA1/FIFO_A, routed to
both speakers. Timer0 uses reload0xFE00 and the DAC uses32768Hz PWM mode.
Pulse1/noise keep existing SFX; the former music pulse2/wave channels are muted.
There is no runtime mixer, decoder, heap, PCM RAM or per-sample interrupt.

Timer1 cascades the actual sample timer. The existing `gVBlankHook` supplies a
physical-frame heartbeat; the pause-menu hook explicitly chains its saved
hook, so browsing and long room construction do not pause music maintenance.
Sixteen-bit sample deltas wrap safely with a normal VBlank interval (<2 seconds).
When a loop boundary is crossed, DMA is repointed to the corresponding loop
position after accounting for consumed samples, with <=3-sample word-alignment
error. The prefetch guard contains8192 actual samples of loop continuation,
so the interval until that next VBlank remains musical. No silence guard or
reading into the next track's ROM data is required in normal operation.

The title preserves its original531-frame introduction. Other selected tracks
loop from their beginning. Header descriptors retain exact manifest frame
counts plus sample counts. Diagnostics expose current game BGM ID, original
catalog ID, sample position, loop count and last DMA origin. They are read-only
observations, not a game control interface.

DMA3 remains the graphics engine's, timers2/3 remain the profiler's, and the
five streams consume8,855,184 cartridge bytes with only small driver state in
RAM. Actual mGBA playback, transitions, SFX coexistence, loop behavior, waveform
fidelity and gameplay timing are qualified against the final frozen ROM by the
release's native validation tools; source inspection alone does not establish
those results.

## SFX lifetime correction found during audio qualification

The first native recording pass matched the title and sewer PCM, but a real
pause-menu opening left an extra pulse tone over forest and boss playback.
`SFX_MENU` uses an envelope with period0, which has no automatic decay; the old
sound driver only decremented its priority timer and never stopped that note.
The restoration now tracks zero-period pulse/noise notes and stops only those
when the existing SFX timer expires. Naturally decaying sword, jump and hit
sound tails keep their original hardware envelopes. Music PCM, instruments,
levels, timing and DMA are unaffected by this focused correction.

`tools/original_music_review.py` captures actual unprocessed mGBA stereo WAV
excerpts for all five gameplay contexts, compares their waveforms with the
imported ROM PCM, observes every full loop, checks the musical guard and actual
sample rate, and verifies SFX/menu/long-generation coexistence. Its navigation,
player-health/invulnerability and coordinate-only sword positioning fixtures
are disclosed; enemy HP/AI and all music state/registers remain live. A
successful release report must come from the final frozen ROM, not this source
inspection or an earlier candidate capture.
