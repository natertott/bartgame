/* Five native graphical atlas arrangements. All terrain/markers/routes come
   from the same pure preview; none of these drawings invents a connection. */
#include "cream_map_concepts.h"

static int ma_abs(int n) {return n<0?-n:n;}
static int ma_min(int a,int b) {return a<b?a:b;}
static int ma_max(int a,int b) {return a>b?a:b;}
static int ma_clamp(int n,int a,int b) {return n<a?a:n>b?b:n;}
static bool8 ma_floor(const CreamMapData* d,int x,int y) {
    int k;
    if(x<0||x>=32||y<0||y>=24)return FALSE;
    k=d->kind[y*32+x];
    return k==CMT_FLOOR||k==CMT_CLIMB||k==CMT_DROP||k==CMT_CAVE;
}
static int ma_height(const CreamMapData* d,int x,int y) {
    int h,up=-1,down=-1,hu=0,hd=0,k;
    if(x<0||x>=32||y<0||y>=24)return 0;
    h=d->height[y*32+x];
    if(h<7&&d->kind[y*32+x]!=CMT_CLIMB)return h;
    /* Climb cells are shafts. Height7 is a routing sentinel, not a seventh
       floor; interpolate their picture between actual supported end levels. */
    for(k=1;k<24;k++) {
        if(up<0&&y-k>=0&&ma_floor(d,x,y-k)&&d->kind[(y-k)*32+x]!=CMT_CLIMB&&d->height[(y-k)*32+x]<7) {
            up=y-k;hu=d->height[up*32+x];
        }
        if(down<0&&y+k<24&&ma_floor(d,x,y+k)&&d->kind[(y+k)*32+x]!=CMT_CLIMB&&d->height[(y+k)*32+x]<7) {
            down=y+k;hd=d->height[down*32+x];
        }
        if(up>=0&&down>=0)break;
    }
    if(up>=0&&down>=0)return (hu*(down-y)+hd*(y-up))/(down-up);
    return up>=0?hu:down>=0?hd:0;
}
static int ma_ink(int h) {
    if(h<=0)return CM_LOW;
    return CM_LEVEL1+ma_min(h-1,3);
}
static int ma_marker_ink(int kind) {
    return kind==CMI_BOSS?CM_BLIGHT:kind==CMI_HEAL?CM_RED:
           kind==CMI_FOLK||kind==CMI_QUEST?CM_GREEN:kind==CMI_CAVE?CM_PALE:CM_GOLD;
}
static int ma_marker_color(const CMMarker* marker) {
    return marker->state&1?CM_EDGE:marker->state&2?CM_BLIGHT:ma_marker_ink(marker->kind);
}
static void ma_frame(int x,int y,int w,int h) {
    cm_box(x,y,w,h,CM_EDGE);
    cm_line(x,y,x+6,y,CM_GOLD);cm_line(x,y,x,y+6,CM_GOLD);
    cm_line(x+w-7,y+h-1,x+w-1,y+h-1,CM_GOLD);
    cm_line(x+w-1,y+h-7,x+w-1,y+h-1,CM_GOLD);
}
static void ma_cell_label(int x,int y,int cell,int ink) {
    char label[3];label[0]='A'+cell%5;label[1]='1'+cell/5;label[2]=0;
    cm_text(x,y,label,ink);
}
static int ma_event(int bits) {
    if(bits&CC_CONTENT_BOSS)return CMI_BOSS;
    if(bits&CC_CONTENT_MISSION)return CMI_TASK;
    if(bits&CC_CONTENT_HEAL)return CMI_HEAL;
    if(bits&CC_CONTENT_CHEST)return CMI_CHEST;
    if(bits&CC_CONTENT_NPC)return CMI_FOLK;
    if(bits&CC_CONTENT_CACHE)return CMI_CACHE;
    if(bits&CC_CONTENT_ENTRY)return CMI_CLIMB;
    return -1;
}
static void ma_events(const CreamMapData* d,int cell,int x,int y) {
    static const u8 bits[7]={CC_CONTENT_BOSS,CC_CONTENT_MISSION,CC_CONTENT_HEAL,
        CC_CONTENT_CHEST,CC_CONTENT_NPC,CC_CONTENT_CACHE,CC_CONTENT_ENTRY};
    static const u8 kinds[7]={CMI_BOSS,CMI_TASK,CMI_HEAL,CMI_CHEST,CMI_FOLK,CMI_CACHE,CMI_CLIMB};
    int i,n=0,first=-1,second=-1;
    for(i=0;i<7;i++)if(d->events[cell]&bits[i]) {
        if(first<0)first=kinds[i];else if(second<0)second=kinds[i];n++;
    }
    if(first<0)return;
    if(second<0)cm_icon(x,y,first,ma_marker_ink(first));
    else {
        cm_icon(x-5,y,first,ma_marker_ink(first));
        cm_icon(x+5,y,second,ma_marker_ink(second));
        if(n>2) {cm_pixel(x-2,y+6,CM_GOLD);cm_pixel(x,y+6,CM_GOLD);cm_pixel(x+2,y+6,CM_GOLD);}
    }
}
static void ma_legend(int x,int y) {
    cm_icon(x+4,y+4,CMI_CLIMB,CM_GOLD);cm_text(x+13,y+1,"UP",CM_PALE);
    cm_icon(x+4,y+17,CMI_DROP,CM_BLIGHT);cm_text(x+13,y+14,"DROP",CM_PALE);
    cm_icon(x+4,y+30,CMI_CAVE,CM_PALE);cm_text(x+13,y+27,"CAVE",CM_PALE);
}
static void ma_scale(int x,int y,int maxh) {
    int h;
    maxh=ma_clamp(maxh,1,6);
    for(h=0;h<=maxh;h++) {
        int yy=y+(maxh-h)*8;
        cm_fill(x,yy,8,6,ma_ink(h));
        cm_number(x+12,yy,h,CM_PALE);
    }
}
static void ma_markers(const CreamMapData* d,int x,int y,int w,int h) {
    int i,j;short drawn[32][2];
    for(i=0;i<d->marker_count&&i<32;i++) {
        const CMMarker* m=&d->markers[i];
        int sx=x+(m->x*w+w/2)/32,sy=y+(m->y*h+h/2)/24,px=sx,py=sy;
        /* Tiny leader lines retain true feature locations when icon groups
           share a room cell; they do not move the underlying event. */
        for(j=0;j<i;j++)if(ma_abs(px-drawn[j][0])<8&&ma_abs(py-drawn[j][1])<8) {
            px=ma_clamp(sx+((i&1)?7:-7),x+4,x+w-5);
            py=ma_clamp(sy+((i&2)?7:-7),y+4,y+h-5);
        }
        drawn[i][0]=px;drawn[i][1]=py;
        if(px!=sx||py!=sy)cm_line(sx,sy,px,py,CM_EDGE);
        cm_icon(px,py,m->kind,ma_marker_color(m));
    }
    if(d->selected==d->current)
        cm_icon(x+d->here_x*w/32,y+d->here_y*h/24,CMI_PLAYER,CM_RED);
}
static void ma_plan(const CreamMapData* d,int x,int y,int w,int h,bool8 markers,bool8 contour) {
    int tx,ty;
    cm_fill(x,y,w,h,CM_INK);
    if(!d->known[d->selected]) {cm_text(x+w/2-2,y+h/2-3,"?",CM_EDGE);return;}
    for(ty=0;ty<24;ty++)for(tx=0;tx<32;tx++) {
        int at=ty*32+tx,k=d->kind[at],z=ma_height(d,tx,ty);
        int px=x+tx*w/32,py=y+ty*h/24,pw=(tx+1)*w/32-tx*w/32,ph=(ty+1)*h/24-ty*h/24;
        int ink=k==CMT_WATER?CM_WATER:k==CMT_GATE?CM_BLIGHT:ma_floor(d,tx,ty)?ma_ink(z):CM_INK;
        cm_fill(px,py,pw,ph,ink);
        if(k==CMT_WATER&&(tx+ty)%5==0)cm_line(px,py,px+pw-1,py,CM_WHITE);
        if(contour&&ma_floor(d,tx,ty)) {
            if(ty==0||!ma_floor(d,tx,ty-1)||ma_height(d,tx,ty-1)!=z)
                cm_line(px,py,px+pw-1,py,CM_EDGE);
            if(tx==0||!ma_floor(d,tx-1,ty)||ma_height(d,tx-1,ty)!=z)
                cm_line(px,py,px,py+ph-1,CM_EDGE);
        }
        if(k==CMT_DROP)cm_line(px,py+ph-1,px+pw-1,py+ph-1,CM_GOLD);
        if(k==CMT_CLIMB) {
            cm_pixel(px+pw/2,py,CM_GOLD);cm_pixel(px+pw/2,py+ph-1,CM_GOLD);
            if((ty&1)==0)cm_line(px,py+ph/2,px+pw-1,py+ph/2,CM_GOLD);
        }
    }
    if(markers)ma_markers(d,x,y,w,h);
}

