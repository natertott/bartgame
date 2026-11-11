/* Additive item/surface vocabulary from the original-game handoff.
   Existing PlayerState, equipment IDs, animations, item pictures and saves
   are not repurposed. New inventory/verbs live in a separate small record. */
#include "legacy_items.h"
#include "player.h"
#include "enemy.h"
#include "legacy_enemies.h"
#include "objects.h"
#include "react.h"
#include "room.h"
#include "video.h"
#include "sound.h"
#include "text.h"
#include "game.h"
#include "util.h"
#include "bomb_throw.h"
#include "handoff_events.h"
#include "journal.h"
#include "cream_room.h"
#include "handoff_objects.h"
#include "handoff_mobility.h"
#define ABS_VALUE(n) ((n)<0?-(n):(n))

#define OBJ_LEGACY_PICKUP 22
#define OBJ_LEGACY_PROJECTILE 23
#define SURFACE_LIMIT 96
#define BIT_HAS(a,n) (((a)[(unsigned)(n)>>5]>>((n)&31))&1u)
#define BIT_SET(a,n) ((a)[(unsigned)(n)>>5]|=1u<<((n)&31))
#define BIT_CLR(a,n) ((a)[(unsigned)(n)>>5]&=~(1u<<((n)&31)))
#define SKILL_SPIN 1
#define SKILL_ROLL 2
#define SKILL_DASH 4
#define SKILL_ROCK 8
#define SKILL_BEAM 16
#define SKILL_GREAT 32
#define SKILL_DOWN 64
#define SKILL_PERIL 128
#define SKILL_FOUR 256
#define SKILL_FAST_SPIN 512
#define SKILL_FAST_SPLIT 1024
#define SKILL_LONG_SPIN 2048

enum { LP_BOOM,LP_MAGIC,LP_PACCI,LP_FIRE,LP_LIGHT,LP_BEAM,LP_GUST };
LegacyInventory gLegacyInventory EWRAM_BSS;
u8 gLegacyHitKind=LE_HIT_SWORD;
#include "legacy_items_metadata.inc"

typedef struct {u16 cell;u8 kind,state;} Surface;
static Surface sSurfaces[SURFACE_LIMIT] EWRAM_BSS;
static u8 sSurfaceCount;
typedef struct {u16 tile;u8 owner,frame;} PickupSlot;
static PickupSlot sPickups[ACTOR_MAX] EWRAM_BSS;
static u8 sPickupCount;
static u16 sToolTile,sMiniTile;
static struct {
    u16 status[LPS_COUNT],gust_charge,sword_charge;
    s16 before_x,before_y,ice_x,ice_y;
    s32 before_fx,before_fy;
    s16 clone_x[3],clone_y[3];
    u8 minish,spin,spin_age,spin_face,beam_latch,boots_charge,dash,clone_mode;
    u8 capture_index,capture_kind,capture_type,clones,split_pads,split_ready;
    u8 dive,sink,gust_load,jar_held,old_floor,stamina;
} s EWRAM_BSS;

static const u8 sEqItem[EQ_TOTAL]={
    LI_NONE,LI_SMITH_SWORD,LI_BOMBS,LI_LANTERN_OFF,LI_ROCS_CAPE,LI_SHIELD,
    LI_BOW,LI_OCARINA,LI_REMOTE_BOMBS,LI_LIGHT_ARROW,LI_BOOMERANG,
    LI_MAGIC_BOOMERANG,LI_MIRROR_SHIELD,LI_GUST_JAR,LI_PACCI_CANE,
    LI_MOLE_MITTS,LI_PEGASUS_BOOTS,LI_FIRE_ROD,LI_OCARINA,
    LI_BOTTLE1,LI_BOTTLE2,LI_BOTTLE3,LI_BOTTLE4,LI_GREEN_SWORD,
    LI_RED_SWORD,LI_BLUE_SWORD,LI_FOURSWORD
};
static int input_dir(void) {
    int dx=(gKeysHeld&KEY_RIGHT?1:0)-(gKeysHeld&KEY_LEFT?1:0);
    int dy=(gKeysHeld&KEY_DOWN?1:0)-(gKeysHeld&KEY_UP?1:0);
    if(!dx&&!dy)return DIR_NONE;
    return dx>0?(dy<0?4:dy>0?12:8):dx<0?(dy<0?28:dy>0?20:24):dy<0?0:16;
}
static bool8 valid(int item) {return item>LI_NONE&&item<LI_COUNT;}
int legacy_item_count(void) {return LI_COUNT;}
const LegacyItemDef* legacy_item_def(int item) {return valid(item)?&gLegacyItemDefs[item]:NULL;}
int legacy_equip_item(int eq) {return (unsigned)eq<EQ_TOTAL?sEqItem[eq]:LI_NONE;}
bool8 legacy_equip_sword(int eq) {return eq==EQ_SWORD||(eq>=EQ_GREEN_SWORD&&eq<=EQ_FOUR_SWORD);}
bool8 legacy_equip_shield(int eq) {return eq==EQ_SHIELD||eq==EQ_MIRROR_SHIELD;}
bool8 legacy_item_seen(int item) {return valid(item)&&BIT_HAS(gLegacyInventory.seen,item);}
int legacy_bomb_capacity(void) {static const u8 caps[]={30,50,70,99};return caps[MIN(3,gLegacyInventory.bomb_bag)];}
int legacy_arrow_capacity(void) {static const u8 caps[]={50,65,80,99};return caps[MIN(3,gLegacyInventory.quiver)];}

