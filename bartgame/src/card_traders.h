#ifndef CARD_TRADERS_H
#define CARD_TRADERS_H

#include "gba.h"
#include "trading_cards.h"

enum {
    CARD_TRADER_PEDDLER,
    CARD_TRADER_GREEN,
    CARD_TRADER_BLUE,
    CARD_TRADER_RED,
    CARD_TRADER_COUNT
};

void card_traders_room_reset(void);
void card_traders_place(int trader, int x, int y, int head_y, int terrace);
void card_traders_draw(void);
bool8 card_traders_try_open(void);
bool8 card_traders_accept(int trader, int card);
bool8 card_traders_completed(int trader);
void card_traders_explain(int trader);
const char* card_traders_name(int trader);
int card_traders_request(int trader);

#endif