/* The selected map keeps Folio's exact grid and uses Exploded Shelves'
   colored event vocabulary, two-icon groups and extra-content pips. */
static void ma_contour_grid(const CreamMapData* d) {
    int cell;
    for(cell=0;cell<25;cell++) {
        int x=12+(cell%5)*30,y=28+(cell/5)*108/5;
        int ink=d->known[cell]?(d->corruption[cell]?CM_LEVEL2:CM_LEVEL1):CM_INK;
        cm_fill(x,y,28,19,ink);
        cm_box(x,y,28,19,cell==d->selected?CM_GOLD:CM_EDGE);
        if(!d->known[cell])continue;
        ma_events(d,cell,x+14,y+9);
        if(cell==d->current)cm_fill(x+1,y+1,2,2,CM_RED);
    }
}

/* 01 — Contour Folio: the full floor plan owns the page; contour bands and
   an elevation scale remain legible beneath a small, explicit icon legend. */
static void ma_contours(const CreamMapData* d) {
    if(!d->zoom) {
        ma_frame(8,24,158,116);ma_contour_grid(d);
        cm_text(175,26,"SHELF",CM_GOLD);ma_cell_label(213,26,d->selected,CM_WHITE);
        ma_plan(d,175,42,56,42,FALSE,TRUE);ma_frame(174,41,58,44);
        ma_legend(176,93);
        cm_icon(180,136,CMI_PLAYER,CM_RED);cm_text(191,133,"HERE",CM_PALE);
    } else {
        ma_frame(8,24,170,116);ma_plan(d,12,28,162,108,TRUE,TRUE);
        cm_text(188,26,"LEVEL",CM_GOLD);ma_scale(190,40,d->high[d->selected]);
        ma_legend(187,99);
    }
}

