/* Five original native atlas arrangements. All terrain, elevation, markers
   and connections come from the supplied preview; no illustration invents
   a route or reveals an unknown room. */
#include "cream_map_concepts.h"

static bool8 walk_kind(int k) {return k!=CMT_WALL && k!=CMT_GATE;}
static int level_ink(int z) {return CM_LOW+CLAMP(z,0,4);}
static int terrain_ink(int k,int z) {
    return k==CMT_WALL?CM_INK:k==CMT_WATER?CM_WATER:
           k==CMT_GATE?CM_BLIGHT:level_ink(z);
}
static bool8 room_known(const CreamMapData* d) {return d->known[d->selected]!=0;}
static int marker_ink(int kind) {
    if(kind==CMI_HEAL)return CM_RED;
    if(kind==CMI_FOLK || kind==CMI_QUEST)return CM_PALE;
    if(kind==CMI_BOSS || kind==CMI_LOCK)return CM_BLIGHT;
    if(kind==CMI_CAVE)return CM_WATER;
    if(kind==CMI_PLAYER)return CM_WHITE;
    return CM_GOLD;
}

static void ornaments(int x,int y,int w,int h,int ink) {
    cm_line(x+4,y,x+w-5,y,ink);cm_line(x+4,y+h-1,x+w-5,y+h-1,ink);
    cm_line(x,y+4,x,y+h-5,ink);cm_line(x+w-1,y+4,x+w-1,y+h-5,ink);
    cm_line(x,y+4,x+4,y,ink);cm_line(x+w-5,y,x+w-1,y+4,ink);
    cm_line(x,y+h-5,x+4,y+h-1,ink);cm_line(x+w-5,y+h-1,x+w-1,y+h-5,ink);
}

static void glint(int x,int y,int ink) {
    cm_line(x-2,y,x+2,y,ink);cm_line(x,y-2,x,y+2,ink);
    cm_pixel(x-1,y-1,CM_WHITE);
}

static void question(int x,int y) {
    cm_diamond(x,y,11,9,CM_EDGE,FALSE);cm_text(x-2,y-3,"?",CM_GOLD_DIM);
}

static void barrier(int x,int y) {
    /* A capability obstruction is not a request for a small key. */
    cm_fill(x-4,y-4,9,9,CM_INK);cm_box(x-3,y-3,7,7,CM_BLIGHT);
    cm_line(x-2,y-2,x+2,y+2,CM_BLIGHT);
    cm_line(x+2,y-2,x-2,y+2,CM_BLIGHT);cm_pixel(x,y,CM_PALE);
}

/* Event icons stay recognizable at9px rather than being replaced by a
   row of ambiguous single letters. A small plus means room zoom has more. */
static void events(const CreamMapData* d,int cell,int x,int y,int maximum) {
    static const u8 bits[]={CC_CONTENT_BOSS,CC_CONTENT_MISSION,CC_CONTENT_HEAL,
                            CC_CONTENT_CHEST,CC_CONTENT_NPC,CC_CONTENT_CACHE};
    static const u8 kinds[]={CMI_BOSS,CMI_TASK,CMI_HEAL,CMI_CHEST,CMI_FOLK,CMI_CACHE};
    int i,n=0;
    if(!d->known[cell])return;
    for(i=0;i<6;i++)if(d->events[cell]&bits[i]) {
        if(n<maximum)cm_icon(x+(n%2)*10,y+(n/2)*9,kinds[i],marker_ink(kinds[i]));
        n++;
    }
    if(n>maximum)cm_text(x+20,y+5,"+",CM_GOLD);
}

static void plan_markers(const CreamMapData* d,int x,int y,int w,int h) {
    int i;
    if(!room_known(d))return;
    for(i=0;i<d->marker_count;i++) {
        const CMMarker* m=&d->markers[i];
        int px=x+(m->x*2+1)*w/64,py=y+(m->y*2+1)*h/48;
        cm_icon(CLAMP(px,x+4,x+w-5),CLAMP(py,y+4,y+h-5),m->kind,
                (m->state&2)?CM_RED:(m->state&1)?CM_GOLD_DIM:marker_ink(m->kind));
    }
    if(d->selected==d->current)cm_icon(x+(d->here_x*2+1)*w/64,
        y+(d->here_y*2+1)*h/48,CMI_PLAYER,CM_WHITE);
}

