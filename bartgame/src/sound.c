/* BARTGAME: sound on the GBA's PSG channels. No mixer, near-zero CPU.
   Channel 1 (square, sweep): sound effects. Channel 2 (square): melody.
   Channel 3 (wave): bass. Channel 4 (noise): percussion and hits.

   The tracker: each song has three tracks of (note, length) pairs, in
   rows of a fixed tick length. Notes are semitones from C-2 (0) with 0xFF
   as a rest. A track loops. The whole thing runs in a few hundred cycles
   a frame. */
#include "gba.h"
#include "sound.h"

static u8 sSfxTimer;
static u8 sSfxCur;
static u8 sBgm;

/* semitone 0 = C2 (65.4 Hz). GBA square freq register: 2048 - 131072/f */
static const u16 sNoteFreq[60] = {
    44, 156, 262, 363, 457, 547, 631, 710, 786, 854, 923, 986,          /* C2..B2 */
    1046, 1102, 1155, 1205, 1253, 1297, 1339, 1379, 1417, 1452, 1486, 1517, /* C3..B3 */
    1546, 1575, 1602, 1627, 1650, 1673, 1694, 1714, 1732, 1750, 1767, 1783, /* C4..B4 */
    1798, 1812, 1825, 1837, 1849, 1860, 1871, 1881, 1890, 1899, 1907, 1915, /* C5..B5 */
    1923, 1930, 1936, 1943, 1949, 1954, 1959, 1964, 1969, 1974, 1978, 1982, /* C6..B6 */
};

#define R 0xFF
#define END 0xFE

typedef struct {
    const u8* melody;   /* note, length (ticks) pairs, END terminates */
    const u8* bass;
    const u8* drums;    /* 0 rest, 1 kick, 2 hat, 3 snare; one byte per row */
    u8 tick;            /* frames per tick */
    u8 drum_rows;       /* length of the drum pattern */
    u8 melody_env;      /* envelope for channel 2 */
    u8 melody_duty;
} Song;

/* The drain: slow, dripping, a minor third hanging in the dark. */
static const u8 sSewerMelody[] = {
    R, 8, 15, 4, R, 4, 18, 4, R, 4, 15, 8, R, 8, 13, 4, R, 4, 15, 4, R, 12,
    R, 8, 10, 4, R, 4, 13, 4, R, 4, 15, 4, 18, 4, R, 4, 15, 8, R, 16,
    END,
};
static const u8 sSewerBass[] = { 3, 16, 3, 16, 1, 16, 1, 16, 3, 16, 3, 16, 6, 8, 5, 8, 3, 16, END };
static const u8 sSewerDrums[] = { 1, 0, 0, 0, 2, 0, 0, 0, 1, 0, 0, 0, 2, 0, 2, 0 };

/* The wood: a lilting, uneasy tune over a droning fifth. */
static const u8 sForestMelody[] = {
    27, 3, 30, 3, 34, 6, 30, 3, 27, 3, 25, 6, 27, 3, 30, 3, 32, 6, 30, 6, R, 6,
    27, 3, 30, 3, 34, 6, 37, 3, 34, 3, 32, 6, 30, 3, 27, 3, 25, 6, 27, 6, R, 6,
    22, 3, 25, 3, 29, 6, 25, 3, 22, 3, 20, 6, 22, 3, 25, 3, 27, 6, 25, 6, R, 6,
    30, 3, 34, 3, 37, 6, 34, 3, 30, 3, 27, 6, 25, 3, 27, 3, 30, 12, R, 6,
    END,
};
static const u8 sForestBass[] = { 3, 12, 10, 12, 3, 12, 10, 12, 1, 12, 8, 12, 3, 12, 10, 12, END };
static const u8 sForestDrums[] = { 1, 0, 2, 0, 0, 0, 2, 0, 1, 0, 2, 0, 3, 0, 2, 2 };

/* The Heart: a hammering pulse. */
static const u8 sBossMelody[] = {
    15, 2, 15, 2, 18, 2, 15, 2, 21, 2, 15, 2, 18, 2, 20, 2,
    15, 2, 15, 2, 18, 2, 15, 2, 22, 2, 21, 2, 18, 2, 15, 2,
    13, 2, 13, 2, 16, 2, 13, 2, 20, 2, 13, 2, 16, 2, 18, 2,
    13, 2, 13, 2, 16, 2, 13, 2, 22, 4, 20, 4,
    END,
};
static const u8 sBossBass[] = { 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 1, 4, 1, 4, 1, 4, 1, 4, 1, 4, 1, 4, 1, 4, 1, 4, END };
static const u8 sBossDrums[] = { 1, 2, 3, 2, 1, 2, 3, 2, 1, 1, 3, 2, 1, 2, 3, 3 };