static void ma_iso_tile(int x,int y,int ink) {
    cm_pixel(x,y,ink);cm_line(x-2,y+1,x+2,y+1,ink);
    cm_line(x-3,y+2,x+3,y+2,ink);cm_line(x-1,y+3,x+1,y+3,ink);
}
static void ma_iso_point(const CreamMapData* d,int tx,int ty,int* x,int* y) {
    *x=112+(tx-ty)*3;*y=62+(tx+ty)-ma_height(d,tx,ty)*4;
}
static void ma_region_iso(const CreamMapData* d) {
    int cell,order;
    /* Broad raised chips preserve the actual5x5 relationship. Their thickness
       is the room's measured range, not a north-row elevation guess. */
    for(order=0;order<9;order++)for(cell=0;cell<25;cell++)if(cell%5+cell/5==order) {
        int gx=cell%5,gy=cell/5,x=106+(gx-gy)*20,y=29+(gx+gy)*10;
        int thick=d->known[cell]?2+ma_min(d->high[cell]-d->low[cell],4):1;
        int i,ink=d->known[cell]?ma_ink(d->high[cell]):CM_BG;
        for(i=thick;i>0;i--)cm_diamond(x,y+6+i,32,13,CM_INK,TRUE);
        cm_diamond(x,y+6,32,13,ink,TRUE);
        cm_line(x-16,y+6,x,y,CM_EDGE);cm_line(x,y,x+16,y+6,d->known[cell]?CM_PALE:CM_EDGE);
        if(cell==d->selected)cm_diamond(x,y+6,34,15,CM_GOLD,FALSE);
        if(d->known[cell])ma_events(d,cell,x,y+6);
        if(cell==d->current)cm_fill(x-1,y+4,3,3,CM_RED);
    }
    cm_text(8,127,"CUT STONE",CM_GOLD);cm_text(8,137,"HEIGHT = DEPTH",CM_PALE);
    ma_cell_label(210,132,d->selected,CM_GOLD);
}

