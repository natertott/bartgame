/* The Curdled Cream has its own directed graph, geometry and persistence.
   The Forest World and its three mandatory trials are never repurposed. */
#include "cream_runtime.h"
#include "cream_room.h"
#include "game.h"
#include "room.h"
#include "player.h"
#include "actor.h"
#include "enemy.h"
#include "legacy_enemies.h"
#include "legacy_items.h"
#include "handoff_events.h"
#include "objects.h"
#include "text.h"
#include "sound.h"
#include "video.h"
#include "util.h"
#include "world_tokens.h"
#include "regional_content.h"

CreamProgress gCreamProgress;
u8 gCreamNode;
static u16 sClimbTile,sFolkTile[3],sDropHeight,sReturnTile;
static u8 sClimbFrame,sDropRows,sDropClock,sRouteCooldown;
static u8 sHadEnemies[2],sEnemyTerrace[ACTOR_MAX];

void cream_runtime_track_enemy(Actor* enemy,const Actor* parent) {
    if(gGame.area!=AREA_CREAM||!enemy||enemy->kind!=AK_ENEMY)return;
    int terrace=cream_room_terrace_at(PX(enemy->x),PX(enemy->y),cream_terrace(gCreamNode));
    if(parent && parent>=gActors && parent<gActors+ACTOR_MAX && sEnemyTerrace[parent-gActors]<2)terrace=sEnemyTerrace[parent-gActors];
    sEnemyTerrace[enemy-gActors]=terrace;sHadEnemies[terrace]=1;
}

static bool8 bit_get(const u32* b,int n) {return (b[n>>5]>>(n&31))&1;}
static void bit_set(u32* b,int n) {b[n>>5]|=1u<<(n&31);}
static CreamTerraceSpots* spots(int node) {return &gCreamRoom.terrace[cream_terrace(node)];}
static bool8 near_spot(Spot p,int radius) {
    return ABS(PX(gPlayer->x)-(p.x*16+8))<=radius && ABS(PX(gPlayer->y)-(p.y*16+22))<=radius;
}

