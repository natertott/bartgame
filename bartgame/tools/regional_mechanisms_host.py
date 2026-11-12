#!/usr/bin/env python3
"""Execute production regional mechanism/mobility C with explicit host fixtures.

Checks actual builders, bounds, native-type semantics, protected dry perimeter,
all42 families, tool/state counters, pressure persistence, red-fusion collision,
cart water support/safe stops, bridge planes, descent and once-only rewards.
These are host logic/geometry checks, not emulator input or screenshot evidence.
"""
import argparse,hashlib,json,subprocess
from pathlib import Path
import handoff_mobility_host as M
import handoff_objects_host as O
GAME=Path(__file__).resolve().parents[1]

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

OBJECT_MAIN=r'''
static int checks;static unsigned long long families;
#define CHECK(c) do{checks++;if(!(c)){fprintf(stderr,"line%d: %s\n",__LINE__,#c);exit(1);}}while(0)
static void base(void){memset(&hero,0,sizeof(hero));memset(&gPl,0,sizeof(gPl));memset(&gHandoffState,0,sizeof(gHandoffState));memset(&gLegacyInventory,0,sizeof(gLegacyInventory));memset(itemOwned,1,sizeof(itemOwned));gRoom.w=32;gRoom.h=24;gGame.area=AREA_FOREST;gGame.cell=7;for(int i=0;i<768;i++){ground[i]=MT_CAVE_FLOOR0;overlay[i]=MT_NONE;}gKeysDown=gKeysHeld=0;clones=hurts=removed=healed=0;next_tile=32;hero.kind=AK_PLAYER;hero.x=Q16(264);hero.y=Q16(334);}
static Mechanism* find(int type){for(int i=0;i<sObj.count;i++)if(sObjects[i].type==type)return &sObjects[i];return NULL;}
static Mechanism* goal(void){for(int i=0;i<sObj.count;i++)if(sObjects[i].type==HO_TARGET&&sObjects[i].goal==128)return &sObjects[i];return NULL;}
static void stand(Mechanism*m){hero.x=Q16(m->x);hero.y=Q16(m->y);hero.z=0;hero.state=PS_NORMAL;}
static void tool(Mechanism*m,int kind){handoff_objects_tool_box(kind,m->x-4,m->y-4,m->x+4,m->y+4);}
static void press(Mechanism*m){hero.x=Q16(m->x);hero.y=Q16(m->y+18);hero.facing=FACE_N;gKeysDown=KEY_R;CHECK(handoff_objects_pre_player());gKeysDown=0;}
static void ring(int x,int y,int w,int h){for(int yy=y;yy<y+h;yy++)for(int xx=x;xx<x+w;xx++)if(xx==x||xx==x+w-1||yy==y||yy==y+h-1){CHECK(room_type(xx,yy)==TT_FLOOR);CHECK(!handoff_objects_box_solid(xx*16+3,yy*16+5,xx*16+12,yy*16+14));}}
int main(void){
 for(unsigned seed=0;seed<64;seed++)for(int pattern=0;pattern<12;pattern++){
  base();handoff_objects_build_regional(seed,pattern);CHECK(sObj.regional&&!sObj.field);CHECK(sObj.required_goals==128);CHECK(sObj.pattern==pattern);CHECK(sObj.count>0&&sObj.count<=12);CHECK(goal()!=NULL);
  for(int i=0;i<sObj.count;i++){Mechanism*m=&sObjects[i];CHECK(m->x>=48&&m->x<=464&&m->y>=48&&m->y<=320);CHECK(m->type<HO_COUNT);families|=1ULL<<m->type;
   if(m->type==HO_WARP||m->type==HO_LADDER_DOWN||m->type==HO_DEST_HOLE)CHECK(m->link<sObj.count);
  }
  CHECK(!handoff_objects_box_solid(15*16,21*16,17*16,23*16));handoff_objects_update();CHECK(!sObj.complete);
 }
 CHECK(families==((1ULL<<HO_COUNT)-1));
 /* Real regional placements can contain noninteractive flora or Cream
    mould (prop-priority ink); an interactive/solid overlay must still veto. */
 base();overlay[9*32+9]=69;CHECK(handoff_objects_build_field(7,0,8,8,5,4));CHECK(overlay[9*32+9]==MT_NONE);
 base();overlay[9*32+9]=MT_CREAM_MOLD_S0;metatile_prop[MT_CREAM_MOLD_S0]=1;CHECK(handoff_objects_build_field(7,0,8,8,5,4));CHECK(overlay[9*32+9]==MT_NONE);
 base();overlay[9*32+9]=69;metatile_prop[69]=1;CHECK(!handoff_objects_build_field(7,0,8,8,5,4));CHECK(overlay[9*32+9]==69);metatile_prop[69]=0;
 base();overlay[9*32+9]=69;metatile_type[69]=TT_SOLID;CHECK(!handoff_objects_build_field(7,0,8,8,5,4));metatile_type[69]=TT_FLOOR;
 base();overlay[9*32+9]=69;gRoom.underlay[9*32+9]=193;routes_valid=0;CHECK(!handoff_objects_build_fusion(7,8,8,5,5));CHECK(!sObj.active&&overlay[9*32+9]==69&&ground[9*32+9]==MT_CAVE_FLOOR0&&gRoom.underlay[9*32+9]==193);routes_valid=1;
 for(int variant=0;variant<4;variant++){
  base();CHECK(handoff_objects_build_field(7,variant,8,8,5,4));ring(8,8,5,4);stand(goal());handoff_objects_update();CHECK(!sObj.complete);
  if(variant==0){
   Mechanism* plate=find(HO_SWITCH);stand(plate);handoff_objects_update();CHECK(plate->state);stand(goal());handoff_objects_update();CHECK(!sObj.complete);
   Mechanism*m=find(HO_STATUE);hero.x=Q16(m->x);hero.y=Q16(m->y+18);hero.facing=FACE_N;gKeysHeld=KEY_R|KEY_UP;
   CHECK(handoff_objects_pre_player());for(int t=0;t<32;t++)CHECK(handoff_objects_pre_player());gKeysHeld=0;CHECK(m->x==plate->x&&m->y==plate->y);
  }else if(variant==1){tool(find(HO_FROZEN_FLOWER),LE_HIT_LANTERN);tool(find(HO_BARREL_WEB),LE_HIT_GUST_SMALL);}
  else if(variant==2)tool(find(HO_BEANSTALK),33);
  else tool(find(HO_PACCI_POT),LE_HIT_PACCI);
  stand(goal());handoff_objects_update();CHECK(sObj.complete);ring(8,8,5,4);
 }
 /* The visible red-fusion pool keeps the old route around its dry rim. */
 base();CHECK(!handoff_objects_build_fusion(7,8,8,5,4));CHECK(handoff_objects_build_fusion(7,8,8,5,5));ring(8,8,5,5);
 CHECK(room_type(10,11)==TT_WATER);stand(goal());handoff_objects_update();CHECK(!sObj.complete);
 gHandoffState.fusion_flags=4;hero.y=Q16(11*16+12);handoff_objects_update();CHECK(ground[11*32+10]==MT_LH_MOB_RAMP);CHECK(!sObj.complete);
 stand(goal());handoff_objects_update();CHECK(sObj.complete);ring(8,8,5,5);
 /* Pressure requires retained weight; a one-frame visit cannot solve it. */
 base();handoff_objects_build_regional(0,0);Mechanism*p=find(HO_SWITCH),*d=find(HO_METAL_DOOR);stand(p);handoff_objects_update();CHECK(!d->solid);hero.x=Q16(264);hero.y=Q16(334);handoff_objects_update();CHECK(d->solid);
 Mechanism*stone=find(HO_STATUE);stone->x=p->x;stone->y=p->y;handoff_objects_update();CHECK(!d->solid);
 /* A bridge writes collision at its own mirrored position. */
 for(int seed=0;seed<2;seed++){base();handoff_objects_build_regional(seed,6);Mechanism*b=find(HO_BRIDGE);CHECK(ground[(b->y/16)*32+b->x/16]==MT_LH_MOB_PIT);press(find(HO_PULL_LEVER));handoff_objects_update();CHECK(ground[(b->y/16)*32+b->x/16]==MT_LH_MOB_DECK);}
 base();handoff_objects_build_regional(0,8);Mechanism*ray=find(HO_LIGHT_RAY);hero.x=Q16(ray->x);hero.y=Q16(ray->y+32);hero.facing=FACE_N;gPl.shield_up=1;handoff_objects_update();CHECK(find(HO_LIGHT_RECEIVER)->state);CHECK(!find(HO_METAL_DOOR)->solid);
 base();handoff_objects_build_regional(0,10);tool(find(HO_PACCI_POT),LE_HIT_PACCI);tool(find(HO_EYE_SWITCH),LE_HIT_ARROW);tool(find(HO_HIT_LEVER),LE_HIT_THROWN);handoff_objects_update();CHECK((sObj.goals&7)==7&&!find(HO_METAL_DOOR)->solid);CHECK(!sObj.complete);
 base();handoff_objects_build_regional(0,11);tool(find(HO_BIG_ICE),33);CHECK(!find(HO_BIG_ICE)->state);tool(find(HO_BIG_ICE),34);tool(find(HO_FROZEN_FLOWER),LE_HIT_LANTERN);tool(find(HO_BARREL_WEB),LE_HIT_FIRE);handoff_objects_update();CHECK(!find(HO_METAL_DOOR)->solid);
 /* A consumed regional key cannot be lost to a door re-closing on revisit. */
 base();handoff_objects_build_regional(0,1);press(find(HO_BIG_DOOR));CHECK(gHandoffState.remaining[HS_TRAVERSAL]&0x100);CHECK(!find(HO_BIG_DOOR)->solid);handoff_objects_build_regional(0,1);CHECK(!find(HO_BIG_DOOR)->solid);
 base();handoff_objects_build_regional(0,7);Mechanism*keydoor=find(HO_BIG_DOOR);press(keydoor);CHECK(gHandoffState.remaining[HS_TRAVERSAL]&0x200);handoff_objects_build_regional(0,7);CHECK(!find(HO_BIG_DOOR)->solid);
 /* Chain eligibility must describe the actual tools needed by each puzzle. */
 memset(itemOwned,0,sizeof(itemOwned));memset(&gLegacyInventory,0,sizeof(gLegacyInventory));
 CHECK(handoff_objects_can_solve(0)&&handoff_objects_can_solve(1)&&handoff_objects_can_solve(2)&&handoff_objects_can_solve(3)&&handoff_objects_can_solve(5)&&handoff_objects_can_solve(6));
 CHECK(!handoff_objects_can_solve(4)&&!handoff_objects_can_solve(7)&&!handoff_objects_can_solve(8)&&!handoff_objects_can_solve(9)&&!handoff_objects_can_solve(10)&&!handoff_objects_can_solve(11));
 CHECK(handoff_objects_field_can_solve(0)&&!handoff_objects_field_can_solve(1)&&!handoff_objects_field_can_solve(2)&&!handoff_objects_field_can_solve(3));
 itemOwned[LI_BOTTLE1]=1;CHECK(handoff_objects_can_solve(4)&&handoff_objects_field_can_solve(2));
 itemOwned[LI_LANTERN_OFF]=1;CHECK(handoff_objects_field_can_solve(1));itemOwned[LI_BOTTLE_MINERAL_WATER]=1;CHECK(!handoff_objects_can_solve(11));gLegacyInventory.bottles[0]=LI_BOTTLE_MINERAL_WATER;CHECK(handoff_objects_can_solve(11));
 itemOwned[LI_POWER_BRACELETS]=1;itemOwned[LI_MIRROR_SHIELD]=1;itemOwned[LI_FOURSWORD]=1;itemOwned[LI_PACCI_CANE]=1;itemOwned[LI_BOW]=1;
 CHECK(handoff_objects_can_solve(7)&&handoff_objects_can_solve(8)&&handoff_objects_can_solve(9)&&handoff_objects_can_solve(10)&&handoff_objects_field_can_solve(3));
 handoff_objects_reset();CHECK(!handoff_objects_complete());CHECK(!handoff_objects_box_solid(0,0,512,384));
 printf("{\"checks\":%d,\"patterns\":12,\"object_families\":%d,\"seeds\":64,\"passed\":true}\n",checks,HO_COUNT);return 0;
}
'''

