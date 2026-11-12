/* Ten native graphical Cream atlas studies. All views share actual/pure
   generated terrain; drawing and navigation never mutate the run. */
#include "cream_map_concepts.h"
#include "cream_topology.h"
#include "cream_runtime.h"
#include "room.h"
#include "game.h"
#include "player.h"
#include "legacy_items.h"
#include "regional_content.h"
#include "handoff_events.h"
#include "video.h"
#include "ui.h"
#include "actor.h"
#include "vwf.h"
#include "text.h"
#include "util.h"

typedef struct {
    CreamMapData data;
    CreamTopology topology;
    CreamRoomInfo info;
    u8 kind[768],height[768],owner[768],mask[768];
} CMWork;
typedef char CMWorkFits[(sizeof(CMWork)<=8800)?1:-1];
static CMWork* sWork EWRAM_BSS;
static u16* sPixels EWRAM_BSS;
static u16 sSavedMap[16] EWRAM_BSS;
static u16 sBackdrop;
static bool8 sActive;
static u8 sHeightSummary[25][3] EWRAM_BSS;
static u32 sHeightSeed,sHeightKnown;
static void height_seed(void) {
    if(sHeightSeed!=gCreamWorld.seed){sHeightSeed=gCreamWorld.seed;sHeightKnown=0;}
}
static void height_summary(int cell,const CreamTopology* topology) {
    int i,low=7,high=0,levels=0,count=0;
    for(i=0;i<768;i++) {
        int c=topology->cells[i],h=c&CT_HEIGHT_MASK;
        if((c&CT_SUPPORT)&&!(c&CT_CLIMB)&&h<7){low=MIN(low,h);high=MAX(high,h);levels|=1<<h;}
    }
    for(i=0;i<7;i++)count+=(levels>>i)&1;
    sHeightSummary[cell][0]=low==7?0:low;sHeightSummary[cell][1]=high;sHeightSummary[cell][2]=count;
    sHeightKnown|=1u<<cell;
}
void cream_map_record_heights(void) {
    height_seed();
    if(gCreamTopology.active && gCreamTopology.cell==gCreamRoom.cell)
        height_summary(gCreamRoom.cell,&gCreamTopology);
}
u8 gCreamMapConcept,gCreamMapZoom,gCreamMapCell;
static const char* const sNames[10]={"Contour Folio","Curdstone Diorama","Geological Section","Exploded Shelves","Pilgrim Ribbon","Chamber Quilt","Surveyor Blueprint","Stained Reliquary","Cairn Locator","Plan & Escarpment"};
const char* cream_map_name(int style){return sNames[CLAMP(style,0,9)];}