bool8 legacy_item_owned(int item) {
    if(!valid(item))return FALSE;
    switch(item) {
      case LI_SMITH_SWORD:return (gPl.items&ITEM_SWORD)!=0;
      case LI_SHIELD:return (gPl.items&ITEM_SHIELD)!=0;
      case LI_BOMBS:return (gPl.items&ITEM_BOMBS)!=0;
      case LI_LANTERN_OFF:case LI_LANTERN_ON:return (gPl.items&ITEM_LAMP)!=0;
      case LI_ROCS_CAPE:return (gPl.items&ITEM_CLOAK)!=0;
      case LI_POWER_BRACELETS:return (gPl.items&ITEM_GAUNTLET)!=0;
      case LI_BOW:return (gPl.items2&ITEM2_BOW)!=0;
      case LI_MAP:return (gPl.items2&ITEM2_MAP)!=0;
      default:return BIT_HAS(gLegacyInventory.owned,item);
    }
}
bool8 legacy_equip_owned(int eq) {
    if(eq==EQ_NONE)return TRUE;
    if(eq==EQ_HUBCAP)return(gPl.items2&ITEM2_HUBCAP)!=0;
    return (unsigned)eq<EQ_TOTAL&&legacy_item_owned(sEqItem[eq]);
}
static void mark(int item) {if(valid(item)){BIT_SET(gLegacyInventory.owned,item);BIT_SET(gLegacyInventory.seen,item);}}
void legacy_items_seed_owned(void) {
    static const u8 map[]={LI_SMITH_SWORD,LI_SHIELD,LI_BOMBS,LI_LANTERN_OFF,LI_ROCS_CAPE,LI_POWER_BRACELETS,LI_BOW,LI_MAP};
    int i;
    for(i=0;i<8;i++)if(legacy_item_owned(map[i]))mark(map[i]);
    if(gPl.items2&ITEM2_SHIELD_UPGRADE)mark(LI_MIRROR_SHIELD);
}
void legacy_items_new_run(void) {
    memset(&gLegacyInventory,0,sizeof(gLegacyInventory));memset(&s,0,sizeof(s));
    legacy_items_seed_owned();bomb_charge_cancel();
}
void legacy_item_remove(int item) {
    int i;
    if(!valid(item))return;
    BIT_CLR(gLegacyInventory.owned,item);
    if(item==LI_SHIELD)gPl.items&=~ITEM_SHIELD;
    if(item==LI_MIRROR_SHIELD)gPl.items2&=~ITEM2_SHIELD_UPGRADE;
    for(i=0;i<SLOT_COUNT;i++)if(legacy_equip_item(gPl.equip[i])==item)gPl.equip[i]=EQ_NONE;
}
static int empty_bottle(void) {int i;for(i=0;i<4;i++)if(legacy_item_owned(LI_BOTTLE1+i)&&!gLegacyInventory.bottles[i])return i;return -1;}
static void refill_bottle(int item,int amount) {
    int i;
    while(amount-->0 && (i=empty_bottle())>=0)gLegacyInventory.bottles[i]=item;
}
void legacy_item_grant(int item,int amount) {
    int i,bit=0;
    bool8 previously_owned=legacy_item_owned(item);
    if(item>=LI_KINSTONE_RED&&item<=LI_KINSTONE_GREEN) {
        int color=item-LI_KINSTONE_RED;
        if(amount>0){gLegacyInventory.kinstones[color]=MIN(999,gLegacyInventory.kinstones[color]+amount);mark(LI_KINSTONE);journal_note_legacy_item(LI_KINSTONE);}return;
    }
    if(item==LI_ENEMY_BEETLE) {
        if(amount>0)enemy_spawn(LE_BEETLE_0,PX(gPlayer->x)+16,PX(gPlayer->y));
        return;
    }
    if(!valid(item)||amount<=0)return;
    mark(item);journal_note_legacy_item(item);
    handoff_notify(HN_ITEM,gGame.area,gGame.cell,item);
    if(item==LI_SHELLS)gLegacyInventory.shells=MIN(999,gLegacyInventory.shells+amount);
    if(item==LI_SHELLS30)gLegacyInventory.shells=MIN(999,gLegacyInventory.shells+30*amount);
    if(!(item>=LI_BOTTLE_EMPTY&&item<=LI_CHARM_DIN)&&handoff_apply_item_effect(item,amount))return;
    switch(item) {
      case LI_SMITH_SWORD:gPl.items|=ITEM_SWORD;break;
      case LI_GREEN_SWORD:gPl.items|=ITEM_SWORD;gLegacyInventory.sword_level=MAX(1,gLegacyInventory.sword_level);break;
      case LI_RED_SWORD:gPl.items|=ITEM_SWORD;gLegacyInventory.sword_level=MAX(2,gLegacyInventory.sword_level);break;
      case LI_BLUE_SWORD:gPl.items|=ITEM_SWORD;gLegacyInventory.sword_level=MAX(3,gLegacyInventory.sword_level);break;
      case LI_FOURSWORD:gPl.items|=ITEM_SWORD;gLegacyInventory.sword_level=4;gLegacyInventory.skills|=SKILL_FOUR;break;
      case LI_BOMBS:case LI_REMOTE_BOMBS:gPl.items|=ITEM_BOMBS;gPl.bombs=MIN(legacy_bomb_capacity(),gPl.bombs+10*amount);break;
      case LI_BOW:case LI_LIGHT_ARROW:gPl.items2|=ITEM2_BOW;gPl.arrows=MIN(legacy_arrow_capacity(),gPl.arrows+10*amount);break;
      case LI_SHIELD:gPl.items|=ITEM_SHIELD;break;
      case LI_MIRROR_SHIELD:gPl.items|=ITEM_SHIELD;gPl.items2|=ITEM2_SHIELD_UPGRADE;break;
      case LI_LANTERN_OFF:case LI_LANTERN_ON:gPl.items|=ITEM_LAMP;break;
      case LI_ROCS_CAPE:gPl.items|=ITEM_CLOAK;break;
      case LI_POWER_BRACELETS:gPl.items|=ITEM_GAUNTLET;break;
      case LI_MAP:case LI_DUNGEON_MAP:gPl.items2|=ITEM2_MAP;break;
      case LI_COMPASS:gPl.items2|=ITEM2_ASTROLABE;break;
      case LI_HEART:player_heal(8*amount);break;
      case LI_FAIRY:player_heal(32*amount);break;
      case LI_HEART_PIECE:while(amount-->0)player_heart_piece();break;
      case LI_HEART_CONTAINER:if(gPl.hp_max<160)gPl.hp_max=MIN(160,gPl.hp_max+8*amount);gPl.hp=gPl.hp_max;break;
      case LI_SMALL_KEY:gPl.keys=MIN(99,gPl.keys+amount);break;
      case LI_RUPEE1:case LI_RUPEE5:case LI_RUPEE20:case LI_RUPEE50:case LI_RUPEE100:case LI_RUPEE200: {
        static const u16 value[]={1,5,20,50,100,200};gPl.gilt=MIN(999,gPl.gilt+value[item-LI_RUPEE1]*amount);break;}
      case LI_BOMBS5:case LI_BOMBS10:case LI_BOMBS30: {
        int n=item==LI_BOMBS5?5:item==LI_BOMBS10?10:30;gPl.bombs=MIN(legacy_bomb_capacity(),gPl.bombs+n*amount);break;}
      case LI_ARROWS5:case LI_ARROWS10:case LI_ARROWS30: {
        int n=item==LI_ARROWS5?5:item==LI_ARROWS10?10:30;gPl.arrows=MIN(legacy_arrow_capacity(),gPl.arrows+n*amount);break;}
      case LI_BOMBBAG:gLegacyInventory.bomb_bag=MIN(3,gLegacyInventory.bomb_bag+amount);break;
      case LI_LARGE_QUIVER:gLegacyInventory.quiver=MIN(3,gLegacyInventory.quiver+amount);break;
      case LI_DIG_BUTTERFLY:gLegacyInventory.dig_upgrade=1;break;
      case LI_SWIM_BUTTERFLY:gLegacyInventory.swim_upgrade=1;break;
      case LI_SHELLS:break;
      case LI_SHELLS30:break;
      case LI_KINSTONE:gLegacyInventory.kinstones[0]=MIN(999,gLegacyInventory.kinstones[0]+amount);break;
      case LI_BOTTLE1:case LI_BOTTLE2:case LI_BOTTLE3:case LI_BOTTLE4:
        if(item==LI_BOTTLE1&&previously_owned)for(i=1;i<4;i++)if(!legacy_item_owned(LI_BOTTLE1+i)){mark(LI_BOTTLE1+i);break;}
        break;
      default:
        if(item>=LI_BOTTLE_EMPTY&&item<=LI_CHARM_DIN)refill_bottle(item==LI_BOTTLE_EMPTY?0:item,amount);
        break;
    }
    if(item>=LI_SKILL_SPIN_ATTACK&&item<=LI_SKILL_PERIL_BEAM)bit=1<<(item-LI_SKILL_SPIN_ATTACK);
    if(item>=LI_SKILL_FAST_SPIN&&item<=LI_SKILL_LONG_SPIN)bit=SKILL_FAST_SPIN<<(item-LI_SKILL_FAST_SPIN);
    gLegacyInventory.skills|=bit;
    /* The first bottle award fills the first free slot; repeatable bottle
       grants do not silently replace contents of a previously owned vessel. */
    if(item==LI_BOTTLE_EMPTY)for(i=0;i<4;i++)if(!legacy_item_owned(LI_BOTTLE1+i)){mark(LI_BOTTLE1+i);break;}
}