MOBILITY_MAIN=r'''
static int checks;
#define CHECK(c) do{checks++;if(!(c)){fprintf(stderr,"line%d: %s\n",__LINE__,#c);exit(1);}}while(0)
static void base(int area){memset(&hero,0,sizeof(hero));memset(&gPl,0,sizeof(gPl));memset(&gHandoffState,0,sizeof(gHandoffState));gRoom.w=32;gRoom.h=24;gGame.area=area;gGame.cell=7;for(int i=0;i<768;i++){ground[i]=MT_CAVE_FLOOR0;overlay[i]=MT_NONE;}gKeysDown=gKeysHeld=0;grants=notifies=0;hero.state=PS_NORMAL;hero.x=Q16(264);hero.y=Q16(334);}
static void ring(int x,int y,int w,int h){for(int yy=y;yy<y+h;yy++)for(int xx=x;xx<x+w;xx++)if(xx==x||xx==x+w-1||yy==y||yy==y+h-1)CHECK(room_type(xx,yy)==TT_FLOOR);}
int main(void){
 base(AREA_FOREST);overlay[9*32+9]=69;CHECK(handoff_mobility_build_field(42,0,47,8,8,6,5));CHECK(overlay[9*32+9]==MT_NONE);
 base(AREA_CREAM);overlay[9*32+9]=MT_CREAM_MOLD_S0;metatile_prop[MT_CREAM_MOLD_S0]=1;CHECK(handoff_mobility_build_field(42,1,47,8,8,6,5));CHECK(overlay[9*32+9]==MT_NONE);
 base(AREA_FOREST);overlay[9*32+9]=69;metatile_prop[69]=1;CHECK(!handoff_mobility_build_field(42,2,47,8,8,6,5));CHECK(overlay[9*32+9]==69);metatile_prop[69]=0;
 base(AREA_FOREST);overlay[9*32+9]=69;metatile_type[69]=TT_PIT;CHECK(!handoff_mobility_build_field(42,2,47,8,8,6,5));metatile_type[69]=TT_FLOOR;
 base(AREA_FOREST);overlay[9*32+9]=69;gRoom.underlay[9*32+9]=193;routes_valid=0;CHECK(!handoff_mobility_build_field(42,2,47,8,8,6,5));CHECK(!sMob.active&&overlay[9*32+9]==69&&ground[9*32+9]==MT_CAVE_FLOOR0&&gRoom.underlay[9*32+9]==193);routes_valid=1;
 for(int seed=0;seed<64;seed++)for(int p=0;p<3;p++)for(int a=0;a<2;a++){
  base(a?AREA_CREAM:AREA_FOREST);CHECK(handoff_mobility_build_field(seed,p,47,8,8,6,5));CHECK(active()&&sMob.field&&sMob.pattern==p);ring(8,8,6,5);
  CHECK(sMob.px>=8&&sMob.px<14&&sMob.py>=8&&sMob.py<13);
 }
 /* Suspended rails retain water semantics and the mounted cart supplies feet. */
 base(AREA_FOREST);CHECK(handoff_mobility_build_field(42,0,47,8,8,6,5));sPadCooldown=0;hero.x=Q16(gMobilityCartX);hero.y=Q16(gMobilityCartY+9);CHECK(handoff_mobility_interact());CHECK(handoff_mobility_busy());
 int water_frames=0;gKeysDown=KEY_A;
 for(int t=0;t<600&&gMobilityMode!=HMOB_WALK;t++){CHECK(handoff_mobility_pre_player());if(room_type_px(PX(hero.x),PX(hero.y))==TT_WATER)water_frames++;if(gMobilityMode==HMOB_CART)CHECK(handoff_mobility_handles_floor(PX(hero.x),PX(hero.y)));}
 CHECK(water_frames>0);CHECK(gMobilityMode==HMOB_WALK&&sMob.cart_done);CHECK(room_type_px(PX(hero.x),PX(hero.y))==TT_FLOOR);
 hero.x=Q16(tile_x(sMob.px));hero.y=Q16(tile_y(sMob.py));CHECK(handoff_mobility_interact());CHECK(grants==1&&(gHandoffState.remaining[47]&0x4000));CHECK(handoff_mobility_interact());CHECK(grants==1);
 /* Both bridge planes are live, with independent route completion. */
 base(AREA_CREAM);CHECK(handoff_mobility_build_field(42,1,47,8,8,6,5));int bx=(sMob.bx0+1)*16+8;
 hero.x=Q16(bx);hero.y=Q16(tile_y(sMob.by1));handoff_mobility_update();CHECK(gMobilityLayer==1);
 for(int y=PX(hero.y);y>=tile_y(sMob.by0)-20;y--){hero.y=Q16(y);handoff_mobility_update();}
 CHECK(sMob.bridge_done&&!gMobilityLayer);
 hero.y=Q16(tile_y(sMob.undery));for(int x=8*16+8;x<=14*16-8;x++){hero.x=Q16(x);handoff_mobility_update();CHECK(gMobilityLayer==0);}
 CHECK(sMob.under_done);CHECK(!handoff_mobility_handles_floor(bx,PX(hero.y)));
 /* The two upper rail edges block lateral leakage, including small bodies. */
 hero.x=Q16(bx);hero.y=Q16(tile_y(sMob.by0));handoff_mobility_update();CHECK(gMobilityLayer==1);CHECK(handoff_mobility_box_solid(sMob.bx0*16,hero.y>>16,sMob.bx0*16+3,(hero.y>>16)+4));
 /* A real launch, steer and folded descent ends on the dry lower shelf. */
 base(AREA_CREAM);CHECK(handoff_mobility_build_field(42,2,47,8,8,6,5));sPadCooldown=0;hero.x=Q16(tile_x(sMob.cx0+1));hero.y=Q16(tile_y(sMob.launch));gKeysDown=KEY_R;CHECK(handoff_mobility_pre_player());CHECK(gMobilityMode==HMOB_PARACHUTE);
 gKeysHeld=KEY_RIGHT|KEY_DOWN;gKeysDown=KEY_A;for(int t=0;t<600&&gMobilityMode!=HMOB_WALK;t++)CHECK(handoff_mobility_pre_player());
 CHECK(sMob.chute_done&&gMobilityMode==HMOB_WALK);CHECK(PX(hero.y)==tile_y(sMob.landing));CHECK(room_type_px(PX(hero.x),PX(hero.y))==TT_FLOOR);ring(8,8,6,5);
 /* The three large room routes are single-purpose, not the old course. */
 for(int p=0;p<3;p++){base(AREA_HANDOFF);handoff_mobility_build_regional(42,p,90);CHECK(active()&&sMob.regional&&!sMob.field);CHECK(sMob.cart+sMob.bridge+sMob.chute==1);CHECK(sMob.site==90);
  /* The ordinary doorway supplies (264,334), with no swimming tool.
     Both the full feet box and the south return corridor must stay dry. */
  for(int y=20;y<=21;y++)for(int x=15;x<=16;x++){CHECK(room_type(x,y)==TT_FLOOR);CHECK(!room_box_solid(x*16+3,y*16+5,x*16+12,y*16+14));CHECK(!handoff_mobility_box_solid(x*16+3,y*16+5,x*16+12,y*16+14));}
 }
 handoff_mobility_reset();CHECK(!active()&&!handoff_mobility_busy());CHECK(!handoff_mobility_handles_floor(150,150));
 printf("{\"checks\":%d,\"patterns\":3,\"field_builds\":384,\"passed\":true}\n",checks);return 0;
}
'''