/* 02 — Curdstone Diorama: a true isometric cutaway, with floor height
   expressed in pixels of extrusion and clear dark near-side rock faces. */
static void ma_diorama(const CreamMapData* d) {
    int sum,tx,ty,i;
    if(!d->zoom) {ma_region_iso(d);return;}
    ma_frame(6,23,228,120);
    if(!d->known[d->selected]) {cm_text(118,76,"?",CM_EDGE);return;}
    for(sum=0;sum<55;sum++)for(ty=0;ty<24;ty++) {
        int x,y,z,face,kind;
        tx=sum-ty;if(tx<0||tx>=32)continue;
        kind=d->kind[ty*32+tx];if(!ma_floor(d,tx,ty)&&kind!=CMT_WATER&&kind!=CMT_GATE)continue;
        ma_iso_point(d,tx,ty,&x,&y);z=ma_height(d,tx,ty);
        face=0;
        if(!ma_floor(d,tx,ty+1))face=z*4+3;
        else face=ma_max(0,(z-ma_height(d,tx,ty+1))*4);
        if(face) {cm_fill(x-2,y+2,3,face,CM_LOW);cm_fill(x+1,y+2,2,face,CM_INK);}
        ma_iso_tile(x,y,kind==CMT_WATER?CM_WATER:kind==CMT_GATE?CM_BLIGHT:ma_ink(z));
        if(kind==CMT_CLIMB) {cm_line(x-1,y,x+1,y,CM_GOLD);cm_pixel(x,y+2,CM_GOLD);}
        if(kind==CMT_DROP)cm_line(x-2,y+3,x+1,y+3,CM_GOLD);
    }
    for(i=0;i<d->marker_count&&i<32;i++) {
        const CMMarker* m=&d->markers[i];int x,y;
        ma_iso_point(d,m->x,m->y,&x,&y);cm_icon(x,y-2,m->kind,ma_marker_color(m));
    }
    if(d->selected==d->current) {int x,y;ma_iso_point(d,d->here_x,d->here_y,&x,&y);cm_icon(x,y-3,CMI_PLAYER,CM_RED);}
    cm_icon(17,131,CMI_CLIMB,CM_GOLD);cm_text(27,128,"RISE",CM_PALE);
    cm_icon(75,131,CMI_DROP,CM_BLIGHT);cm_text(85,128,"FALL",CM_PALE);
    cm_text(180,128,"3D CUT",CM_GOLD);
}

static int ma_cut_column(const CreamMapData* d) {
    int x,y,best=16,bestscore=-1;
    for(x=3;x<29;x++) {
        unsigned levels=0;int score=0;
        for(y=0;y<24;y++)if(ma_floor(d,x,y)) {
            int z=ma_height(d,x,y);if(z<16)levels|=1u<<z;
            score+=d->kind[y*32+x]==CMT_CLIMB?2:1;
        }
        for(y=0;y<16;y++)if(levels&(1u<<y))score+=7;
        if(score>bestscore){best=x;bestscore=score;}
    }
    return best;
}

