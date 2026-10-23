#ifndef TEXT_H
#define TEXT_H
#include "gba.h"

void text_init(void);
void text_flush(void);
void bg0_clear(void);
void bg0_put(int tx, int ty, u16 tile);
void bg0_print(int tx, int ty, const char* s);
void bg0_print_gold(int tx, int ty, const char* s);
void bg0_print_num(int tx, int ty, int n, int width);
/* over the world, nothing behind the letters: the HUD and the title */
void bg0_print_hud(int tx, int ty, const char* s);
void bg0_print_num_hud(int tx, int ty, int n, int width);
void bg0_fill(int tx, int ty, int w, int h, u16 tile);
void bg0_frame(int tx, int ty, int w, int h);

/* the message box: plain, or with a speaker's name and portrait */
void textbox_open(const char* s);
void textbox_open_named(const char* name, int portrait, const char* s);
void textbox_open_menu(const char* prompt, const char* const* options, int count);
int textbox_menu_result(void); /* -2 open, -1 cancelled, else the choice */
void textbox_update(void);
void textbox_draw(void);
bool8 textbox_active(void);
void textbox_close(void);

/* the shop */
typedef struct {
    const char* name;
    const char* desc1;
    const char* desc2;
    u16 price;
    u8 icon; /* a frame of the items sheet */
} ShopItem;
void shop_open(const char* title, const ShopItem* items, int n);
void shop_update(void);
void shop_draw(void);
void shop_close(void);
int shop_result(void); /* -2 open, -1 left, else the choice */
bool8 shop_active(void);

/* the HUD and the mini-map */
void hud_draw(void);
void hud_equip_icon(int eq, int px, int py, int prio);
void hud_clear(void);
void minimap_render(void);

#endif
