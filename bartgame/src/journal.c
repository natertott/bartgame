/* The Drain arcade's field journal. Discovery is a profile fact: a new game,
   run death or run-save migration must not erase something Bloom has seen.
   Run SaveFile v1/v2 and appearance preferences keep their existing formats. */
#include "gba.h"
#include "assets.h"
#include "appearance.h"
#include "player.h"
#include "objects.h"
#include "enemy.h"
#include "journal.h"

#define JOURNAL_SRAM ((volatile u8*)(0x0E000000u + JOURNAL_SRAM_OFFSET))
#define JOURNAL_MAGIC 0x314E524Au /* JRN1 */
#define JOURNAL_VERSION 1u
#define ITEM_MASK (0xFFFFFFFFu >> (32 - JI_COUNT))
#define ENEMY_MASK ((1u << JOURNAL_ENEMY_COUNT) - 1u)

u32 gJournalItems;
u16 gJournalEnemies, gJournalRevision;
static u32 sGeneration;
static u8 sCurrentSlot;

typedef struct {
    u32 magic;
    u16 version, size;
    u32 generation;
    u32 items;
    u16 enemies, reserved;
    u32 reserved2[2];
    u32 sum;
} JournalRecord;
typedef char JournalRecordIs32[(sizeof(JournalRecord)==JOURNAL_SLOT_BYTES)?1:-1];
typedef char JournalBeforePreferences[(JOURNAL_SRAM_END<=APPEARANCE_SRAM_OFFSET)?1:-1];
typedef char JournalItemMaskFits[(JI_COUNT>0 && JI_COUNT<=32)?1:-1];
typedef char JournalEnemiesMatchBuild[(EN_COUNT==JOURNAL_ENEMY_COUNT)?1:-1];