/* Pixel-faithful top-down shape, with optional relief or engineering lines.
   Unlike a height diagram, markers retain exact room-relative coordinates. */
static void plan(const CreamMapData* d,int x,int y,int w,int h,int mode,bool8 marks) {
    int tx,ty;
    cm_fill(x,y,w,h,CM_INK);
    if(!room_known(d)){question(x+w/2,y+h/2);return;}
    for(ty=0;ty<24;ty++)for(tx=0;tx<32;tx++) {
        int at=ty*32+tx,k=d->kind[at],z=d->height[at];
        int px=x+tx*w/32,py=y+ty*h/24,ww=x+(tx+1)*w/32-px,hh=y+(ty+1)*h/24-py;
        if(k==CMT_WALL)continue;
        if(mode==1) {
            cm_fill(px,py,ww,hh,k==CMT_WATER?CM_WATER:CM_BG);
            if(ty==0 || d->kind[at-32]==CMT_WALL || d->height[at-32]!=z)
                cm_line(px,py,px+ww-1,py,CM_PALE);
            if(tx==0 || d->kind[at-1]==CMT_WALL || d->height[at-1]!=z)
                cm_line(px,py,px,py+hh-1,CM_EDGE);
            if(ty==23 || d->kind[at+32]==CMT_WALL || d->height[at+32]!=z)
                cm_line(px,py+hh-1,px+ww-1,py+hh-1,CM_GOLD_DIM);
            if(tx==31 || d->kind[at+1]==CMT_WALL || d->height[at+1]!=z)
                cm_line(px+ww-1,py,px+ww-1,py+hh-1,CM_EDGE);
        } else {
            cm_fill(px,py,ww,hh,terrain_ink(k,z));
            if(ty==0 || d->kind[at-32]==CMT_WALL || d->height[at-32]>z)
                cm_line(px,py,px+ww-1,py,CM_PALE);
            if(ty==23 || d->kind[at+32]==CMT_WALL || d->height[at+32]<z) {
                cm_line(px,py+hh-1,px+ww-1,py+hh-1,CM_INK);
                if(mode==2 && hh>2)cm_line(px,py+hh-2,px+ww-1,py+hh-2,CM_EDGE);
            }
        }
        if(k==CMT_WATER && ww>=3 && hh>=3)cm_line(px,py+1,px+ww-2,py+1,CM_PALE);
        if(k==CMT_CLIMB && ww>=3 && hh>=3) {
            cm_line(px+1,py,px+1,py+hh-1,CM_GOLD);
            cm_line(px+ww-2,py,px+ww-2,py+hh-1,CM_GOLD);
            cm_line(px+1,py+hh/2,px+ww-2,py+hh/2,CM_GOLD);
        }
        if(k==CMT_DROP && (tx==0 || d->kind[at-1]!=CMT_DROP))
            cm_arrow(px+ww/2,py,px+ww/2,py+MAX(2,hh-1),CM_RED);
        if(k==CMT_GATE && (tx==0 || d->kind[at-1]!=CMT_GATE))
            barrier(px+ww/2,py+hh/2);
    }
    if(marks)plan_markers(d,x,y,w,h);
}

static void height_key(const CreamMapData* d,int x,int y,int w,int h,bool8 cairn) {
    int z,n=0,max_z=0;u32 present=0;
    if(!room_known(d))return;
    for(z=0;z<32*24;z++)if(walk_kind(d->kind[z])) {
        int hh=MIN(d->height[z],15);present|=1u<<hh;max_z=MAX(max_z,hh);
    }
    for(z=0;z<=max_z;z++)if(present&(1u<<z))n++;
    if(!n)return;
    int step=MIN(15,h/n),i=0;
    for(z=0;z<=max_z;z++)if(present&(1u<<z)) {
        int yy=y+h-(++i)*step,ww=cairn?w-2*(i&1):w;
        cm_fill(x+(w-ww)/2,yy+1,ww,MAX(4,step-3),level_ink(z));
        cm_line(x+(w-ww)/2+1,yy,x+(w+ww)/2-2,yy,CM_PALE);
        cm_line(x+(w-ww)/2,yy+MAX(4,step-3),x+(w+ww)/2-1,yy+MAX(4,step-3),CM_INK);
        cm_number(x+w+3,yy,z,CM_GOLD);
    }
}

