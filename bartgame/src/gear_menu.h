#ifndef GEAR_MENU_H
#define GEAR_MENU_H
#include "gba.h"
/* Additive Satchel and directed Cream atlas. Original pause pages remain. */
void gear_menu_open(void);
void gear_menu_open_map(void);
void gear_menu_update(void);
bool8 gear_menu_active(void);
#endif
