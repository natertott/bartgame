#ifndef TROPHY_DATA_H
#define TROPHY_DATA_H

#include "trading_cards.h"

enum TrophyVictory {
    TROPHY_VICTORY_GRAIL, TROPHY_VICTORY_SUMMIT, TROPHY_VICTORY_SEALS,
    TROPHY_VICTORY_COUNT
};

typedef struct {
    const char* name;
    const char* description;
    u8 sheet, frame, palette;
    bool8 earned;
} TrophyMilestone;

/* The profile stores these masks independently of the active run. */
typedef struct {
    u32 cards, milestones;
} TrophyProgress;

extern TrophyProgress gTrophyProgress;

int trophy_milestone_count(void);
bool8 trophy_milestone_entry(int index, TrophyMilestone* out);
bool8 trophy_card_seen(int card);

void trophy_note_card(int card);
void trophy_note_trade(int trader, int card);
void trophy_note_golden_victory(int trader);
void trophy_note_victory(enum TrophyVictory victory); /* persisted by retiring the run */

bool8 trophy_progress_valid(const TrophyProgress* progress);
bool8 trophy_recover_cards(const TradingCardProgress* cards);

#endif