/* 03 — Geological Section: a labelled N/S physical slice accompanies the
   actual top-down cut location, rather than flattening many levels into text. */
static void ma_section(const CreamMapData* d) {
    int cell,y;
    if(!d->zoom) {
        ma_frame(8,24,224,119);
        for(cell=0;cell<25;cell++) {
            int gx=cell%5,gy=cell/5,x=15+gx*44,base=44+gy*22;
            int hi=ma_min(d->high[cell],6),lo=ma_min(d->low[cell],6),z;
            cm_fill(x,base+1,34,3,CM_INK);
            if(d->known[cell]) {
                for(z=0;z<=hi;z++)cm_fill(x,base-z*2,34,2,ma_ink(z));
                cm_line(x,base-hi*2,x+33,base-hi*2,CM_PALE);
                cm_line(x+3,base-lo*2,x+30,base-lo*2,CM_GOLD_DIM);
                ma_events(d,cell,x+17,base-hi*2-2);
            } else cm_box(x,base-5,34,7,CM_EDGE);
            if(cell==d->selected)cm_box(x-2,base-14,38,20,CM_GOLD);
            if(cell==d->current)cm_fill(x+29,base-2,3,3,CM_RED);
        }
        return;
    }
    {
        int cut=ma_cut_column(d),x,maxh=ma_clamp(d->high[d->selected],1,6),scale=10;
        cm_text(10,24,"N / S SECTION",CM_GOLD);
        ma_plan(d,154,24,74,34,FALSE,TRUE);ma_frame(153,23,76,36);
        x=154+cut*74/32;cm_line(x,24,x,57,CM_RED);
        cm_text(10,37,"N",CM_PALE);cm_text(198,137,"S",CM_PALE);
        if(!d->known[d->selected]){cm_text(96,91,"?",CM_EDGE);return;}
        for(y=0;y<24;y++) {
            int k=d->kind[y*32+cut],z=ma_height(d,cut,y),px=12+y*8,top=136-z*scale;
            if(ma_floor(d,cut,y)) {
                int h;for(h=0;h<=z;h++)cm_fill(px,136-h*scale,8,scale,ma_ink(h));
                cm_line(px,top,px+7,top,CM_PALE);
                if(k==CMT_CLIMB) {
                    cm_line(px+1,top-2,px+6,top-2,CM_GOLD);
                    if(y==23||d->kind[(y+1)*32+cut]!=CMT_CLIMB)
                        cm_icon(px+3,top-5,CMI_CLIMB,CM_GOLD);
                }
                if(k==CMT_DROP)cm_icon(px+3,top-4,CMI_DROP,CM_BLIGHT);
            } else if(k==CMT_WATER)cm_fill(px,70,8,67,CM_WATER);
            else if(k==CMT_GATE) {
                cm_fill(px,70,8,67,CM_BLIGHT);
                cm_line(px+1,77,px+6,82,CM_GOLD);cm_line(px+6,77,px+1,82,CM_GOLD);
            }
            else {cm_fill(px,68,8,69,CM_INK);for(x=0;x<7;x+=3)cm_line(px+x,76,px+x+2,79,CM_EDGE);}
        }
        for(y=0;y<d->marker_count&&y<32;y++) {
            const CMMarker* m=&d->markers[y];
            if(ma_abs(m->x-cut)<=1)cm_icon(15+m->y*8,132-ma_height(d,m->x,m->y)*scale,m->kind,ma_marker_color(m));
        }
        for(y=0;y<=maxh;y++) {cm_line(210,136-y*scale,214,136-y*scale,CM_GOLD);cm_number(220,133-y*scale,y,CM_PALE);}
        cm_line(210,71,210,137,CM_EDGE);
    }
}

