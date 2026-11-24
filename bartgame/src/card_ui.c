#include "card_ui.h"
#include "trading_cards.h"
#include "card_traders.h"
#include "actor.h"
#include "bomb_throw.h"
#include "game.h"
#include "menu.h"
#include "room.h"
#include "sound.h"
#include "text.h"
#include "ui.h"
#include "video.h"

/* The room's BG maps can be rebuilt after borrowing charblock 3. The card
   artwork sits on BG1, above the chosen menu material and below BG0 text. */
enum { ART_MAP = 30, ART_BLANK = UI_BG3 + UI_TILE_COUNT, ART_PAL = 8, ART_BANKS = 4 };
enum { NO_CARD = 255, LIST_ROWS = 5 };
_Static_assert(ART_BLANK + 1 + 2 * (6 * 8 + 3 * 3) <= (ART_MAP - 24) * 64,
               "Trade art must fit before its screenblock");
_Static_assert(ARRAY_COUNT(trading_card_art) == CARD_COUNT && ARRAY_COUNT(trading_card_thumbs) == CARD_COUNT,
               "Each card needs an illustration and thumbnail");

u8 gCardUiMode EWRAM_BSS;
u8 gCardUiSelected EWRAM_BSS;
u8 gCardUiRequest EWRAM_BSS;
u8 gCardUiRefusals EWRAM_BSS;
static u16 sArtMap[32 * 32] EWRAM_BSS ALIGN4;
static u16 sWorldPal[ART_BANKS * 16] EWRAM_BSS ALIGN4;
static u16 sWorldBg1, sWorldBg3, sWorldBlend, sWorldBrightness, sWorldWindows;
static s16 sWorldScroll[2][2];
static u16 sNextTile;
static u8 sCards[CARD_COUNT] EWRAM_BSS;
static u8 sOwned, sCursor;
static u8 sTrader, sPortrait;
static bool8 sRefused;
static const char* sTraderName;
static void (*sPreviousHook)(void);
static volatile u16 sInputHeld, sInputQueue[8];
static volatile u8 sInputRead, sInputWrite;
static const char* const sRarity[] = { "Common", "Uncommon", "Rare", "Ultra-rare" };

static void card_input(void) {
    u16 held = (~REG_KEYINPUT) & KEY_ANY;
    u16 down = held & ~sInputHeld;
    u8 next = (sInputWrite + 1) & 7;
    sInputHeld = held;
    if (down && next != sInputRead) {
        sInputQueue[sInputWrite] = down;
        sInputWrite = next;
    }
    if (sPreviousHook) sPreviousHook();
}

static void place_art(int x, int y, int w, int h, int bank,
                      const u16* tiles, const u16* palette) {
    pal_set_bg(ART_PAL + bank, palette);
    vram_queue(tiles, CHARBLOCK(3) + sNextTile * 16, w * h * 32);
    for (int row = 0; row < h; row++) {
        for (int col = 0; col < w; col++) {
            sArtMap[(y + row) * 32 + x + col] = sNextTile | ((ART_PAL + bank) << 12);
            sNextTile++;
        }
    }
}

static void thumbnail(int card, int x, int y, int bank) {
    place_art(x, y, 3, 3, bank, trading_card_thumbs[card], trading_card_palettes[card]);
}

static void center(Canvas* canvas, int y, const char* label, int ink) {
    vwf_text(canvas, MAX(0, (canvas->tw * 8 - vwf_width(label)) / 2), y, label, ink);
}

static void header(const char* title) {
    Canvas head;
    ui_frame(gBg3, UI_BG3, 1, 1, 28, 2, FR_ROW);
    bg0_canvas(&head, 2, 1, 26, 2);
    center(&head, 3, title, UI_INK_GOLD);
    vwf_flush(&head, FALSE);
}

static void footer(const char* controls, const char* response) {
    Canvas foot;
    ui_frame(gBg3, UI_BG3, 1, 16, 28, 3, FR_ROW);
    bg0_canvas(&foot, 2, 16, 26, 3);
    if (response) {
        vwf_block(&foot, 0, 2, 208, 9, response, UI_INK_GOLD, 2);
    } else {
        center(&foot, 7, controls, UI_INK_CREAM);
    }
    vwf_flush(&foot, FALSE);
}