static void dotted(int x0,int y0,int x1,int y1,int ink) {
    int steps=MAX(ABS(x1-x0),ABS(y1-y0)),i;
    if(!steps){cm_pixel(x0,y0,ink);return;}
    for(i=0;i<=steps;i+=3)cm_pixel(x0+(x1-x0)*i/steps,y0+(y1-y0)*i/steps,ink);
}

static void graph_links(const CreamMapData* d,int x,int y,int sx,int sy,bool8 diamonds) {
    int cell,i;
    for(cell=0;cell<25;cell++)if(d->known[cell])for(i=0;i<cm_routes(cell);i++) {
        CMRoute r;int ax,ay,bx,by;
        if(!cm_route(cell,i,&r) || r.target>=25 || !d->known[r.target] || r.target==cell)continue;
        if(r.kind!=CC_DROP && r.target<cell)continue;
        if(diamonds) {
            ax=x+(cell%5-cell/5)*sx;ay=y+(cell%5+cell/5)*sy;
            bx=x+(r.target%5-r.target/5)*sx;by=y+(r.target%5+r.target/5)*sy;
        } else {
            ax=x+(cell%5)*sx;ay=y+(cell/5)*sy;
            bx=x+(r.target%5)*sx;by=y+(r.target/5)*sy;
            /* Keep a directional head outside the card; drawing to its
               center and painting the card afterward would hide it. */
            int dx=bx-ax,dy=by-ay,len=MAX(ABS(dx),ABS(dy));
            int margin=ABS(dx)>=ABS(dy)?15:9;
            if(len>margin*2) {
                ax+=dx*margin/len;ay+=dy*margin/len;
                bx-=dx*margin/len;by-=dy*margin/len;
            }
        }
        int ink=r.required&&!r.open?CM_BLIGHT:r.kind==CC_DROP?CM_RED:r.kind==CC_CLIMB?CM_GOLD:CM_EDGE;
        if(r.kind==CC_CAVE)dotted(ax,ay,bx,by,CM_BLIGHT);
        else if(r.kind==CC_DROP)cm_arrow(ax,ay,bx,by,ink);
        else {
            cm_line(ax,ay,bx,by,ink);
            if(r.kind==CC_CLIMB) {
                int mx=(ax+bx)/2,my=(ay+by)/2;
                cm_line(mx-2,my-2,mx+2,my-2,CM_GOLD);
                cm_line(mx-2,my+1,mx+2,my+1,CM_GOLD);
            }
        }
        if(r.required&&!r.open)barrier((ax+bx)/2,(ay+by)/2);
    }
}

/*6: quilted miniature rooms, with full-height relief in the expanded panel. */
static void chamber_quilt(const CreamMapData* d) {
    int cell;
    ornaments(5,22,230,122,CM_GOLD_DIM);
    if(d->zoom) {
        plan(d,11,28,176,108,2,TRUE);
        cm_box(10,27,178,110,CM_GOLD);
        height_key(d,197,35,20,92,TRUE);
        cm_icon(210,135,CMI_CLIMB,CM_GOLD);
        return;
    }
    for(cell=0;cell<25;cell++) {
        int x=11+(cell%5)*38,y=27+(cell/5)*22,selected=cell==d->selected;
        cm_fill(x+2,y+2,34,19,CM_INK);
        if(d->known[cell]) {
            int n=CLAMP(d->levels[cell],1,5),j;
            cm_fill(x,y,34,19,CM_LOW);
            for(j=0;j<n;j++) {
                int yy=y+17-j*3;
                cm_line(x+23,yy,x+30,yy,level_ink(d->low[cell]+j));
                cm_pixel(x+22,yy-1,CM_PALE);
            }
            events(d,cell,x+5,y+5,4);
        } else {cm_fill(x,y,34,19,CM_BG);cm_pixel(x+16,y+9,CM_GOLD_DIM);}
        cm_box(x,y,34,19,selected?CM_GOLD:CM_EDGE);
        if(selected)cm_box(x-1,y-1,36,21,CM_GOLD_DIM);
        if(cell==d->current)cm_icon(x+29,y+4,CMI_PLAYER,CM_WHITE);
    }
    cm_line(206,29,206,132,CM_GOLD_DIM);
    cm_icon(220,39,CMI_CHEST,CM_GOLD);cm_icon(220,61,CMI_FOLK,CM_PALE);
    cm_icon(220,83,CMI_HEAL,CM_RED);cm_icon(220,105,CMI_BOSS,CM_BLIGHT);
    cm_text(212,124,"A",CM_GOLD);
}