void legacy_item_hit(Actor* target,int kind,int damage,int direction,int knockback) {
    int old=gLegacyHitKind;
    gLegacyHitKind=kind;enemy_hurt(target,damage,direction,knockback);gLegacyHitKind=old;
}
static u16 keys_for(int eq) {return player_equip_keys(eq);}
static u16 sword_keys(void) {int i;u16 bits=0;for(i=0;i<SLOT_COUNT;i++)if(legacy_equip_sword(gPl.equip[i]))bits|=i==SLOT_A?KEY_A:i==SLOT_B?KEY_B:KEY_L;return bits;}
static void affect_box(int x0,int y0,int x1,int y1,int kind,int damage,int knock) {
    int i;
    handoff_tool_box(kind,x0,y0,x1,y1);
    for(i=1;i<ACTOR_MAX;i++) {
        Actor* e=&gActors[i];
        if(e->kind!=AK_ENEMY||e->iframes)continue;
        if(!damage&&e->type<LEGACY_ENEMY_BASE&&kind!=LE_HIT_BOOMERANG)continue;
        if(legacy_enemy_hit_parts(e,x0,y0,x1,y1,kind,damage,facing_to_dir(gPlayer->facing)))continue;
        if(actor_box_overlap(e,x0,y0,x1,y1))legacy_item_hit(e,kind,damage,actor_dir_to(gPlayer,e),knock);
    }
}

static void spin_hit(int px,int py,int radius,int damage) {
    int i;
    handoff_tool_box(LE_HIT_SWORD,px-radius,py-radius,px+radius,py+radius);
    for(i=1;i<ACTOR_MAX;i++) {
        Actor* e=&gActors[i];const Hitbox* hb;int x,y,nearx,neary,dx,dy;
        if(e->kind!=AK_ENEMY||e->iframes)continue;
        hb=&gHitboxes[e->hitbox];x=PX(e->x)+hb->ox;y=PX(e->y)+hb->oy;
        nearx=CLAMP(px,x-hb->hw,x+hb->hw);neary=CLAMP(py,y-hb->hh,y+hb->hh);
        dx=nearx-px;dy=neary-py;
        if(dx*dx+dy*dy<=radius*radius)legacy_item_hit(e,LE_HIT_SWORD,damage,actor_dir_to(gPlayer,e),Q8(1.5));
        /* Four thin inscribed strips cover multipart components without
           letting the square's unreachable corners take a circular hit. */
        legacy_enemy_hit_parts(e,px-radius,py-radius/3,px+radius,py+radius/3,LE_HIT_SWORD,damage,facing_to_dir(gPlayer->facing));
        legacy_enemy_hit_parts(e,px-radius/3,py-radius,px+radius/3,py+radius,LE_HIT_SWORD,damage,facing_to_dir(gPlayer->facing));
    }
}

void legacy_surface_clear(void) {sSurfaceCount=0;}
void legacy_surface_set(int tx,int ty,int kind) {
    int i;u16 cell=(ty<<6)|tx;
    if(tx<0||ty<0||tx>=32||ty>=32)return;
    for(i=0;i<sSurfaceCount;i++)if(sSurfaces[i].cell==cell){sSurfaces[i].kind=kind;sSurfaces[i].state=0;return;}
    if(sSurfaceCount<SURFACE_LIMIT){sSurfaces[sSurfaceCount].cell=cell;sSurfaces[sSurfaceCount].kind=kind;sSurfaces[sSurfaceCount].state=0;sSurfaceCount++;}
}
static Surface* surface_record(int tx,int ty) {int i;u16 cell=(ty<<6)|tx;for(i=0;i<sSurfaceCount;i++)if(sSurfaces[i].cell==cell)return &sSurfaces[i];return NULL;}
int legacy_surface_at(int px,int py) {
    int tx=px>>4,ty=py>>4;Surface* cell=surface_record(tx,ty);u16 mt=room_get(tx,ty);
    if(cell)return cell->kind;
#ifdef MT_LH_ICE
    if(mt==MT_LH_ICE)return LS_ICE;
    if(mt==MT_LH_SWAMP)return LS_SWAMP;
    if(mt==MT_LH_DUST)return LS_DUST;
    if(mt==MT_LH_LAVA)return LS_LAVA;
    if(mt==MT_LH_DIG)return LS_DIG;
    if(mt==MT_LH_DIG_WALL)return LS_DIG_WALL;
    if(mt==MT_LH_SPRING)return LS_SPRING;
    if(mt==MT_LH_MINISH_PORTAL)return LS_MINISH_PORTAL;
    if(mt==MT_LH_MINISH_GAP)return LS_MINISH_GAP;
    if(mt==MT_LH_CLONE_PLATE)return LS_CLONE_PLATE;
    if(mt==MT_LH_CRUMBLE)return LS_CRUMBLE;
    if(mt>=MT_LH_CONVEYOR_N&&mt<=MT_LH_CONVEYOR_W)return LS_CONVEYOR_N+mt-MT_LH_CONVEYOR_N;
    if(mt==MT_LH_SHALLOW)return LS_SHALLOW;
    if(mt==MT_LH_SLOPE_X)return LS_SLOPE_X;
    if(mt==MT_LH_SLOPE_Y)return LS_SLOPE_Y;
    if(mt==MT_LH_DASH_WALL)return LS_DASH_WALL;
    if(mt==MT_LH_ICE_BLOCK)return LS_ICE_BLOCK;
    if(mt==MT_LH_WATER_SPROUT)return LS_WATER_SPROUT;
#endif
#ifdef TT_CLIMB
    if(room_type(tx,ty)==TT_CLIMB)return LS_CLIMB;
#endif
    return LS_NONE;
}
bool8 legacy_minish_gap_at(int px,int py) {return s.minish&&legacy_surface_at(px,py)==LS_MINISH_GAP;}
static u16 floor_tile(int tx,int ty) {
#ifdef TS_CREAM
    extern u16 cream_room_floor(int,int);
    if(gGame.area==AREA_CREAM)return cream_room_floor(tx,ty);
#endif
    int x,y;
    for(y=-1;y<=1;y++)for(x=-1;x<=1;x++) {
        u16 m=room_get(tx+x,ty+y);
        if(m!=MT_NONE&&metatile_type[m]==TT_FLOOR&&legacy_surface_at((tx+x)*16+8,(ty+y)*16+8)==LS_NONE)return m;
    }
    return MT_MOSS0;
}
static void clear_surface(int tx,int ty) {
    Surface* c=surface_record(tx,ty);if(c)c->kind=LS_NONE;
    room_change(tx,ty,floor_tile(tx,ty));
    handoff_tile_cleared(tx,ty);fx_spawn(FX_PUFF,tx*16+8,ty*16+8);
}

