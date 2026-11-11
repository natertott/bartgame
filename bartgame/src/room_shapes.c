/* Optional2px collision shapes. The original room grid/layout is unchanged;
   rooms without a new shape take the existing coarse collision fast path. */
#include "room_shapes.h"
#include "room.h"
u16 gRoomShapeCount;
static u8 sShapes[ROOM_MAX_W*ROOM_MAX_H] EWRAM_BSS;
void room_shapes_clear(void){memset32(sShapes,0,sizeof(sShapes));gRoomShapeCount=0;}
void room_shape_tile(int tx,int ty,u16 mt){
    if(tx<0||ty<0||tx>=gRoom.w||ty>=gRoom.h)return;
    int index=ty*ROOM_MAX_W+tx;u8 old=sShapes[index],shape=0;
    if(mt>=MT_LH_SHAPE_NW&&mt<=MT_LH_SHAPE_THREE_EIGHTHS)shape=1+mt-MT_LH_SHAPE_NW;
    if(old&&!shape)gRoomShapeCount--;
    if(!old&&shape)gRoomShapeCount++;
    sShapes[index]=shape;
}
int room_shape_solid(int px,int py){
    u8 shape=sShapes[(py>>4)*ROOM_MAX_W+(px>>4)];
    int x=(px&15)>>1,y=(py&15)>>1;
    if(!shape)return-1;
    {
        u16 overlay=room_get_overlay(px>>4,py>>4);
        int quarter=((py&15)>>3)*2+((px&15)>>3);
        if(overlay!=MT_NONE && (metatile_coll[overlay]&(8u>>quarter)))return 1;
    }
    switch(shape){
        case 1:return x+y<=7;case 2:return x>=y;case 3:return x+y>=7;case 4:return x<=y;
        case 5:return y<4;case 6:return y>=4;case 7:return x<4;case 8:return x>=4;case 9:return x<3;
    }
    return-1;
}
