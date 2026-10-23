#ifndef TEXT_H
#define TEXT_H
#include "gba.h"

void text_init(void);
void text_flush(void);
void bg0_clear(void);
void bg0_put(int tx, int ty, u16 tile);
void bg0_print(int tx, int ty, const char* s);
void bg0_print_num(int tx, int ty, int n, int width);
void bg0_fill(int tx, int ty, int w, int h, u16 tile);
void bg0_frame(int tx, int ty, int w, int h);

/* the message box */
void textbox_open(const char* s);
void textbox_open_menu(const char* prompt, const char* const* options, int count);
int textbox_menu_result(void); /* -2 open, -1 cancelled, else the choice */
void textbox_update(void);
bool8 textbox_active(void);
void textbox_close(void);

/* the HUD */
void hud_draw(void);
void hud_clear(void);

#endif
