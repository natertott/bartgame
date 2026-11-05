/* Original translations of three curated TMC mechanics, now admitted into
   production encounters. LAB1 retains isolated demonstration controls only.
   Numbers/adaptations and production safety rules are recorded in the notes. */
#include "gba.h"
#include "video.h"
#include "util.h"
#include "room.h"
#include "actor.h"
#include "enemy.h"
#include "enemy_prototypes.h"
#include "player.h"
#include "objects.h"
#include "npc.h"
#include "sound.h"
#include "game.h"
#include "text.h"

u16 gEnemyPrototypeEvents[EP_EVENT_COUNT];
#if BART_ENEMY_LAB
u8 gEnemyPrototypeRequest, gEnemyPrototypeCase, gEnemyPrototypeSpawned;
s16 gEnemyPrototypePositions[8];
#endif

enum { PO_IDLE, PO_WALK1, PO_WALK2, PO_TELL, PO_ATTACK, PO_RECOVER, PO_HURT, PO_BURIED };

static void pose(Actor* e, int p) {
    e->frame = p * 4 + e->facing;
    e->hflip = 0;
}

/* A dry, walkable footprint, away from entrances and authored features.
   This reads semantic collision, never edits procedural room geometry. */
static bool8 dry_footprint(int x, int y) {
    if (x < 24 || y < 32 || x > room_px_w()-24 || y > room_px_h()-16)
        return FALSE;
    if (room_type_px(x-6,y-2) != TT_FLOOR || room_type_px(x+6,y-2) != TT_FLOOR ||
        room_type_px(x-6,y-10) != TT_FLOOR || room_type_px(x+6,y-10) != TT_FLOOR ||
        room_box_solid(x-7,y-12,x+6,y-1))
        return FALSE;
    return TRUE;
}

static bool8 dry_safe(int x,int y) {
    if (!dry_footprint(x,y)) return FALSE;
#if BART_FOREST_VARIANT >= 19
    if (gGame.area == AREA_FOREST && room_canopy_scene_reserved(x>>4,(y-4)>>4))
        return FALSE;
#endif
    return TRUE;
}

/* Spawn markers already belong to the generated reachable component. Repair
   only a near-edge native footprint, without teleporting across an obstacle. */
bool8 enemy_prototypes_spawn_point(int type,int* px,int* py) {
    static const s8 offset[][2]={{0,0},{0,-4},{0,4},{-4,0},{4,0},
        {0,-8},{0,8},{-8,0},{8,0},{-8,-8},{8,-8},{-8,8},{8,8}};
    int i,ox=*px,oy=*py;
    for(i=0;i<(int)(sizeof(offset)/sizeof(offset[0]));i++) {
        int x=ox+offset[i][0],y=oy+offset[i][1];
        if(!dry_safe(x,y)) continue;
        if(type==EN_RELIQUARY_SNOUT &&
           (!dry_footprint(x-16,y) || !dry_footprint(x+16,y) ||
            !dry_footprint(x,y-16) || !dry_footprint(x,y+16))) continue;
        *px=x;*py=y;return TRUE;
    }
    return FALSE;
}

static bool8 move_dry(Actor* e, int speed) {
    s32 ox=e->x, oy=e->y;
    actor_move(e,speed,e->dir);
    if (!dry_footprint(PX(e->x),PX(e->y))) {
        e->x=ox; e->y=oy;
        return FALSE;
    }
    return !e->coll;
}

void enemy_prototypes_recoil(Actor* e) {
    int dir=e->dir;
    e->dir=e->kb_dir;
    move_dry(e,e->kb_speed);
    e->dir=dir;
}

/* Cardinal line-up is the warning: the charge cannot steer after telling. */
static int charge_line(const Actor* e) {
    int dx=PX(gPlayer->x)-PX(e->x),dy=PX(gPlayer->y)-PX(e->y);
    int dir,dist,step,x=PX(e->x),y=PX(e->y);
    if (ABS(dx)<=8 && ABS(dy)>=20 && ABS(dy)<=112) {
        dir=dy<0?DIR_N:DIR_S; dist=ABS(dy);
    } else if (ABS(dy)<=8 && ABS(dx)>=20 && ABS(dx)<=112) {
        dir=dx<0?DIR_W:DIR_E; dist=ABS(dx);
    } else return DIR_NONE;
    for (step=8;step<dist;step+=8) {
        int sx=x+(dir==DIR_E?step:dir==DIR_W?-step:0);
        int sy=y+(dir==DIR_S?step:dir==DIR_N?-step:0);
        if (!dry_footprint(sx,sy)) return DIR_NONE;
    }
    return dir;
}

static void begin(Actor* e,int state,int ticks,int p) {
    e->state=state; e->timer=ticks; pose(e,p);
}

