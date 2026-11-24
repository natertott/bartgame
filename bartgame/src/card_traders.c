#include "card_traders.h"
#include "actor.h"
#include "card_ui.h"
#include "cream_runtime.h"
#include "game.h"
#include "handoff_events.h"
#include "legacy_items.h"
#include "player.h"
#include "room.h"
#include "sound.h"
#include "text.h"
#include "trophy_data.h"
#include "trading_cards.h"
#include "util.h"
#include "video.h"

enum { BUBBLE_REACH = 52, TRADE_REACH = 30, BUBBLE_TICKS = 12 };

typedef struct {
    const char* name;
    const char* wait;
    const char* done;
    u8 request;
    u8 reward;
} CardTrader;

static const CardTrader sTraders[CARD_TRADER_COUNT] = {
    {"Billious Peddler", NULL, "Blightseeds, printed on dry paper. Finally, a safe way to stock them. Take this boomerang.",
     CARD_BLIGHTSEEDS, LI_BOOMERANG},
    {"Moss Archivist", "Clear four monsters from the paths. Then I'll have a quiet minute to trade.",
     "A perfect Quill Moth. Here's 100 gilt. I'll open the little cache nearby, too.", CARD_SPORE_BAT, LI_RUPEE100},
    {"Brook Locksmith", "My card album stays shut on a first visit. Come back through when the brook is quiet.",
     "The tree in this print marks an old pocket. I've unlatched the door just over there.", CARD_BLIGHTED_TREE, LI_NONE},
    {"Rind Collector", "Tell me you've felled fifteen monsters. I have a trade for a seasoned climber.",
     "The Heart completes my album. Hear that skitter? Something golden is loose on this shelf.",
     CARD_BLIGHT_HEART, LI_NONE},
};

static struct {
    s16 x, y, head_y;
    u16 tile;
    u8 active, trader, terrace, frame, bubble, offering;
    u8 area, cell;
} sTrader EWRAM_BSS;

static bool8 valid(int trader) {
    return (unsigned)trader < CARD_TRADER_COUNT;
}

const char* card_traders_name(int trader) {
    return valid(trader) ? sTraders[trader].name : "Collector";
}

int card_traders_request(int trader) {
    return valid(trader) ? sTraders[trader].request : -1;
}

bool8 card_traders_completed(int trader) {
    return valid(trader) && (gTradingCardProgress.completed & (1u << trader));
}

static bool8 ready(int trader) {
    if (card_traders_completed(trader)) return FALSE;
    switch (trader) {
        case CARD_TRADER_PEDDLER: return TRUE;
        case CARD_TRADER_GREEN: return gGame.kills >= 4;
        case CARD_TRADER_BLUE:
            return gTradingCardProgress.visits[trader] >= 3 ||
                   (gTradingCardProgress.visits[trader] == 2 && gGame.run_frames % 480 < 360);
        case CARD_TRADER_RED: return gGame.kills >= 15;
        default: return FALSE;
    }
}

static bool8 near_trader(int reach) {
    if (!sTrader.active || !gPlayer || gPlayer->state == PS_DEAD || gPlayer->z ||
        sTrader.area != gGame.area || (sTrader.area != AREA_SEWER && sTrader.cell != gGame.cell)) return FALSE;
    if (gGame.area == AREA_CREAM && cream_terrace(gCreamNode) != sTrader.terrace) return FALSE;
    return ABS(PX(gPlayer->x) - sTrader.x) <= reach && ABS(PX(gPlayer->y) - sTrader.y) <= reach;
}

void card_traders_room_reset(void) {
    memset(&sTrader, 0, sizeof(sTrader));
}

void card_traders_place(int trader, int x, int y, int head_y, int terrace) {
    if (!valid(trader)) return;
    sTrader.active = TRUE;
    sTrader.trader = trader;
    sTrader.x = x;
    sTrader.y = y;
    sTrader.head_y = head_y;
    sTrader.terrace = terrace;
    sTrader.area = gGame.area;
    sTrader.cell = gGame.cell;
    sTrader.frame = 255;
    if (gTradingCardProgress.visits[trader] < 255) gTradingCardProgress.visits[trader]++;
}