static void show_portrait(int x, int portrait, int bank, const char* name) {
    Canvas plate;
    ui_frame(gBg3, UI_BG3, x, 4, 8, 11, FR_PANEL);
    place_art(x + 1, 5, 6, 8, bank, trading_portrait_art[portrait], trading_portrait_palettes[portrait]);
    bg0_canvas(&plate, x + 1, 13, 6, 2);
    if (vwf_width(name) <= 48) center(&plate, 1, name, UI_INK_CREAM);
    else vwf_block(&plate, 0, 0, 48, 8, name, UI_INK_CREAM, 2);
    vwf_flush(&plate, FALSE);
}

static void trade(void) {
    static const char* const refusal[] = {
        "Fine print, wrong frog. Have another look.",
        "I'd trade for lunch, but this card isn't even edible.",
        "Tempting. My collection has a different hole in it.",
        "The card is lovely. The answer is still no."
    };
    Canvas choices;
    int offer = gCardUiSelected;
    int wanted = gCardUiRequest;
    char number[6];

    header("TRADING CARDS");
    show_portrait(1, 0, 0, "Bloom");
    show_portrait(21, sPortrait, 1, sTraderName);
    ui_frame(gBg3, UI_BG3, 9, 3, 12, 6, FR_SLOT);
    ui_frame(gBg3, UI_BG3, 9, 9, 12, 6, sOwned ? FR_SEL : FR_SLOT);
    bg0_canvas(&choices, 9, 3, 12, 12);
    vwf_text(&choices, 8, 5, "Wants", UI_INK_GOLD);
    thumbnail(wanted, 10, 5, 2);
    vwf_block(&choices, 36, 16, 55, 9, gTradingCards[wanted].name, UI_INK_HIGH, 2);
    vwf_text(&choices, 36, 34, sRarity[gTradingCards[wanted].rarity], UI_INK_DIM);
    vwf_text(&choices, 8, 53, "Your offer", UI_INK_GOLD);
    if (sOwned) {
        int next = vwf_text(&choices, 63, 53, vwf_num(number, sCursor + 1, 0), UI_INK_CREAM);
        next = vwf_text(&choices, next, 53, "/", UI_INK_DIM);
        vwf_text(&choices, next, 53, vwf_num(number, sOwned, 0), UI_INK_CREAM);
        thumbnail(offer, 10, 11, 3);
        vwf_block(&choices, 36, 64, 55, 9, gTradingCards[offer].name, UI_INK_HIGH, 2);
        next = vwf_text(&choices, 36, 82, "Owned ", UI_INK_DIM);
        vwf_text(&choices, next, 82, vwf_num(number, trading_card_count(offer), 0), UI_INK_CREAM);
    } else {
        vwf_block(&choices, 8, 68, 80, 9, "No cards to offer yet.", UI_INK_DIM, 2);
    }
    vwf_flush(&choices, FALSE);
    footer(sOwned ? "Up/Down browse    A offer    B back" : "B back",
           sRefused ? refusal[sTrader % ARRAY_COUNT(refusal)] : NULL);
}

static void collection(void) {
    Canvas list, preview;
    int first = sCursor / LIST_ROWS * LIST_ROWS;
    int card = gCardUiSelected;
    char number[6];

    header("CARD COLLECTION");
    ui_frame(gBg3, UI_BG3, 1, 3, 14, 13, FR_PANEL);
    ui_frame(gBg3, UI_BG3, 15, 3, 14, 13, FR_PANEL);
    if (sOwned) ui_frame(gBg3, UI_BG3, 2, 5 + (sCursor - first) * 2, 12, 2, FR_SROW);
    bg0_canvas(&list, 2, 4, 12, 12);
    vwf_text(&list, 4, 0, "Card", UI_INK_GOLD);
    vwf_text(&list, 76, 0, "Qty", UI_INK_GOLD);
    if (sOwned > LIST_ROWS) {
        int next = vwf_text(&list, 49, 0, vwf_num(number, first / LIST_ROWS + 1, 0), UI_INK_DIM);
        next = vwf_text(&list, next, 0, "/", UI_INK_DIM);
        vwf_text(&list, next, 0, vwf_num(number, (sOwned + LIST_ROWS - 1) / LIST_ROWS, 0), UI_INK_DIM);
    }
    for (int row = 0; row < LIST_ROWS && first + row < sOwned; row++) {
        int id = sCards[first + row];
        int ink = id == card ? UI_INK_HIGH : UI_INK_CREAM;
        int y = 12 + row * 16;
        vwf_text(&list, 5, y, gTradingCards[id].name, ink);
        const char* qty = vwf_num(number, trading_card_count(id), 0);
        vwf_text(&list, 90 - vwf_width(qty), y, qty, ink);
    }
    vwf_flush(&list, FALSE);

    bg0_canvas(&preview, 16, 11, 12, 4);
    if (sOwned) {
        ui_frame(gBg3, UI_BG3, 19, 5, 5, 5, FR_SLOT);
        thumbnail(card, 20, 6, 0);
        center(&preview, 3, gTradingCards[card].name, UI_INK_HIGH);
        center(&preview, 16, sRarity[gTradingCards[card].rarity], UI_INK_GOLD);
    } else {
        vwf_block(&preview, 3, 0, 88, 12, "No cards in the collection yet.", UI_INK_CREAM, 3);
    }
    vwf_flush(&preview, FALSE);
    footer(sOwned ? "D-pad browse    A inspect    B pause" : "B pause    Start close", NULL);
}