#define ENTRY(n,d,s,f,p) { n,d,s,f,p,0,0 }
static const JournalEntry sItems[JI_COUNT] = {
    [JI_SWORD] = ENTRY("Sword", "A hopeful little blade. Deals 2 HP per hit. Cuts bushes and bats seeds back.", SHEET_ICON32,F_ICON32_SWORD,PAL_OBJ_IRON),
    [JI_SHIELD] = ENTRY("Bark Shield", "Hold it toward a threat. Blocks frontal bites and seeds. Your back stays exposed.", SHEET_ICON32,F_ICON32_SHIELD,PAL_OBJ_GEAR),
    [JI_SHIELD_UPGRADED] = ENTRY("Gilded Shield", "Green wood and gold trim. Uses the same frontal guard as the Bark Shield.", SHEET_ICON32,F_ICON32_SHIELD_UPGRADED,PAL_OBJ_GEAR),
    [JI_BOMBS] = ENTRY("Blightseeds", "Set one and stand clear. The blast opens cracked walls and deals 8 enemy HP.", SHEET_ICON32,F_ICON32_BOMBS,PAL_OBJ_BLIGHT),
    [JI_LAMP] = ENTRY("Grail Lamp", "Burns webs and thorns; lights censers. This flame clears terrain, not enemy HP.", SHEET_ICON32,F_ICON32_LAMP,PAL_OBJ_GEAR),
    [JI_CLOAK] = ENTRY("Petal Cloak", "Use while moving to leap a gap. Land on safe ground beyond the hole.", SHEET_ICON32,F_ICON32_CLOAK,PAL_OBJ_BUGS),
    [JI_GAUNTLET] = ENTRY("Root Gauntlet", "Worn, not equipped. Press R beside a boulder to lift it; throw it for 4 HP.", SHEET_ICON32,F_ICON32_GAUNTLET,PAL_OBJ_GEAR),
    [JI_BOW] = ENTRY("Thorn Bow", "Fires along your facing. Each arrow costs one shot and deals 2 enemy HP.", SHEET_ICON32,F_ICON32_BOW,PAL_OBJ_GEAR),
    [JI_HUBCAP] = ENTRY("Drain Cap", "Equip and use it to return to the Drain. The way home waits beneath your feet.", SHEET_ICON32,F_ICON32_HUBCAP,PAL_OBJ_IRON),
    [JI_MAP] = ENTRY("Map of the Wood", "Reveals every room's shape on the map. Discover features to learn their marks.", SHEET_ICON32,F_ICON32_MAP,PAL_OBJ_GEAR),
    [JI_ASTROLABE] = ENTRY("Astrolabe", "Adds chests, the Heart and barriers to the map. Brass remembers the hidden ways.", SHEET_ICON32,F_ICON32_ASTROLABE,PAL_OBJ_GEAR),
    [JI_RELIC] = ENTRY("The Relic", "A precious thing from another chamber. Return it to the Weeping Nun.", SHEET_ICON32,F_ICON32_RELIC,PAL_OBJ_GEAR),
    [JI_HEART_PIECE] = ENTRY("Piece of Heart", "Four quarters grow one whole heart. A little life is still worth finding.", SHEET_ICON32,F_ICON32_HEART_PIECE,PAL_OBJ_HERO),
    [JI_HEART_CONTAINER] = ENTRY("Heart Container", "Adds one heart to maximum health. One whole player heart holds 8 HP.", SHEET_ICON32,F_ICON32_HEART_CONTAINER,PAL_OBJ_HERO),
    [JI_KEY] = ENTRY("Small Key", "Walk into a locked door to spend one key. A large keyhole shows its purpose.", SHEET_ICON32,F_ICON32_KEY,PAL_OBJ_GEAR),
    [JI_HEART] = ENTRY("Heart", "A loose heart restores 8 HP: one whole player heart. Gather it by touch or sword.", SHEET_PICK32,F_PICK32_HEART,PAL_OBJ_HERO),
    [JI_GILT] = ENTRY("Gilt", "A little glimmer worth one gilt. Spend it at the frog's market in the Drain.", SHEET_PICK32,F_PICK32_GILT,PAL_OBJ_GEAR),
    [JI_GILT_BIG] = ENTRY("Purse of Gilt", "A dropped purse holds 10 gilt. Larger chest rewards may hold more. Carry up to 999.", SHEET_ICON32,F_ICON32_GILT_BIG,PAL_OBJ_GEAR),
    [JI_BOMB_PICKUP] = ENTRY("Blightseed Refill", "A dropped refill adds three seeds if you own blightseeds. Carry up to 30.", SHEET_PICK32,F_PICK32_BOMB_PICKUP,PAL_OBJ_BLIGHT),
    [JI_ARROW1] = ENTRY("Arrow", "Adds one shot for the Thorn Bow. Walls stop arrows. Carry up to 50 shots.", SHEET_PICK32,F_PICK32_ARROW1,PAL_OBJ_IRON),
    [JI_ARROW5] = ENTRY("Five Arrows", "A small tied bundle adds five shots. Ammunition never exceeds 50.", SHEET_PICK32,F_PICK32_ARROW5,PAL_OBJ_IRON),
    [JI_ARROW10] = ENTRY("Ten Arrows", "A full bundle adds ten shots. The frog sells these once you have a bow.", SHEET_PICK32,F_PICK32_ARROW10,PAL_OBJ_IRON),
    [JI_GRAIL] = ENTRY("The Grail", "The Heart releases this when it falls. Claim the Grail to finish the journey.", SHEET_PICK32,F_PICK32_GRAIL,PAL_OBJ_GEAR),
    [JI_HEALING_PETAL] = ENTRY("Healing Petal", "The frog's preserved snack costs 10 gilt and restores two player hearts.", SHEET_ITEMS,F_ITEMS_HEART,PAL_OBJ_HERO),
};
#undef ENTRY