static bool8 allocate_pickup(Actor* a,int item) {
    int i;
    for(i=0;i<sPickupCount;i++)if(sPickups[i].owner) {
        Actor* old=&gActors[sPickups[i].owner];
        if(old==a||old->kind!=AK_OBJECT||old->type!=OBJ_LEGACY_PICKUP||old->sub!=i+1)sPickups[i].owner=0;
    }
    for(i=0;i<sPickupCount;i++)if(!sPickups[i].owner)break;
    if(i==sPickupCount){u16 tile=sprite_alloc(4);if(!tile)return FALSE;sPickups[i].tile=tile;sPickupCount++;}
    sPickups[i].owner=a-gActors;sPickups[i].frame=item|128;a->sub=i+1;a->tile=sPickups[i].tile;return TRUE;
}
Actor* legacy_item_spawn(int item,int px,int py) {
    Actor* a;if(!valid(item))return NULL;
    a=actor_new(AK_OBJECT,OBJ_LEGACY_PICKUP,px,py);if(!a)return NULL;
    actor_set_sheet(a,SHEET_HANDOFF_ITEMS,0);
    if(!allocate_pickup(a,item)){actor_free(a);return NULL;}
    a->v[0]=item;a->frame=0;a->flags=AF_FLYING;a->hitbox=HB_SMALL;a->prio=2;
    return a;
}
void legacy_items_flush_frames(void) {
    int i;
    handoff_objects_flush_frames();
    for(i=0;i<sPickupCount;i++)if(sPickups[i].owner&&(sPickups[i].frame&128)) {
        PickupSlot* p=&sPickups[i];Actor* a=&gActors[p->owner];
        if(a->kind==AK_OBJECT&&a->type==OBJ_LEGACY_PICKUP&&a->sub==i+1) {
            int frame=p->frame&127;const SpriteSheet* sh=&sheets[SHEET_HANDOFF_ITEMS];
            dma3_copy32(sh->tiles+frame*sh->frame_tiles*16,OBJ_TILE(p->tile),128);p->frame=frame;
        } else p->owner=0;
    }
}
static Actor* projectile(int kind,int damage) {
    Actor* a;
    if(!sToolTile)sToolTile=sprite_load_sheet(SHEET_HANDOFF_TOOL_FX);
    if(!sToolTile)return NULL;
    a=actor_new(AK_OBJECT,OBJ_LEGACY_PROJECTILE,PX(gPlayer->x),PX(gPlayer->y)-5);if(!a)return NULL;
    actor_set_sheet(a,SHEET_HANDOFF_TOOL_FX,sToolTile);a->v[0]=kind;a->damage=damage;
    a->dir=facing_to_dir(gPlayer->facing);a->facing=gPlayer->facing;
    a->flags=AF_FLYING;a->hitbox=HB_PROJ;a->prio=2;a->z=Q16(5);
    a->speed=kind==LP_FIRE||kind==LP_LIGHT?Q8(4):kind==LP_BEAM?Q8(3.5):kind==LP_MAGIC?Q8(2.5):Q8(2);
    a->frame=kind*2;sfx_play(SFX_SPIT);return a;
}
static int projectile_kind(int kind) {
    return kind==LP_BOOM||kind==LP_MAGIC?LE_HIT_BOOMERANG:kind==LP_PACCI?LE_HIT_PACCI:kind==LP_FIRE?LE_HIT_FIRE:kind==LP_LIGHT?LE_HIT_ARROW:kind==LP_BEAM?LE_HIT_BEAM:LE_HIT_GUST_BIG;
}
static void projectile_update(Actor* a) {
    int kind=a->v[0],i,t=++a->timer,px,py;
    int hitkind=kind==LP_GUST&&a->damage<2?LE_HIT_GUST_SMALL:projectile_kind(kind);
    bool8 boom=kind==LP_BOOM||kind==LP_MAGIC;
    if(boom) {
        if(!a->state && (t>=(kind==LP_MAGIC?60:30)||a->coll))a->state=1;
        if(a->state) {a->dir=actor_dir_to(a,gPlayer);a->speed=MIN(Q8(4),Q8(2)+t*8);}
        else if(kind==LP_MAGIC) {int dir=input_dir();if(dir!=DIR_NONE)a->dir=dir;}
    }
    actor_move_free(a,a->speed,a->dir);px=PX(a->x);py=PX(a->y);
    a->frame=kind*2+((gFrame>>2)&1);
    if(kind==LP_FIRE) {
        react_burn_box(px-5,py-8,px+5,py+2);
        if(legacy_surface_at(px,py)==LS_ICE_BLOCK)clear_surface(px>>4,py>>4);
    }
    if(kind==LP_PACCI&&legacy_surface_at(px,py)==LS_SPRING) {
        Surface* cell=surface_record(px>>4,py>>4);
        if(!cell){legacy_surface_set(px>>4,py>>4,LS_SPRING);cell=surface_record(px>>4,py>>4);}
        if(cell)cell->state=1;
        fx_spawn(FX_SPARK,px,py);actor_free(a);return;
    }
    if(px<4||py<4||px>=room_px_w()-4||py>=room_px_h()-4||room_solid_px(px,py-4)) {
        if(boom){a->state=1;a->coll=1;}else{actor_free(a);return;}
    }
    handoff_tool_box(hitkind,px-5,py-10,px+5,py+1);
    for(i=1;i<ACTOR_MAX;i++) {
        Actor* e=&gActors[i];
        if(e->kind==AK_ENEMY&&!e->iframes&&legacy_enemy_hit_parts(e,px-5,py-10,px+5,py+1,hitkind,a->damage,a->dir)) {
            if(!boom){actor_free(a);return;}continue;
        }
        if(e->kind==AK_ENEMY&&!e->iframes&&actors_overlap(a,e)) {
            int hp=e->hp;legacy_item_hit(e,hitkind,a->damage,a->dir,Q8(1));
            if(boom&&e->kind==AK_ENEMY&&(e->hp<hp||e->iframes)) {e->kb_timer=60;e->kb_speed=0;}
            if(!boom&&kind!=LP_LIGHT){actor_free(a);return;}
        }
        if(boom&&(e->kind==AK_PICKUP||(e->kind==AK_OBJECT&&e->type==OBJ_LEGACY_PICKUP))&&actor_dist2(a,e)<12*12) {
            e->x=gPlayer->x;e->y=gPlayer->y;e->z=0;
        }
    }
    if(boom&&a->state&&actor_dist2(a,gPlayer)<10*10){actor_free(a);return;}
    if(t>=150){actor_free(a);return;}
}

bool8 legacy_items_actor_owned(const Actor* a) {return a->kind==AK_OBJECT&&(a->type==OBJ_LEGACY_PICKUP||a->type==OBJ_LEGACY_PROJECTILE);}
void legacy_items_actor_update(Actor* a) {
    if(a->type==OBJ_LEGACY_PROJECTILE){projectile_update(a);return;}
    if(a->timer<255)a->timer++;
    if(a->timer>6&&actors_overlap(a,gPlayer)) {
        int item=a->v[0];legacy_item_grant(item,1);sfx_play(SFX_ITEM);
        if(a->sub&&a->sub<=sPickupCount)sPickups[a->sub-1].owner=0;
        actor_free(a);
    }
}
void legacy_items_actor_draw(Actor* a) {
    if(a->type==OBJ_LEGACY_PROJECTILE && a->v[0]==LP_LIGHT) {
        int frame=a->dir==DIR_N?F_ARROW_N:a->dir==DIR_S?F_ARROW_S:F_ARROW_E;
        /* The existing cardinal arrow is centered on this projectile's
           actual small collision box. Its path/damage remain unchanged. */
        u16 tile=arrow_sheet_tile();
        if(tile)draw_sprite(PX(a->x)-8-gCamX,PX(a->y)-14-gCamY,SHEET_ARROW,tile,frame,a->dir==DIR_W,a->prio,sheets[SHEET_ARROW].pal);
        return;
    }
    int count=gOamCount;actor_draw(a);
    if(a->type==OBJ_LEGACY_PICKUP&&gOamCount>count){BIT_SET(gLegacyInventory.seen,a->v[0]);journal_note_legacy_item(a->v[0]);}
}

/* Status ownership is independent of actor.state: no capture, ice or jar
   action can overwrite a death, room transition or an existing conversation. */
