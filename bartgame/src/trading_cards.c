#include "trading_cards.h"
#include "actor.h"
#include "game.h"
#include "handoff_events.h"
#include "objects.h"
#include "player.h"
#include "room.h"
#include "text.h"
#include "trophy_data.h"
#include "util.h"
#include "video.h"

const TradingCardDef gTradingCards[CARD_COUNT] = {
    [CARD_BLOOM] = {"Bloom", "A sprout with a sword and a habit of checking every suspicious door.", CARD_COMMON},
    [CARD_BILLIOUS_PEDDLER] = {"Billious Peddler", "The Drain's frog merchant keeps one eye on his gilt and the other on his customers.", CARD_COMMON},
    [CARD_BLIGHTSEEDS] = {"Blightseeds", "A warm seed with a fuse. It opens cracked stone after a short wait.", CARD_COMMON},
    [CARD_HEALTHY_TREE] = {"Healthy Tree", "A green canopy shelters what still grows in the wood.", CARD_COMMON},
    [CARD_PALE_GATEKEEPER] = {"Pale Gatekeeper", "She guards the Drain by the soft light of a wisp in her palm.", CARD_UNCOMMON},
    [CARD_GRAIL_LAMP] = {"Grail Lamp", "Its flame lights cold censers and burns through the silk that seals a path.", CARD_UNCOMMON},
    [CARD_THORN_BOW] = {"Thorn Bow", "A bent thorn branch sends an arrow farther than Bloom can reach with a sword.", CARD_UNCOMMON},
    [CARD_SPORE_BAT] = {"Quill Moth", "Watch for its wings to fold before it swoops out of the gloom.", CARD_UNCOMMON},
    [CARD_BLIGHTED_TREE] = {"Blighted Tree", "Colour drains from the crown as the blight takes hold of the roots.", CARD_RARE},
    [CARD_PETAL_CLOAK] = {"Petal Cloak", "Its petals catch enough air to carry Bloom over a broken shelf.", CARD_RARE},
    [CARD_THORN_KNIGHT] = {"Moth Confessor", "A heavy blade and patient footwork make this guard difficult to pass.", CARD_RARE},
    [CARD_PACCI_CANE] = {"Pacci Cane", "One twist turns a stubborn shell and exposes whatever hides beneath it.", CARD_RARE},
    [CARD_BLIGHT_HEART] = {"Blight Heart", "Deep in the wood, the Heart beats through the roots and keeps the blight alive.", CARD_ULTRA_RARE},
    [CARD_GLEEROK] = {"Summit Guardian", "A plated guardian watches the highest ledge of The Curdled Cream.", CARD_ULTRA_RARE},
    [CARD_GRIP_BRACELET] = {"Grip Bracelet", "A trusted hold on the marked rock faces of The Curdled Cream.", CARD_ULTRA_RARE},
    [CARD_GOLDEN_ROPE] = {"Golden Rope", "A flash of gold on the cliffs. The gleam moves faster than you expect.", CARD_ULTRA_RARE},
};
_Static_assert(sizeof(trading_card_art) / sizeof(trading_card_art[0]) == CARD_COUNT,
               "Trading card art must cover the catalogue");

TradingCardProgress gTradingCardProgress EWRAM_BSS;
static u16 sCardTile;
static u8 sNoticeCard, sNoticeTicks;

void trading_cards_new_run(void) {
    memset(&gTradingCardProgress, 0, sizeof(gTradingCardProgress));
    sNoticeTicks = 0;
}

/* Old saves kept three shape counts per colour. Preserve each stack in a
   related rarity while leaving already opened fusion gates intact. */
void trading_cards_import_halves(const u8 shapes[3][3]) {
    for (int rarity = CARD_COMMON; rarity <= CARD_RARE; rarity++)
        for (int shape = 0; shape < 3; shape++)
            gTradingCardProgress.counts[rarity * 4 + shape] = MIN(shapes[rarity][shape], CARD_STACK_MAX);
}

int trading_card_count(int id) {
    return (unsigned)id < CARD_COUNT ? gTradingCardProgress.counts[id] : 0;
}