void enemy_prototypes_init(Actor* e) {
    e->facing=dir_to_facing(actor_dir_to(e,gPlayer));
    e->dir=facing_to_dir(e->facing);
    /* Movement owns vx/vy. Keep the original dry spawn anchor in four free
       bytes instead, so a later burrow survives exposed motion and recoil. */
    e->v[0]=PX(e->x)&255;e->v[1]=(PX(e->x)>>8)&255;
    e->v[2]=PX(e->y)&255;e->v[3]=(PX(e->y)>>8)&255;
    if (e->type==EN_PROTO_LEEVER) {
        e->flags &= ~(AF_HITTABLE|AF_HURTS);
        begin(e,EP_BURIED,90,PO_BURIED);
    } else begin(e,EP_ROAM,24,PO_IDLE);
}

static void rope_update(Actor* e) {
    switch (e->state) {
        case EP_ROAM: {
            int d=charge_line(e);
            if (d!=DIR_NONE) {
                e->dir=d; e->facing=dir_to_facing(d);
                begin(e,EP_TELL,30,PO_TELL);
                break;
            }
            if (!move_dry(e,Q8(0.5))) {
                e->dir=(e->dir+8)&31;
                e->facing=dir_to_facing(e->dir);
            }
            pose(e,(gFrame&8)?PO_WALK1:PO_WALK2);
            break;
        }
        case EP_TELL:
            pose(e,PO_TELL);
            if (--e->timer==0) {
                begin(e,EP_ATTACK,36,PO_ATTACK);
                gEnemyPrototypeEvents[EP_EVENT_ROPE_CHARGE]++;
            }
            break;
        case EP_ATTACK:
            pose(e,PO_ATTACK);
            if (!move_dry(e,Q8(1.625)) || --e->timer==0)
                begin(e,EP_RECOVER,36,PO_RECOVER);
            break;
        case EP_RECOVER:
            pose(e,PO_RECOVER);
            if (--e->timer==0) begin(e,EP_ROAM,24,PO_IDLE);
            break;
    }
}

/* The visible mound always precedes emergence by24 updates. Relocation only
   occurs while buried, at least40px from Bloom, and never on wet/pit/feature
   tiles. Twelve bounded local candidates avoid a per-frame room scan. */
static bool8 reachable_dry(int x,int y) {
    int i,ox=PX(gPlayer->x),oy=PX(gPlayer->y),dx=x-ox,dy=y-oy;
    int steps=(MAX(ABS(dx),ABS(dy))+3)/4;
    int qx,qy,rx,ry,ex=0,ey=0,sx=dx<0?-1:1,sy=dy<0?-1:1;
    if (!dry_footprint(ox,oy)) return FALSE;
    if (!steps) return TRUE;
    /* Exact rational DDA: these are the same C-truncated coordinates as
       ox+dx*i/steps,oy+dy*i/steps, without two divisions at every sample.
       Signed quotients and positive residual carries preserve negative rays. */
    qx=dx/steps;qy=dy/steps;
    rx=ABS(dx)-ABS(qx)*steps;ry=ABS(dy)-ABS(qy)*steps;
    for (i=1;i<=steps;i++) {
        ox+=qx;oy+=qy;ex+=rx;ey+=ry;
        if(ex>=steps) {ox+=sx;ex-=steps;}
        if(ey>=steps) {oy+=sy;ey-=steps;}
        if (!dry_footprint(ox,oy)) return FALSE;
    }
    return TRUE;
}

static bool8 maw_emergence(Actor* e) {
    int i;
    for (i=0;i<12;i++) {
        int d=rand_range(32),r=48+rand_range(49);
        int x=PX(gPlayer->x)+(SIN(d*8)*r>>14);
        int y=PX(gPlayer->y)-(COS(d*8)*r>>14);
        int dx=x-PX(gPlayer->x),dy=y-PX(gPlayer->y);
        if (dx*dx+dy*dy<40*40 || !dry_safe(x,y) || !reachable_dry(x,y)) continue;
        e->x=Q16(x);e->y=Q16(y);e->v[5]=0;
        return TRUE;
    }
    if (actor_dist2(e,gPlayer)>=40*40 && dry_safe(PX(e->x),PX(e->y)) &&
        reachable_dry(PX(e->x),PX(e->y))) {e->v[5]=0;return TRUE;}
#if !BART_ENEMY_LAB
    /* The lab intentionally exposes strict admission failures. A real last
       wave must not stay buried forever merely because sight is obstructed.
       Try readable close dry sites, then the original validated floor anchor.
       A player camping that anchor still receives the full harmless24 tell. */
    if (++e->v[5]>=3) {
        static const s8 radius[]={48,32,16};
        static const s8 axis[4][2]={{0,-1},{1,0},{0,1},{-1,0}};
        int r,d;
        for(r=0;r<3;r++) for(d=0;d<4;d++) {
            int x=PX(gPlayer->x)+axis[d][0]*radius[r];
            int y=PX(gPlayer->y)+axis[d][1]*radius[r];
            if(dry_safe(x,y) && reachable_dry(x,y)) {
                e->x=Q16(x);e->y=Q16(y);e->v[5]=0;return TRUE;
            }
        }
        {
            int ax=e->v[0]|(e->v[1]<<8),ay=e->v[2]|(e->v[3]<<8);
            if(dry_safe(ax,ay)) {
                e->x=Q16(ax);e->y=Q16(ay);e->v[5]=0;return TRUE;
            }
        }
    }
#endif
    gEnemyPrototypeEvents[EP_EVENT_UNSAFE]++;
    return FALSE;
}