void legacy_player_status_apply(int kind,int ticks) {
    int immune=handoff_immunities();
    if((unsigned)kind>=LPS_COUNT||ticks<=0)return;
    if((kind==LPS_BURN&&(immune&1))||(kind==LPS_FREEZE&&(immune&2))||(kind==LPS_SHOCK&&(immune&4)))return;
    s.status[kind]=MAX(s.status[kind],MIN(65535,ticks));
}
void legacy_player_status_clear(int kind) {if((unsigned)kind<LPS_COUNT)s.status[kind]=0;}
int legacy_player_status(int kind) {return (unsigned)kind<LPS_COUNT?s.status[kind]:0;}
void legacy_player_capture(Actor* captor,int ticks) {
    if(!captor||captor<gActors||captor>=gActors+ACTOR_MAX)return;
    s.capture_index=captor-gActors;s.capture_kind=captor->kind;s.capture_type=captor->type;
    legacy_player_status_apply(LPS_CAPTURE,ticks);
}
bool8 legacy_player_minish(void) {return s.minish!=0;}
bool8 legacy_player_submerged(void) {return s.dive&&room_type_px(PX(gPlayer->x),PX(gPlayer->y)-1)==TT_WATER;}
int legacy_player_clone_count(void) {return s.clones;}
bool8 legacy_clone_position(int index,int* x,int* y) {
    if((unsigned)index>=s.clones)return FALSE;
    *x=s.clone_x[index];*y=s.clone_y[index];return TRUE;
}
void legacy_player_on_hurt(void) {
    s.sword_charge=s.boots_charge=s.gust_charge=0;s.dash=s.spin=s.clones=s.clone_mode=0;
    bomb_charge_cancel();
}
int legacy_player_incoming_damage(int damage) {
    int i;
    if(s.dive&&room_type_px(PX(gPlayer->x),PX(gPlayer->y)-1)==TT_WATER)return 0;
    if(gPl.hp>0&&damage>=gPl.hp)for(i=0;i<4;i++)if(gLegacyInventory.bottles[i]==LI_BOTTLE_FAIRY) {
        gLegacyInventory.bottles[i]=0;gPl.hp=MIN(gPl.hp_max,32);gPlayer->iframes=90;
        fx_spawn(FX_SPARK,PX(gPlayer->x),PX(gPlayer->y)-12);sfx_play(SFX_ITEM);return 0;
    }
    return damage;
}
int legacy_player_outgoing_damage(int damage) {return damage;}
int legacy_player_walk_speed(int speed) {
    int surface=legacy_surface_at(PX(gPlayer->x),PX(gPlayer->y)-1);
    if(s.status[LPS_SLOW])speed=speed*2/3;
    if(s.sword_charge)speed=MIN(speed,Q8(.875));
    if(s.jar_held)speed=MIN(speed,Q8(.5));
    if(surface==LS_DUST||surface==LS_SWAMP)speed=MIN(speed,Q8(.75));
    if(surface==LS_SHALLOW)speed=MIN(speed,Q8(1));
    if(surface==LS_SLOPE_X||surface==LS_SLOPE_Y)speed=MAX(Q8(.5),speed-Q8(.3125));
    if(room_type_px(PX(gPlayer->x),PX(gPlayer->y)-1)==TT_WATER&&legacy_item_owned(LI_FLIPPERS))speed=gLegacyInventory.swim_upgrade?Q8(1):Q8(.75);
    return speed;
}
bool8 legacy_player_handles_floor(int type) {
    if(handoff_objects_support(PX(gPlayer->x),PX(gPlayer->y)-1))return TRUE;
    if(s.minish&&legacy_surface_at(PX(gPlayer->x),PX(gPlayer->y)-1)==LS_MINISH_GAP)return TRUE;
    return type==TT_WATER&&legacy_item_owned(LI_FLIPPERS);
}
static void manual_timers(void) {
    if(gPlayer->iframes)gPlayer->iframes--;
    if(gPl.item_cooldown)gPl.item_cooldown--;
    if(gPl.input_lock)gPl.input_lock--;
}
static void start_fall(bool8 water) {
    if(gPlayer->state!=PS_NORMAL)return;
    gPlayer->state=PS_FALL;gPlayer->sub=water;gPlayer->timer=36;
    gPlayer->z=gPlayer->zvel=0;gPl.sword_active=0;s.clones=0;
    sfx_play(SFX_FALL);
}
static void front_center(int distance,int* px,int* py) {
    int d=facing_to_dir(gPlayer->facing);
    *px=PX(gPlayer->x)+(d==DIR_E?distance:d==DIR_W?-distance:0);
    *py=PX(gPlayer->y)-4+(d==DIR_S?distance:d==DIR_N?-distance:0);
}
static void dig_front(void) {
    int x,y;front_center(13,&x,&y);int tx=x>>4,ty=y>>4,kind=legacy_surface_at(x,y);
    if(kind==LS_DIG||kind==LS_DIG_WALL||kind==LS_DUST) {
        clear_surface(tx,ty);sfx_play(SFX_SWORD);
        if(((tx*17+ty*31+gGame.seed)&7)==0)pickup_spawn(PK_GILT,x,y);
        if(((tx*13+ty*11+gGame.seed)&31)==1)pickup_spawn(PK_HEART,x,y);
    }else fx_spawn(FX_PUFF,x,y);
    handoff_tool_box(HTOOL_DIG,x-9,y-9,x+9,y+9);
    player_item_pose(EQ_MOLE_MITTS);gPl.item_cooldown=gLegacyInventory.dig_upgrade?6:12;
}
static bool8 use_bottle(int slot) {
    int content=gLegacyInventory.bottles[slot],x,y;
    if(!legacy_item_owned(LI_BOTTLE1+slot))return FALSE;
    if(!content) {
        int i;front_center(12,&x,&y);
        for(i=1;i<ACTOR_MAX;i++)if(gActors[i].kind==AK_OBJECT&&gActors[i].type==OBJ_LEGACY_PICKUP&&gActors[i].v[0]==LI_FAIRY&&actor_dist2(gPlayer,&gActors[i])<24*24) {
            actor_free(&gActors[i]);gLegacyInventory.bottles[slot]=LI_BOTTLE_FAIRY;sfx_play(SFX_ITEM);return TRUE;
        }
        if(room_type_px(x,y)==TT_WATER||legacy_surface_at(x,y)==LS_SHALLOW) {
            gLegacyInventory.bottles[slot]=LI_BOTTLE_WATER;sfx_play(SFX_ITEM);return TRUE;
        }
        return FALSE;
    }
    if(content==LI_BOTTLE_WATER||content==LI_BOTTLE_MINERAL_WATER) {
        front_center(16,&x,&y);
        if(legacy_surface_at(x,y)==LS_WATER_SPROUT) {
            Surface* cell=surface_record(x>>4,y>>4);
            if(!cell){legacy_surface_set(x>>4,y>>4,LS_WATER_SPROUT);cell=surface_record(x>>4,y>>4);}
            if(cell)cell->state=1;
            handoff_tool_box(LE_HIT_PACCI,x-8,y-8,x+8,y+8);fx_spawn(FX_SPARK,x,y);
        }else if(content==LI_BOTTLE_MINERAL_WATER&&legacy_surface_at(x,y)==LS_ICE_BLOCK)clear_surface(x>>4,y>>4);
        handoff_tool_box(content==LI_BOTTLE_MINERAL_WATER?34:33,x-8,y-8,x+8,y+8);
    }else if(content==LI_BOTTLE_RED_POTION)player_heal(gPl.hp_max);
    else if(content==LI_BOTTLE_BLUE_POTION)player_heal(40);
    else if(content==LI_BOTTLE_MILK||content==LI_BOTTLE_HALF_MILK)player_heal(40);
    else if(content==LI_BOTTLE_FAIRY)player_heal(32);
    else if(content==LI_BOTTLE_BUTTER)player_heal(8);
    else handoff_apply_item_effect(content,1);
    gLegacyInventory.bottles[slot]=content==LI_BOTTLE_MILK?LI_BOTTLE_HALF_MILK:0;
    player_item_pose(EQ_BOTTLE1+slot);sfx_play(SFX_ITEM);return TRUE;
}
static void gust_action(void) {
    u16 keys=keys_for(EQ_GUST_JAR);int x,y,i;
    s.jar_held=(keys&gKeysHeld)!=0&&gPlayer->state==PS_NORMAL&&!gPl.input_lock;
    if(s.jar_held) {
        if(s.gust_charge<240)s.gust_charge++;
        front_center(24,&x,&y);
        affect_box(x-11,y-14,x+11,y+10,LE_HIT_GUST_SMALL,0,0);
        for(i=1;i<ACTOR_MAX;i++) {
            Actor* a=&gActors[i];
            if(a->kind==AK_PICKUP&&actor_box_overlap(a,x-18,y-18,x+18,y+18))actor_move_free(a,Q8(1.5),actor_dir_to(a,gPlayer));
        }
        if((gFrame&7)==0) {
            front_center(16,&x,&y);
            if(legacy_surface_at(x,y)==LS_DUST)clear_surface(x>>4,y>>4);
            if(room_type_px(x,y)==TT_WEB)room_web_burn(x>>4,y>>4);
        }
    }else if(s.gust_charge) {
        int charge=s.gust_charge;s.gust_charge=0;
        if(gPlayer->state!=PS_NORMAL)return;
        front_center(charge>=240?32:24,&x,&y);
        affect_box(x-16,y-20,x+16,y+14,charge>=240?LE_HIT_GUST_BIG:LE_HIT_GUST_SMALL,charge>=120?2:0,Q8(2));
        if(charge>=120)projectile(LP_GUST,charge>=240?2:1);
        player_item_pose(EQ_GUST_JAR);gPl.item_cooldown=12;
    }
}
static void clone_combat(void) {
    int ci,ei,x0,y0,x1,y1;
    if(!s.clones||!s.clone_mode)return;
    bool8 sword=player_sword_box(&x0,&y0,&x1,&y1);
    int damage=handoff_outgoing_damage(legacy_player_outgoing_damage(gPl.sword_dmg));
    for(ci=0;ci<s.clones;ci++) {
        int dx=s.clone_x[ci]-PX(gPlayer->x),dy=s.clone_y[ci]-PX(gPlayer->y);
        Actor body=*gPlayer;body.x=Q16(s.clone_x[ci]);body.y=Q16(s.clone_y[ci]);
        if(sword) {
            handoff_tool_box(LE_HIT_SWORD,x0+dx,y0+dy,x1+dx,y1+dy);
            react_cut_box(x0+dx,y0+dy,x1+dx,y1+dy);
        }
        for(ei=1;ei<ACTOR_MAX;ei++) {
            Actor* e=&gActors[ei];if(e->kind!=AK_ENEMY)continue;
            if((e->flags&AF_HURTS)&&actors_overlap(e,&body)) {s.clones=s.clone_mode=0;return;}
            if(!sword||e->iframes)continue;
            if(legacy_enemy_hit_parts(e,x0+dx,y0+dy,x1+dx,y1+dy,LE_HIT_SWORD,damage,facing_to_dir(gPlayer->facing)))continue;
            if((e->flags&AF_HITTABLE)&&actor_box_overlap(e,x0+dx,y0+dy,x1+dx,y1+dy))legacy_item_hit(e,LE_HIT_SWORD,damage,actor_dir_to(&body,e),handoff_sword_knockback(Q8(1.5)));
        }
    }
}
static void split_update(int surface) {
    if(!(gLegacyInventory.skills&SKILL_FOUR)){s.clones=0;return;}
    if(!s.clone_mode&&surface==LS_CLONE_PLATE&&s.sword_charge>=(gLegacyInventory.skills&SKILL_FAST_SPLIT?40:80)) {
        int x=PX(gPlayer->x),y=PX(gPlayer->y),i,cap=MIN(3,MAX(1,gLegacyInventory.sword_level-1));
        for(i=0;i<s.clones;i++)if(ABS_VALUE(s.clone_x[i]-x)<8&&ABS_VALUE(s.clone_y[i]-y)<8)break;
        if(!s.split_ready&&s.clones<cap&&i==s.clones) {
            s.clone_x[s.clones]=x;s.clone_y[s.clones]=y;s.clones++;s.split_ready=1;sfx_play(SFX_ITEM);
        }
    }else if(surface!=LS_CLONE_PLATE)s.split_ready=0;
    if(s.clones&&s.clone_mode) {
        int dx=PX(gPlayer->x)-s.before_x,dy=PX(gPlayer->y)-s.before_y,i;
        for(i=0;i<s.clones;i++) {
            if(room_box_solid(s.clone_x[i]+dx-3,s.clone_y[i]+dy-5,s.clone_x[i]+dx+3,s.clone_y[i]+dy)) {s.clones=s.clone_mode=0;break;}
            s.clone_x[i]+=dx;s.clone_y[i]+=dy;
        }
        if(s.clones)for(i=0;i<s.clones;i++)handoff_tool_box(LE_HIT_SHIELD,s.clone_x[i]-6,s.clone_y[i]-6,s.clone_x[i]+6,s.clone_y[i]+1);
    }
}