void card_traders_explain(int trader) {
    if (!valid(trader)) return;
    if (card_traders_completed(trader)) textbox_open("That card already has a place in my album.");
    else if (ready(trader)) textbox_open("I have a card in mind. Stand nearby and press Select to see it.");
    else if (trader == CARD_TRADER_BLUE && gTradingCardProgress.visits[trader] == 2)
        textbox_open("I'm minding the sluice for a moment. Give me a little time, or come back through.");
    else textbox_open(sTraders[trader].wait);
}

bool8 card_traders_try_open(void) {
    int trader = sTrader.trader;
    if (!(gKeysDown & KEY_SELECT) || !near_trader(TRADE_REACH) || gPlayer->state != PS_NORMAL ||
        !ready(trader) || legacy_player_status(LPS_CAPTURE) || legacy_player_status(LPS_FREEZE) ||
        legacy_player_status(LPS_SHOCK)) return FALSE;
    sTrader.offering = TRUE;
    card_ui_open_trade(trader, sTraders[trader].request, trader + 1, sTraders[trader].name);
    return TRUE;
}

bool8 card_traders_accept(int trader, int card) {
    if (!sTrader.offering || !near_trader(TRADE_REACH) || trader != sTrader.trader ||
        card_traders_completed(trader) || card != card_traders_request(trader) || !trading_card_spend(card)) return FALSE;
    sTrader.offering = FALSE;
    gTradingCardProgress.completed |= 1u << trader;
    /* Reuse the saved gates that already belong to these three sites. */
    if (trader != CARD_TRADER_PEDDLER) gHandoffState.fusion_flags |= 1u << (trader - 1);
    int reward = sTraders[trader].reward;
    const char* response = sTraders[trader].done;
    if (trader == CARD_TRADER_PEDDLER && legacy_item_owned(reward)) {
        reward = LI_RUPEE100;
        response = "A fine print. You've already got my boomerang, so here's 100 gilt.";
    }
    if (reward != LI_NONE) legacy_item_grant(reward, 1);
    trophy_note_trade(trader, card);
    sfx_play(SFX_SECRET);
    textbox_open(response);
    return TRUE;
}

void card_traders_draw(void) {
    if (!sTrader.active) return;
    if (near_trader(BUBBLE_REACH) && ready(sTrader.trader)) {
        if (sTrader.bubble < BUBBLE_TICKS) sTrader.bubble++;
    } else if (sTrader.bubble) sTrader.bubble--;
    if (!sTrader.bubble || textbox_active()) return;

    const SpriteSheet* sheet = &sheets[SHEET_CARD_BUBBLE];
    int x = sTrader.x - 16 - gCamX;
    int y = sTrader.head_y - 27 - gCamY;
    int step = (sTrader.bubble - 1) / 4;
    int frame = step == 0 ? F_CARD_BUBBLE_POP_1 : step == 1 ? F_CARD_BUBBLE_POP_2 :
                (gFrame & 16) ? F_CARD_BUBBLE_BOB : F_CARD_BUBBLE_OPEN;
    if (!sTrader.tile) sTrader.tile = sprite_alloc(sheet->frame_tiles);
    if (!sTrader.tile) return;
    if (sTrader.frame != frame) {
        sTrader.frame = frame;
        vram_queue(sheet->tiles + frame * sheet->frame_tiles * 16, OBJ_TILE(sTrader.tile), sheet->frame_tiles * 32);
    }
    if (step == 2) {
        u16 tile = trading_cards_world_tile();
        int rarity = gTradingCards[sTraders[sTrader.trader].request].rarity;
        if (tile) draw_sprite(x + 12, y + (frame == F_CARD_BUBBLE_BOB ? 8 : 9),
                             SHEET_TRADING_CARD, tile, F_TRADING_CARD_COMMON + rarity,
                             0, 0, trading_cards_world_palette());
    }
    draw_sprite(x, y, SHEET_CARD_BUBBLE, sTrader.tile, 0, 0, 0, PAL_OBJ_FX);
}
