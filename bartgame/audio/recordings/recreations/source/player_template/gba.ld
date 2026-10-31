/* BARTGAME linker script. ROM code and data, IWRAM for hot code and the
   actor pools, EWRAM for the big buffers (room maps, generated world). */
OUTPUT_FORMAT("elf32-littlearm")
OUTPUT_ARCH(arm)
ENTRY(_start)

MEMORY
{
    rom   (rx)  : ORIGIN = 0x08000000, LENGTH = 32M
    iwram (rwx) : ORIGIN = 0x03000000, LENGTH = 32K - 256
    ewram (rw)  : ORIGIN = 0x02000000, LENGTH = 256K
}

SECTIONS
{
    .text :
    {
        KEEP(*(.text.startup))
        *(.text .text.* .gnu.linkonce.t.*)
        *(.glue_7) *(.glue_7t) *(.v4_bx)
        . = ALIGN(4);
    } > rom

    .rodata :
    {
        *(.rodata .rodata.* .gnu.linkonce.r.*)
        . = ALIGN(4);
    } > rom

    .ARM.exidx : { *(.ARM.exidx*) } > rom

    /* ARM hot code and initialised IWRAM data, copied from ROM at boot. */
    .iwram :
    {
        __iwram_start = .;
        *_iwram.o(.text .text.* .rodata .rodata.*)
        *(.iwram .iwram.*)
        *(.data .data.* .gnu.linkonce.d.*)
        . = ALIGN(4);
        __iwram_end = .;
    } > iwram AT > rom
    __iwram_lma = LOADADDR(.iwram);

    .bss (NOLOAD) :
    {
        __bss_start = .;
        *(.bss .bss.* .gnu.linkonce.b.*)
        *(COMMON)
        . = ALIGN(4);
        __bss_end = .;
    } > iwram

    /* Initialised EWRAM data, copied from ROM at boot. */
    .ewram :
    {
        __ewram_start = .;
        *(.ewram .ewram.*)
        . = ALIGN(4);
        __ewram_end = .;
    } > ewram AT > rom
    __ewram_lma = LOADADDR(.ewram);

    .ewram_bss (NOLOAD) :
    {
        __ewram_bss_start = .;
        *(.ewram_bss .ewram_bss.*)
        . = ALIGN(4);
        __ewram_bss_end = .;
    } > ewram

    __rom_end = LOADADDR(.ewram) + SIZEOF(.ewram);

    /DISCARD/ : { *(.comment) *(.note*) *(.ARM.attributes) }
}
