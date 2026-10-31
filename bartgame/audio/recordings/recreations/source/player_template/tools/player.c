/* Standalone GBA sound-test player. The sound driver and song data are linked
   directly from the game source tree; the recorder never substitutes a synth. */
#include "gba.h"
#include "sound.h"
#include "soundtrack_data.h"

volatile u8 gVBlankFlag;
volatile u32 gFrame;
volatile u32 gAudioProfileMaxCycles, gAudioProfileSumCycles, gAudioProfileCalls;
volatile u32 gAudioProfileLastCycles;
static u16 sSelected = 1;
static u16 sOldKeys;
static u8 sPlaying;

#define REG_TM2CNT_L REG16(0x108)
#define REG_TM2CNT_H REG16(0x10A)
#define REG_TM3CNT_L REG16(0x10C)
#define REG_TM3CNT_H REG16(0x10E)

/* Five columns, seven bits per column. ASCII space through Z; lower-case
   titles are rendered as upper-case. Unsupported punctuation becomes space. */
static const u8 sFont[59][5] = {
    ['!'-32]={0,0,95,0,0}, ['#'-32]={20,127,20,127,20},
    ['&'-32]={54,73,85,34,80}, ['\''-32]={0,5,3,0,0},
    ['('-32]={0,28,34,65,0}, [')'-32]={0,65,34,28,0},
    ['+'-32]={8,8,62,8,8}, ['-'-32]={8,8,8,8,8},
    ['.'-32]={0,96,96,0,0}, ['/'-32]={32,16,8,4,2},
    ['0'-32]={62,81,73,69,62}, ['1'-32]={0,66,127,64,0},
    ['2'-32]={66,97,81,73,70}, ['3'-32]={33,65,69,75,49},
    ['4'-32]={24,20,18,127,16}, ['5'-32]={39,69,69,69,57},
    ['6'-32]={60,74,73,73,48}, ['7'-32]={1,113,9,5,3},
    ['8'-32]={54,73,73,73,54}, ['9'-32]={6,73,73,41,30},
    [':'-32]={0,54,54,0,0}, ['<'-32]={8,20,34,65,0},
    ['='-32]={20,20,20,20,20}, ['>'-32]={0,65,34,20,8},
    ['?'-32]={2,1,81,9,6},
    ['A'-32]={126,17,17,17,126}, ['B'-32]={127,73,73,73,54},
    ['C'-32]={62,65,65,65,34}, ['D'-32]={127,65,65,34,28},
    ['E'-32]={127,73,73,73,65}, ['F'-32]={127,9,9,9,1},
    ['G'-32]={62,65,73,73,122}, ['H'-32]={127,8,8,8,127},
    ['I'-32]={0,65,127,65,0}, ['J'-32]={32,64,65,63,1},
    ['K'-32]={127,8,20,34,65}, ['L'-32]={127,64,64,64,64},
    ['M'-32]={127,2,12,2,127}, ['N'-32]={127,4,8,16,127},
    ['O'-32]={62,65,65,65,62}, ['P'-32]={127,9,9,9,6},
    ['Q'-32]={62,65,81,33,94}, ['R'-32]={127,9,25,41,70},
    ['S'-32]={70,73,73,73,49}, ['T'-32]={1,1,127,1,1},
    ['U'-32]={63,64,64,64,63}, ['V'-32]={31,32,64,32,31},
    ['W'-32]={127,32,24,32,127}, ['X'-32]={99,20,8,20,99},
    ['Y'-32]={3,4,120,4,3}, ['Z'-32]={97,81,73,69,67},
};

void vblank_isr(void) { gVBlankFlag = 1; ++gFrame; }

static void rect(int x, int y, int width, int height, u16 color) {
    int xx, yy;
    if (x == 0 && width == 240) {
        REG_DMA3CNT = 0;
        REG_DMA3SAD = (u32)&color;
        REG_DMA3DAD = (u32)(MEM_VRAM + y * 240);
        REG_DMA3CNT = 0x81000000 | (width * height);
        return;
    }
    for (yy = 0; yy < height; ++yy)
        for (xx = 0; xx < width; ++xx)
            MEM_VRAM[(y + yy) * 240 + x + xx] = color;
}