static int ma_levels(const CreamMapData* d,u8 levels[7]) {
    unsigned bits=0;int x,y,h,n=0;
    for(y=0;y<24;y++)for(x=0;x<32;x++) {
        int k=d->kind[y*32+x];
        /* Shafts connect floors; interpolated shaft heights are not new
           occupied floor planes in the exploded diagram. */
        if(k==CMT_CLIMB || d->height[y*32+x]>=7)continue;
        if(ma_floor(d,x,y)||k==CMT_WATER||k==CMT_GATE)
            bits|=1u<<ma_clamp(ma_height(d,x,y),0,6);
    }
    for(h=0;h<=6;h++)if(bits&(1u<<h))levels[n++]=h;
    return n;
}

/* 04 — Exploded Shelves: separate actual elevation planes, preserving each
   floor footprint. The gaps are diagram spacing, never invented paths. */
static void ma_exploded(const CreamMapData* d) {
    int cell,i,x,y;
    if(!d->zoom) {
        for(cell=0;cell<25;cell++) {
            int gx=cell%5,gy=cell/5,px=12+gx*44,py=28+gy*22;
            int n=d->known[cell]?ma_clamp(d->levels[cell],1,4):1;
            for(i=0;i<n;i++) {
                cm_fill(px+i*2,py+12-i*3,29,5,CM_INK);
                cm_fill(px+i*2,py+10-i*3,29,3,d->known[cell]?ma_ink(d->low[cell]+i):CM_BG);
                cm_line(px+i*2,py+10-i*3,px+i*2+28,py+10-i*3,CM_EDGE);
            }
            if(cell==d->selected)cm_box(px-2,py-2,38,21,CM_GOLD);
            if(d->known[cell])ma_events(d,cell,px+16,py+8-n*2);
            if(cell==d->current)cm_fill(px+31,py+13,3,3,CM_RED);
        }
        return;
    }
    {
        u8 levels[7];int n=ma_levels(d,levels),step=n>1?ma_min(18,88/(n-1)):0;
        if(!d->known[d->selected]) {cm_text(118,77,"?",CM_EDGE);return;}
        /* More than five heights remain visible with a smaller separation;
           no known plane is silently dropped to make the composition fit. */
        for(i=0;i<n;i++) {
            int px=16+i*step,py=113-i*step,z=levels[i];
            cm_box(px-2,py-2,68,28,CM_EDGE);
            cm_line(px-2,py+26,px+65,py+26,CM_INK);
            for(y=0;y<24;y++)for(x=0;x<32;x++)if(ma_height(d,x,y)==z) {
                int k=d->kind[y*32+x];
                if(!ma_floor(d,x,y)&&k!=CMT_WATER&&k!=CMT_GATE)continue;
                cm_fill(px+x*2,py+y,2,1,k==CMT_WATER?CM_WATER:k==CMT_GATE?CM_BLIGHT:ma_ink(z));
                if(k==CMT_CLIMB)cm_pixel(px+x*2,py+y,CM_GOLD);
                if(k==CMT_DROP)cm_pixel(px+x*2+1,py+y,CM_BLIGHT);
            }
            cm_number(px+69,py+4,z,CM_GOLD);
            for(y=0;y<d->marker_count&&y<32;y++) {
                const CMMarker* m=&d->markers[y];
                if(ma_height(d,m->x,m->y)==z)cm_icon(px+m->x*2,py+m->y,m->kind,ma_marker_color(m));
            }
            if(d->selected==d->current&&ma_height(d,d->here_x,d->here_y)==z)
                cm_icon(px+d->here_x*2,py+d->here_y,CMI_PLAYER,CM_RED);
        }
        cm_text(179,28,"LAYERS",CM_GOLD);ma_legend(179,43);
        cm_text(181,112,"HIGH",CM_PALE);cm_arrow(190,132,190,122,CM_GOLD);
    }
}

