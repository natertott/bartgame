#ifndef TRADING_CARDS_H
#define TRADING_CARDS_H

#include "gba.h"

enum CardRarity { CARD_COMMON, CARD_UNCOMMON, CARD_RARE, CARD_ULTRA_RARE, CARD_RARITY_COUNT };

/* Order is shared with the published artwork and the saved inventory. */
enum TradingCardId {
    CARD_BLOOM, CARD_BILLIOUS_PEDDLER, CARD_BLIGHTSEEDS, CARD_HEALTHY_TREE,
    CARD_PALE_GATEKEEPER, CARD_GRAIL_LAMP, CARD_THORN_BOW, CARD_SPORE_BAT,
    CARD_BLIGHTED_TREE, CARD_PETAL_CLOAK, CARD_THORN_KNIGHT, CARD_PACCI_CANE,
    CARD_BLIGHT_HEART, CARD_GLEEROK, CARD_GRIP_BRACELET, CARD_GOLDEN_ROPE,
    CARD_COUNT
};

enum CardRewardSource { CARD_REWARD_CHEST, CARD_REWARD_QUEST, CARD_REWARD_EVENT };

#define CARD_STACK_MAX 99
#define CARD_TRADE_SLOTS 4

typedef struct {
    const char* name;
    const char* description;
    u8 rarity;
} TradingCardDef;

typedef struct {
    u8 counts[CARD_COUNT];
    u8 completed, golden_defeated;
    u8 visits[CARD_TRADE_SLOTS];
    u8 reserved[2];
} TradingCardProgress;

extern const TradingCardDef gTradingCards[CARD_COUNT];
extern TradingCardProgress gTradingCardProgress;

void trading_cards_new_run(void);
void trading_cards_import_halves(const u8 shapes[3][3]);
int trading_card_count(int id);
bool8 trading_card_grant(int id);
bool8 trading_card_spend(int id);
void trading_card_enemy_drop(int px, int py, u32 roll);
void trading_card_reward(int source, int area, int cell);
void trading_cards_room_reset(void);
u16 trading_cards_world_tile(void);
int trading_cards_world_palette(void);
void trading_cards_draw_notice(void);

#endif
