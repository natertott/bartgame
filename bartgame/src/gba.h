/* BARTGAME: GBA hardware and basic types. */
#ifndef GBA_H
#define GBA_H

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef signed char s8;
typedef signed short s16;
typedef signed int s32;
typedef volatile u8 vu8;
typedef volatile u16 vu16;
typedef volatile u32 vu32;
typedef u8 bool8;
#define TRUE 1
#define FALSE 0
#define NULL ((void*)0)

#define IWRAM_CODE __attribute__((section(".iwram"), long_call))
#define EWRAM_DATA __attribute__((section(".ewram")))
#define EWRAM_BSS __attribute__((section(".ewram_bss")))
#define ALIGN4 __attribute__((aligned(4)))
#define ARRAY_COUNT(a) ((int)(sizeof(a) / sizeof((a)[0])))
#define ABS(x) ((x) < 0 ? -(x) : (x))
#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define CLAMP(v, lo, hi) ((v) < (lo) ? (lo) : (v) > (hi) ? (hi) : (v))

/* fixed point: positions are Q16.16 (pixel = >> 16), speeds Q8.8 */
#define Q8(n) ((s32)((n) * 256))
#define Q16(n) ((s32)((n) * 65536))
#define PX(q16) ((q16) >> 16)

#define REG_BASE 0x04000000
#define REG16(o) (*(vu16*)(REG_BASE + (o)))
#define REG32(o) (*(vu32*)(REG_BASE + (o)))

#define REG_DISPCNT REG16(0x00)
#define REG_DISPSTAT REG16(0x04)
#define REG_VCOUNT REG16(0x06)
#define REG_BG0CNT REG16(0x08)
#define REG_BG1CNT REG16(0x0A)
#define REG_BG2CNT REG16(0x0C)
#define REG_BG3CNT REG16(0x0E)
#define REG_BG0HOFS REG16(0x10)
#define REG_BG0VOFS REG16(0x12)
#define REG_BG1HOFS REG16(0x14)
#define REG_BG1VOFS REG16(0x16)
#define REG_BG2HOFS REG16(0x18)
#define REG_BG2VOFS REG16(0x1A)
#define REG_BG3HOFS REG16(0x1C)
#define REG_BG3VOFS REG16(0x1E)
#define REG_BG2PA REG16(0x20)
#define REG_BG2PB REG16(0x22)
#define REG_BG2PC REG16(0x24)
#define REG_BG2PD REG16(0x26)
#define REG_BG2X REG32(0x28)
#define REG_BG2Y REG32(0x2C)
#define REG_WIN0H REG16(0x40)
#define REG_WIN1H REG16(0x42)
#define REG_WIN0V REG16(0x44)
#define REG_WIN1V REG16(0x46)
#define REG_WININ REG16(0x48)
#define REG_WINOUT REG16(0x4A)
#define REG_MOSAIC REG16(0x4C)
#define REG_BLDCNT REG16(0x50)
#define REG_BLDALPHA REG16(0x52)
#define REG_BLDY REG16(0x54)

#define REG_SOUND1CNT_L REG16(0x60)
#define REG_SOUND1CNT_H REG16(0x62)
#define REG_SOUND1CNT_X REG16(0x64)
#define REG_SOUND2CNT_L REG16(0x68)
#define REG_SOUND2CNT_H REG16(0x6C)
#define REG_SOUND3CNT_L REG16(0x70)
#define REG_SOUND3CNT_H REG16(0x72)
#define REG_SOUND3CNT_X REG16(0x74)
#define REG_SOUND4CNT_L REG16(0x78)
#define REG_SOUND4CNT_H REG16(0x7C)
#define REG_SOUNDCNT_L REG16(0x80)
#define REG_SOUNDCNT_H REG16(0x82)
#define REG_SOUNDCNT_X REG16(0x84)
#define REG_SOUNDBIAS REG16(0x88)
#define WAVE_RAM ((vu32*)(REG_BASE + 0x90))

#define REG_DMA3SAD REG32(0xD4)
#define REG_DMA3DAD REG32(0xD8)
#define REG_DMA3CNT REG32(0xDC)

#define REG_TM0CNT_L REG16(0x100)
#define REG_TM0CNT_H REG16(0x102)

#define REG_KEYINPUT REG16(0x130)
#define REG_IE REG16(0x200)
#define REG_IF REG16(0x202)
#define REG_WAITCNT REG16(0x204)
#define REG_IME REG16(0x208)