static void text(int x, int y, const char* string, u16 color, int scale) {
    int start = x;
    while (*string) {
        unsigned c = (u8)*string++;
        int col, row;
        if (c >= 'a' && c <= 'z') c -= 32;
        if (c == '\n' || x + 5 * scale >= 230) {
            x = start; y += 10 * scale;
            if (c == '\n') continue;
        }
        if (c < 32 || c > 90) c = 32;
        for (col = 0; col < 5; ++col)
            for (row = 0; row < 7; ++row)
                if (sFont[c - 32][col] & (1 << row))
                    rect(x + col * scale, y + row * scale, scale, scale, color);
        x += 6 * scale;
    }
}

static void ui(void) {
    const u16 ink = RGB15(25,29,31), muted = RGB15(12,17,21), accent = RGB15(5,26,25);
    char index[4] = { 'P', 'C', 'M', 0 };
    const char* title = gSoundtrackSongs[1].title;
    u8 instrument = 0;
    if (!title) title = "SOURCE RECORDING";
    if ((title[0]=='R' || title[0]=='I') && title[1]>='0' && title[1]<='9' && title[2]>='0' && title[2]<='9') {
        instrument = title[0]=='I';
        index[0]=title[0]; index[1]=title[1]; index[2]=title[2];
        if (title[3]==' ' && title[4]=='-' && title[5]==' ') title+=6;
    }
    rect(0,0,240,160,RGB15(2,4,7));
    rect(12,12,3,19,accent);
    text(22,13,instrument ? "INSTRUMENTS" : "SOURCE AUDIO",ink,2);
    text(22,34,instrument ? "GBA ARRANGEMENT REVIEW" : "GBA DIRECT PCM REVIEW",muted,1);
    rect(12,52,216,1,RGB15(5,10,14));
    text(14,62,index,accent,1);
    text(48,62,instrument ? "INSTRUMENT REMAKE" : "ORIGINAL MIX",muted,1);
    text(14,79,title,ink,1);
    text(14,105,sPlaying ? "PLAYING" : "READY",accent,1);
    text(14,124,"A  PLAY/STOP    START  RESTART",muted,1);
    text(14,136,"B  STOP",muted,1);
    text(14,148,instrument ? "INSTRUMENTS IN GBA PCM" : "SOURCE MIX IN GBA PCM",muted,1);
}

int main(void) {
    REG_DISPCNT = DCNT_BLANK;
    REG_WAITCNT = 0x4317;
    REG_DISPSTAT = 8;
    REG_IE = 1;
    REG_IME = 1;
    sound_init();
    ui();
    REG_DISPCNT = 0x0403; /* mode 3, BG2 */
    for (;;) {
        u16 keys, down;
        u8 dirty = 0;
        gVBlankFlag = 0;
        while (!gVBlankFlag) { __asm__ volatile("swi 0x02" ::: "memory"); }
        keys = ~REG_KEYINPUT & KEY_ANY;
        down = keys & ~sOldKeys;
        sOldKeys = keys;
        if ((dirty && sPlaying) || (down & KEY_START)) {
            gAudioReviewRequest = sSelected;
            sPlaying = 1;
            dirty = 1;
        }
        if (down & KEY_A) {
            gAudioReviewRequest = sPlaying ? 0xFFFF : sSelected;
            sPlaying = !sPlaying;
            dirty = 1;
        }
        if (down & KEY_B) {
            gAudioReviewRequest = 0xFFFF;
            sPlaying = 0;
            dirty = 1;
        }
        /* Draw a newly selected title before starting its music, so a UI
           redraw can never consume the opening song's sequencer frames. */
        if (dirty) ui();
        REG_TM2CNT_H = 0;
        REG_TM3CNT_H = 0;
        REG_TM2CNT_L = 0;
        REG_TM3CNT_L = 0;
        REG_TM3CNT_H = 0x0084;
        REG_TM2CNT_H = 0x0080;
        sound_update();
        REG_TM2CNT_H = 0;
        REG_TM3CNT_H = 0;
        gAudioProfileLastCycles = ((u32)REG_TM3CNT_L << 16) | REG_TM2CNT_L;
        if (gAudioProfileLastCycles > gAudioProfileMaxCycles)
            gAudioProfileMaxCycles = gAudioProfileLastCycles;
        gAudioProfileSumCycles += gAudioProfileLastCycles;
        ++gAudioProfileCalls;
        if (gAudioReviewActive && (!sPlaying || gAudioReviewActive != sSelected)) {
            sSelected = gAudioReviewActive;
            sPlaying = 1;
        }
    }
}