void cm_pixel(int x,int y,int ink){
    if((unsigned)x>=240 || (unsigned)y>=160)return;
    unsigned at=((y>>3)*30+(x>>3))*16+(y&7)*2+((x&7)>>2),shift=(x&3)*4;
    sPixels[at]=(sPixels[at]&~(15u<<shift))|((ink&15)<<shift);
}
void cm_fill(int x,int y,int w,int h,int ink){
    int xx,yy;int x1=MIN(240,x+w),y1=MIN(160,y+h);x=MAX(0,x);y=MAX(0,y);
    for(yy=y;yy<y1;yy++)for(xx=x;xx<x1;xx++)cm_pixel(xx,yy,ink);
}
void cm_line(int x0,int y0,int x1,int y1,int ink){
    int dx=ABS(x1-x0),sx=x0<x1?1:-1,dy=-ABS(y1-y0),sy=y0<y1?1:-1,e=dx+dy;
    while(1){int d;cm_pixel(x0,y0,ink);if(x0==x1&&y0==y1)break;d=e*2;if(d>=dy){e+=dy;x0+=sx;}if(d<=dx){e+=dx;y0+=sy;}}
}
void cm_box(int x,int y,int w,int h,int ink){if(w<1||h<1)return;cm_line(x,y,x+w-1,y,ink);cm_line(x,y+h-1,x+w-1,y+h-1,ink);cm_line(x,y,x,y+h-1,ink);cm_line(x+w-1,y,x+w-1,y+h-1,ink);}
void cm_text(int x,int y,const char* text,int ink){
    while(*text && x<240){unsigned ch=(u8)*text++;int g,r,b;if(ch==' '){x+=VWF_SPACE;continue;}if(ch<VWF_FIRST||ch>=VWF_FIRST+VWF_COUNT)ch='?';g=ch-VWF_FIRST;
        for(r=0;r<VWF_HEIGHT;r++){u8 bits=vwf_bits[g*VWF_HEIGHT+r];for(b=0;bits;b++,bits>>=1)if(bits&1)cm_pixel(x+b,y+r,ink);}x+=vwf_w[g]+1;}
}
void cm_number(int x,int y,int value,int ink){char buf[10];cm_text(x,y,vwf_num(buf,value,0),ink);}
void cm_diamond(int x,int y,int w,int h,int ink,bool8 fill){
    int yy;if(w<1||h<1)return;
    if(fill)for(yy=-h/2;yy<=h/2;yy++){int half=(h/2-ABS(yy))*w/MAX(1,h);cm_line(x-half,y+yy,x+half,y+yy,ink);}
    else{cm_line(x-w/2,y,x,y-h/2,ink);cm_line(x,y-h/2,x+w/2,y,ink);cm_line(x+w/2,y,x,y+h/2,ink);cm_line(x,y+h/2,x-w/2,y,ink);}
}
void cm_arrow(int x0,int y0,int x1,int y1,int ink){
    int dx=x1-x0,dy=y1-y0;cm_line(x0,y0,x1,y1,ink);
    if(ABS(dx)>ABS(dy)){int s=dx>0?1:-1;cm_line(x1,y1,x1-3*s,y1-2,ink);cm_line(x1,y1,x1-3*s,y1+2,ink);}
    else{int s=dy>0?1:-1;cm_line(x1,y1,x1-2,y1-3*s,ink);cm_line(x1,y1,x1+2,y1-3*s,ink);}
}
void cm_icon(int x,int y,int kind,int ink){
    cm_fill(x-4,y-4,9,9,CM_INK);
    switch(kind){
    case CMI_CHEST:cm_fill(x-3,y-2,7,5,ink);cm_line(x-3,y,x+3,y,CM_INK);cm_pixel(x,y,CM_WHITE);cm_pixel(x,y+1,CM_GOLD);break;
    case CMI_FOLK:case CMI_QUEST:cm_fill(x-1,y-3,3,3,ink);cm_fill(x-2,y+1,5,3,ink);cm_pixel(x-3,y+2,ink);cm_pixel(x+3,y+2,ink);break;
    case CMI_HEAL:cm_fill(x-3,y-2,3,3,ink);cm_fill(x+1,y-2,3,3,ink);cm_line(x-3,y,x,y+3,ink);cm_line(x+3,y,x,y+3,ink);cm_fill(x-1,y-1,3,3,ink);cm_pixel(x-2,y-2,CM_WHITE);break;
    case CMI_BOSS:cm_icon(x,y,CMI_HEAL,ink);cm_line(x,y-2,x-1,y,CM_WHITE);cm_line(x-1,y,x+1,y+2,CM_WHITE);break;
    case CMI_CAVE:cm_box(x-3,y-2,7,6,ink);cm_fill(x-2,y-3,5,2,ink);cm_fill(x-1,y-1,3,5,CM_INK);cm_line(x-3,y+3,x+3,y+3,CM_PALE);break;
    case CMI_CLIMB:cm_line(x-3,y-4,x-3,y+4,ink);cm_line(x+3,y-4,x+3,y+4,ink);cm_line(x-2,y-2,x+2,y-2,ink);cm_line(x-2,y+1,x+2,y+1,ink);cm_line(x-2,y+4,x+2,y+4,ink);break;
    case CMI_DROP:cm_line(x-3,y-3,x+3,y-3,ink);cm_arrow(x,y-1,x,y+4,ink);break;
    case CMI_LOCK:cm_box(x-3,y-3,7,7,ink);cm_line(x-2,y-2,x+2,y+2,ink);cm_line(x+2,y-2,x-2,y+2,ink);break;
    case CMI_PLAYER:cm_diamond(x,y,7,7,CM_WHITE,TRUE);cm_pixel(x,y,CM_RED);break;
    case CMI_TASK:cm_line(x-2,y-4,x-2,y+4,ink);cm_fill(x-1,y-4,5,3,ink);cm_pixel(x+3,y-1,ink);break;
    case CMI_MECHANISM:cm_box(x-3,y-3,7,7,ink);cm_fill(x-1,y-1,3,3,CM_WHITE);break;
    default:cm_diamond(x,y,7,7,ink,TRUE);cm_pixel(x-1,y-1,CM_WHITE);break;
    }
}
static bool8 has(const u32* bits,int node){return(bits[node>>5]>>(node&31))&1;}
static bool8 known(int cell){return (gCreamProgress.visited>>cell)&1 || legacy_item_owned(LI_MAP) || (gPl.items2&ITEM2_MAP);}
static int event_bits(int cell){
    int t,bits=0;for(t=0;t<2;t++){int node=cell*2+t,b=gCreamWorld.content[node];
        if(has(gCreamProgress.chests,node))b&=~(CC_CONTENT_CHEST|CC_CONTENT_CACHE);
        if(has(gCreamProgress.healed,node))b&=~CC_CONTENT_HEAL;
        if(gCreamProgress.rewards&cream_reward_bit(node))b&=~CC_CONTENT_MISSION;
        if(gCreamProgress.boss_dead)b&=~CC_CONTENT_BOSS;
        bits|=b;}
    return bits;
}
static void mark(CreamMapData* d,int x,int y,int kind,int state){
    int i;if(x<0||y<0||x>=32||y>=24||d->marker_count>=32)return;
    for(i=0;i<d->marker_count;i++)if(d->markers[i].x==x&&d->markers[i].y==y&&d->markers[i].kind==kind)return;
    d->markers[d->marker_count++]=(CMMarker){x,y,kind,state};
}
static void load_plan(int cell){
    if(gGame.area==AREA_CREAM && cell==gGame.cell && gCreamTopology.active){sWork->info=gCreamRoom;sWork->topology=gCreamTopology;cream_room_preview(cell,0,sWork->mask);}
    else{cream_room_preview(cell,&sWork->info,sWork->mask);cream_topology_preview(cell,&sWork->info,&sWork->topology);}
}
static void expand(int cell){
    int x,y;bool8 live=gGame.area==AREA_CREAM&&cell==gGame.cell&&gCreamTopology.active;
    for(y=0;y<24;y++)for(x=0;x<32;x++){
        int at=y*32+x,f=sWork->topology.cells[at],k=(f&CT_CLIMB)?CMT_CLIMB:(f&CT_SUPPORT)?((f&CT_DROP)?CMT_DROP:CMT_FLOOR):CMT_WALL;
        if(sWork->mask[at]==4)k=CMT_CAVE;
        else if(sWork->mask[at]==6)k=CMT_GATE;
        if(live){u16 mt=room_get(x,y);int t=mt<METATILE_COUNT?metatile_type[mt]:TT_SOLID;
            if(t==TT_WATER)k=CMT_WATER;else if(t==TT_MYST)k=CMT_CAVE;
            else if(t==TT_PIT||t==TT_CRACK||t==TT_WEB||t==TT_THORN)k=CMT_GATE;}
        sWork->kind[at]=k;sWork->height[at]=f&CT_HEIGHT_MASK;sWork->owner[at]=(f&CT_UPPER)?1:0;
    }
}
static void prepare_data(int cell,bool8 zoom,int concept){
    int c,t,i,x,y;CreamMapData* d=&sWork->data;memset(d,0,sizeof(*d));height_seed();
    d->kind=sWork->kind;d->height=sWork->height;d->owner=sWork->owner;
    d->selected=CLAMP(cell,0,24);d->current=gGame.area==AREA_CREAM?gGame.cell:cream_cell(gCreamNode);d->zoom=zoom;d->concept=concept;
    if(gPlayer){d->here_x=CLAMP(PX(gPlayer->x)/16,0,31);d->here_y=CLAMP((PX(gPlayer->y)-4)/16,0,23);}
    for(c=0;c<25;c++){
        d->known[c]=known(c);d->visited[c]=(gCreamProgress.visited>>c)&1;
        if(!d->known[c])continue;
        d->corruption[c]=gCreamWorld.corruption[c];d->summit[c]=cream_cell(gCreamWorld.goal_node)==c;
        d->events[c]=event_bits(c);
        if(!(sHeightKnown&(1u<<c))){load_plan(c);height_summary(c,&sWork->topology);}
        d->low[c]=sHeightSummary[c][0];d->high[c]=sHeightSummary[c][1];d->levels[c]=sHeightSummary[c][2];
    }
    if(!d->known[d->selected]){memset(sWork->kind,CMT_WALL,768);memset(sWork->height,0,768);memset(sWork->owner,0,768);return;}
    load_plan(d->selected);expand(d->selected);
    for(t=0;t<2;t++){
        int n=d->selected*2+t,b=gCreamWorld.content[n];CreamTerraceSpots* p=&sWork->info.terrace[t];
        if((b&CC_CONTENT_CHEST)&&!has(gCreamProgress.chests,n))mark(d,p->chest.x,p->chest.y,CMI_CHEST,0);
        if(b&CC_CONTENT_NPC)mark(d,p->npc.x,p->npc.y,CMI_FOLK,0);
        if((b&CC_CONTENT_HEAL)&&!has(gCreamProgress.healed,n))mark(d,p->heal.x,p->heal.y,CMI_HEAL,0);
        if((b&CC_CONTENT_MISSION)&&!(gCreamProgress.rewards&cream_reward_bit(n)))mark(d,p->mission.x,p->mission.y,CMI_TASK,0);
        if((b&CC_CONTENT_CACHE)&&!has(gCreamProgress.chests,n))mark(d,p->cache.x,p->cache.y,CMI_CACHE,0);
        if((b&CC_CONTENT_BOSS)&&!gCreamProgress.boss_dead)mark(d,p->spawns[0].x,p->spawns[0].y,CMI_BOSS,0);
    }
    for(y=0;y<24;y++)for(x=0;x<32;x++)if(sWork->kind[y*32+x]==CMT_CAVE){mark(d,x,y,CMI_CAVE,0);while(x+1<32&&sWork->kind[y*32+x+1]==CMT_CAVE)x++;}
    for(i=0;i<sWork->topology.climbs;i++){CreamTopologyClimb* p=&sWork->topology.climb[i];mark(d,p->x,(p->top+p->bottom)/2,CMI_CLIMB,0);}
    for(i=0;i<sWork->topology.drops;i++){CreamTopologyDrop* p=&sWork->topology.drop[i];mark(d,p->x/16,p->y/16,CMI_DROP,0);}
    {RegionalContentDiscovery r;regional_content_marks(AREA_CREAM,d->selected,&r);
     if(r.marks&RC_MARK_DOOR)mark(d,r.door.x,r.door.y,CMI_CAVE,0);
     if(r.marks&(RC_MARK_QUEST|RC_MARK_FUSION|RC_MARK_WAVE))mark(d,r.npc.x,r.npc.y,CMI_QUEST,0);
     if(r.marks&RC_MARK_MECHANISM)mark(d,r.mechanism.x,r.mechanism.y,CMI_MECHANISM,0);
     if(r.marks&RC_MARK_CACHE)mark(d,r.cache.x,r.cache.y,CMI_CACHE,0);}
    if(gGame.area==AREA_CREAM && d->selected==gGame.cell)mark(d,d->here_x,d->here_y,CMI_PLAYER,0);
}
static bool8 route_raw(int cell,int index,CMRoute* out){
    int t,i,n=0;CMRoute seen[12];
    for(t=0;t<2;t++)for(i=0;i<cream_edge_count(cell*2+t);i++){
        const CreamEdge* e=cream_edge(cell*2+t,i);int k,target=cream_cell(e->target);bool8 open=!e->require||((gCreamOpenEdges[cell*2+t]>>i)&1)||(e->require==CC_TOKEN_CAPE_PACCI&&cream_edge_open(e,cream_runtime_tokens()));
        for(k=0;k<n;k++)if(seen[k].target==target&&seen[k].kind==e->kind&&seen[k].required==e->require)break;
        if(k<n)continue;
        seen[n++]=(CMRoute){target,e->kind,e->require,open};
    }
    if(index<0)return n!=0;
    if(index>=n)return FALSE;
    *out=seen[index];return TRUE;
}
int cm_routes(int cell){int i;CMRoute r;for(i=0;i<12&&route_raw(cell,i,&r);i++);return i;}
bool8 cm_route(int cell,int index,CMRoute* out){if(!route_raw(cell,index,out))return FALSE;return sWork->data.known[cell]&&sWork->data.known[out->target];}
static int height_ink(int h){return h<=0?CM_LOW:h<5?CM_LEVEL1+h-1:h==5?CM_PALE:CM_WHITE;}
void cm_room_plan(const CreamMapData* d,int x,int y,int w,int h,int mode){
    int xx,yy;cm_fill(x,y,w,h,CM_INK);if(!d->known[d->selected]){cm_text(x+w/2-3,y+h/2-4,"?",CM_EDGE);return;}
    for(yy=0;yy<24;yy++)for(xx=0;xx<32;xx++){
        int at=yy*32+xx,k=d->kind[at],v=d->height[at],px=x+xx*w/32,py=y+yy*h/24,tw=(xx+1)*w/32-xx*w/32,th=(yy+1)*h/24-yy*h/24;
        int color=k==CMT_WATER?CM_WATER:k==CMT_WALL?CM_INK:k==CMT_GATE?CM_RED:height_ink(v<7?v:d->owner[at]?3:0);
        if(mode==2){if(k!=CMT_WALL)cm_box(px,py,tw,th,color);}
        else cm_fill(px,py,tw,th,color);
        if(k!=CMT_WALL&&yy<23&&d->kind[at+32]==CMT_WALL)cm_line(px,py+th-1,px+tw-1,py+th-1,CM_GOLD_DIM);
        if(k==CMT_CLIMB)cm_line(px,py+th/2,px+tw-1,py+th/2,CM_GOLD);
    }
    for(xx=0;xx<d->marker_count;xx++){const CMMarker* m=&d->markers[xx];int ink=m->kind==CMI_HEAL?CM_RED:m->kind==CMI_BOSS?CM_BLIGHT:m->kind==CMI_FOLK?CM_GREEN:CM_GOLD;cm_icon(x+(m->x*2+1)*w/64,y+(m->y*2+1)*h/48,m->kind,ink);}
}
void cm_region_grid(const CreamMapData* d,int x,int y,int w,int h,int mode){
    int c;for(c=0;c<25;c++){
        int px=x+(c%5)*w/5,py=y+(c/5)*h/5,cw=w/5-2,ch=h/5-2;
        int ink=d->known[c]?(d->corruption[c]?CM_LEVEL2:CM_LEVEL1):CM_INK;
        if(mode!=2)cm_fill(px,py,cw,ch,ink);
        cm_box(px,py,cw,ch,c==d->selected?CM_GOLD:CM_EDGE);
        if(!d->known[c])continue;
        if(mode==1)cm_line(px+1,py+ch-2,px+cw-2,py+ch-2,CM_GOLD_DIM);
        if(cw>=12&&ch>=10){int b=d->events[c],kind=b&CC_CONTENT_BOSS?CMI_BOSS:b&CC_CONTENT_MISSION?CMI_TASK:b&CC_CONTENT_CHEST?CMI_CHEST:b&CC_CONTENT_NPC?CMI_FOLK:b&CC_CONTENT_HEAL?CMI_HEAL:CMI_CACHE; if(b&~(CC_CONTENT_ENEMIES|CC_CONTENT_ENTRY))cm_icon(px+cw/2,py+ch/2,kind,CM_GOLD);}
        if(c==d->current)cm_fill(px+1,py+1,2,2,CM_RED);
    }
}
static void palette(int style){
    u16 p[16]={RGB15(2,2,4),RGB15(4,4,6),RGB15(9,10,10),RGB15(13,14,12),RGB15(17,17,13),RGB15(21,20,15),RGB15(25,23,18),RGB15(5,17,25),RGB15(20,8,25),RGB15(31,25,11),RGB15(18,13,7),RGB15(11,12,13),RGB15(31,30,26),RGB15(29,8,10),RGB15(10,23,15),RGB15(28,27,23)};
    if(style==2||style==4){p[0]=RGB15(26,24,18);p[1]=RGB15(7,7,8);p[2]=RGB15(14,13,10);p[11]=RGB15(17,14,10);p[12]=RGB15(31,30,25);}
    if(style==6){p[0]=RGB15(2,5,10);p[1]=RGB15(3,8,15);p[2]=RGB15(5,12,18);p[3]=RGB15(8,15,20);p[4]=RGB15(12,19,23);p[5]=RGB15(17,23,26);p[6]=RGB15(22,27,29);p[11]=RGB15(10,18,23);}
    if(style==7){p[0]=RGB15(4,1,7);p[1]=RGB15(7,3,11);p[2]=RGB15(7,10,14);p[3]=RGB15(9,15,16);p[4]=RGB15(13,14,21);p[5]=RGB15(18,11,24);p[6]=RGB15(24,14,25);}
    pal_set_bg(PAL_SLOT_MAP,p);gPalBg[0]=p[0];gPalDirty=1;
}
void cream_map_render(int cell,bool8 zoom,int concept){
    int i,x,y;bool8 entering=!sActive;
    sPixels=menu_cream_pixel_scratch();sWork=(CMWork*)menu_cream_plan_scratch();
    if(!sActive){for(i=0;i<16;i++)sSavedMap[i]=gPalBg[PAL_SLOT_MAP*16+i];sBackdrop=gPalBg[0];sActive=TRUE;}
    gCreamMapConcept=concept%10;gCreamMapCell=CLAMP(cell,0,24);gCreamMapZoom=zoom;
    /* Gameplay is paused: style/zoom changes reuse exactly the same terrain
       and markers. A different selected room only needs its own pure plan. */
    if(entering || sWork->data.selected!=gCreamMapCell)prepare_data(cell,zoom,gCreamMapConcept);
    else{sWork->data.zoom=zoom;sWork->data.concept=gCreamMapConcept;}
    memset(sPixels,0,19200);palette(gCreamMapConcept);
    cm_text(5,3,cream_map_name(gCreamMapConcept),CM_GOLD);cm_number(218,3,gCreamMapConcept+1,CM_PALE);
    cm_line(4,17,235,17,CM_GOLD_DIM);
    if(gCreamMapConcept<5)cream_map_forms_a(gCreamMapConcept,&sWork->data);else cream_map_forms_b(gCreamMapConcept,&sWork->data);
    cm_line(4,147,235,147,CM_GOLD_DIM);cm_text(4,150,"L style  A zoom  B back  R items",CM_PALE);
    bg0_clear();text_flush();vram_flush_queue();gBg3Dirty=0;
    dma3_copy32(sPixels,CHARBLOCK(2),19200);
    for(y=0;y<32;y++)for(x=0;x<32;x++)SCREENBLOCK(31)[y*32+x]=(y<20&&x<30?y*30+x:0)|(PAL_SLOT_MAP<<12);
    /* The shared display helper claims the standard menu background first.
       Select this atlas's private character/map blocks after that helper. */
    video_show(DCNT_BG3);
    REG_BG3CNT=BGCNT_PRIO(0)|BGCNT_CHARBASE(2)|BGCNT_SCREENBASE(31)|BGCNT_SIZE_32x32;
    gBgScroll[3][0]=gBgScroll[3][1]=0;
}
void cream_map_leave(void){
    if(!sActive)return;
    sActive=FALSE;pal_set_bg(PAL_SLOT_MAP,sSavedMap);gPalBg[0]=sBackdrop;gPalDirty=1;
    REG_BG3CNT=BGCNT_PRIO(3)|BGCNT_CHARBASE(3)|BGCNT_SCREENBASE(22)|BGCNT_SIZE_32x32;
    ui_backdrop_open();video_show(DCNT_BG0|DCNT_BG3|DCNT_OBJ);
}