/*7: a deliberately sparse surveying diagram with ledge hatching and rulers. */
static void surveyor_blueprint(const CreamMapData* d) {
    int cell,i;
    cm_box(7,24,226,116,CM_GOLD_DIM);
    for(i=12;i<230;i+=8)cm_pixel(i,140,CM_EDGE);
    if(!d->zoom) {
        graph_links(d,26,36,44,22,FALSE);
        for(cell=0;cell<25;cell++) {
            int x=26+(cell%5)*44,y=36+(cell/5)*22;
            cm_fill(x-14,y-8,29,17,CM_BG);
            cm_box(x-14,y-8,29,17,cell==d->selected?CM_GOLD:CM_EDGE);
            if(!d->known[cell]){cm_pixel(x,y,CM_GOLD_DIM);continue;}
            if(cell==d->selected)cm_box(x-16,y-10,33,21,CM_GOLD_DIM);
            events(d,cell,x-8,y,2);
            for(i=0;i<MIN(d->levels[cell],5);i++)cm_line(x+10,y+6-i*3,x+12,y+6-i*3,CM_PALE);
            if(cell==d->current)cm_icon(x+13,y-8,CMI_PLAYER,CM_WHITE);
        }
        return;
    }
    plan(d,15,30,160,96,1,TRUE);
    for(i=0;i<=32;i+=4) {
        int x=15+i*5;cm_line(x,127,x,130,CM_GOLD_DIM);
        if(!(i&7))cm_number(x-2,132,i,CM_GOLD_DIM);
    }
    for(i=0;i<=24;i+=4) {
        int y=30+i*4;cm_line(10,y,13,y,CM_GOLD_DIM);
    }
    cm_line(183,29,183,134,CM_GOLD_DIM);
    height_key(d,193,34,15,76,FALSE);
    cm_icon(205,121,CMI_CLIMB,CM_GOLD);cm_icon(224,121,CMI_DROP,CM_RED);
}

