/* Common runtime requirements over real inventory, counted keys, current
   switch facts, latched puzzles, fusions and independent region bosses. */
#include "world_tokens.h"
#include "player.h"
#include "legacy_items.h"
#include "handoff_events.h"
#include "cream_runtime.h"
#include "room.h"
#include "world.h"

WorldTokenNeed world_tokens_empty(void) {
    WorldTokenNeed n={0,0,0,0,0,WT_NO_SITE,0,WT_NO_SITE,0};
    return n;
}
bool8 world_tokens_meet(const WorldTokenNeed* n) {
    u16 items;
    if(!n)return FALSE;
    items=(u16)(gPl.items|((u16)gPl.items2<<8));
    if((items&n->old_items)!=n->old_items || gPl.keys<n->keys ||
       (gHandoffState.fusion_flags&n->fusions)!=n->fusions ||
       (gHandoffState.gold_fused&n->gold)!=n->gold ||
       (n->legacy_item&&!legacy_item_owned(n->legacy_item)))return FALSE;
    if(n->switch_mask && (n->switch_site==WT_NO_SITE ||
       (handoff_switch_facts(n->switch_site)&n->switch_mask)!=n->switch_mask))return FALSE;
    if(n->puzzle_site!=WT_NO_SITE && !(gHandoffState.completed[n->puzzle_site>>3]&(1u<<(n->puzzle_site&7))))return FALSE;
    if(n->boss_flags&~(WT_BOSS_HEART|WT_BOSS_CREAM))return FALSE;
    if((n->boss_flags&WT_BOSS_HEART) && (gWorld.goal>=CELLS || !(gWorld.cells[gWorld.goal].flags&CF_CLEARED)))return FALSE;
    if((n->boss_flags&WT_BOSS_CREAM) && !gCreamProgress.boss_dead)return FALSE;
    return TRUE;
}
bool8 world_tokens_cream_open(u8 required) {
    WorldTokenNeed n=world_tokens_empty();
    if(required&~CC_TOKEN_ALL)return FALSE;
    if(required&CC_TOKEN_BOMB)n.old_items|=ITEM_BOMBS;
    if(required&CC_TOKEN_LAMP)n.old_items|=ITEM_LAMP;
    if(required&CC_TOKEN_CAPE_PACCI){n.old_items|=ITEM_CLOAK;n.legacy_item=LI_PACCI_CANE;}
    return world_tokens_meet(&n);
}
u8 world_tokens_cream_mask(void) {
    u8 result=0,bit;
    for(bit=1;bit<=CC_TOKEN_CAPE_PACCI;bit<<=1)if(world_tokens_cream_open(bit))result|=bit;
    return result;
}
static bool8 predicate(int kind,int tx,int ty) {
    int type,surface;
    if(tx<1||ty<1||tx>=gRoom.w-1||ty>=gRoom.h-1)return FALSE;
    type=room_type(tx,ty);surface=legacy_surface_at(tx*16+8,ty*16+8);
    if(kind==WH_CUT)return type==TT_THORN||type==TT_LIFT1;
    if(kind==WH_DIG)return surface==LS_DIG||surface==LS_DIG_WALL;
    if(kind==WH_BOMB)return type==TT_CRACK;
    return FALSE;
}
/* Dry feet, not merely non-solid tiles: swimming/ice/lava/sinking surfaces
   never become mandatory hidden-prize approaches by accident. */
static bool8 dry_front(int tx,int ty) {
    int t,s;
    if(tx<1||ty<1||tx>=gRoom.w-1||ty>=gRoom.h-1)return FALSE;
    t=room_type(tx,ty);s=legacy_surface_at(tx*16+8,ty*16+8);
    if(t!=TT_FLOOR&&t!=TT_DOOR_OPEN&&t!=TT_CHEST_OPEN&&t!=TT_SWITCH)return FALSE;
    if(s==LS_ICE||s==LS_SWAMP||s==LS_LAVA||s==LS_CRUMBLE)return FALSE;
    return !room_box_solid(tx*16+3,ty*16+7,tx*16+12,ty*16+14);
}
static void flood(Spot start,u32* visited) {
    u16 queue[ROOM_MAX_W*ROOM_MAX_H];
    int head=0,tail=0,x,y,i;
    static const s8 dx[4]={0,1,0,-1},dy[4]={-1,0,1,0};
    for(i=0;i<ROOM_MAX_H;i++)visited[i]=0;
    if(!dry_front(start.x,start.y))return;
    visited[start.y]|=1u<<start.x;queue[tail++]=(start.y<<5)|start.x;
    while(head<tail) {
        int cell=queue[head++];x=cell&31;y=cell>>5;
        for(i=0;i<4;i++) {
            int xx=x+dx[i],yy=y+dy[i];
            if(xx<1||yy<1||xx>=gRoom.w-1||yy>=gRoom.h-1 || (visited[yy]&(1u<<xx)) || !dry_front(xx,yy))continue;
            visited[yy]|=1u<<xx;queue[tail++]=(yy<<5)|xx;
        }
    }
}
static bool8 approached(int kind,Spot p,const u32* visited) {
    static const s8 dx[4]={0,1,0,-1},dy[4]={-1,0,1,0};
    int i;
    if(!predicate(kind,p.x,p.y))return FALSE;
    if(visited[p.y]&(1u<<p.x))return TRUE;
    for(i=0;i<4;i++) {
        int x=p.x+dx[i],y=p.y+dy[i];
        if(x>0&&x<gRoom.w-1&&y>0&&y<gRoom.h-1 && (visited[y]&(1u<<x)))return TRUE;
    }
    return FALSE;
}
bool8 world_hidden_reachable(int kind,Spot candidate,Spot start) {
    u32 visited[ROOM_MAX_H];
    if(gRoom.w>ROOM_MAX_W||gRoom.h>ROOM_MAX_H||kind<WH_CUT||kind>WH_BOMB)return FALSE;
    flood(start,visited);return approached(kind,candidate,visited);
}
bool8 world_hidden_find(int kind,Spot origin,Spot start,int rings,Spot* out) {
    u32 visited[ROOM_MAX_H];
    int r,x,y;
    if(!out||gRoom.w>ROOM_MAX_W||gRoom.h>ROOM_MAX_H||kind<WH_CUT||kind>WH_BOMB)return FALSE;
    rings=CLAMP(rings,0,8);flood(start,visited);
    for(r=0;r<=rings;r++)for(y=(int)origin.y-r;y<=(int)origin.y+r;y++)for(x=(int)origin.x-r;x<=(int)origin.x+r;x++) {
        Spot p;
        if(r&&ABS(x-origin.x)!=r&&ABS(y-origin.y)!=r)continue;
        if(x<1||y<1||x>=gRoom.w-1||y>=gRoom.h-1)continue;
        p.x=x;p.y=y;
        if(approached(kind,p,visited)){*out=p;return TRUE;}
    }
    return FALSE;
}