/* The title: sparse, bell-like. */
static const u8 sTitleMelody[] = { 27, 6, R, 2, 34, 6, R, 2, 30, 4, 32, 4, 30, 12, R, 12, 25, 6, R, 2, 32, 6, R, 2, 30, 4, 27, 4, 25, 12, R, 20, END };
static const u8 sTitleBass[] = { 3, 24, 6, 24, 1, 24, 3, 24, END };
static const u8 sTitleDrums[] = { 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0 };

/* The win: a rising fanfare that resolves. */
static const u8 sWinMelody[] = { 27, 4, 30, 4, 34, 4, 39, 8, 37, 4, 34, 4, 30, 4, 34, 12, R, 8, 25, 4, 29, 4, 32, 4, 37, 8, 34, 4, 37, 4, 39, 16, R, 24, END };
static const u8 sWinBass[] = { 3, 16, 8, 16, 1, 16, 3, 16, 5, 16, 8, 16, 3, 32, END };
static const u8 sWinDrums[] = { 1, 0, 2, 0, 1, 0, 2, 0, 1, 0, 2, 0, 3, 0, 3, 3 };

static const Song sSongs[] = {
    [BGM_NONE] = { 0, 0, 0, 8, 16, 0, 0 },
    [BGM_SEWER] = { sSewerMelody, sSewerBass, sSewerDrums, 10, 16, 0x52, 2 },
    [BGM_FOREST] = { sForestMelody, sForestBass, sForestDrums, 7, 16, 0x62, 1 },
    [BGM_BOSS] = { sBossMelody, sBossBass, sBossDrums, 5, 16, 0x72, 0 },
    [BGM_TITLE] = { sTitleMelody, sTitleBass, sTitleDrums, 8, 16, 0x43, 2 },
    [BGM_WIN] = { sWinMelody, sWinBass, sWinDrums, 7, 16, 0x72, 2 },
};

typedef struct {
    const u8* pos;
    u8 left;
} Track;

static Track sMel, sBass;
static u8 sTickTimer, sRow;

/* a hollow, organ-like wave for channel 3 */
static const u32 sWave[4] = { 0x02468ACE, 0xFFFFFFFF, 0xFDB97531, 0x00000000 };

void sound_init(void) {
    REG_SOUNDCNT_X = 0x80;      /* master on */
    REG_SOUNDCNT_L = 0xFF77;    /* all channels both sides, volume 7 */
    REG_SOUNDCNT_H = 0x0002;    /* PSG 100% */
    REG_SOUNDBIAS = 0x0200;
    sSfxTimer = 0;
    /* load the wave */
    REG_SOUND3CNT_L = 0x0040; /* bank 1 selected for playing so we can write bank 0 */
    WAVE_RAM[0] = sWave[0];
    WAVE_RAM[1] = sWave[1];
    WAVE_RAM[2] = sWave[2];
    WAVE_RAM[3] = sWave[3];
    REG_SOUND3CNT_L = 0x0080; /* bank 0 plays, channel on */
}

static void ch1(u16 sweep, u16 env, u16 freq) {
    REG_SOUND1CNT_L = sweep;
    REG_SOUND1CNT_H = env;
    REG_SOUND1CNT_X = freq | 0x8000;
}

static void ch4(u16 env, u16 poly) {
    REG_SOUND4CNT_L = env;
    REG_SOUND4CNT_H = poly | 0x8000;
}

static void ch2_note(int note, int env, int duty) {
    if (note == R || note >= 60) {
        REG_SOUND2CNT_L = 0x0000;
        REG_SOUND2CNT_H = 0x8000;
        return;
    }
    REG_SOUND2CNT_L = (env << 8) | (duty << 6);
    REG_SOUND2CNT_H = sNoteFreq[note] | 0x8000;
}

static void ch3_note(int note) {
    if (note == R || note >= 60) {
        REG_SOUND3CNT_H = 0x0000;
        return;
    }
    REG_SOUND3CNT_H = 0x2000; /* volume 50% */
    REG_SOUND3CNT_X = sNoteFreq[note] | 0x8000;
}

