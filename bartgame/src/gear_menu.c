/* An additive native Satchel/atlas; the original three pause pages remain.
   Twelve 16px icons borrow only the 48 reserved HUD tiles while paused.
   BG0 canvases total at most 327 tiles, within the existing 328 tile text pool. */
#include "gear_menu.h"
#include "legacy_items.h"
#include "player.h"
#include "menu.h"
#include "room.h"
#include "game.h"
#include "actor.h"
#include "video.h"
#include "sound.h"
#include "text.h"
#include "ui.h"
#include "objects.h"
#include "cream_world.h"
#include "cream_room.h"
#include "cream_runtime.h"
#include "regional_content.h"
#include "handoff_events.h"
#include "world.h"
#if BART_CREAM_VARIANT == 12
#include "cream_map_concepts.h"
#endif

enum { GM_SATCHEL,GM_MAP };
#define GM_PAGE 12
static u8 sActive,sPage,sCursor,sCount,sMapCell,sTerrace,sZoom,sFilter;
static u8 sList[LI_COUNT],sIcons[GM_PAGE];
static u16 sSavedBg3;
static s16 sSavedScroll[2];
static void (*sOldHook)(void);
static volatile u16 sInputHeld,sInputQueue[16];
static volatile u8 sInputRead,sInputWrite;
/* Drawing a whole native atlas can span a video tick. Preserve short presses
   arriving during that work, just as the existing full-screen menu does. */
static void input_irq(void) {
    u16 held=(~REG_KEYINPUT)&KEY_ANY,down=held&~sInputHeld;
    u8 next=(sInputWrite+1)&15;
    sInputHeld=held;
    if(down&&next!=sInputRead) {sInputQueue[sInputWrite]=down;sInputWrite=next;}
    if(sOldHook)sOldHook();
}
static Canvas sHead,sBody,sDetail,sFoot,sSide;
static CreamRoomInfo sPreview EWRAM_BSS;
static u8 sMask[CREAM_ROOM_W*CREAM_ROOM_H] EWRAM_BSS;
GearMapMarker gGearMapMarkers[24] EWRAM_BSS;
u8 gGearMapMarkerCount EWRAM_BSS;
static const char* const sFilters[]={"Tools & blades","Keepsakes","All possessions"};