static void glass_room(const CreamMapData* d) {
    int tx,ty,z;u32 levels=0;
    const int x=40,y=30,w=160,h=100;
    if(!room_known(d)){question(120,81);return;}
    cm_fill(x-2,y-2,w+4,h+4,CM_INK);
    for(ty=0;ty<24;ty++)for(tx=0;tx<32;tx++) {
        int at=ty*32+tx,k=d->kind[at],level=MIN(d->height[at],15);
        int px=x+tx*w/32,py=y+ty*h/24,ww=x+(tx+1)*w/32-px,hh=y+(ty+1)*h/24-py;
        if(k==CMT_WALL)continue;
        levels|=1u<<level;
        cm_fill(px,py,ww,hh,terrain_ink(k,level));
        /* A few subdued diagonal facets describe glass, not a new route.
           Their contrast is weaker than the true height-boundary leading. */
        if(k==CMT_FLOOR && ((tx+ty*2)%13)==3) {
            cm_line(px+1,py,px+ww-2,py+hh-1,CM_EDGE);
            cm_pixel(px+1,py,CM_PALE);
        }
        if(ty==0 || d->kind[at-32]==CMT_WALL || d->height[at-32]!=level)
            cm_line(px,py,px+ww-1,py,CM_GOLD);
        if(tx==0 || d->kind[at-1]==CMT_WALL || d->height[at-1]!=level)
            cm_line(px,py,px,py+hh-1,CM_GOLD_DIM);
        if(ty==23 || d->kind[at+32]==CMT_WALL || d->height[at+32]<level) {
            cm_line(px,py+hh-1,px+ww-1,py+hh-1,CM_GOLD_DIM);
            if(hh>2)cm_line(px,py+hh-2,px+ww-1,py+hh-2,CM_INK);
        }
        if(k==CMT_WATER)cm_line(px,py+1,px+ww-2,py+1,CM_PALE);
        if(k==CMT_CLIMB) {
            cm_line(px+1,py,px+1,py+hh-1,CM_GOLD);
            cm_line(px+ww-2,py,px+ww-2,py+hh-1,CM_GOLD);
            cm_line(px+1,py+hh/2,px+ww-2,py+hh/2,CM_GOLD);
        }
        if(k==CMT_DROP && (!tx || d->kind[at-1]!=CMT_DROP))cm_arrow(px+ww/2,py,px+ww/2,py+hh-1,CM_RED);
        if(k==CMT_GATE && (!tx || d->kind[at-1]!=CMT_GATE))barrier(px+ww/2,py+hh/2);
    }
    plan_markers(d,x,y,w,h);
    /* Actual occupied elevations become jewels in the window's mullion. */
    int n=0;
    for(z=0;z<16;z++)if(levels&(1u<<z))n++;
    if(n) {
        int step=MIN(15,100/n),i=0;
        for(z=0;z<16;z++)if(levels&(1u<<z)) {
            int yy=130-(i++)*step;
            cm_diamond(19,yy,13,9,level_ink(z),TRUE);
            cm_diamond(19,yy,13,9,CM_GOLD_DIM,FALSE);
            cm_number(28,yy-2,z,CM_GOLD);
            cm_diamond(221,yy,9,7,level_ink(z),TRUE);
        }
    }
}

static void window_pane(int x,int y,int color,int outline) {
    int yy;
    for(yy=-10;yy<=9;yy++) {
        int half=18;
        if(yy<-3)half=18-(-3-yy)*2;
        else if(yy>6)half=18-(yy-6)*3;
        cm_line(x-half,y+yy,x+half,y+yy,color);
        cm_pixel(x-half,y+yy,outline);cm_pixel(x+half,y+yy,outline);
    }
    cm_line(x-10,y-10,x+10,y-10,outline);
    cm_line(x-9,y+9,x+9,y+9,outline);
    cm_line(x-15,y-2,x-12,y-5,CM_PALE);
}

/*8: stained elevation panes retain the actual top-down room silhouette.
   Gold leading follows true height borders; it is not a second isometric
   cutaway or a decorative recoloring of another concept's layout. */
static void stained_reliquary(const CreamMapData* d) {
    int cell;
    ornaments(6,23,228,121,CM_GOLD);
    cm_line(8,24,120,21,CM_GOLD_DIM);cm_line(120,21,232,24,CM_GOLD_DIM);
    glint(15,31,CM_GOLD);glint(225,31,CM_GOLD);glint(15,135,CM_GOLD);glint(225,135,CM_GOLD);
    if(d->zoom){glass_room(d);return;}
    graph_links(d,32,35,44,22,FALSE);
    for(cell=0;cell<25;cell++) {
        int x=32+(cell%5)*44,y=35+(cell/5)*22;
        window_pane(x,y,d->known[cell]?level_ink(d->high[cell]):CM_BG,
                    cell==d->selected?CM_GOLD:CM_GOLD_DIM);
        if(d->known[cell])events(d,cell,x-5,y,2);
        else cm_pixel(x,y,CM_EDGE);
        if(cell==d->current)cm_icon(x+14,y-2,CMI_PLAYER,CM_WHITE);
    }
}

/*9: focus+context atlas: the selected chamber is always large, never buried
   behind a separate page of text. The context grid stays geographically5x5. */
