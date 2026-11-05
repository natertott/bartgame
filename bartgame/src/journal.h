#ifndef JOURNAL_H
#define JOURNAL_H
#include "gba.h"

/* The arcade remembers discoveries independently of a run. IDs are saved;
   append new entries rather than renumbering existing ones. */
enum {
    JI_SWORD, JI_SHIELD, JI_SHIELD_UPGRADED, JI_BOMBS, JI_LAMP, JI_CLOAK,
    JI_GAUNTLET, JI_BOW, JI_HUBCAP, JI_MAP, JI_ASTROLABE, JI_RELIC,
    JI_HEART_PIECE, JI_HEART_CONTAINER, JI_KEY, JI_HEART, JI_GILT,
    JI_GILT_BIG, JI_BOMB_PICKUP, JI_ARROW1, JI_ARROW5, JI_ARROW10,
    JI_GRAIL, JI_HEALING_PETAL, JI_COUNT
};
#define JOURNAL_ENEMY_COUNT 9
#define JOURNAL_SRAM_OFFSET 0x7EC0u
#define JOURNAL_SLOT_BYTES 32u
#define JOURNAL_SRAM_END (JOURNAL_SRAM_OFFSET + 2u * JOURNAL_SLOT_BYTES)

typedef struct {
    const char* name;
    const char* description;
    u8 sheet, frame, palette;
    u8 hp, damage; /* enemy HP/contact damage; one player heart is8 HP */
} JournalEntry;

/* Read-only masks and revision support the UI and emulator evidence. */
extern u32 gJournalItems;
extern u16 gJournalEnemies;
extern u16 gJournalRevision;

void journal_init(void);
void journal_note_item(int item);
void journal_note_enemy(int type);
void journal_note_owned(void); /* seed only facts recoverable from inventory */
void journal_note_pickup(int pickup); /* PK_*: visible or collected */
void journal_note_icon(int icon); /* F_ICON32_*: awarded item */
void journal_note_shop_icon(int icon); /* F_ITEMS_*: visible stock */
bool8 journal_item_seen(int item);
bool8 journal_enemy_seen(int type);
int journal_item_count(void);
int journal_enemy_count(void);
int journal_items_found(void);
int journal_enemies_found(void);
const JournalEntry* journal_item_entry(int item);
const JournalEntry* journal_enemy_entry(int type);

#endif