bool8 gear_menu_active(void) {return sActive!=0;}
int gear_menu_region(int* cell) {
    int area=gGame.area,at=gGame.cell;
    if(area==AREA_HANDOFF) {
        int site=handoff_current_site();
        if(site>=160&&site<163) {area=AREA_CREAM;at=cream_cell(gCreamWorld.reward_node[site-160]);}
        else for(int i=0;i<RC_ROOMS;i++) {
            RegionalContentPlan p;
            if(regional_content_get(i<25?AREA_FOREST:AREA_CREAM,i%25,&p)&&p.interior_site==site) {area=p.area;at=p.cell;break;}
        }
    }
    if(area!=AREA_CREAM) {area=AREA_FOREST;if(at>=CELLS||gGame.area==AREA_SEWER)at=gWorld.entry;}
    if(cell)*cell=at;
    return area;
}
static void text_at(Canvas* c,int x,int y,const char* words,int ink) {
    vwf_text_fx(c,x,y,words,ink,UI_INK_DARK,FX_SHADOW);
}
static void line(Canvas* c,int x0,int y0,int x1,int y1,int ink) {
    int dx=ABS(x1-x0),sx=x0<x1?1:-1,dy=-ABS(y1-y0),sy=y0<y1?1:-1,err=dx+dy;
    while(1) {int e;vwf_pixel(c,x0,y0,ink);if(x0==x1&&y0==y1)break;e=err*2;if(e>=dy){err+=dy;x0+=sx;}if(e<=dx){err+=dx;y0+=sy;}}
}
static void rect(Canvas* c,int x,int y,int w,int h,int ink,bool8 filled) {
    int a,b;
    if(filled) {for(b=y;b<y+h;b++)for(a=x;a<x+w;a++)vwf_pixel(c,a,b,ink);}
    else {line(c,x,y,x+w-1,y,ink);line(c,x,y+h-1,x+w-1,y+h-1,ink);line(c,x,y,x,y+h-1,ink);line(c,x+w-1,y,x+w-1,y+h-1,ink);}
}
static void number(Canvas* c,int x,int y,int value,int ink) {char b[7];text_at(c,x,y,vwf_num(b,value,0),ink);}
static bool8 bit(const u32* bits,int n) {return (bits[n>>5]>>(n&31))&1;}
static bool8 surveyed(int cell) {return ((gCreamProgress.visited>>cell)&1)||legacy_item_owned(LI_MAP)||(gPl.items2&ITEM2_MAP);}
static void sync(void) {gBg3Dirty=1;vwf_flush(&sHead,FALSE);vwf_flush(&sFoot,FALSE);}
static void blank(void) {
    bg0_clear();bg0_pool_reset_full();ui_backdrop_clear();
    ui_frame(gBg3,UI_BG3,0,0,30,20,FR_PANEL);
    memset(sIcons,0,sizeof(sIcons));
}
static void gather(void) {
    int i;sCount=0;
    legacy_items_seed_owned();
    for(i=1;i<LI_COUNT;i++) {
        const LegacyItemDef* d=legacy_item_def(i);
        if(!legacy_item_owned(i) || (d->flags&LIF_HIDDEN)) continue;
        if(sFilter==0 && d->equip==EQ_NONE) continue;
        if(sFilter==1 && d->equip!=EQ_NONE) continue;
        sList[sCount++]=i;
    }
    if(sCursor>=sCount) sCursor=sCount?sCount-1:0;
}
static void queue_icons(void) {
    const SpriteSheet* sheet=&sheets[SHEET_HANDOFF_ITEMS];int i,start=(sCursor/GM_PAGE)*GM_PAGE;
    pal_set_obj(12,&pal_obj[sheet->pal*16]);
    for(i=0;i<GM_PAGE;i++) {
        int item=start+i<sCount?sList[start+i]:LI_NONE;
        sIcons[i]=item;
        if(item) {
            int frame=legacy_item_def(item)->frame;
            vram_queue(sheet->tiles+frame*sheet->frame_tiles*16,OBJ_TILE(OBJ_TILE_HUD_ICONS+i*4),128);
        }
    }
}
static void satchel(void) {
    int i,start;
    const LegacyItemDef* chosen;
    /* Twelve icons and four text canvases fill the16-entry upload queue.
       Finish the previous owner before admitting this complete page. */
    vram_flush_queue();
    blank();gather();start=(sCursor/GM_PAGE)*GM_PAGE;
    bg0_canvas(&sHead,2,1,26,2);
    text_at(&sHead,0,0,"THE SATCHEL",UI_INK_GOLD);
    text_at(&sHead,0,9,sFilters[sFilter],UI_INK_CREAM);
    number(&sHead,165,1,sCount?(sCursor/GM_PAGE)+1:0,UI_INK_HIGH);text_at(&sHead,178,1,"/",UI_INK_DIM);
    number(&sHead,185,1,(sCount+GM_PAGE-1)/GM_PAGE,UI_INK_DIM);
    for(i=0;i<GM_PAGE;i++) ui_frame(gBg3,UI_BG3,2+(i%4)*4,4+(i/4)*3,4,3,
        start+i>=sCount?FR_EMPTY:start+i==sCursor?FR_SEL:FR_SLOT);
    ui_frame(gBg3,UI_BG3,20,3,9,10,FR_PANEL);
    bg0_canvas(&sSide,21,4,7,8);
    for(i=0;i<SLOT_COUNT;i++) {
        static const u8 badges[]={UI_BADGE_A,UI_BADGE_B,UI_BADGE_L};
        int eq=gPl.equip[i],item=legacy_equip_item(eq);
        ui_tile(gBg3,UI_BG3,21,4+i*3,badges[i],0);
        if(eq==EQ_HUBCAP) text_at(&sSide,11,i*24,"Drain Cap",UI_INK_CREAM);
        else if(item>0 && item<LI_COUNT) vwf_block(&sSide,11,i*24,45,8,legacy_item_def(item)->name,UI_INK_CREAM,2);
        else text_at(&sSide,11,i*24,"Empty",UI_INK_DIM);
    }
    ui_frame(gBg3,UI_BG3,1,14,28,5,FR_PANEL);bg0_canvas(&sDetail,2,14,26,4);
    chosen=sCount?legacy_item_def(sList[sCursor]):0;
    if(chosen) {
        text_at(&sDetail,1,2,chosen->name,UI_INK_GOLD);
        vwf_block(&sDetail,1,13,205,9,chosen->description,UI_INK_CREAM,2);
    } else text_at(&sDetail,1,8,"No possessions in this folio.",UI_INK_DIM);
    bg0_canvas(&sFoot,1,19,28,1);
    text_at(&sFoot,0,0,"A B L equip  R atlas  Select back",UI_INK_CREAM);
    queue_icons();vwf_flush(&sSide,FALSE);vwf_flush(&sDetail,FALSE);sync();
}