/* Entries follow stable production enemy IDs, including the retained boss. */
static const JournalEntry sEnemies[JOURNAL_ENEMY_COUNT] = {
    [EN_BEETLE] = { "Coin Toad", "Scuttles toward nearby prey. Keep room to swing; a normal sword hit defeats it.", SHEET_BEETLE,F_BEETLE_WALK_S1,PAL_OBJ_ITEMS,2,2 },
    [EN_BAT] = { "Quill Moth", "Rests, then flies after you. Watch its body and shadow; strike when it comes close.", SHEET_BAT,F_BAT_FLY1,PAL_OBJ_ITEMS,2,2 },
    [EN_SPITTER] = { "Trumpet Bellflower", "Pauses and points before spitting. Step out of its lane or bat a seed back.", SHEET_SPITTER,F_SPITTER_IDLE_S,PAL_OBJ_BLIGHT,2,2 },
    [EN_SLIME] = { "Pear Bladder", "Compresses before a hop. Give the landing space, then close in for two sword hits.", SHEET_SLIME,F_SLIME_IDLE,PAL_OBJ_ITEMS,4,2 },
    [EN_KNIGHT] = { "Moth Confessor", "A heavy blade follows a visible windup. Dodge the strike, punish recovery. Five sword hits.", SHEET_KNIGHT,F_KNIGHT_IDLE_S,PAL_OBJ_IRON,10,4 },
    [EN_BOSS] = { "Blight Heart", "A split purple heart. Its pulse becomes spores, minions and lunges as its strength fades.", SHEET_BOSS,F_BOSS_PULSE1,PAL_OBJ_BLIGHT,40,4 },
    [EN_PROTO_ROPE] = { "Gilt Leech", "Compresses, locks a lane, then charges straight. Sidestep the rush and punish its recovery.", SHEET_PROTO_ROPE,F_PROTO_ROPE_IDLE_S,PAL_OBJ_ITEMS,4,2 },
    [EN_PROTO_LEEVER] = { "Root Maw", "A mound announces emergence. Buried and rising bodies reject hits; strike while exposed.", SHEET_PROTO_LEEVER,F_PROTO_LEEVER_IDLE_S,PAL_OBJ_BLIGHT,6,2 },
    [EN_PROTO_HELMASAUR] = { "Reliquary Snout", "Its brass front blocks hits. Dodge the committed rush and strike a soft side or rear.", SHEET_PROTO_HELMASAUR,F_PROTO_HELMASAUR_IDLE_S,PAL_OBJ_FX,4,2 },
};

static u32 journal_checksum(const JournalRecord* r) {
    const u8* data=(const u8*)r;
    u32 value=2166136261u;
    int i;
    for (i=0;i<(int)sizeof(*r)-4;i++) value=(value^data[i])*16777619u;
    return value;
}

static void read_slot(JournalRecord* r,int slot) {
    u8* data=(u8*)r;
    int i;
    for (i=0;i<(int)sizeof(*r);i++) data[i]=JOURNAL_SRAM[slot*JOURNAL_SLOT_BYTES+i];
}

static bool8 valid_slot(const JournalRecord* r) {
    return r->magic==JOURNAL_MAGIC && r->version==JOURNAL_VERSION &&
           r->size==sizeof(*r) && !(r->items&~ITEM_MASK) &&
           !(r->enemies&~ENEMY_MASK) && !r->reserved &&
           !r->reserved2[0] && !r->reserved2[1] && r->sum==journal_checksum(r);
}

static void journal_store(void) {
#if !BART_ENEMY_LAB
    JournalRecord r;
    volatile u8* target;
    const u8* data=(const u8*)&r;
    int i,slot=sCurrentSlot^1;
    r.magic=JOURNAL_MAGIC;r.version=JOURNAL_VERSION;r.size=sizeof(r);
    r.generation=sGeneration+1;r.items=gJournalItems;r.enemies=gJournalEnemies;
    r.reserved=0;r.reserved2[0]=r.reserved2[1]=0;r.sum=journal_checksum(&r);
    target=JOURNAL_SRAM+slot*JOURNAL_SLOT_BYTES;
    /* Invalidate the target first. The other complete generation stays valid.
       Publishing all four magic bytes last makes torn records reject safely. */
    for (i=0;i<4;i++) target[i]=0;
    for (i=4;i<(int)sizeof(r);i++) target[i]=data[i];
    for (i=0;i<4;i++) target[i]=data[i];
    sCurrentSlot=slot;sGeneration=r.generation;
#endif
}

void journal_init(void) {
    JournalRecord a,b;
    bool8 av,bv;
    read_slot(&a,0);read_slot(&b,1);av=valid_slot(&a);bv=valid_slot(&b);
    gJournalItems=0;gJournalEnemies=0;sGeneration=0;sCurrentSlot=1;
    if (av || bv) {
        const JournalRecord* chosen;
        if (bv && (!av || (s32)(b.generation-a.generation)>0)) {
            chosen=&b;sCurrentSlot=1;
        } else {chosen=&a;sCurrentSlot=0;}
        gJournalItems=chosen->items;gJournalEnemies=chosen->enemies;
        sGeneration=chosen->generation;
    }
    gJournalRevision++;
}

void journal_note_item(int item) {
    u32 bit;
    if (item<0 || item>=JI_COUNT) return;
    bit=1u<<item;
    if (gJournalItems&bit) return;
    gJournalItems|=bit;gJournalRevision++;journal_store();
}