static void drum(int d) {
    if (sSfxTimer)
        return; /* effects own the noise channel while they play */
    switch (d) {
        case 1: ch4(0x6100, 0x0056); break; /* kick: low, short */
        case 2: ch4(0x3100, 0x0024); break; /* hat: high, very short */
        case 3: ch4(0x8200, 0x0045); break; /* snare */
        default: break;
    }
}

void sfx_play(int id) {
    if (sSfxTimer && id < sSfxCur)
        return;
    sSfxCur = id;
    sSfxTimer = 8;
    switch (id) {
        case SFX_SWORD: ch1(0x0039, 0xC180, 0x0600); break;
        case SFX_HURT: ch1(0x002E, 0xA1C0, 0x0400); ch4(0xA100, 0x0057); break;
        case SFX_ROLL: ch1(0x0017, 0x6280, 0x0300); break;
        case SFX_BUMP: ch4(0x7100, 0x0045); break;
        case SFX_FALL: ch1(0x003F, 0xD2C0, 0x0580); break;
        case SFX_ITEM: ch1(0x0000, 0xF080, 0x06C0); sSfxTimer = 20; break;
        case SFX_JUMP: ch1(0x0014, 0x7280, 0x0420); break;
        case SFX_HIT: ch4(0xC100, 0x0036); ch1(0x0039, 0x8180, 0x0500); break;
        case SFX_KILL: ch4(0xF200, 0x0067); sSfxTimer = 12; break;
        case SFX_PICKUP: ch1(0x0000, 0x8180, 0x0700); break;
        case SFX_HEART: ch1(0x0000, 0xA180, 0x0680); break;
        case SFX_KEY: ch1(0x0000, 0xB1C0, 0x0720); sSfxTimer = 14; break;
        case SFX_DOOR: ch4(0xA300, 0x0047); ch1(0x0040, 0x9280, 0x0200); break;
        case SFX_BOMB_SET: ch1(0x0000, 0x5080, 0x0580); break;
        case SFX_BOMB: ch4(0xF700, 0x0074); sSfxTimer = 30; break;
        case SFX_TEXT: ch1(0x0000, 0x3080, 0x0740); sSfxTimer = 2; break;
        case SFX_MENU: ch1(0x0000, 0x6080, 0x0700); break;
        case SFX_SPIT: ch4(0x6100, 0x0032); break;
        case SFX_LAMP: ch4(0x9300, 0x0024); ch1(0x0020, 0x7280, 0x0400); break;
        case SFX_SECRET: ch1(0x0000, 0xF1C0, 0x0740); sSfxTimer = 24; break;
        case SFX_CHEST: ch1(0x0000, 0xC180, 0x0640); sSfxTimer = 16; break;
        case SFX_BOSS_HIT: ch4(0xE200, 0x0056); ch1(0x0037, 0xB1C0, 0x0380); break;
        case SFX_WIN: ch1(0x0000, 0xF0C0, 0x0700); sSfxTimer = 40; break;
        default: break;
    }
}

static void track_start(Track* t, const u8* data) {
    t->pos = data;
    t->left = 0;
}

void bgm_play(int id) {
    if (id == sBgm)
        return;
    sBgm = id;
    const Song* s = &sSongs[id];
    track_start(&sMel, s->melody);
    track_start(&sBass, s->bass);
    sTickTimer = 0;
    sRow = 0;
    if (!s->melody) {
        ch2_note(R, 0, 0);
        ch3_note(R);
    }
}

void bgm_stop(void) {
    sBgm = BGM_NONE;
    ch2_note(R, 0, 0);
    ch3_note(R);
}

/* advance a track by one tick; returns a note to play or -1 */
static int track_tick(Track* t, const u8* loop) {
    if (!t->pos)
        return -1;
    if (t->left > 0) {
        t->left--;
        return -1;
    }
    if (t->pos[0] == END)
        t->pos = loop;
    int note = t->pos[0];
    t->left = t->pos[1] - 1;
    t->pos += 2;
    return note;
}

void sound_update(void) {
    if (sSfxTimer)
        sSfxTimer--;
    const Song* s = &sSongs[sBgm];
    if (!s->melody)
        return;
    if (++sTickTimer < s->tick)
        return;
    sTickTimer = 0;
    int n = track_tick(&sMel, s->melody);
    if (n >= 0)
        ch2_note(n, s->melody_env, s->melody_duty);
    n = track_tick(&sBass, s->bass);
    if (n >= 0)
        ch3_note(n);
    drum(s->drums[sRow]);
    sRow = (sRow + 1) % s->drum_rows;
}
