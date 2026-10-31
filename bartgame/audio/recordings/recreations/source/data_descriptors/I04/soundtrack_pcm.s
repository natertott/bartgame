.section .rodata.music,"a"
.balign 16
.global pcmL
pcmL:
.incbin "pcm_left.bin"
.balign 16
.global pcmR
pcmR:
.incbin "pcm_right.bin"
