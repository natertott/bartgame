#include "trophy_data.h"
#include "assets.h"
#include "card_traders.h"
#include "handoff_events.h"
#include "run_extension.h"

/* Route and trader bits use the order already recorded by their systems. */
enum {
    FEAT_TRADE = TROPHY_VICTORY_COUNT,
    FEAT_GOLDEN = FEAT_TRADE + CARD_TRADE_SLOTS,
    FEAT_COUNT
};
#define CARD_MASK ((1u << CARD_COUNT) - 1u)
#define FEAT_MASK ((1u << FEAT_COUNT) - 1u)

_Static_assert(CARD_COUNT < 32 && FEAT_COUNT < 32, "Trophy profile mask capacity");

TrophyProgress gTrophyProgress EWRAM_BSS;

static u32 card_bit(int card) {
    return (unsigned)card < CARD_COUNT ? (1u << card) : 0u;
}

bool8 trophy_card_seen(int card) {
    return (gTrophyProgress.cards & card_bit(card)) != 0;
}

static bool8 record(u32 cards, u32 milestones) {
    if (!(cards & ~gTrophyProgress.cards) && !(milestones & ~gTrophyProgress.milestones))
        return FALSE;
    gTrophyProgress.cards |= cards;
    gTrophyProgress.milestones |= milestones;
    return TRUE;
}

void trophy_note_card(int card) {
    if (record(card_bit(card), 0))
        run_profile_write();
}

void trophy_note_trade(int trader, int card) {
    if ((unsigned)trader < CARD_TRADE_SLOTS && record(card_bit(card), 1u << (FEAT_TRADE + trader)))
        run_profile_write();
}

void trophy_note_golden_victory(int trader) {
    if (trader == CARD_TRADER_RED && record(0, 1u << FEAT_GOLDEN))
        run_profile_write();
}

void trophy_note_victory(enum TrophyVictory victory) {
    if ((unsigned)victory < TROPHY_VICTORY_COUNT)
        gTrophyProgress.milestones |= 1u << victory;
}

bool8 trophy_progress_valid(const TrophyProgress* progress) {
    return !(progress->cards & ~CARD_MASK) && !(progress->milestones & ~FEAT_MASK);
}

bool8 trophy_recover_cards(const TradingCardProgress* saved) {
    u32 cards = 0, milestones = (u32)saved->completed << FEAT_TRADE;
    for (int card = 0; card < CARD_COUNT; card++)
        if (saved->counts[card])
            cards |= 1u << card;
    /* Successful swaps prove ownership of their requested card, even when
       the last copy was spent before this checkpoint. */
    for (int trader = 0; trader < CARD_TRADE_SLOTS; trader++)
        if (saved->completed & (1u << trader))
            cards |= card_bit(card_traders_request(trader));
    if (saved->golden_defeated & (1u << CARD_TRADER_RED))
        milestones |= 1u << FEAT_GOLDEN;
    return record(cards, milestones);
}

enum { EARNED_FEAT, EARNED_ALBUM, EARNED_ENTITLEMENT, EARNED_RANK };

typedef struct {
    const char* name;
    const char* description;
    u8 sheet, frame, palette, source, value;
} MilestoneRule;

