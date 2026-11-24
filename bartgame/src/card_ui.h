#ifndef CARD_UI_H
#define CARD_UI_H

#include "gba.h"

enum { CARD_UI_NONE, CARD_UI_COLLECTION, CARD_UI_INSPECT, CARD_UI_TRADE };

extern u8 gCardUiMode, gCardUiSelected, gCardUiRequest, gCardUiRefusals;

void card_ui_open_collection(void);
void card_ui_open_trade(int trader, int request_card, int portrait, const char* name);
void card_ui_update(void);

#endif