static void inspect(void) {
    Canvas name, detail;
    int card = gCardUiSelected;
    char number[6];

    header("CARD COLLECTION");
    ui_frame(gBg3, UI_BG3, 2, 3, 11, 13, FR_SEL);
    ui_frame(gBg3, UI_BG3, 3, 5, 9, 8, FR_SLOT);
    place_art(4, 6, 6, 6, 0, trading_card_art[card], trading_card_palettes[card]);
    bg0_canvas(&name, 3, 13, 9, 2);
    center(&name, 4, sRarity[gTradingCards[card].rarity], UI_INK_GOLD);
    vwf_flush(&name, FALSE);

    ui_frame(gBg3, UI_BG3, 14, 3, 15, 13, FR_PANEL);
    bg0_canvas(&detail, 15, 4, 13, 11);
    vwf_block(&detail, 1, 1, 100, 10, gTradingCards[card].name, UI_INK_GOLD, 2);
    vwf_block(&detail, 1, 24, 100, 11, gTradingCards[card].description, UI_INK_CREAM, 5);
    int next = vwf_text(&detail, 1, 77, "Copies owned ", UI_INK_DIM);
    vwf_text(&detail, next, 77, vwf_num(number, trading_card_count(card), 0), UI_INK_HIGH);
    vwf_flush(&detail, FALSE);
    footer("Left/Right browse    B collection", NULL);
}

static void redraw(void) {
    vram_flush_queue();
    bg0_clear();
    bg0_pool_reset_full();
    ui_backdrop_clear();
    ui_frame(gBg3, UI_BG3, 0, 0, 30, 20, FR_PANEL);
    memset32(sArtMap, ART_BLANK * 0x00010001u, sizeof(sArtMap));
    sNextTile = ART_BLANK + 1;
    gCardUiSelected = sOwned ? sCards[sCursor] : NO_CARD;
    if (gCardUiMode == CARD_UI_TRADE) trade();
    else if (gCardUiMode == CARD_UI_INSPECT) inspect();
    else collection();
    vram_queue(sArtMap, SCREENBLOCK(ART_MAP), sizeof(sArtMap));
}

static void open(int mode) {
    bomb_charge_cancel();
    sOwned = 0;
    for (int card = 0; card < CARD_COUNT; card++) {
        if (trading_card_count(card)) sCards[sOwned++] = card;
    }
    sCursor = 0;
    sRefused = FALSE;
    gCardUiRefusals = 0;
    sPreviousHook = gVBlankHook;
    sInputRead = sInputWrite = 0;
    sInputHeld = (~REG_KEYINPUT) & KEY_ANY;
    gVBlankHook = card_input;
    sWorldBg1 = REG_BG1CNT;
    sWorldBg3 = REG_BG3CNT;
    sWorldBlend = REG_BLDCNT;
    sWorldBrightness = REG_BLDY;
    sWorldWindows = REG_DISPCNT & (DCNT_WIN0 | DCNT_WIN1 | DCNT_OBJWIN);
    memcpy32(sWorldPal, &gPalBg[ART_PAL * 16], sizeof(sWorldPal));
    for (int axis = 0; axis < 2; axis++) {
        sWorldScroll[0][axis] = gBgScroll[1][axis];
        sWorldScroll[1][axis] = gBgScroll[3][axis];
        gBgScroll[1][axis] = gBgScroll[3][axis] = 0;
    }
    REG_BG1CNT = BGCNT_PRIO(1) | BGCNT_CHARBASE(3) | BGCNT_SCREENBASE(ART_MAP) | BGCNT_SIZE_32x32;
    REG_BG3CNT = BGCNT_PRIO(3) | BGCNT_CHARBASE(3) | BGCNT_SCREENBASE(22) | BGCNT_SIZE_32x32;
    REG_BLDCNT = REG_BLDY = 0;
    REG_DISPCNT = DCNT_BLANK;
    ui_backdrop_open();
    dma3_fill32(0, CHARBLOCK(3) + ART_BLANK * 16, 32);
    gGame.state = GS_MAP;
    gCardUiMode = mode;
    gKeysDown = 0;
    redraw();
    vram_flush_queue();
    text_flush();
    video_flush();
    video_show(DCNT_BG0 | DCNT_BG1 | DCNT_BG3);
    sfx_play(SFX_MENU);
}

