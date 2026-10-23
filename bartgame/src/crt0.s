@ BARTGAME startup. ROM header, stacks, section copies, IRQ dispatch.
    .section .text.startup, "ax"
    .arm
    .global _start
_start:
    b       start_vector
    .fill   156, 1, 0               @ Nintendo logo, written by gbafix
    .ascii  "BARTGAME    "          @ title (12)
    .ascii  "BART"                  @ game code
    .ascii  "00"                    @ maker code
    .byte   0x96                    @ fixed value
    .byte   0, 0                    @ unit code, device type
    .fill   7, 1, 0                 @ reserved
    .byte   0                       @ version
    .byte   0                       @ header checksum, written by gbafix
    .hword  0                       @ reserved

start_vector:
    mov     r0, #0x12               @ IRQ mode stack
    msr     cpsr_c, r0
    ldr     sp, =0x03007FA0
    mov     r0, #0x1F               @ system mode stack
    msr     cpsr_c, r0
    ldr     sp, =0x03007F00

    @ .iwram: ROM -> IWRAM
    ldr     r0, =__iwram_lma
    ldr     r1, =__iwram_start
    ldr     r2, =__iwram_end
    bl      copy_words
    @ .ewram: ROM -> EWRAM
    ldr     r0, =__ewram_lma
    ldr     r1, =__ewram_start
    ldr     r2, =__ewram_end
    bl      copy_words
    @ zero .bss and .ewram_bss
    ldr     r1, =__bss_start
    ldr     r2, =__bss_end
    bl      zero_words
    ldr     r1, =__ewram_bss_start
    ldr     r2, =__ewram_bss_end
    bl      zero_words

    @ IRQ handler address for the BIOS
    ldr     r0, =irq_handler
    ldr     r1, =0x03007FFC
    str     r0, [r1]

    ldr     r0, =main
    bx      r0

@ r0 src, r1 dst, r2 end (dst)
copy_words:
    cmp     r1, r2
    bxge    lr
1:  ldr     r3, [r0], #4
    str     r3, [r1], #4
    cmp     r1, r2
    blt     1b
    bx      lr

zero_words:
    mov     r0, #0
    cmp     r1, r2
    bxge    lr
1:  str     r0, [r1], #4
    cmp     r1, r2
    blt     1b
    bx      lr

@ The IRQ handler lives in IWRAM. It acknowledges the interrupt, sets the
@ BIOS flag IntrWait reads, and calls the C handler for VBlank.
    .section .iwram, "ax"
    .arm
    .align 2
    .global irq_handler
irq_handler:
    mov     r3, #0x04000000
    add     r3, r3, #0x200
    ldr     r0, [r3]                @ IE | IF << 16
    and     r1, r0, r0, lsr #16     @ pending = IE & IF
    strh    r1, [r3, #2]            @ acknowledge in IF
    ldr     r2, =0x03007FF8         @ BIOS IntrWait flags
    ldrh    r0, [r2]
    orr     r0, r0, r1
    strh    r0, [r2]
    tst     r1, #1                  @ VBlank?
    bxeq    lr
    @ switch to system mode, enable IRQ nesting off, call vblank_isr()
    mrs     r2, spsr
    push    {r2, lr}
    mov     r0, #0x1F
    msr     cpsr_c, r0
    push    {lr}
    ldr     r0, =vblank_isr
    mov     lr, pc
    bx      r0
    pop     {lr}
    mov     r0, #0x92
    msr     cpsr_c, r0
    pop     {r2, lr}
    msr     spsr, r2
    bx      lr
    .pool