static void cairn_locator(const CreamMapData* d) {
    ornaments(6,23,228,121,CM_GOLD_DIM);
    if(!d->zoom) {
        cm_box(10,27,145,110,CM_GOLD);
        plan(d,13,30,139,104,0,TRUE);
        cm_region_grid(d,164,29,64,65,3);
        height_key(d,178,100,22,38,TRUE);
        cm_line(157,81,163,81,CM_GOLD);cm_arrow(157,81,152,81,CM_GOLD);
        cm_icon(218,109,CMI_CLIMB,CM_GOLD);cm_icon(218,131,CMI_DROP,CM_RED);
    } else {
        plan(d,11,28,180,108,2,TRUE);cm_box(10,27,182,110,CM_GOLD);
        height_key(d,203,30,14,61,TRUE);
        cm_region_grid(d,198,102,32,34,2);
        cm_line(196,96,230,96,CM_GOLD_DIM);
    }
}

static void ridge_profile(const CreamMapData* d,int x,int y,int w,int h) {
    int tx,ty,max_z=1;
    if(!room_known(d))return;
    for(ty=0;ty<24;ty++)for(tx=0;tx<32;tx++)
        if(walk_kind(d->kind[ty*32+tx]))max_z=MAX(max_z,MIN(d->height[ty*32+tx],15));
    cm_line(x,y+h-1,x+w-1,y+h-1,CM_GOLD_DIM);
    for(tx=0;tx<32;tx++) {
        int z=-1,climb=0;
        for(ty=0;ty<24;ty++)if(walk_kind(d->kind[ty*32+tx])) {
            z=MAX(z,MIN(d->height[ty*32+tx],15));
            if(d->kind[ty*32+tx]==CMT_CLIMB)climb=1;
        }
        if(z<0)continue;
        int px=x+tx*w/32,ww=x+(tx+1)*w/32-px,hh=3+z*(h-4)/max_z;
        cm_fill(px,y+h-hh,ww,hh,level_ink(z));
        cm_line(px,y+h-hh,px+ww-1,y+h-hh,CM_PALE);
        if(climb)cm_line(px+ww/2,y+h-hh,px+ww/2,y+h-2,CM_GOLD);
    }
}

/*10: the plan and its real height envelope share an x-axis. This is an
   elevation summary, not a claim that disconnected shelves form one route. */
static void plan_and_escarpment(const CreamMapData* d) {
    int row;
    ornaments(6,23,228,121,CM_GOLD_DIM);
    if(d->zoom) {
        plan(d,13,29,160,76,1,TRUE);cm_box(12,28,162,78,CM_GOLD_DIM);
        cm_text(14,109,"RIDGE PROFILE",CM_GOLD);
        ridge_profile(d,13,119,160,20);
        cm_line(182,29,182,138,CM_GOLD_DIM);
        height_key(d,194,33,16,82,FALSE);
        cm_icon(199,131,CMI_CLIMB,CM_GOLD);cm_icon(221,131,CMI_DROP,CM_RED);
        return;
    }
    cm_region_grid(d,11,28,151,108,1);
    cm_line(169,29,169,138,CM_GOLD_DIM);
    cm_text(177,28,"COLUMN",CM_GOLD);
    for(row=0;row<5;row++) {
        int cell=row*5+d->selected%5,y=43+row*18;
        cm_line(180,y+12,225,y+12,CM_EDGE);
        if(!d->known[cell]){cm_pixel(203,y+6,CM_GOLD_DIM);continue;}
        int low=MIN(d->low[cell],7),high=MIN(d->high[cell],7);
        cm_fill(184+low*3,y+2,MAX(4,(high-low+1)*4),9,level_ink(high));
        cm_line(184+low*3,y+1,184+low*3+MAX(4,(high-low+1)*4)-1,y+1,CM_PALE);
        if(cell==d->selected)cm_box(180,y-1,46,15,CM_GOLD);
        if(d->summit[cell])cm_icon(225,y+3,CMI_BOSS,CM_BLIGHT);
    }
}

void cream_map_forms_b(int style,const CreamMapData* d) {
    switch(style) {
        case 5:chamber_quilt(d);break;
        case 6:surveyor_blueprint(d);break;
        case 7:stained_reliquary(d);break;
        case 8:cairn_locator(d);break;
        default:plan_and_escarpment(d);break;
    }
}