bool8 legacy_items_pre_player(void) {
    Actor* a=gPlayer;int i,dir=input_dir(),surface=legacy_surface_at(PX(a->x),PX(a->y)-1);
    s.before_x=PX(a->x);s.before_y=PX(a->y);s.before_fx=a->x;s.before_fy=a->y;
    for(i=0;i<LPS_COUNT;i++)if(s.status[i])s.status[i]--;
    if(handoff_mobility_busy()) {
        s.dash=s.spin=s.clones=s.clone_mode=s.dive=s.jar_held=0;s.sword_charge=s.gust_charge=s.boots_charge=0;
        bomb_charge_cancel();return FALSE;
    }
    if(a->state==PS_DEAD||a->state==PS_FALL||a->state==PS_TALK||a->state==PS_ITEMGET||a->state==PS_SWALLOWED||a->state==PS_CLIMB)return FALSE;
    if(s.status[LPS_CAPTURE]) {
        Actor* c=&gActors[s.capture_index];
        if(c->kind!=s.capture_kind||c->type!=s.capture_type||!c->hp)s.status[LPS_CAPTURE]=0;
        else {
            if(gKeysDown&(KEY_A|KEY_B|KEY_R))s.status[LPS_CAPTURE]=MAX(0,s.status[LPS_CAPTURE]-12);
            a->x=c->x;a->y=c->y;gPl.sword_active=0;manual_timers();return TRUE;
        }
    }
    if(s.status[LPS_FREEZE]||s.status[LPS_SHOCK]) {
        if(gKeysDown&(KEY_A|KEY_B|KEY_R)) {
            int st=s.status[LPS_FREEZE]?LPS_FREEZE:LPS_SHOCK;s.status[st]=MAX(0,s.status[st]-5);
        }
        gPl.sword_active=0;manual_timers();return TRUE;
    }
    if(s.dive) {gKeysDown&=~(KEY_A|KEY_B|KEY_L|KEY_R);gPl.sword_active=0;gPl.shield_up=0;}
    if(s.status[LPS_BURN]&&a->state==PS_NORMAL) {
        if(gKeysDown&KEY_R)s.status[LPS_BURN]=0;
        else {
            int burn_dir=dir==DIR_NONE?facing_to_dir(a->facing):dir;
            player_external_walk_tick(Q8(3),burn_dir);actor_move(a,a->speed,burn_dir);manual_timers();
            gPl.sword_active=0;gKeysDown&=~(KEY_A|KEY_B|KEY_L);return TRUE;
        }
    }
    if(s.status[LPS_SILENCE])gKeysDown&=~sword_keys();
    if(s.status[LPS_DRUGGED]) {
        u16 held=gKeysHeld&(KEY_UP|KEY_DOWN|KEY_LEFT|KEY_RIGHT);
        gKeysHeld=(gKeysHeld&~held)|((held&KEY_UP)?KEY_DOWN:0)|((held&KEY_DOWN)?KEY_UP:0)|((held&KEY_LEFT)?KEY_RIGHT:0)|((held&KEY_RIGHT)?KEY_LEFT:0);
    }
    if(s.spin) {
        int px=PX(a->x),py=PX(a->y),radius=gLegacyInventory.skills&SKILL_GREAT?32:24;
        int damage=gLegacyInventory.sword_level>=3?8:gLegacyInventory.sword_level>=2?6:4;
        manual_timers();a->state=PS_NORMAL;gPl.sword_active=0;a->speed=0;
        a->facing=(s.spin_face+((s.spin_age/4)&3))&3;
        spin_hit(px,py-8,radius,handoff_outgoing_damage(damage));
        react_cut_box(px-radius,py-radius,px+radius,py+radius);
        if(++s.spin_age>=s.spin){s.spin=0;a->facing=s.spin_face;}return TRUE;
    }
    if(s.dash) {
        manual_timers();a->state=PS_NORMAL;gPl.sword_active=0;
        if(!(keys_for(EQ_PEGASUS_BOOTS)&gKeysHeld)){s.dash=0;return FALSE;}
        a->speed=s.minish?Q8(2.5):Q8(3);
        player_external_walk_tick(a->speed,facing_to_dir(a->facing));
        if(actor_move(a,a->speed,facing_to_dir(a->facing))) {
            int x,y;front_center(14,&x,&y);
            if(legacy_surface_at(x,y)==LS_DASH_WALL){clear_surface(x>>4,y>>4);sfx_play(SFX_SWORD);}
            else {s.dash=0;a->state=PS_JUMP;a->zvel=Q16(2);a->dir=(facing_to_dir(a->facing)+16)&31;a->speed=Q8(1);sfx_play(SFX_BUMP);}
        }
        if(gLegacyInventory.skills&SKILL_DASH) {
            int x,y;front_center(14,&x,&y);affect_box(x-9,y-12,x+9,y+7,LE_HIT_SWORD,handoff_outgoing_damage(4),Q8(2));
        }
        return TRUE;
    }
    if(surface==LS_MINISH_PORTAL&&(gKeysDown&KEY_R)&&a->state==PS_NORMAL) {
        s.minish^=1;s.clones=0;fx_spawn(FX_SPARK,PX(a->x),PX(a->y)-8);sfx_play(SFX_ITEM);gKeysDown&=~KEY_R;
    }
    if(surface==LS_SPRING&&(gKeysDown&KEY_R)) {
        Surface* cell=surface_record(PX(a->x)>>4,(PX(a->y)-1)>>4);
        if(cell&&cell->state) {a->state=PS_JUMP;a->zvel=Q16(1.625);a->dir=facing_to_dir(a->facing);a->speed=Q8(.46875);gKeysDown&=~KEY_R;}
    }
    if(s.minish&&(surface==LS_CLIMB||surface==LS_LADDER))return FALSE;
    if(surface==LS_WATER_SPROUT) {
        Surface* cell=surface_record(PX(a->x)>>4,(PX(a->y)-1)>>4);
        if(cell&&cell->state&&dir!=DIR_NONE)actor_move(a,Q8(.75),DIR_N);
    }
    return FALSE;
}

