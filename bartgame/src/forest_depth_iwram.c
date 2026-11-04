/* Native tree depth is queried for every actor and shadow. ARM code in fast
   internal RAM avoids repeated Thumb register spills in this small hot loop. */
#include "gba.h"
#include "assets.h"
#if BART_FOREST_VARIANT >= 31
#include "forest_trees.h"
#include "room.h"

static bool8 lower_box_ink(const ForestTree* t,int x0,int y0,int x1,int y1) {
    int y;
    x0=MAX(0,x0-t->x);x1=MIN(forest_tree_width[t->frame],x1-t->x);
    y0=MAX(16,y0-t->y);y1=MIN(32,y1-t->y);
    if(x0>=x1 || y0>=y1)return FALSE;
    /* The same native authored root alpha as the previous depth query. */
    u32 span=0xffffffffu>>(32-(x1-x0));
    u32 mask=span<<x0;
    for(y=y0;y<y1;y++)if(forest_tree_opaque_rows[t->frame][y]&mask)return TRUE;
    return FALSE;
}

int IWRAM_CODE forest_trees_priority(int px,int py,int z,int width,int height,int priority) {
    int x,y,front=0;
    if(priority!=2 || !forest_trees_active())return priority;
    int x0=px-MIN(width/2,16),x1=px+MIN(width/2,16);
    int y0=py-z-MIN(height,64),y1=py-z;
    int cx0=MAX(0,x0/16),cx1=MIN(gRoom.w-1,x1/16);
    int cy0=MAX(0,(y0-16)/16),cy1=MIN(gRoom.h-1,(y1+16)/16);
    if(cx0>cx1 || cy0>cy1)return priority;
    u32 columns=(0xffffffffu<<cx0)&(0xffffffffu>>(31-cx1));
    for(y=cy0;y<=cy1;y++) {
        int previous=0;
        if(!(gForestTreeRootRows[y]&columns))continue;
        for(x=cx0;x<=cx1;x++) {
            int owner=gForestTreeRoots[y*32+x];
            if(!owner || owner==previous)continue;
            previous=owner;
            const ForestTree* t=&gForestTrees[owner-1];
            int w=forest_tree_width[t->frame];
            int left=t->x+forest_tree_anchor_x[t->frame]-w/2;
            if(x1<=left || x0>=left+w || y1<=t->y || y0>=t->y+32)continue;
            if(py>=t->y+forest_tree_anchor_y[t->frame] || z>=16)front=1;
            /* Behind ink dominates all later front flags. The query has no
               side effects, so no further owners need to be examined. */
            else if(lower_box_ink(t,MAX(x0,left),MAX(y0,t->y+16),
                                 MIN(x1,left+w),MIN(y1,t->y+32)))return 3;
        }
    }
    return front ? 1 : priority;
}
#endif