static const MilestoneRule sMilestones[] = {
    {"First Victory", "Finish any route. Your first win earns Fairy Well trials in entitlement mode.",
     SHEET_HANDOFF_ITEMS, F_HANDOFF_ITEMS_FAIRY, PAL_OBJ_GEAR, EARNED_ENTITLEMENT, HENT_FAIRY},
    {"The Grail", "Cut down the Blight Heart and claim the Grail in the Blighted Wood.",
     SHEET_PICK32, F_PICK32_GRAIL, PAL_OBJ_GEAR, EARNED_FEAT, TROPHY_VICTORY_GRAIL},
    {"Summit Guardian", "Reach the summit of The Curdled Cream and defeat the Peak Curd Wyrm.",
     SHEET_HANDOFF_ITEMS, F_HANDOFF_ITEMS_GRIP_RING, PAL_OBJ_GEAR, EARNED_FEAT, TROPHY_VICTORY_SUMMIT},
    {"Four-Seal Champion", "Complete the regional Four Seals contract and claim the Earth Element.",
     SHEET_HANDOFF_ITEMS, F_HANDOFF_ITEMS_EARTH_ELEMENT, PAL_OBJ_GEAR, EARNED_FEAT, TROPHY_VICTORY_SEALS},
    {"Peddler's Exchange", "Bring the Blightseeds card to the Billious Peddler in the Drain.",
     SHEET_HANDOFF_ITEMS, F_HANDOFF_ITEMS_BOOMERANG, PAL_OBJ_GEAR, EARNED_FEAT, FEAT_TRADE + CARD_TRADER_PEDDLER},
    {"Moss Archivist", "Trade the Quill Moth card to the Moss Archivist to open the nearby cache.",
     SHEET_INTERACTIVECHEST, F_INTERACTIVECHEST_WOODEN_OPEN, PAL_OBJ_GEAR, EARNED_FEAT, FEAT_TRADE + CARD_TRADER_GREEN},
    {"Brook Locksmith", "Trade the Blighted Tree card to the Brook Locksmith to open the hidden pocket.",
     SHEET_ICON32, F_ICON32_KEY, PAL_OBJ_GEAR, EARNED_FEAT, FEAT_TRADE + CARD_TRADER_BLUE},
    {"Rind Collector", "Trade the Blight Heart card to the Rind Collector to draw out the Golden Rope.",
     SHEET_HANDOFF_ITEMS, F_HANDOFF_ITEMS_RUPEE200, PAL_OBJ_GEAR, EARNED_FEAT, FEAT_TRADE + CARD_TRADER_RED},
    {"Golden Rope", "Defeat the Golden Rope summoned by the Rind Collector's trade.",
     SHEET_LEGACY_ROPE_GOLDEN_0, F_LEGACY_ROPE_GOLDEN_0_IDLE_S, PAL_OBJ_FX, EARNED_FEAT, FEAT_GOLDEN},
    {"Complete Card Album", "Collect every Trading Card. Cards you've traded still count.",
     SHEET_HANDOFF_ITEMS, F_HANDOFF_ITEMS_QST_CARLOV_MEDAL, PAL_OBJ_GEAR, EARNED_ALBUM, 0},
    {"Cream Access", "Earn 500 points or win once to qualify for Cream access, tier 2 rewards and more quests in entitlement mode.",
     SHEET_ICON32, F_ICON32_MAP, PAL_OBJ_GEAR, EARNED_ENTITLEMENT, HENT_FIELD},
    {"Hidden Pot Trials", "Earn 500 points to qualify for hidden pot trials and pot quests in entitlement mode.",
     SHEET_ICON32, F_ICON32_RELIC, PAL_OBJ_GEAR, EARNED_ENTITLEMENT, HENT_POTS},
    {"Advanced Trials", "Earn 1,500 points or win twice to qualify for portals, secret pockets, boss trials and tier 3 rewards in entitlement mode.",
     SHEET_ICON32, F_ICON32_ASTROLABE, PAL_OBJ_GEAR, EARNED_ENTITLEMENT, HENT_ADVANCED},
    {"Rank IV", "Earn 2,000 points across your runs to reach the highest rank.",
     SHEET_HANDOFF_ITEMS, F_HANDOFF_ITEMS_FOURSWORD, PAL_OBJ_GEAR, EARNED_RANK, 4},
};

int trophy_milestone_count(void) {
    return ARRAY_COUNT(sMilestones);
}

bool8 trophy_milestone_entry(int index, TrophyMilestone* out) {
    if (!out || (unsigned)index >= ARRAY_COUNT(sMilestones))
        return FALSE;
    const MilestoneRule* rule = &sMilestones[index];
    *out = (TrophyMilestone){rule->name, rule->description, rule->sheet, rule->frame, rule->palette, FALSE};
    switch (rule->source) {
    case EARNED_FEAT:
        out->earned = (gTrophyProgress.milestones & (1u << rule->value)) != 0;
        break;
    case EARNED_ALBUM:
        out->earned = gTrophyProgress.cards == CARD_MASK;
        break;
    case EARNED_ENTITLEMENT:
        out->earned = handoff_entitlement_earned(rule->value);
        break;
    case EARNED_RANK:
        out->earned = gHandoffState.rank >= rule->value;
        break;
    }
    return TRUE;
}