void journal_note_enemy(int type) {
    u16 bit;
    if (type<0 || type>=JOURNAL_ENEMY_COUNT) return;
    bit=(u16)(1u<<type);
    if (gJournalEnemies&bit) return;
    gJournalEnemies|=bit;gJournalRevision++;journal_store();
}

void journal_note_owned(void) {
    int i;
    static const u8 bits[]={ITEM_SWORD,ITEM_SHIELD,ITEM_BOMBS,ITEM_LAMP,ITEM_CLOAK,ITEM_GAUNTLET,ITEM_RELIC};
    static const u8 ids[]={JI_SWORD,JI_SHIELD,JI_BOMBS,JI_LAMP,JI_CLOAK,JI_GAUNTLET,JI_RELIC};
    for (i=0;i<7;i++) if (gPl.items&bits[i]) journal_note_item(ids[i]);
    if (gPl.items2&ITEM2_BOW) journal_note_item(JI_BOW);
    if (gPl.items2&ITEM2_HUBCAP) journal_note_item(JI_HUBCAP);
    if (gPl.items2&ITEM2_MAP) journal_note_item(JI_MAP);
    if (gPl.items2&ITEM2_ASTROLABE) journal_note_item(JI_ASTROLABE);
    if (gPl.items2&ITEM2_SHIELD_UPGRADE) journal_note_item(JI_SHIELD_UPGRADED);
    if (gPl.keys) journal_note_item(JI_KEY);
    if (gPl.gilt) journal_note_item(JI_GILT);
    if (gPl.bombs) journal_note_item(JI_BOMBS);
    if (gPl.arrows) journal_note_item(JI_ARROW1);
    if (gPl.hearts_pieces) journal_note_item(JI_HEART_PIECE);
    /* A larger maximum may come from four quarters, so it cannot establish
       that a standalone Heart Container has ever been encountered. */
}

void journal_note_pickup(int pickup) {
    static const u8 ids[]={JI_HEART,JI_GILT,JI_BOMB_PICKUP,JI_GILT_BIG,JI_KEY,JI_RELIC,JI_GRAIL,JI_ARROW1,JI_ARROW5,JI_ARROW10};
    if (pickup>=0 && pickup<(int)(sizeof(ids)/sizeof(ids[0]))) journal_note_item(ids[pickup]);
}

void journal_note_icon(int icon) {
    static const s8 ids[]={-1,JI_BOMBS,JI_LAMP,JI_CLOAK,JI_KEY,JI_HEART_PIECE,JI_HEART_CONTAINER,
                          JI_GILT_BIG,JI_RELIC,JI_GAUNTLET,JI_BOW,JI_HUBCAP,JI_MAP,JI_ASTROLABE,
                          JI_SWORD,JI_SHIELD,JI_SHIELD_UPGRADED};
    if (icon>=0 && icon<(int)(sizeof(ids)/sizeof(ids[0])) && ids[icon]>=0) journal_note_item(ids[icon]);
}

void journal_note_shop_icon(int icon) {
    if (icon==F_ITEMS_HEART) journal_note_item(JI_HEALING_PETAL);
    else if (icon==F_ITEMS_BOMBS) journal_note_item(JI_BOMBS);
    else if (icon==F_ITEMS_ARROW10) journal_note_item(JI_ARROW10);
}

bool8 journal_item_seen(int item) {
    return item>=0 && item<JI_COUNT && (gJournalItems&(1u<<item))!=0;
}
bool8 journal_enemy_seen(int type) {
    return type>=0 && type<JOURNAL_ENEMY_COUNT && (gJournalEnemies&(1u<<type))!=0;
}
int journal_item_count(void) {return JI_COUNT;}
int journal_enemy_count(void) {return JOURNAL_ENEMY_COUNT;}
static int bit_count(u32 bits) {
    int n=0;
    while (bits) {bits&=bits-1;n++;}
    return n;
}
int journal_items_found(void) {return bit_count(gJournalItems);}
int journal_enemies_found(void) {return bit_count(gJournalEnemies);}
const JournalEntry* journal_item_entry(int item) {return item>=0 && item<JI_COUNT?&sItems[item]:0;}
const JournalEntry* journal_enemy_entry(int type) {return type>=0 && type<JOURNAL_ENEMY_COUNT?&sEnemies[type]:0;}