static void maw_update(Actor* e) {
    switch (e->state) {
        case EP_BURIED:
            pose(e,PO_BURIED);
            if (--e->timer==0) {
                if (!maw_emergence(e)) { e->timer=30; break; }
                e->facing=dir_to_facing(actor_dir_to(e,gPlayer));
                begin(e,EP_EMERGE,24,PO_TELL);
                gEnemyPrototypeEvents[EP_EVENT_MAW_EMERGE]++;
            }
            break;
        case EP_EMERGE:
            pose(e,e->timer>12?PO_TELL:PO_RECOVER);
            if (--e->timer==0) {
                e->flags |= AF_HITTABLE|AF_HURTS;
                e->dir=actor_dir_to(e,gPlayer);
                e->facing=dir_to_facing(e->dir);
                begin(e,EP_EXPOSED,180,PO_ATTACK);
            }
            break;
        case EP_EXPOSED:
            if ((e->timer&7)==0) {
                e->dir=actor_dir_to(e,gPlayer);
                e->facing=dir_to_facing(e->dir);
            }
            move_dry(e,Q8(0.5));
            pose(e,(gFrame&8)?PO_WALK1:PO_WALK2);
            if (--e->timer==0) {
                e->flags &= ~AF_HURTS;
                begin(e,EP_RETREAT,24,PO_RECOVER);
            }
            break;
        case EP_RETREAT:
            pose(e,PO_RECOVER);
            if (--e->timer==0) {
                e->flags &= ~(AF_HITTABLE|AF_HURTS);
                begin(e,EP_BURIED,240,PO_BURIED);
                gEnemyPrototypeEvents[EP_EVENT_MAW_BURY]++;
            }
            break;
    }
}

static void snout_update(Actor* e) {
    switch (e->state) {
        case EP_ROAM:
            if ((e->timer&7)==0) {
                e->facing=dir_to_facing(actor_dir_to(e,gPlayer));
                e->dir=facing_to_dir(e->facing);
            }
            move_dry(e,Q8(1));
            pose(e,(gFrame&8)?PO_WALK1:PO_WALK2);
            if (--e->timer==0) {
                e->facing=dir_to_facing(actor_dir_to(e,gPlayer));
                e->dir=facing_to_dir(e->facing);
                begin(e,EP_TELL,60,PO_TELL);
            }
            break;
        case EP_TELL:
            pose(e,PO_TELL);
            if (--e->timer==0) {
                begin(e,EP_ATTACK,30,PO_ATTACK);
                gEnemyPrototypeEvents[EP_EVENT_SNOUT_CHARGE]++;
            }
            break;
        case EP_ATTACK:
            pose(e,PO_ATTACK);
            if (!move_dry(e,Q8(3)) || --e->timer==0)
                begin(e,EP_RECOVER,30,PO_RECOVER);
            break;
        case EP_RECOVER:
            /* Keep facing locked, so walking around its armor has a payoff. */
            pose(e,PO_RECOVER);
            if (--e->timer==0) begin(e,EP_ROAM,24,PO_IDLE);
            break;
    }
}

void enemy_prototypes_update(Actor* e) {
    if (e->v[4]) e->v[4]--;
    switch (e->type) {
        case EN_PROTO_ROPE: rope_update(e); break;
        case EN_PROTO_LEEVER: maw_update(e); break;
        case EN_PROTO_HELMASAUR: snout_update(e); break;
    }
}