bool8 trading_card_grant(int id) {
    if ((unsigned)id >= CARD_COUNT || trading_card_count(id) >= CARD_STACK_MAX)
        return FALSE;
    gTradingCardProgress.counts[id]++;
    trophy_note_card(id);
    sNoticeCard = id;
    sNoticeTicks = 54;
    return TRUE;
}

bool8 trading_card_spend(int id) {
    if (!trading_card_count(id))
        return FALSE;
    gTradingCardProgress.counts[id]--;
    return TRUE;
}

/* Thresholds are cumulative percentages. Decide rarity before sampling the
   four identities in that rarity, with a separate part of the mixed roll. */
static int card_roll(u32 roll, bool8 reward) {
    int roll_rarity = ((roll >> 8) & 0xffff) % 100;
    int rarity;
    if (roll_rarity < (reward ? 42 : 56))
        rarity = CARD_COMMON;
    else if (roll_rarity < (reward ? 72 : 81))
        rarity = CARD_UNCOMMON;
    else if (roll_rarity < (reward ? 90 : 94))
        rarity = CARD_RARE;
    else
        rarity = CARD_ULTRA_RARE;
    return rarity * 4 + (roll & 3);
}

void trading_card_enemy_drop(int px, int py, u32 roll) {
    u32 mixed = hash32(roll, 0x43415244u);
    if (((mixed >> 24) * 100 >> 8) >= (handoff_drop_bias(1) ? 45u : 30u))
        return;
    int id = card_roll(mixed, FALSE);
    if (trading_card_count(id) >= CARD_STACK_MAX)
        return;

    /* Keep a card from landing inside scenery or underneath a heart/gilt
       drop. A struck flyer can be over a pit or inside an opaque wall. */
    static const s8 dx[] = {10, -10, 0, 0, 0};
    static const s8 dy[] = {0, 0, 10, -10, 0};
    for (unsigned i = 0; i < sizeof(dx); i++) {
        int x = px + dx[i], y = py + dy[i];
        int kind = room_type_px(x, y - 4);
        if (kind != TT_PIT && kind != TT_WATER && !room_box_solid(x - 3, y - 7, x + 3, y - 1)) {
            pickup_spawn_trading_card(id, x, y);
            return;
        }
    }
    pickup_spawn_trading_card(id, gPl.safe_x, gPl.safe_y);
}

void trading_card_reward(int source, int area, int cell) {
    /* Completing a one-shot source gives the bonus directly. It is saved
       with the opened chest or completed quest even if the player leaves. */
    u32 context = 0x43415244u + source * 2048 + area * 256 + cell;
    u32 roll = hash32(gGame.seed ^ gGame.run_frames, context);
    trading_card_grant(card_roll(roll, TRUE));
}

void trading_cards_room_reset(void) {
    sCardTile = 0;
}

u16 trading_cards_world_tile(void) {
    if (textbox_active())
        return 0;
    if (!sCardTile)
        sCardTile = sprite_load_sheet(SHEET_TRADING_CARD);
    return sCardTile;
}

int trading_cards_world_palette(void) {
    /* The portrait bank is available only while the world has no textbox.
       All four card colours coexist in this bank. */
    if (!textbox_active()) {
        const u16* current = &gPalObj[PAL_OBJ_PORTRAIT * 16];
        for (int i = 0; i < 16; i++) {
            if (current[i] != trading_card_ground_palette[i]) {
                pal_set_obj(PAL_OBJ_PORTRAIT, trading_card_ground_palette);
                break;
            }
        }
    }
    return PAL_OBJ_PORTRAIT;
}

void trading_cards_draw_notice(void) {
    if (!sNoticeTicks || !gPlayer)
        return;
    u16 tile = trading_cards_world_tile();
    if (!tile)
        return;
    int age = 54 - sNoticeTicks--;
    if (age >= 46 && (gFrame & 2))
        return;
    int x = PX(gPlayer->x) + 10 - gCamX;
    int y = PX(gPlayer->y) - 27 - age / 6 - PX(gPlayer->z) - gCamY;
    draw_sprite(x, y, SHEET_TRADING_CARD, tile, F_TRADING_CARD_COMMON + gTradingCards[sNoticeCard].rarity,
                0, 1, trading_cards_world_palette());
}
