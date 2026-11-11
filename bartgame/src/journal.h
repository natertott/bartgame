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
    JI_GRAIL, JI_HEALING_PETAL, JI_BASE_COUNT,
    JI_LEGACY_BASE = JI_BASE_COUNT, JI_LEGACY_END = JI_LEGACY_BASE + 118,
    JI_GOLD_FLOW = JI_LEGACY_END, JI_GOLD_LEFT, JI_GOLD_MIDDLE, JI_GOLD_RIGHT, JI_COUNT
};
#define JOURNAL_BASE_ENEMY_COUNT 9
#define JOURNAL_ENEMY_COUNT 84
#define JOURNAL_ITEM_BYTES 20u
#define JOURNAL_ENEMY_BYTES 12u
#define JOURNAL_SRAM_OFFSET 0x7E40u
#define JOURNAL_SLOT_BYTES 64u
/* v1 remains untouched until a valid v2 generation has been published. */
#define JOURNAL_V1_SRAM_OFFSET 0x7EC0u
#define JOURNAL_V1_SLOT_BYTES 32u
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
extern u8 gJournalItemBits[JOURNAL_ITEM_BYTES];
extern u8 gJournalEnemyBits[JOURNAL_ENEMY_BYTES];

void journal_init(void);
void journal_note_item(int item);
void journal_note_enemy(int type);
void journal_note_legacy_item(int legacy_id);
void journal_note_gold_half(int index);
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
/* Visible catalogue ordinals omit source-only hidden helpers. Raw saved IDs
   and the APIs above stay stable; never serialize a visible ordinal. */
int journal_list_count(int page);
int journal_list_id(int page,int index);
int journal_list_found(int page);
/* Caller-owned metadata remains valid while other entries are queried.
   Page0=items, page1=enemies; this also describes undiscovered entries, so
   presentation must separately check journal_*_seen before displaying it. */
bool8 journal_entry(int page, int id, JournalEntry* out);
/* Stable pointers for the original24/9 entries; extended entries use out. */
const JournalEntry* journal_item_entry(int item);
const JournalEntry* journal_enemy_entry(int type);

#endif