static void ma_route_point(int cell,int* x,int* y) {
    int gx=cell%5,gy=cell/5;*x=22+gx*44+(gy&1)*3;*y=31+gy*24;
}
static void ma_region_routes(const CreamMapData* d) {
    int from,i,cell;
    for(from=0;from<25;from++)if(d->known[from])for(i=0;i<cm_routes(from);i++) {
        CMRoute edge;int x,y,xx,yy,ink;
        if(!cm_route(from,i,&edge)||edge.target>=25||edge.target==from||!d->known[edge.target])continue;
        if(edge.kind==CC_WALK&&from>edge.target)continue;
        ma_route_point(from,&x,&y);ma_route_point(edge.target,&xx,&yy);
        ink=!edge.open?CM_RED:edge.kind==CC_CLIMB?CM_GOLD:edge.kind==CC_DROP?CM_BLIGHT:CM_EDGE;
        if(edge.kind==CC_CAVE) {
            int s,steps=ma_max(ma_abs(xx-x),ma_abs(yy-y));
            for(s=0;s<=steps;s+=4)cm_fill(x+(xx-x)*s/ma_max(steps,1),y+(yy-y)*s/ma_max(steps,1),2,1,CM_WATER);
        } else if(edge.kind==CC_WALK)cm_line(x,y,xx,yy,ink);
        else cm_arrow(x,y,xx,yy,ink);
    }
    for(cell=0;cell<25;cell++) {
        int x,y,e;ma_route_point(cell,&x,&y);
        cm_fill(x-13,y-6,27,14,CM_INK);cm_box(x-13,y-6,27,14,d->known[cell]?CM_GOLD_DIM:CM_EDGE);
        if(d->known[cell]) {
            cm_line(x-10,y+3,x+10,y+3,ma_ink(d->high[cell]));
            e=ma_event(d->events[cell]);if(e>=0)ma_events(d,cell,x,y-1);
            else ma_cell_label(x-5,y-3,cell,CM_PALE);
        }
        if(cell==d->selected)cm_box(x-15,y-8,31,18,CM_GOLD);
        if(cell==d->current)cm_fill(x+10,y-5,3,3,CM_RED);
    }
}

/* 05 — Pilgrim Ribbon: an actual macro-route constellation, then a terrain
   plan paired with a measured elevation ribbon carrying the room's icons. */
static void ma_pilgrim(const CreamMapData* d) {
    int z,maxh,i;
    if(!d->zoom){ma_region_routes(d);return;}
    ma_frame(7,24,164,118);ma_plan(d,11,28,156,110,TRUE,TRUE);
    cm_text(180,25,"RISE",CM_GOLD);maxh=ma_clamp(d->high[d->selected],1,6);
    if(!d->known[d->selected])return;
    for(z=0;z<=maxh;z++) {
        int yy=130-z*14,xx=189+((z&1)?4:0);
        cm_fill(xx,yy,17,7,ma_ink(z));cm_line(xx,yy,xx+16,yy,CM_PALE);
        if(z<maxh)cm_line(xx+8,yy-7,xx+8,yy-1,CM_GOLD_DIM);
        cm_number(217,yy,z,CM_PALE);
    }
    for(i=0;i<d->marker_count&&i<32;i++) {
        const CMMarker* m=&d->markers[i];int h=ma_height(d,m->x,m->y);
        cm_icon(196+(i&1)*10,132-h*14,m->kind,ma_marker_color(m));
    }
    cm_icon(180,143,CMI_CLIMB,CM_GOLD);cm_text(191,140,"HEIGHT",CM_PALE);
}

void cream_map_forms_a(int style,const CreamMapData* data) {
    switch(style) {
        case 0:ma_contours(data);break;
        case 1:ma_diorama(data);break;
        case 2:ma_section(data);break;
        case 3:ma_exploded(data);break;
        default:ma_pilgrim(data);break;
    }
}