def compile_run(source,name,out):
    c=out/(name+'.c');c.write_text(source);exe=out/name
    cmd=['cc','-std=gnu11','-O1','-g','-fsanitize=undefined,bounds','-fno-sanitize-recover=all',str(c),'-o',str(exe)]
    r=subprocess.run(cmd,capture_output=True,text=True);(out/(name+'-compile.log')).write_text(r.stdout+r.stderr);r.check_returncode()
    r=subprocess.run([str(exe)],capture_output=True,text=True);(out/(name+'-run.log')).write_text(r.stdout+r.stderr);r.check_returncode();return json.loads(r.stdout)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    object_fixture=O.fixture().replace("bool8 legacy_item_owned(int item){(void)item;return TRUE;}","static u8 itemOwned[256];bool8 legacy_item_owned(int item){return item>=0&&item<256&&itemOwned[item];}");objects=compile_run(object_fixture+OBJECT_MAIN,'regional-objects',a.out)
    mobility=compile_run(M.fixture()+MOBILITY_MAIN,'regional-mobility',a.out)
    files=['src/handoff_objects.c','src/handoff_objects.h','src/handoff_mobility.c','src/handoff_mobility.h','art/handoff_mobility.py']
    adapters=['tools/handoff_mobility_host.py','tools/handoff_objects_host.py']
    report=dict(method=__doc__,passed=True,objects=objects,mobility=mobility,checks=objects['checks']+mobility['checks'],source_sha256={n:digest(GAME/n) for n in files},adapter_sha256={n:digest(GAME/n) for n in adapters},asset_symbol_registry_sha256=digest(GAME/'build/gen/assets.h'),tool_sha256=digest(__file__))
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