#define DCNT_MODE0 0x0000
#define DCNT_MODE3 0x0003
#define DCNT_OBJ_1D 0x0040
#define DCNT_BG0 0x0100
#define DCNT_BG1 0x0200
#define DCNT_BG2 0x0400
#define DCNT_BG3 0x0800
#define DCNT_OBJ 0x1000
#define DCNT_WIN0 0x2000
#define DCNT_WIN1 0x4000
#define DCNT_OBJWIN 0x8000
#define DCNT_BLANK 0x0080

#define BGCNT_PRIO(p) (p)
#define BGCNT_CHARBASE(n) ((n) << 2)
#define BGCNT_SCREENBASE(n) ((n) << 8)
#define BGCNT_SIZE_32x32 (0 << 14)
#define BGCNT_SIZE_64x32 (1 << 14)
#define BGCNT_SIZE_32x64 (2 << 14)
#define BGCNT_SIZE_64x64 (3 << 14)

#define KEY_A 0x0001
#define KEY_B 0x0002
#define KEY_SELECT 0x0004
#define KEY_START 0x0008
#define KEY_RIGHT 0x0010
#define KEY_LEFT 0x0020
#define KEY_UP 0x0040
#define KEY_DOWN 0x0080
#define KEY_R 0x0100
#define KEY_L 0x0200
#define KEY_ANY 0x03FF
#define KEY_DPAD (KEY_RIGHT | KEY_LEFT | KEY_UP | KEY_DOWN)

#define MEM_PAL_BG ((vu16*)0x05000000)
#define MEM_PAL_OBJ ((vu16*)0x05000200)
#define MEM_VRAM ((vu16*)0x06000000)
#define MEM_VRAM_OBJ ((vu16*)0x06010000)
#define MEM_OAM ((vu16*)0x07000000)
#define CHARBLOCK(n) ((vu16*)(0x06000000 + (n) * 0x4000))
#define SCREENBLOCK(n) ((vu16*)(0x06000000 + (n) * 0x800))
#define OBJ_TILE(n) ((vu16*)(0x06010000 + (n) * 32))

#define RGB15(r, g, b) ((r) | ((g) << 5) | ((b) << 10))

/* OAM attributes */
#define ATTR0_Y(y) ((y) & 0xFF)
#define ATTR0_BLEND 0x0400
#define ATTR0_WINDOW 0x0800
#define ATTR0_HIDE 0x0200
#define ATTR0_SQUARE 0x0000
#define ATTR0_WIDE 0x4000
#define ATTR0_TALL 0x8000
#define ATTR1_X(x) ((x) & 0x1FF)
#define ATTR1_HFLIP 0x1000
#define ATTR1_VFLIP 0x2000
#define ATTR1_SIZE(s) ((s) << 14)
#define ATTR2_TILE(t) ((t) & 0x3FF)
#define ATTR2_PRIO(p) ((p) << 10)
#define ATTR2_PAL(p) ((p) << 12)

typedef struct {
    u16 attr0, attr1, attr2, fill;
} OamEntry;

/* DMA3 */
#define DMA_ENABLE 0x80000000
#define DMA_16 0x00000000
#define DMA_32 0x04000000
#define DMA_SRC_FIXED 0x01000000
static inline void dma3_copy32(const void* src, volatile void* dst, u32 bytes) {
    REG_DMA3SAD = (u32)src;
    REG_DMA3DAD = (u32)dst;
    REG_DMA3CNT = DMA_ENABLE | DMA_32 | (bytes >> 2);
}
static inline void dma3_copy16(const void* src, volatile void* dst, u32 bytes) {
    REG_DMA3SAD = (u32)src;
    REG_DMA3DAD = (u32)dst;
    REG_DMA3CNT = DMA_ENABLE | DMA_16 | (bytes >> 1);
}
static inline void dma3_fill32(u32 value, volatile void* dst, u32 bytes) {
    static volatile u32 v;
    v = value;
    REG_DMA3SAD = (u32)&v;
    REG_DMA3DAD = (u32)dst;
    REG_DMA3CNT = DMA_ENABLE | DMA_32 | DMA_SRC_FIXED | (bytes >> 2);
}

static inline void vblank_wait(void) {
    __asm__ volatile("swi 0x05" ::: "r0", "r1", "r2", "r3", "memory");
}

void* memcpy(void* dst, const void* src, u32 n);
void* memset(void* dst, int c, u32 n);
void memcpy32(void* dst, const void* src, u32 bytes);
void memset32(void* dst, u32 value, u32 bytes);

#endif
