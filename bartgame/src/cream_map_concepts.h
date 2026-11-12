#ifndef CREAM_MAP_CONCEPTS_H
#define CREAM_MAP_CONCEPTS_H
#include "gba.h"
#include "cream_world.h"

/* Native240x160 graphical review atlas. Primitives clip to the viewport. */
enum { CM_BG,CM_INK,CM_LOW,CM_LEVEL1,CM_LEVEL2,CM_LEVEL3,CM_LEVEL4,
       CM_WATER,CM_BLIGHT,CM_GOLD,CM_GOLD_DIM,CM_EDGE,CM_WHITE,CM_RED,CM_GREEN,CM_PALE };
enum { CMT_WALL,CMT_FLOOR,CMT_CLIMB,CMT_DROP,CMT_CAVE,CMT_WATER,CMT_GATE };
enum { CMI_CHEST,CMI_FOLK,CMI_HEAL,CMI_TASK,CMI_BOSS,CMI_CAVE,CMI_CACHE,
       CMI_LOCK,CMI_PLAYER,CMI_CLIMB,CMI_DROP,CMI_QUEST,CMI_MECHANISM };
typedef struct {u8 x,y,kind,state;} CMMarker;
typedef struct {u8 target,kind,required,open;} CMRoute;
typedef struct {
    const u8 *kind,*height,*owner; /* selectedroom:32x24, pure preview */
    u8 selected,current,here_x,here_y,zoom,concept,marker_count;
    u8 known[25],visited[25],events[25],summit[25],corruption[25];
    u8 low[25],high[25],levels[25]; /* actualcoreterrainranges; zero if unknown */
    CMMarker markers[32];
} CreamMapData;
void cm_pixel(int x,int y,int ink);
void cm_fill(int x,int y,int w,int h,int ink);
void cm_box(int x,int y,int w,int h,int ink);
void cm_line(int x0,int y0,int x1,int y1,int ink);
void cm_text(int x,int y,const char* text,int ink);
void cm_number(int x,int y,int value,int ink);
void cm_icon(int x,int y,int kind,int ink); /* centered recognizable9pxicons */
void cm_arrow(int x0,int y0,int x1,int y1,int ink);
void cm_diamond(int x,int y,int w,int h,int ink,bool8 fill);
int cm_routes(int cell);
bool8 cm_route(int cell,int index,CMRoute* out);
void cm_room_plan(const CreamMapData* data,int x,int y,int w,int h,int mode);
void cm_region_grid(const CreamMapData* data,int x,int y,int w,int h,int mode);
/* Each artist owns five genuinely different arrangements, not palettes. */
void cream_map_forms_a(int style,const CreamMapData* data);
void cream_map_forms_b(int style,const CreamMapData* data);
const char* cream_map_name(int style);
void cream_map_render(int cell,bool8 zoom,int concept);
void cream_map_leave(void);
/* Cache only navigation height summaries from the actual loaded room. */
void cream_map_record_heights(void);
u16* menu_cream_pixel_scratch(void);
void* menu_cream_plan_scratch(void);
extern u8 gCreamMapConcept;
extern u8 gCreamMapZoom,gCreamMapCell;
#endif