/* Small3x5letters are reserved for dense map marks. Full-size names and a
   legend sit beside the selected room; background shape never supplies a
   meaning that depends only on color. */
static const u16 sGlyph[18]={
    0x5bea, 0x3aeb, 0x624e, 0x3b6b, 0x72cf, 0x12cf, 0x6b4e, 0x5bed, 0x5aed, 0x388e, 0x2497, 0x2b6a, 0x05fd, 0x20a3
    ,0x4d6a,0x5f6d,0x2b6d,0x05d0
};
static int glyph_for(int ch) {
    const char* letters="ABCDEFGHKSTO";int i;
    if(ch=='@')return 12;
    if(ch=='?')return 13;
    if(ch=='Q')return 14;
    if(ch=='W')return 15;
    if(ch=='V')return 16;
    if(ch=='+')return 17;
    for(i=0;i<12;i++)if(letters[i]==ch)return i;
    return 13;
}
static void tiny(Canvas* c,int x,int y,int ch,int ink) {
    u16 g=sGlyph[glyph_for(ch)];int a,b;
    for(b=0;b<5;b++)for(a=0;a<3;a++)if(g&(1u<<(b*3+a)))vwf_pixel(c,x+a,y+b,ink);
}
static void append_mark(char* out,int* count,int ch) {
    int i;for(i=0;i<*count;i++)if(out[i]==ch)return;
    if(*count<19)out[(*count)++]=ch;
}
static u8 regional_marks(int cell,int terrace,RegionalContentDiscovery* d) {
    RegionalContentPlan p;u8 flags=regional_content_marks(AREA_CREAM,cell,d);
    if(!regional_content_get(AREA_CREAM,cell,&p))return 0;
    return (d->marks?d->terrace:p.terrace)==terrace?(flags&63u):0;
}
static bool8 chain_room(int area,int cell,int* tx,int* ty) {
    int a,c,x,y;if(!handoff_chain_location(&a,&c,&x,&y)||a!=area||c!=cell)return FALSE;
    if(tx)*tx=x;
    if(ty)*ty=y;
    return TRUE;
}
static int marks(int node,char* out) {
    int content=gCreamWorld.content[node],n=0,i;
    RegionalContentDiscovery d;u8 flags=regional_marks(cream_cell(node),cream_terrace(node),&d);
    RegionalContentPlan plan;
    if(chain_room(AREA_CREAM,cream_cell(node),NULL,NULL)&&
       regional_content_get(AREA_CREAM,cream_cell(node),&plan)&&plan.terrace==cream_terrace(node))append_mark(out,&n,'O');
    if((content&CC_CONTENT_BOSS)&&!gCreamProgress.boss_dead)append_mark(out,&n,'@');
    if((content&CC_CONTENT_MISSION)&&!(gCreamProgress.rewards&cream_reward_bit(node)))append_mark(out,&n,'T');
    if(flags&RC_MARK_QUEST)append_mark(out,&n,'Q');
    if(flags&RC_MARK_DOOR)append_mark(out,&n,'D');
    if(flags&RC_MARK_WAVE)append_mark(out,&n,'W');
    if(flags&RC_MARK_MECHANISM)append_mark(out,&n,'K');
    if(flags&RC_MARK_FUSION)append_mark(out,&n,'V');
    if(flags&RC_MARK_CACHE)append_mark(out,&n,'G');
    if((content&CC_CONTENT_CHEST)&&!bit(gCreamProgress.chests,node))append_mark(out,&n,'C');
    if(content&CC_CONTENT_NPC)append_mark(out,&n,'F');
    if((content&CC_CONTENT_HEAL)&&!bit(gCreamProgress.healed,node))append_mark(out,&n,'H');
    for(i=0;i<cream_edge_count(node);i++) if(cream_edge(node,i)->kind==CC_CAVE){append_mark(out,&n,'D');break;}
    if(content&CC_CONTENT_CACHE)append_mark(out,&n,'G');
    if((content&CC_CONTENT_ENEMIES)&&!bit(gCreamProgress.cleared,node))append_mark(out,&n,'E');
    if(content&CC_CONTENT_ENTRY)append_mark(out,&n,'S');
    out[n]=0;return n;
}
static void arrow(Canvas* c,int x0,int y0,int x1,int y1,int ink) {
    int dx=x1-x0,dy=y1-y0;
    line(c,x0,y0,x1,y1,ink);
    if(ABS(dx)>ABS(dy)) {int s=dx>0?-1:1;line(c,x1,y1,x1+s*3,y1-2,ink);line(c,x1,y1,x1+s*3,y1+2,ink);}
    else {int s=dy>0?-1:1;line(c,x1,y1,x1-2,y1+s*3,ink);line(c,x1,y1,x1+2,y1+s*3,ink);}
}
static void overview_body(void) {
    int cell,i,t,node=sMapCell*2+sTerrace;
    vwf_clear(&sBody,UI_INK_DEEP);
    for(cell=0;cell<CC_ROOMS;cell++) {
        int x=2+(cell%5)*23,y=1+(cell/5)*17;
        bool8 known=surveyed(cell),here=gGame.area==AREA_CREAM&&cell==gGame.cell;
        int edge=cell==sMapCell?UI_INK_HIGH:here&&!(gFrame&16)?UI_INK_GOLD:UI_INK_EDGE;
        rect(&sBody,x,y,22,16,UI_INK_NAVY,TRUE);rect(&sBody,x,y,22,16,edge,FALSE);
        line(&sBody,x+1,y+7,x+20,y+7,UI_INK_EDGE);
        if(!known) {
            if(chain_room(AREA_CREAM,cell,NULL,NULL)) {tiny(&sBody,x+4,y+5,'O',UI_INK_GOLD);tiny(&sBody,x+13,y+5,'?',UI_INK_DIM);}
            else tiny(&sBody,x+9,y+5,'?',UI_INK_DIM);
            continue;
        }
        for(t=0;t<2;t++) {
            char events[20];int n=marks(cell*2+(t==0?CC_UPPER:CC_LOWER),events),k;
            for(k=0;k<n&&k<4;k++) {
                int ch=n>4&&k==3?'+':events[k];
                tiny(&sBody,x+3+k*4,y+1+t*8,ch,ch=='@'?UI_INK_RED:ch=='T'||ch=='O'?UI_INK_GOLD:UI_INK_CREAM);
            }
        }
        if(here && !(gFrame&16)) {vwf_pixel(&sBody,x+1,y+1,UI_INK_PALE);vwf_pixel(&sBody,x+20,y+14,UI_INK_PALE);}
    }
    if(surveyed(sMapCell)) for(i=0;i<cream_edge_count(node);i++) {
        const CreamEdge* e=cream_edge(node,i);int target=cream_cell(e->target),dx=target%5-sMapCell%5,dy=target/5-sMapCell/5;
        int sx=2+(sMapCell%5)*23,sy=1+(sMapCell/5)*17,tx=2+(target%5)*23,ty=1+(target/5)*17;
        int ink=e->kind==CC_DROP?UI_INK_RED:e->kind==CC_CAVE?UI_INK_HIGH:UI_INK_GOLD;
        if(target==sMapCell||!surveyed(target))continue;
        if(dy) {
            int gx=sx+22;
            line(&sBody,sx+21,sy+7,gx,sy+7,ink);
            line(&sBody,gx,sy+7,gx,ty+7,ink);
            arrow(&sBody,gx,ty+7,tx+21,ty+7,ink);
        } else if(dx>0) arrow(&sBody,sx+21,sy+7,tx,ty+7,ink);
        else arrow(&sBody,sx,sy+7,tx+21,ty+7,ink);
    }
    vwf_flush(&sBody,FALSE);
}
static void route_words(Canvas* c,int y,const CreamEdge* e) {
    static const char* const kinds[]={"","Walk ","Climb ","Drop ","Cave "};
    char dest[5];int cell=cream_cell(e->target);
    dest[0]='A'+cell%5;dest[1]='1'+cell/5;dest[2]=cream_terrace(e->target)==CC_UPPER?'U':'L';dest[3]=0;
    text_at(c,1,y,kinds[e->kind],cream_edge_open(e,cream_runtime_tokens())?UI_INK_CREAM:UI_INK_RED);
    text_at(c,31,y,dest,UI_INK_GOLD);
}
static void paired_legend(int* count,const char* label,int ink) {
    int at=(*count)++;
    if(at<12)text_at(&sSide,(at&1)*36,18+(at/2)*9,label,ink);
}
static void map_side(void) {
    int node=sMapCell*2+sTerrace,i,yy=18;char loc[6];
    vwf_clear(&sSide,0);
    loc[0]='A'+sMapCell%5;loc[1]='1'+sMapCell/5;loc[2]=' ';loc[3]=sTerrace?'U':'L';loc[4]=0;
    text_at(&sSide,0,0,loc,UI_INK_GOLD);text_at(&sSide,0,9,sTerrace?"Upper shelf":"Lower shelf",UI_INK_CREAM);
    if(!surveyed(sMapCell)) {vwf_block(&sSide,0,24,80,9,chain_room(AREA_CREAM,sMapCell,NULL,NULL)?"Goal here. Explore to locate its feature.":"Uncharted. A map reveals the unvisited shelves.",UI_INK_DIM,5);vwf_flush(&sSide,FALSE);return;}
    if(sZoom) {
        int content=gCreamWorld.content[node];
        RegionalContentDiscovery d;u8 flags=regional_marks(sMapCell,sTerrace,&d);
        bool8 goal=chain_room(AREA_CREAM,sMapCell,NULL,NULL);
        if(flags||goal) {
            int count=0;
            if(goal)paired_legend(&count,"O Goal",UI_INK_GOLD);
            if((content&CC_CONTENT_MISSION)&&!(gCreamProgress.rewards&cream_reward_bit(node)))paired_legend(&count,"T Task",UI_INK_GOLD);
            if(flags&RC_MARK_QUEST)paired_legend(&count,"Q Quest",UI_INK_CREAM);
            if(flags&RC_MARK_DOOR)paired_legend(&count,"D Door",UI_INK_CREAM);
            if(flags&RC_MARK_WAVE)paired_legend(&count,"W Wave",UI_INK_CREAM);
            if(flags&RC_MARK_MECHANISM)paired_legend(&count,"K Work",UI_INK_CREAM);
            if(flags&RC_MARK_FUSION)paired_legend(&count,"V Fuse",UI_INK_CREAM);
            if((flags&RC_MARK_CACHE)||(content&CC_CONTENT_CACHE))paired_legend(&count,"G Cache",UI_INK_CREAM);
            if((content&CC_CONTENT_CHEST)&&!bit(gCreamProgress.chests,node))paired_legend(&count,"C Chest",UI_INK_CREAM);
            if(content&CC_CONTENT_NPC)paired_legend(&count,"F Folk",UI_INK_CREAM);
            if((content&CC_CONTENT_HEAL)&&!bit(gCreamProgress.healed,node))paired_legend(&count,"H Heal",UI_INK_CREAM);
            if((content&CC_CONTENT_BOSS)&&!gCreamProgress.boss_dead)paired_legend(&count,"B Peak",UI_INK_RED);
            vwf_flush(&sSide,FALSE);return;
        }
        if((content&CC_CONTENT_MISSION)&&!(gCreamProgress.rewards&cream_reward_bit(node))) {text_at(&sSide,0,yy,"T  Task",UI_INK_GOLD);yy+=9;}
        if((content&CC_CONTENT_CHEST)&&!bit(gCreamProgress.chests,node)) {text_at(&sSide,0,yy,"C  Chest",UI_INK_CREAM);yy+=9;}
        if(content&CC_CONTENT_NPC) {text_at(&sSide,0,yy,"F  Folk",UI_INK_CREAM);yy+=9;}
        if((content&CC_CONTENT_HEAL)&&!bit(gCreamProgress.healed,node)) {text_at(&sSide,0,yy,"H  Heal",UI_INK_CREAM);yy+=9;}
        for(i=0;i<cream_edge_count(node)&&yy<66;i++) if(cream_edge(node,i)->kind==CC_CAVE) {text_at(&sSide,0,yy,"D  Cave",UI_INK_CREAM);yy+=9;break;}
        if((content&CC_CONTENT_CACHE)&&yy<=63) {text_at(&sSide,0,yy,"G  Cache",UI_INK_CREAM);yy+=9;}
        if((content&CC_CONTENT_BOSS)&&!gCreamProgress.boss_dead&&yy<=63) text_at(&sSide,0,yy,"B  Peak",UI_INK_RED);

    } else {
        for(i=0;i<cream_edge_count(node)&&i<6;i++)route_words(&sSide,yy+i*9,cream_edge(node,i));
        text_at(&sSide,0,73,"U above / L below",UI_INK_DIM);
    }
    vwf_flush(&sSide,FALSE);
}
static void mark_at(int tx,int ty,int ch) {
    static const s8 offsets[][2]={{0,0},{0,-10},{8,0},{0,10},{-8,0},{8,-10},{-8,-10},{8,10},{-8,10},{0,-20},{16,0},{0,20},{-16,0}};
    int sx=tx*4+2,sy=ty*4+1,x=sx,y=sy,i,j;
    if(tx<0||tx>=32||ty<0||ty>=24||gGearMapMarkerCount>=24)return;
    for(i=0;i<(int)(sizeof(offsets)/sizeof(offsets[0]));i++) {
        x=CLAMP(sx+offsets[i][0],3,124);y=CLAMP(sy+offsets[i][1],4,91);
        for(j=0;j<gGearMapMarkerCount;j++)if(ABS(x-gGearMapMarkers[j].x)<8&&ABS(y-gGearMapMarkers[j].y)<10)break;
        if(j==gGearMapMarkerCount)break;
    }
    GearMapMarker* m=&gGearMapMarkers[gGearMapMarkerCount++];
    m->tile_x=tx;m->tile_y=ty;m->ch=ch;m->source_x=sx;m->source_y=sy;m->x=x;m->y=y;
}
static void draw_marks(void) {
    int i;
    for(i=0;i<gGearMapMarkerCount;i++) {
        const GearMapMarker* m=&gGearMapMarkers[i];
        if(m->x!=m->source_x||m->y!=m->source_y)line(&sBody,m->source_x,m->source_y,m->x,m->y,UI_INK_CREAM);
    }
    for(i=0;i<gGearMapMarkerCount;i++) {
        const GearMapMarker* m=&gGearMapMarkers[i];
        rect(&sBody,m->x-3,m->y-4,7,9,UI_INK_DARK,TRUE);
        vwf_glyph(&sBody,m->x-2,m->y-3,m->ch,m->ch=='T'||m->ch=='O'?UI_INK_GOLD:UI_INK_HIGH);
    }
}
static void zoom_body(void) {
    int x,y,t,node=sMapCell*2+sTerrace;
    vwf_clear(&sBody,UI_INK_DEEP);
    gGearMapMarkerCount=0;
    if(!surveyed(sMapCell)) {vwf_flush(&sBody,FALSE);return;}
    cream_room_preview(sMapCell,&sPreview,sMask);
    for(y=0;y<CREAM_ROOM_H;y++)for(x=0;x<CREAM_ROOM_W;x++) {
        int v=sMask[y*CREAM_ROOM_W+x],ink=v==1?UI_INK_EDGE:v==2?UI_INK_GOLD_MID:v==3?UI_INK_GOLD:v==4?UI_INK_DARK:v==5?UI_INK_RED:v==6?UI_INK_RED:UI_INK_DEEP;
        rect(&sBody,x*4,y*4,4,4,ink,TRUE);
        if(v==3)line(&sBody,x*4,y*4+1,x*4+3,y*4+1,UI_INK_PALE);
        if(v==4)rect(&sBody,x*4,y*4,4,4,UI_INK_CREAM,FALSE);
        if(v==6) {vwf_pixel(&sBody,x*4,y*4,UI_INK_PALE);vwf_pixel(&sBody,x*4+3,y*4+3,UI_INK_DARK);}
    }
    for(t=0;t<2;t++) {
        int n=sMapCell*2+t,content=gCreamWorld.content[n];CreamTerraceSpots* p=&sPreview.terrace[t];
        if((content&CC_CONTENT_CHEST)&&!bit(gCreamProgress.chests,n))mark_at(p->chest.x,p->chest.y,'C');
        if(content&CC_CONTENT_NPC)mark_at(p->npc.x,p->npc.y,'F');
        if((content&CC_CONTENT_HEAL)&&!bit(gCreamProgress.healed,n))mark_at(p->heal.x,p->heal.y,'H');
        if((content&CC_CONTENT_MISSION)&&!(gCreamProgress.rewards&cream_reward_bit(n)))mark_at(p->mission.x,p->mission.y,'T');
        if(content&CC_CONTENT_CACHE)mark_at(p->cache.x,p->cache.y,'G');
        if((content&CC_CONTENT_BOSS)&&!gCreamProgress.boss_dead)mark_at(16,8,'B');
    }
    /* Mark door mouths at their actual preview cells rather than merely
       listing that the room contains a doorway. */
    for(y=0;y<CREAM_ROOM_H;y++)for(x=0;x<CREAM_ROOM_W;x++)if(sMask[y*CREAM_ROOM_W+x]==4) {
        mark_at(x,y,'D');while(x+1<CREAM_ROOM_W&&sMask[y*CREAM_ROOM_W+x+1]==4)x++;
    }
    {
        RegionalContentDiscovery d;regional_content_marks(AREA_CREAM,sMapCell,&d);
        if(d.marks&RC_MARK_DOOR)mark_at(d.door.x,d.door.y,'D');
        if(d.marks&RC_MARK_QUEST)mark_at(d.npc.x,d.npc.y,'Q');
        if(d.marks&RC_MARK_FUSION)mark_at(d.npc.x,d.npc.y,'V');
        if(d.marks&RC_MARK_WAVE)mark_at(d.npc.x,d.npc.y,'W');
        if(d.marks&RC_MARK_MECHANISM)mark_at(d.mechanism.x,d.mechanism.y,'K');
        if(d.marks&RC_MARK_CACHE)mark_at(d.cache.x,d.cache.y,'G');
    }
    {
        int tx,ty;if(chain_room(AREA_CREAM,sMapCell,&tx,&ty))mark_at(tx,ty,'O');
    }
    draw_marks();
    if(gGame.area==AREA_CREAM&&sMapCell==gGame.cell&&!(gFrame&16)) {
        int px=PX(gPlayer->x)/4,py=PX(gPlayer->y)/4;
        rect(&sBody,px-2,py-2,5,5,UI_INK_PALE,TRUE);rect(&sBody,px-1,py-1,3,3,UI_INK_RED,TRUE);
    }
    (void)node;vwf_flush(&sBody,FALSE);
}
static void atlas(void) {
#if BART_CREAM_VARIANT == 12
    cream_map_render(sMapCell,sZoom,0);return;
#endif
    blank();bg0_canvas(&sHead,2,1,26,1);text_at(&sHead,0,0,"THE CURDLED CREAM",UI_INK_GOLD);
    bg0_canvas(&sFoot,1,19,28,1);text_at(&sFoot,0,0,sZoom?"B overview  L shelf  R satchel":"A room  L shelf  B back  R satchel",UI_INK_CREAM);
    if(sZoom) {
        ui_frame(gBg3,UI_BG3,1,3,18,14,FR_PANEL);bg0_canvas(&sBody,2,4,16,12);
        ui_frame(gBg3,UI_BG3,19,3,10,13,FR_PANEL);bg0_canvas(&sSide,20,4,9,9);
        zoom_body();
    } else {
        ui_frame(gBg3,UI_BG3,1,3,17,13,FR_PANEL);bg0_canvas(&sBody,2,4,15,11);
        ui_frame(gBg3,UI_BG3,18,3,11,13,FR_PANEL);bg0_canvas(&sSide,19,4,10,10);
        overview_body();
    }
    map_side();sync();
}
static void redraw(void) {
#if BART_CREAM_VARIANT == 12
    if(sPage==GM_SATCHEL)cream_map_leave();
#endif
    if(sPage==GM_SATCHEL)satchel();else atlas();
}
static void open_page(int page) {
    sActive=1;sPage=page;sCursor=sZoom=0;sFilter=2;
    sInputRead=sInputWrite=0;sInputHeld=(~REG_KEYINPUT)&KEY_ANY;
    sOldHook=gVBlankHook;gVBlankHook=input_irq;
    {int cell;if(gear_menu_region(&cell)==AREA_CREAM)sMapCell=cell;else sMapCell=cream_cell(gCreamWorld.entry_node);}
    sTerrace=gGame.area==AREA_CREAM?cream_terrace(gCreamNode):CC_LOWER;
    /* The old pause may have borrowed actor palette banks for its icons. */
    icon32_menu_end();icon32_menu_begin();
    sSavedBg3=REG_BG3CNT;sSavedScroll[0]=gBgScroll[3][0];sSavedScroll[1]=gBgScroll[3][1];
    REG_BG3CNT=BGCNT_PRIO(3)|BGCNT_CHARBASE(3)|BGCNT_SCREENBASE(22)|BGCNT_SIZE_32x32;
    gBgScroll[3][0]=gBgScroll[3][1]=0;REG_BLDCNT=0;REG_BLDY=0;
    video_show(DCNT_BG0|DCNT_BG3|DCNT_OBJ);ui_backdrop_open();gGame.state=GS_MAP;gKeysDown=0;
    redraw();sfx_play(SFX_MENU);
}
void gear_menu_open(void) {open_page(GM_SATCHEL);}
void gear_menu_open_map(void) {
    int cell;if(gear_menu_region(&cell)==AREA_FOREST){menu_open_map_at(cell);return;}
    open_page(GM_MAP);
}
static void close(bool8 old_menu) {
#if BART_CREAM_VARIANT == 12
    cream_map_leave();
#endif
    sActive=0;gVBlankHook=sOldHook;icon32_menu_end();hud_invalidate_icons();gKeysDown=0;
    REG_BG3CNT=sSavedBg3;gBgScroll[3][0]=sSavedScroll[0];gBgScroll[3][1]=sSavedScroll[1];
    if(old_menu) {menu_open();return;}
    bg0_clear();room_render();video_show(DCNT_BG0|DCNT_BG1|DCNT_BG2|DCNT_OBJ);gGame.state=GS_PLAY;
}
static void item_sprites(void) {
    int i;
    for(i=0;i<GM_PAGE;i++)if(sIcons[i])draw_sprite((2+(i%4)*4)*8+8,(4+(i/4)*3)*8+4,
        SHEET_HANDOFF_ITEMS,OBJ_TILE_HUD_ICONS+i*4,0,0,1,12);
}
void gear_menu_update(void) {
    bool8 dirty=FALSE;
    if(!sActive)return;
    gKeysDown=0;
    if(sInputRead!=sInputWrite) {gKeysDown=sInputQueue[sInputRead];sInputRead=(sInputRead+1)&15;}
    if(gKeysDown&KEY_START) {close(FALSE);return;}
    if(gKeysDown&KEY_R) {
        int cell;
        if(sPage==GM_SATCHEL&&gear_menu_region(&cell)==AREA_FOREST) {close(FALSE);menu_open_map_at(cell);return;}
        sPage^=1;sZoom=0;dirty=TRUE;
    }
    else if(gKeysDown&KEY_SELECT) {
        close(TRUE);return;
    } else if(sPage==GM_SATCHEL) {
        int c=sCursor;
        if((gKeysDown&KEY_RIGHT)&&c+1<sCount)c++;
        if((gKeysDown&KEY_LEFT)&&c)c--;
        if((gKeysDown&KEY_DOWN)&&c+4<sCount)c+=4;
        if((gKeysDown&KEY_UP)&&c>=4)c-=4;
        if(c!=sCursor) {sCursor=c;dirty=TRUE;}
        if(sCount&&(gKeysDown&(KEY_A|KEY_B|KEY_L))) {
            const LegacyItemDef* d=legacy_item_def(sList[sCursor]);
            int slot=(gKeysDown&KEY_A)?SLOT_A:(gKeysDown&KEY_B)?SLOT_B:SLOT_L;
            if(d->equip!=EQ_NONE&&legacy_equip_owned(d->equip)) {player_equip_set(slot,d->equip);sfx_play(SFX_ITEM);dirty=TRUE;}
            else if(gKeysDown&KEY_B) {close(TRUE);return;}else sfx_play(SFX_BUMP);
        }
    } else {
        int c=sMapCell;
        if(gKeysDown&KEY_B) {if(sZoom){sZoom=0;dirty=TRUE;}else{close(TRUE);return;}}
#if BART_CREAM_VARIANT != 12
        if(gKeysDown&KEY_L) {sTerrace^=1;dirty=TRUE;}
#endif
        if(!sZoom) {
            if((gKeysDown&KEY_LEFT)&&c%5)c--;
            if((gKeysDown&KEY_RIGHT)&&c%5<4)c++;
            if((gKeysDown&KEY_UP)&&c>=5)c-=5;
            if((gKeysDown&KEY_DOWN)&&c<20)c+=5;
            if(c!=sMapCell) {sMapCell=c;dirty=TRUE;}
            if(gKeysDown&KEY_A) {sZoom=1;dirty=TRUE;}
        }
    }
    if(dirty) {redraw();sfx_play(SFX_MENU);}
    if(sPage==GM_SATCHEL)item_sprites();
    else if((gFrame&15)==0) {
#if BART_CREAM_VARIANT != 12
        if(sZoom)zoom_body();else overview_body();
#endif
    }
}