bool8 enemy_prototypes_accept_hit(Actor* e,int damage,int from_dir) {
    int delta;
    (void)damage;
    if (!(e->flags&AF_HITTABLE)) return FALSE;
    if (e->type==EN_PROTO_HELMASAUR) {
        /* from_dir travels toward the enemy. Reverse it to find the weapon's
           side relative to its head. The new90-degree guard is an adaptation;
           sword/arrow/bomb all use the existing damage interface consistently. */
        delta=((from_dir+16)-facing_to_dir(e->facing))&31;
        if (delta<=4 || delta>=28) {
            if (!e->v[4]) {
                fx_spawn(FX_CLANG,PX(e->x),PX(e->y)-8);
                sfx_play(SFX_BUMP);
                gEnemyPrototypeEvents[EP_EVENT_ARMOR_BLOCK]++;
                e->v[4]=6;
            }
            return FALSE;
        }
    }
    pose(e,PO_HURT);
    gEnemyPrototypeEvents[EP_EVENT_HIT]++;
    return TRUE;
}

#if BART_ENEMY_LAB
/* Find the nearest safe native floor footprint. Prefer an open cross, while
   preserving the entire actual generated room and all its tile artwork. */
static bool8 fixture_floor(int tx,int ty,int min_player,int* outx,int* outy) {
    int x,y,best=0x7FFFFFFF,bx=0,by=0;
    for (y=32;y<room_px_h()-16;y+=8) for (x=24;x<room_px_w()-24;x+=8) {
        int i,score,dx=x-tx,dy=y-ty;
        if (!dry_safe(x,y)) continue;
        if (min_player) {
            int px=x-PX(gPlayer->x),py=y-PX(gPlayer->y);
            if (px*px+py*py<min_player*min_player) continue;
        }
        for (i=1;i<ACTOR_MAX;i++) {
            Actor* a=&gActors[i];
            int ax=x-PX(a->x),ay=y-PX(a->y);
            if (a->kind==AK_ENEMY && ax*ax+ay*ay<28*28) break;
        }
        if (i!=ACTOR_MAX) continue;
        score=dx*dx+dy*dy;
        if (!dry_footprint(x-16,y) || !dry_footprint(x+16,y) ||
            !dry_footprint(x,y-16) || !dry_footprint(x,y+16)) score+=4096;
        if (score<best) {best=score;bx=x;by=y;}
    }
    if (best==0x7FFFFFFF) return FALSE;
    *outx=bx;*outy=by;
    return TRUE;
}

void enemy_prototypes_enter(int case_index) {
    static const s8 offset[3][2]={{0,-64},{64,0},{-64,0}};
    int i,px=PX(gPlayer->x),py=PX(gPlayer->y),count;
    case_index=CLAMP(case_index,0,3);
    actors_clear();
    sprites_reset();
    objects_room_reset();
    npc_room_reset();
    enemy_load_sheets_for_theme(0);
    player_new_game();
    gPl.hp=gPl.hp_max=80;
    gPl.items=ITEM_SWORD|ITEM_BOMBS|ITEM_LAMP|ITEM_CLOAK|ITEM_GAUNTLET|ITEM_SHIELD;
    gPl.items2=ITEM2_BOW|ITEM2_HUBCAP|ITEM2_MAP|ITEM2_ASTROLABE;
    gPl.bombs=20;gPl.arrows=50;
    gPl.equip[SLOT_A]=EQ_BOMBS;
    gPl.equip[SLOT_B]=EQ_SWORD;
    gPl.equip[SLOT_L]=EQ_SHIELD;
    fixture_floor(room_px_w()/2,room_px_h()/2+24,0,&px,&py);
    player_init(px,py,FACE_N);
    camera_update(px,py-16,TRUE);
    memset(gEnemyPrototypeEvents,0,sizeof(gEnemyPrototypeEvents));
    memset(gEnemyPrototypePositions,0,sizeof(gEnemyPrototypePositions));
    gEnemyPrototypePositions[0]=px;gEnemyPrototypePositions[1]=py;
    gEnemyPrototypeSpawned=0;gEnemyPrototypeCase=case_index;
    count=case_index==3?3:1;
    for (i=0;i<count;i++) {
        int x,y,type=EN_PROTO_ROPE+(case_index==3?i:case_index);
        if (fixture_floor(px+offset[i][0],py+offset[i][1],40,&x,&y)) {
            if (enemy_spawn(type,x,y)) {
                gEnemyPrototypePositions[2+i*2]=x;
                gEnemyPrototypePositions[3+i*2]=y;
                gEnemyPrototypeSpawned++;
            }
        }
    }
}

void enemy_prototypes_tick(void) {
    if (textbox_active() || npc_dialogue_active()) return;
    if (gKeysDown&KEY_SELECT) {
        gEnemyPrototypeRequest=(gEnemyPrototypeCase+1)%4+1;
        gKeysDown &= ~KEY_SELECT;
    }
    if (gEnemyPrototypeRequest>=1 && gEnemyPrototypeRequest<=4) {
        int index=gEnemyPrototypeRequest-1;
        gEnemyPrototypeRequest=0;
        enemy_prototypes_enter(index);
    }
}
#endif
