/* Signed8-bit mono ROM streams, no runtime decoder or sample buffers. */
.section .rodata.original_music_pcm,"a",%progbits
.balign 16
.global gOriginalPcm_sewer
gOriginalPcm_sewer:
.incbin "audio/original/pcm/sewer.pcm"
.balign 16
.global gOriginalPcm_forest
gOriginalPcm_forest:
.incbin "audio/original/pcm/forest.pcm"
.balign 16
.global gOriginalPcm_boss
gOriginalPcm_boss:
.incbin "audio/original/pcm/boss.pcm"
.balign 16
.global gOriginalPcm_title
gOriginalPcm_title:
.incbin "audio/original/pcm/title.pcm"
.balign 16
.global gOriginalPcm_win
gOriginalPcm_win:
.incbin "audio/original/pcm/win.pcm"
.balign 16