void card_ui_open_collection(void) {
    gCardUiRequest = NO_CARD;
    open(CARD_UI_COLLECTION);
}

void card_ui_open_trade(int trader, int request_card, int portrait, const char* name) {
    if ((unsigned)request_card >= CARD_COUNT || (unsigned)portrait >= ARRAY_COUNT(trading_portrait_art)) return;
    sTrader = trader;
    sPortrait = portrait;
    sTraderName = name;
    gCardUiRequest = request_card;
    open(CARD_UI_TRADE);
}

static void close(void) {
    vram_flush_queue();
    REG_DISPCNT = DCNT_BLANK;
    gVBlankHook = sPreviousHook;
    gCardUiMode = CARD_UI_NONE;
    gKeysDown = 0;
    for (int bank = 0; bank < ART_BANKS; bank++) pal_set_bg(ART_PAL + bank, &sWorldPal[bank * 16]);
    REG_BG1CNT = sWorldBg1;
    REG_BG3CNT = sWorldBg3;
    for (int axis = 0; axis < 2; axis++) {
        gBgScroll[1][axis] = sWorldScroll[0][axis];
        gBgScroll[3][axis] = sWorldScroll[1][axis];
    }
    bg0_clear();
    gBg3Dirty = 0;
    room_render();
    text_flush();
    video_flush();
    video_show(DCNT_BG0 | DCNT_BG1 | DCNT_BG2 | DCNT_OBJ | sWorldWindows);
    REG_BLDCNT = sWorldBlend;
    REG_BLDY = sWorldBrightness;
    gGame.state = GS_PLAY;
}

void card_ui_update(void) {
    u16 down;
    int cursor;
    if (sInputRead == sInputWrite) return;
    down = sInputQueue[sInputRead];
    sInputRead = (sInputRead + 1) & 7;
    if (down & KEY_START) {
        close();
        return;
    }
    if (down & KEY_B) {
        if (gCardUiMode == CARD_UI_INSPECT) {
            gCardUiMode = CARD_UI_COLLECTION;
            redraw();
        } else {
            int mode = gCardUiMode;
            close();
            if (mode == CARD_UI_COLLECTION) menu_open_keys();
        }
        return;
    }

    cursor = sCursor;
    if (sOwned && (down & (KEY_UP | KEY_LEFT)) && cursor > 0) cursor--;
    if (sOwned && (down & (KEY_DOWN | KEY_RIGHT)) && cursor + 1 < sOwned) cursor++;
    if (cursor != sCursor) {
        sCursor = cursor;
        sRefused = FALSE;
        sfx_play(SFX_MENU);
        redraw();
        return;
    }
    if (!(down & KEY_A) || !sOwned) return;
    if (gCardUiMode == CARD_UI_COLLECTION) {
        gCardUiMode = CARD_UI_INSPECT;
        sfx_play(SFX_MENU);
    } else if (gCardUiMode == CARD_UI_TRADE) {
        int offer = gCardUiSelected;
        if (offer == gCardUiRequest) {
            close();
            if (!card_traders_accept(sTrader, offer)) textbox_open("The trader has put their cards away.");
            return;
        }
        sRefused = !sRefused;
        if (sRefused) {
            gCardUiRefusals++;
            sfx_play(SFX_BUMP);
        }
    }
    redraw();
}