void cream_runtime_new_run(u32 seed) {
    memset(&gCreamProgress,0,sizeof(gCreamProgress));
    gCreamProgress.seed=hash32(seed,0x43524541);
    cream_generate(gCreamProgress.seed);
    gCreamProgress.node=gCreamNode=gCreamWorld.entry_node;
    cream_room_reset_progress();
}
u8 cream_runtime_tokens(void) {
    return world_tokens_cream_mask();
}
void cream_runtime_room_reset(void) {
    sClimbTile=sReturnTile=0;sClimbFrame=255;
    memset(sFolkTile,0,sizeof(sFolkTile));
    sDropRows=sDropClock=sDropHeight=0;sRouteCooldown=20;
    memset(sHadEnemies,0,sizeof(sHadEnemies));memset(sEnemyTerrace,255,sizeof(sEnemyTerrace));
}
void cream_runtime_build(int node) {
    if(node<0||node>=CC_NODES)node=gCreamWorld.entry_node;
    gCreamNode=gCreamProgress.node=node;
    gGame.cell=cream_cell(node);
    gCreamProgress.visited|=1u<<gGame.cell;
    cream_room_build(gGame.cell);
    for(int i=0;i<2;i++) {
        int n=gGame.cell*2+i;CreamTerraceSpots* p=spots(n);
        if(bit_get(gCreamProgress.chests,n) && (p->content&CC_CONTENT_CACHE) && !(p->content&CC_CONTENT_CHEST))room_set_overlay(p->cache.x,p->cache.y,MT_NONE);
        for(int j=0;j<cream_edge_count(n);j++)if(cream_edge(n,j)->require==CC_TOKEN_ALL && cream_runtime_tokens()==CC_TOKEN_ALL)cream_room_unlock_edge(n,j);
    }
    room_render();
    if((spots(gGame.cell*2)->content&CC_CONTENT_CHEST)&&bit_get(gCreamProgress.chests,gGame.cell*2))cream_room_set_chest_open(gGame.cell*2,TRUE);
    if((spots(gGame.cell*2+1)->content&CC_CONTENT_CHEST)&&bit_get(gCreamProgress.chests,gGame.cell*2+1))cream_room_set_chest_open(gGame.cell*2+1,TRUE);
}
void cream_runtime_enter(void) {
    int t,i;
    cream_runtime_room_reset();
    /* Every entrance has a visible climbing lesson; it cannot be stranded
       behind a tool the player has not found in the separate Forest. */
    if(!legacy_item_owned(LI_GRIP_RING))legacy_item_grant(LI_GRIP_RING,1);
    for(t=0;t<2;t++) {
        int node=gGame.cell*2+t;
        CreamTerraceSpots* p=spots(node);
        if((p->content&CC_CONTENT_ENEMIES)&&gGame.cell!=cream_cell(gCreamWorld.goal_node)&&!bit_get(gCreamProgress.cleared,node)) {
            for(i=0;i<p->spawn_count;i++) {
                Spot point=p->spawns[i];
                if(!regional_content_spawn_point(t,i,&point))continue;
                p->spawns[i]=point;
                int type=handoff_pick_enemy(gCreamWorld.stage[node],gCreamWorld.corruption[gGame.cell],hash32(gCreamProgress.seed,node*13+i));
                if(type<0||type>=EN_COUNT||!legacy_enemy_can_spawn(type))type=EN_PROTO_ROPE;
                Actor* e=enemy_spawn(type,point.x*16+8,point.y*16+14);
                if(e){sHadEnemies[t]=1;sEnemyTerrace[e-gActors]=t;}
            }
        }
        if((p->content&CC_CONTENT_BOSS)&&!gCreamProgress.boss_dead)
            enemy_spawn(LE_CREAM_GLEEROK,p->spawns[0].x*16+8,p->spawns[0].y*16+14);
    }
    cream_runtime_return();
}
void cream_runtime_return(void) {
    int i;
    for(i=0;i<3;i++) {
        int site=160+i;
        if((gHandoffState.completed[site>>3]&(1<<(site&7))) && !(gCreamProgress.rewards&(1<<i))) {
            gCreamProgress.rewards|=1<<i;
            if(i==0) {legacy_item_grant(LI_BOMBS,1);gPl.bombs=MAX(gPl.bombs,12);}
            if(i==1) {gPl.items|=ITEM_LAMP;player_auto_equip(EQ_LAMP);}
            if(i==2) {gPl.items|=ITEM_CLOAK;player_auto_equip(EQ_CLOAK);legacy_item_grant(LI_PACCI_CANE,1);}
            textbox_open(i==0?"The sealed curds yield Blightseeds.|Hold, then release. The seed bursts on landing.":i==1?"A Grail Lamp wakes.|Its flame clears the silk across the climbing seams.":"You found the Petal Cloak and Pacci Cane.|Leap the broken shelves. Turn the peak beast to expose its core.");
        }
    }
    for(int t=0;t<2;t++) {int node=gGame.cell*2+t;
        for(int j=0;j<cream_edge_count(node);j++)if(cream_edge(node,j)->require==CC_TOKEN_ALL && cream_runtime_tokens()==CC_TOKEN_ALL)cream_room_unlock_edge(node,j);
    }
}
bool8 cream_runtime_pre_player(void) {
    Actor* a=gPlayer;
    if(gGame.area!=AREA_CREAM)return FALSE;
    if(a->state==PS_DEAD){sDropRows=0;return FALSE;}
    if(sDropRows) {
        if(a->iframes)a->iframes--;
        if(gPl.item_cooldown)gPl.item_cooldown--;
        if(gPl.lamp_timer)gPl.lamp_timer--;
        /* A committed drop has visible acceleration and landing recovery.
           The transition presents each skipped cliff screen in game.c. */
        if(sDropClock<30) {
            int tick=++sDropClock; s32 previous=a->z;
            a->z=Q16(sDropHeight-(sDropHeight*tick*tick)/900);
            a->zvel=a->z-previous;
            if(a->state==PS_JUMP || a->state==PS_CLIMB)a->timer=4+tick;
        } else {
            a->z=a->zvel=0;sDropRows=0;
            if(a->state==PS_JUMP || a->state==PS_CLIMB){a->state=PS_NORMAL;a->sub=0;}
            a->iframes=MAX(a->iframes,20);sRouteCooldown=25;sfx_play(SFX_BUMP);
        }
        return TRUE;
    }
    int px=PX(a->x),py=PX(a->y),type=room_type_px(px,py-4);
    if(a->state!=PS_CLIMB) {
        if(a->state!=PS_NORMAL||a->z||!legacy_item_owned(LI_GRIP_RING))return FALSE;
        int probe=py-4+((gKeysHeld&KEY_UP)?-7:(gKeysHeld&KEY_DOWN)?7:0);
        if(type!=TT_CLIMB && room_type_px(px,probe)!=TT_CLIMB)return FALSE;
        if(!(gKeysHeld&(KEY_UP|KEY_DOWN)))return FALSE;
        a->state=PS_CLIMB;a->z=0;gPl.sword_active=gPl.shield_up=0;
    }
    int dy=(gKeysHeld&KEY_DOWN)?1:(gKeysHeld&KEY_UP)?-1:0;
    if(a->iframes)a->iframes--;
    if(gPl.item_cooldown)gPl.item_cooldown--;
    if(gPl.lamp_timer)gPl.lamp_timer--;
    if(dy) {
        int next=py+dy;
        if(!room_box_solid(px-4,next-7,px+3,next-1)) {a->y=Q16(next);a->anim_t++;}
        a->facing=dy<0?FACE_N:FACE_S;
    }
    a->x=Q16((px>>4)*16+8);
    if(room_type_px(PX(a->x),PX(a->y)-4)!=TT_CLIMB && !room_solid_px(PX(a->x),PX(a->y)-4)) {
        a->state=PS_NORMAL;gPl.safe_x=PX(a->x);gPl.safe_y=PX(a->y);
        int terrace=cream_room_terrace_at(PX(a->x),PX(a->y),cream_terrace(gCreamNode));
        gCreamNode=gCreamProgress.node=cream_node(gGame.cell,terrace);
    }
    return TRUE;
}
static void begin_drop(int rows,int height) {
    if(!gPlayer || gPlayer->state==PS_DEAD)return;
    sDropRows=CLAMP(rows,1,4);sDropClock=0;sDropHeight=CLAMP(height,0,512);
    gPlayer->state=PS_JUMP;gPlayer->sub=2;gPlayer->timer=4;
    gPlayer->z=Q16(sDropHeight);gPlayer->zvel=0;
    gPl.sword_active=gPl.shield_up=0;
}
void cream_runtime_drop(int rows) {
    if(!gPlayer)return;
    /* The final background starts with the body entering at world y14,
       regardless of the target terrace's generated landing height. */
    begin_drop(rows,MAX(48,PX(gPlayer->y)-14));
}
bool8 cream_runtime_draw_player(void) {
    if(gGame.area!=AREA_CREAM||gPlayer->state!=PS_CLIMB||sDropRows)return FALSE;
    const SpriteSheet* sh=&sheets[SHEET_CREAMCLIMB];
    int frame=(gPlayer->anim_t>>3)&3;
    if(!sClimbTile)sClimbTile=sprite_alloc(sh->frame_tiles);
    if(sClimbTile && frame!=sClimbFrame) {vram_queue(sh->tiles+frame*sh->frame_tiles*16,OBJ_TILE(sClimbTile),sh->frame_tiles*32);sClimbFrame=frame;}
    if(sClimbTile)draw_sprite(PX(gPlayer->x)-16-gCamX,PX(gPlayer->y)-32-gCamY,SHEET_CREAMCLIMB,sClimbTile,0,0,2,sh->pal);
    return TRUE;
}
bool8 cream_runtime_interact(void) {
    if(gGame.area!=AREA_CREAM||gPlayer->state!=PS_NORMAL)return FALSE;
    int node=gCreamNode,i;
    CreamTerraceSpots* p=spots(node);
    if((p->content&CC_CONTENT_ENTRY)&&near_spot(gCreamRoom.return_door,24)) {game_leave_cream();return TRUE;}
    if((p->content&CC_CONTENT_MISSION)&&near_spot(p->mission,24)) {
        for(i=0;i<3;i++)if(gCreamWorld.reward_node[i]==node) {
            if(gCreamProgress.rewards&(1<<i))textbox_open("The climbing trial is complete. Its route remains open.");
            else game_open_handoff(160+i,i==0?HS_SWITCHES:i==1?HS_WAVES:HS_MINIBOSS);
            return TRUE;
        }
    }
    if((p->content&CC_CONTENT_CHEST)&&!bit_get(gCreamProgress.chests,node)&&near_spot(p->chest,28)) {
        int choices[]={LI_BOOMERANG,LI_GUST_JAR,LI_MOLE_MITTS,LI_PEGASUS_BOOTS,LI_FLIPPERS,LI_POWER_BRACELETS,LI_BOW,LI_HEART_PIECE};
        int item=choices[hash32(gCreamProgress.seed,node*19)%8];
        bit_set(gCreamProgress.chests,node);cream_room_set_chest_open(node,TRUE);legacy_item_grant(item,1);
        textbox_open(legacy_item_def(item)->description);sfx_play(SFX_CHEST);return TRUE;
    }
    if((p->content&CC_CONTENT_CACHE)&&!(p->content&CC_CONTENT_CHEST)&&!bit_get(gCreamProgress.chests,node)&&near_spot(p->cache,24)) {
        bit_set(gCreamProgress.chests,node);gPl.gilt+=25;
        if(gPl.items&ITEM_BOMBS)gPl.bombs=MIN(99,gPl.bombs+3);
        room_set_overlay(p->cache.x,p->cache.y,MT_NONE);room_render();
        textbox_open("A climber's cache:25 gilt. Take the spare Blightseeds too.");sfx_play(SFX_PICKUP);return TRUE;
    }
    if((p->content&CC_CONTENT_HEAL)&&near_spot(p->heal,24)) {
        if(!bit_get(gCreamProgress.healed,node)){player_heal(gPl.hp_max);bit_set(gCreamProgress.healed,node);textbox_open("Cool whey. The cistern restores you.");}
        else textbox_open("The cistern is empty. Its golden lip is still warm.");
        return TRUE;
    }
    if((p->content&CC_CONTENT_NPC)&&near_spot(p->npc,24)) {
        static const char*const words[]={"Climb the pale seams. A black face without handholds cannot be climbed.|Some drops pass several terraces. Look before you leap.","Purple silk closes the path. A flame opens it.|The brightest veins gather near the peak.","The caves fold the mountain. A door far above may open beside your feet.|Bring the Pacci Cane to the peak. Turn the head; strike the exposed core."};
        textbox_open(words[hash32(gCreamProgress.seed,node)%3]);return TRUE;
    }
    return FALSE;
}
void cream_runtime_update(void) {
    if(gGame.area!=AREA_CREAM)return;
    for(int t=0;t<2;t++)if(sHadEnemies[t]) {
        bool8 live=FALSE;
        for(int i=1;i<ACTOR_MAX;i++)if(sEnemyTerrace[i]==t && gActors[i].kind==AK_ENEMY){live=TRUE;break;}
        if(!live){bit_set(gCreamProgress.cleared,gGame.cell*2+t);sHadEnemies[t]=0;}
    }
    if(sRouteCooldown){sRouteCooldown--;return;}
    if(gPlayer->state!=PS_NORMAL&&gPlayer->state!=PS_CLIMB)return;
    if(gPlayer->z)return;
    if(cream_runtime_tokens()==CC_TOKEN_ALL) {
        int index;for(index=0;index<cream_edge_count(gCreamNode);index++) {
            const CreamEdge* gate=cream_edge(gCreamNode,index);
            if(gate->require==CC_TOKEN_ALL && !(gCreamOpenEdges[gCreamNode]&(1u<<index)))cream_room_unlock_edge(gCreamNode,index);
        }
    }
    CreamRoomRoute route;
    if(!cream_room_route(gCreamNode,PX(gPlayer->x),PX(gPlayer->y),gPlayer->facing,gKeysHeld|gKeysDown,&route))return;
    const CreamEdge* e=cream_edge(gCreamNode,route.edge);
    if(!e||!world_tokens_cream_open(e->require))return;
    if(e->require==CC_TOKEN_ALL)cream_room_unlock_edge(gCreamNode,route.edge);
    if(route.mode==CCR_LOCAL_UP||route.mode==CCR_LOCAL_DOWN) {
        gCreamNode=gCreamProgress.node=route.target;
        /* A physical descent down a climb already put the body on its
           lower floor. Only its logical component needs to catch up. */
        sRouteCooldown=20;return;
    }
    if(route.mode==CCR_DROP && cream_cell(route.target)==gGame.cell) {
        int takeoff_y=PX(gPlayer->y);
        gCreamNode=gCreamProgress.node=route.target;player_set_pos(route.x,route.y);
        begin_drop(1,MAX(0,route.y-takeoff_y));return;
    }
    int px=route.x,py=route.y,facing=gPlayer->facing;
    cream_room_arrival(gCreamNode,e,&px,&py,&facing);
    game_travel_cream(e->target,px,py,facing,route.mode==CCR_DROP?route.rows:0);
}
void cream_runtime_draw(void) {
    if(gGame.area!=AREA_CREAM)return;
    int t;
    for(t=0;t<2;t++) {
        int node=gGame.cell*2+t;
        CreamTerraceSpots* p=spots(node);
        if(p->content&CC_CONTENT_ENTRY) {
            const SpriteSheet* sh=&sheets[SHEET_CREAMDOORS];Spot door=gCreamRoom.return_door;
            if(!sReturnTile)sReturnTile=sprite_load_frame(SHEET_CREAMDOORS,2);
            if(sReturnTile)draw_sprite(door.x*16-gCamX,(door.y+1)*16-2-sh->h-gCamY,SHEET_CREAMDOORS,sReturnTile,0,0,2,sh->pal);
        }
        if(p->content&CC_CONTENT_NPC) {
            int style=hash32(gCreamProgress.seed,node)%3;
            if(!sFolkTile[style])sFolkTile[style]=sprite_load_frame(SHEET_CREAMFOLK,style*4);
            if(sFolkTile[style])draw_sprite(p->npc.x*16-8-gCamX,p->npc.y*16-18-gCamY,SHEET_CREAMFOLK,sFolkTile[style],0,0,2,sheets[SHEET_CREAMFOLK].pal);
        }
    }
}