void legacy_items_post_player(void) {
    if(handoff_mobility_busy())return;
    Actor* a=gPlayer;int px=PX(a->x),py=PX(a->y)-1,surface=legacy_surface_at(px,py);
    if(a->state==PS_DEAD||a->state==PS_FALL||a->state==PS_CLIMB)return;
    if(a->state==PS_NORMAL&&!a->z) {
        int type=room_type_px(px,py);
        if((type==TT_PIT||type==TT_WATER)&&!legacy_player_handles_floor(type)) {start_fall(type==TT_WATER);return;}
        if(surface==LS_ICE) {
            int dx=(a->x-s.before_fx)>>8,dy=(a->y-s.before_fy)>>8;
            s.ice_x=(s.ice_x*7+dx)/8;s.ice_y=(s.ice_y*7+dy)/8;
            a->x=s.before_fx;a->y=s.before_fy;
            if(s.ice_x)actor_move(a,ABS_VALUE(s.ice_x),s.ice_x>0?DIR_E:DIR_W);
            if(s.ice_y)actor_move(a,ABS_VALUE(s.ice_y),s.ice_y>0?DIR_S:DIR_N);
        }else s.ice_x=s.ice_y=0;
        if(surface>=LS_CONVEYOR_N&&surface<=LS_CONVEYOR_W)actor_move(a,Q8(.5),(surface-LS_CONVEYOR_N)*8);
        if(surface==LS_SWAMP&&input_dir()==DIR_NONE) {if(++s.sink>=60){s.sink=0;start_fall(TRUE);}}
        else s.sink=0;
        if(surface==LS_LAVA&&!handoff_objects_support(px,py)&&!a->iframes) {player_hurt(4,DIR_S);legacy_player_status_apply(LPS_BURN,90);}
        if(surface==LS_CRUMBLE) {
            Surface* c=surface_record(px>>4,py>>4);
            if(!c){legacy_surface_set(px>>4,py>>4,LS_CRUMBLE);c=surface_record(px>>4,py>>4);}
            if(c&&c->state<255&&++c->state>=8){
                c->kind=LS_NONE;
                room_change(px>>4,py>>4,gGame.area==AREA_CREAM?MT_CREAM_PIT_S0+gCreamRoom.stage*(MT_CREAM_PIT_S1-MT_CREAM_PIT_S0):MT_LH_MOB_PIT);
                fx_spawn(FX_PUFF,px,py);start_fall(FALSE);
            }
        }
        if(room_type_px(px,py)==TT_WATER&&legacy_item_owned(LI_FLIPPERS)) {
            if((gKeysDown&KEY_A)&&!s.dive){s.dive=90;gKeysDown&=~KEY_A;}
            if(s.dive)s.dive--;
            if((gFrame&15)==0)fx_spawn(FX_PUFF,px,py+1);
        }else s.dive=0;
        if(surface==LS_SHALLOW&&(gFrame&15)==0&&input_dir()!=DIR_NONE)fx_spawn(FX_PUFF,px,py+1);
    }
    if(s.status[LPS_BURN]&&(gFrame%30)==0&&!a->iframes)player_hurt(1,DIR_NONE);
    if((gLegacyInventory.skills&SKILL_DOWN)&&(sword_keys()&gKeysHeld)&&a->state==PS_JUMP&&a->zvel<0&&PX(a->z)<=16) {
        affect_box(px-10,py-12,px+10,py+4,LE_HIT_SWORD,handoff_outgoing_damage(gLegacyInventory.sword_level>=3?6:4),Q8(1));
    }
    if((gLegacyInventory.skills&SKILL_ROLL)&&a->state==PS_ROLL&&a->timer>=4&&a->timer<16) {
        int x,y;front_center(14,&x,&y);
        int along=a->facing==FACE_N||a->facing==FACE_S;
        affect_box(x-(along?4:8),y-(along?8:4),x+(along?4:8),y+(along?8:4),LE_HIT_SWORD,handoff_outgoing_damage(gLegacyInventory.sword_level>=4?6:4),Q8(1.5));
    }
    split_update(surface);clone_combat();
}

void legacy_items_update(void) {
    if(handoff_mobility_busy())return;
    Actor* a=gPlayer;int i,px=PX(a->x),py=PX(a->y),surface=legacy_surface_at(px,py-1);
    u16 sk=sword_keys(),held=sk&gKeysHeld;
    /* Preserve the selected step-and-cut's ordinary timing and hitbox.
       Charge begins during recovery, and only the new release spin takes
       movement ownership; a tap always remains the existing swing. */
    if((gLegacyInventory.skills&(SKILL_SPIN|SKILL_FOUR))&&!s.spin&&!s.status[LPS_SILENCE]&&(a->state==PS_NORMAL||a->state==PS_ATTACK)) {
        if(held) {if(s.sword_charge<240)s.sword_charge++;}
        else if(s.sword_charge) {
            int need=gLegacyInventory.skills&SKILL_FAST_SPIN?40:80;
            if(s.clones&&!s.clone_mode)s.clone_mode=1;
            else if(s.sword_charge>=need&&(gLegacyInventory.skills&SKILL_SPIN)) {
                s.spin=gLegacyInventory.skills&SKILL_LONG_SPIN?68:34;s.spin_age=0;s.spin_face=a->facing;
                a->state=PS_NORMAL;gPl.sword_active=0;sfx_play(SFX_SWORD);
            }
            s.sword_charge=0;
        }
    }else if(!held)s.sword_charge=0;
    if(gPl.sword_active&&!s.beam_latch) {
        bool8 full=gPl.hp==gPl.hp_max||handoff_beam_any_health();
        bool8 peril=(gLegacyInventory.skills&SKILL_PERIL)&&gPl.hp<=8;
        if(((gLegacyInventory.skills&SKILL_BEAM)&&full)||peril)projectile(LP_BEAM,handoff_outgoing_damage(2));
        s.beam_latch=1;
        if(gLegacyInventory.skills&SKILL_ROCK) {
            int x0,y0,x1,y1,tx,ty;
            if(player_sword_box(&x0,&y0,&x1,&y1))for(ty=y0>>4;ty<=y1>>4;ty++)for(tx=x0>>4;tx<=x1>>4;tx++) {
                int type=room_type(tx,ty);
                if(type==TT_LIFT1)room_break_lift(tx,ty);
            }
            int x,y;front_center(16,&x,&y);if(legacy_surface_at(x,y)==LS_DASH_WALL)clear_surface(x>>4,y>>4);
        }
    }
    if(a->state!=PS_ATTACK&&!gPl.sword_active)s.beam_latch=0;
    if(gPl.lamp_timer) {
        int x0,y0,x1,y1;
        if(player_lamp_box(&x0,&y0,&x1,&y1))for(i=1;i<ACTOR_MAX;i++) {
            Actor* e=&gActors[i];if(e->kind==AK_ENEMY&&e->type>=LEGACY_ENEMY_BASE&&actor_box_overlap(e,x0,y0,x1,y1))legacy_item_hit(e,LE_HIT_LANTERN,2,facing_to_dir(a->facing),Q8(1));
        }
    }
    if(gPl.shield_up) {
        int x,y;front_center(11,&x,&y);affect_box(x-8,y-12,x+8,y+5,LE_HIT_SHIELD,0,Q8(1));
    }
    if(s.status[LPS_FREEZE]||s.status[LPS_SHOCK]||s.status[LPS_CAPTURE]||s.dive)return;
    gust_action();
    if(a->state!=PS_NORMAL||gPl.input_lock||s.spin||s.dash||gBombChargeKey)return;
    {
        u16 boots=keys_for(EQ_PEGASUS_BOOTS);
        if(boots&gKeysHeld) {
            if(s.boots_charge<16)s.boots_charge++;
            if(s.boots_charge==16){s.dash=1;sfx_play(SFX_ROLL);return;}
        }else s.boots_charge=0;
    }
    if(gPl.item_cooldown)return;
    if(keys_for(EQ_MOLE_MITTS)&gKeysHeld){dig_front();return;}
    if(gKeysDown&keys_for(EQ_BOOMERANG)) {
        if(!actor_find(AK_OBJECT,OBJ_LEGACY_PROJECTILE))projectile(LP_BOOM,0);
        player_item_pose(EQ_BOOMERANG);gPl.item_cooldown=12;
    }else if(gKeysDown&keys_for(EQ_MAGIC_BOOMERANG)) {
        if(!actor_find(AK_OBJECT,OBJ_LEGACY_PROJECTILE))projectile(LP_MAGIC,0);
        player_item_pose(EQ_MAGIC_BOOMERANG);gPl.item_cooldown=12;
    }else if(gKeysDown&keys_for(EQ_PACCI_CANE)) {
        projectile(LP_PACCI,handoff_outgoing_damage(2));player_item_pose(EQ_PACCI_CANE);gPl.item_cooldown=16;
    }else if(gKeysDown&keys_for(EQ_FIRE_ROD)) {
        projectile(LP_FIRE,handoff_outgoing_damage(4));player_item_pose(EQ_FIRE_ROD);gPl.item_cooldown=20;
    }else if(gKeysDown&keys_for(EQ_LIGHT_ARROW)) {
        if(gPl.arrows&&projectile(LP_LIGHT,handoff_outgoing_damage(4))) {gPl.arrows--;player_item_pose(EQ_LIGHT_ARROW);gPl.item_cooldown=legacy_item_owned(LI_ARROW_BUTTERFLY)?8:16;}
        else sfx_play(SFX_BUMP);
    }else if(gKeysDown&keys_for(EQ_OCARINA)) {
        if(gGame.area!=AREA_SEWER)player_swallow();else sfx_play(SFX_SECRET);
        player_item_pose(EQ_OCARINA);gPl.item_cooldown=30;
    }else for(i=0;i<4;i++)if(gKeysDown&keys_for(EQ_BOTTLE1+i)) {
        if(use_bottle(i))gPl.item_cooldown=24;else sfx_play(SFX_BUMP);break;
    }
    (void)surface;
}

static void draw_tool_frame(int frame,int x,int y,int priority) {
    if(!sToolTile)sToolTile=sprite_load_sheet(SHEET_HANDOFF_TOOL_FX);
    if(sToolTile)draw_sprite(x-8-gCamX,y-8-gCamY,SHEET_HANDOFF_TOOL_FX,sToolTile,frame,0,priority,sheets[SHEET_HANDOFF_TOOL_FX].pal);
}
bool8 legacy_player_draw_override(void) {
    int f,pose;
    if(s.dive) {
        draw_tool_frame(24+((gFrame>>3)&1),PX(gPlayer->x),PX(gPlayer->y)-4,2);return TRUE;
    }
    if(!s.minish)return FALSE;
    if(gPlayer->state==PS_DEAD)return FALSE;
    if(!sMiniTile)sMiniTile=sprite_load_sheet(SHEET_HANDOFF_MINISH);
    if(!sMiniTile)return FALSE;
    pose=gPlayer->state==PS_ROLL?3:gPlayer->state==PS_HURT?4:gPlayer->state==PS_JUMP?5:gPlayer->state==PS_FALL?6:gPlayer->speed?1+((gFrame>>3)&1):0;
    f=gPlayer->facing*7+pose;
    draw_sprite(PX(gPlayer->x)-4-gCamX,PX(gPlayer->y)-16-PX(gPlayer->z)-gCamY,SHEET_HANDOFF_MINISH,sMiniTile,f,0,gPlayer->prio,sheets[SHEET_HANDOFF_MINISH].pal);
    return TRUE;
}
void legacy_items_draw(void) {
    Actor* a=gPlayer;int px=PX(a->x),py=PX(a->y)-PX(a->z),i;
    if(a->state==PS_DEAD)return;
    if((gLegacyInventory.skills&SKILL_ROLL)&&a->state==PS_ROLL&&a->timer>=4&&a->timer<16) {
        int x,y;front_center(14,&x,&y);draw_tool_frame(20+a->facing,x,y,1);
    }
    if(s.spin) {
        int dir=(s.spin_age*32/17)&31,r=gLegacyInventory.skills&SKILL_GREAT?28:20;
        int x=px+(sin_table[(dir*8)&255]*r>>14),y=py-8-(sin_table[((dir*8)+64)&255]*r>>14);
        draw_tool_frame(14+((s.spin_age>>2)&1),x,y,1);
    }
    if(s.sword_charge>=(gLegacyInventory.skills&SKILL_FAST_SPIN?40:80))draw_tool_frame(16+((gFrame>>3)&1),px,py-15,1);
    if(s.jar_held) {
        int x,y;front_center(17,&x,&y);draw_tool_frame(12+((gFrame>>2)&1),x,y,2);
    }
    if(s.status[LPS_FREEZE]||s.status[LPS_SHOCK])draw_tool_frame(18+((gFrame>>3)&1),px,py-8,1);
    for(i=0;i<s.clones;i++) {
        int x=s.clone_x[i],y=s.clone_y[i];
        player_draw_clone(x,y);
        draw_tool_frame(16+((gFrame>>4)&1),x,y-20,1);
    }
}
void legacy_items_room_reset(void) {
    u8 mini=s.minish;
    memset(&s,0,sizeof(s));s.minish=mini;
    sToolTile=sMiniTile=0;
    sPickupCount=0;memset(sPickups,0,sizeof(sPickups));bomb_charge_cancel();
    /* sSurfaces belongs to the newly built room and intentionally survives. */
}
