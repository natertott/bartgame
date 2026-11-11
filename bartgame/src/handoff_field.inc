/* Regional field events share the ordinary generated geometry. No full field
   is cleared or substituted with an Annex room. All anchors and spawn points
   are surveyed against the loaded room's actual dry component. */
static bool8 regional_scene(void){return r.active&&r.plan.area==gGame.area&&r.plan.cell==gGame.cell;}
static bool8 regional_quest_local(void){
 HandoffQuest*q=&gHandoffState.quest;
 return regional_scene()&&q->origin_area==gGame.area&&q->origin_cell==gGame.cell&&q->kind;
}
static bool8 field_has(int x,int y){
 int n=y*32+x;return x>=0&&y>=0&&x<gRoom.w&&y<gRoom.h&&(r.component[n>>3]&(1u<<(n&7)));
}
static bool8 field_floor(int x,int y){
 int t,px=sx(x),py=sy(y);
 if(x<1||y<1||x>=gRoom.w-1||y>=gRoom.h-1)return FALSE;
 t=room_type(x,y);if(t!=TT_FLOOR&&t!=TT_SLOW&&t!=TT_SWITCH)return FALSE;
 if(room_box_solid(px-5,py-8,px+4,py-1))return FALSE;
 if(gGame.area==AREA_CREAM&&!cream_room_node_floor(gGame.cell*2+r.plan.terrace,x,y))return FALSE;
 return TRUE;
}
static void field_component(Spot start){
 int head=0,tail=0;clear_bytes(r.component,sizeof(r.component));
 if(!field_floor(start.x,start.y))return;
 r.queue[tail++]=start.y*32+start.x;r.component[(start.y*32+start.x)>>3]|=1u<<((start.y*32+start.x)&7);
 while(head<tail){int at=r.queue[head++],x=at%32,y=at/32;
  for(int d=0;d<4;d++){int nx=x+sDX[d],ny=y+sDY[d],n=ny*32+nx;
   if(!field_floor(nx,ny)||field_has(nx,ny))continue;
   r.component[n>>3]|=1u<<(n&7);r.queue[tail++]=n;
  }
 }
}
static bool8 field_point(int salt,int distance,Spot* out){
 u32 best=0;bool8 found=FALSE;
 for(int y=1;y<gRoom.h-1;y++)for(int x=1;x<gRoom.w-1;x++){
  u32 score;int reject=0;if(!field_has(x,y)||regional_content_reserved(x,y))continue;
  if(ABS(x-r.giver.x)+ABS(y-r.giver.y)<distance||(ABS(x-r.giver.x)<3&&ABS(y-r.giver.y)<3))continue;
  if(room_box_solid(sx(x)-8,sy(y)-14,sx(x)+7,sy(y)))continue;
  for(int i=0;i<r.point_count;i++)if(ABS(x-r.points[i].x)+ABS(y-r.points[i].y)<2){reject=1;break;}
  if(reject)continue;
  score=hash32(gGame.seed^s.seed,salt*1009+x+y*32);
  if(!found||score>best){best=score;out->x=x;out->y=y;found=TRUE;}
 }
 return found;
}
static int field_alive(void){int count=0;for(int i=1;i<ACTOR_MAX;i++)if(r.owned[i]&&gActors[i].kind==AK_ENEMY)count++;return count;}
void handoff_track_enemy(Actor* enemy,const Actor* parent){
 int at;if(!regional_scene()||!enemy||enemy<gActors||enemy>=gActors+ACTOR_MAX)return;
 at=enemy-gActors;
 if(parent&&parent>=gActors&&parent<gActors+ACTOR_MAX&&r.owned[parent-gActors])r.owned[at]=1;
 else if(field_has(PX(enemy->x)/16,PX(enemy->y)/16))r.owned[at]=1;
}
static bool8 field_spawn(int type){
 Spot best={0,0};u32 score=0;bool8 found=FALSE;
 for(int y=2;y<gRoom.h-2;y++)for(int x=2;x<gRoom.w-2;x++){
  int px=sx(x),py=sy(y);u32 value;bool8 clear=TRUE;
  if(!field_has(x,y)||regional_content_reserved(x,y)||room_box_solid(px-10,py-16,px+9,py+2))continue;
  if(ABS(px-PX(gPlayer->x))<56&&ABS(py-PX(gPlayer->y))<48)continue;
  for(int i=1;i<ACTOR_MAX;i++)if(gActors[i].kind==AK_ENEMY&&ABS(px-PX(gActors[i].x))<24&&ABS(py-PX(gActors[i].y))<24){clear=FALSE;break;}
  if(!clear)continue;
  value=hash32(s.seed+s.clock,x+y*32);
  if(!found||value>score){score=value;best.x=x;best.y=y;found=TRUE;}
 }
 if(!found)return FALSE;
 if(type<0)type=wave_pick();
 if(!legacy_enemy_can_spawn(type))return FALSE;
 Actor*a=enemy_spawn(type,sx(best.x),sy(best.y));if(!a)return FALSE;
 r.owned[a-gActors]=1;fx_spawn(FX_PUFF,PX(a->x),PX(a->y)-8);return TRUE;
}
static void field_refill(int target){
 int count=field_alive();for(int i=count;i<target&&i<6;i++)if(!field_spawn(-1))break;
}
static void field_wave_begin(void){
 int n=r.wave_site,wave=gHandoffState.wave[n];
 if(!wave)gHandoffState.wave[n]=wave=1;
 rng_seed(&s.rng,hash32(s.seed,wave));cast_wave_at(MIN(12,gHandoffState.difficulty+wave/3));
 if(!gHandoffState.remaining[n])gHandoffState.remaining[n]=MAX(field_alive(),MAX(3,(3+MIN(9,wave/2)+gHandoffState.difficulty/3)*sShapes[s.theme].percent/100));
 field_refill(MIN(3,gHandoffState.remaining[n]));
}
static void field_reward(int tier){
 int item=random_reward(tier),x=sx(gRegionalSpots.cache.x),y=sy(gRegionalSpots.cache.y);
 if(!gRegionalSpots.has_cache){x=sx(r.giver.x);y=sy(r.giver.y);}
 if(!legacy_item_spawn(item,x,y))give(item);
 sfx_play(SFX_CHEST);
}
static void field_quest_win(void){
 HandoffQuest*q=&gHandoffState.quest;if(q->state==3)return;
 q->state=3;if(q->kind==HQ_BLOCKS)r.board=0;HSET(gHandoffState.completed,r.plan.field_site);
 gHandoffState.score+=20+5*q->difficulty;refresh_rank();
 field_reward(1);handoff_notify(HN_QUEST,q->origin_area,q->origin_cell,0);sfx_play(SFX_SECRET);
}
static void field_board_setup(void){
 int base=768;RegionalContentRect rect;
 rect=gRegionalSpots.quest_rect;
 if(rect.w!=7||rect.h!=7){r.board=0;return;}
 r.board_rect=rect;r.board=1;s.board_x=rect.x+1;s.board_y=rect.y+1;
 s.kind=HS_QUEST_BLOCKS;s.site=r.plan.field_site;
 gHandoffPuzzleIndex=base+hash32(s.seed,33)%760;
 if(!handoff_puzzle_verify(handoff_puzzle(gHandoffPuzzleIndex)))gHandoffPuzzleIndex=base;
 for(int i=0;i<3;i++)gHandoffBoardBlocks[i]=handoff_puzzle(gHandoffPuzzleIndex)->blocks[i];
 gHandoffBoardPlayer=handoff_puzzle(gHandoffPuzzleIndex)->entry;gHandoffPushes=gHandoffBoardSolved=0;
}
static void field_quest_start(void){
 HandoffQuest*q=&gHandoffState.quest;char message[300];char*p;int kind=r.plan.quest_kind;
 if(!kind||kind==RC_NONE)return;
 clear_bytes(q,sizeof(*q));q->kind=kind;q->state=1;q->difficulty=gHandoffState.difficulty;
 q->stake=q->difficulty<4?0:q->difficulty<8?1:q->difficulty<12?2:3;
 q->origin_area=gGame.area;q->origin_cell=gGame.cell;q->quota=kind==HQ_HUNT?7+rng_range(&s.rng,7):kind==HQ_POT?MAX(1,r.point_count):1;
 q->timer=kind==HQ_HUNT?1800:kind==HQ_STEALTH?2400:kind==HQ_SCAV?2700:0;
 q->target_area=gGame.area==AREA_FOREST?AREA_CREAM:AREA_FOREST;
 q->target_cell=q->target_area==AREA_FOREST?gWorld.entry:cream_cell(gCreamWorld.entry_node);
 q->cargo_x=sx(r.point_count?r.points[0].x:r.giver.x);q->cargo_y=sy(r.point_count?r.points[0].y:r.giver.y);q->cargo_ground=1;
 q->receiver_x=sx(r.receiver.x);q->receiver_y=sy(r.receiver.y);s.clean=0;q->mode=hash32(s.seed,41)%3;
 if(kind==HQ_POT)q->wave=s.count=hash32(s.seed,29)%MAX(1,r.point_count);
 if(kind==HQ_SCAV){
  Spot origin={q->cargo_x/16,q->cargo_y/16},start={r.giver.x,r.giver.y},found;
  if(q->mode==2&&!legacy_item_owned(LI_MOLE_MITTS))q->mode=1;
  if(q->mode&&!world_hidden_find(q->mode==2?WH_DIG:WH_CUT,origin,start,8,&found))q->mode=0;
  else if(q->mode){q->cargo_x=sx(found.x);q->cargo_y=sy(found.y);}
 }
 if(kind==HQ_BLOCKS){field_board_setup();if(!r.board){q->state=0;say("The stones need a wider clearing. The route remains open; return after exploring another approach.");return;}}
 if(kind==HQ_COURIER)q->cargo_held=1;
 p=cat(message,"Quest accepted. Failure costs ");p=cat(p,q->stake==0?"nothing":q->stake==1?"up to 50 gilt":q->stake==2?"up to 100 gilt and half health":"up to 200 gilt, half health and one good charm");p=cat(p,". ");
 p=cat(p,kind==HQ_POT?"Search these marked pots with your sword.":kind==HQ_HUNT?"Defeat the pack within 30 seconds.":kind==HQ_SCAV?"Follow the glint. Catch it, cut its cover, or dig its earth.":kind==HQ_STEALTH?"Reach the far seal without entering the watchers' sight.":kind==HQ_CARRY?"A lifts the sound pot. Carry it through two ambushes to the receiver. Recover it if thrown.":kind==HQ_COURIER?"Carry this parcel to the messenger beside the other region's arrival.":"Push the field stones to open the marked goal. Select safely resets them.");
 if(kind==HQ_COURIER){p=cat(p," Destination: ");p=cat(p,q->target_area==AREA_FOREST?"Forest ":"Cream ");p=num(p,q->target_cell%5+1);p=cat(p,",");p=num(p,q->target_cell/5+1);cat(p,".");}
 say(message);if(kind==HQ_HUNT){cast_wave();field_refill(MIN(4,q->quota));}
}
static void field_icon_load(int frame){
 const SpriteSheet*sh=&sheets[SHEET_HANDOFF];u16 tile;
 if(frame<0||frame>=32||r.icons[frame])return;
 tile=sprite_alloc(sh->frame_tiles);if(!tile)return;
 r.icons[frame]=tile;vram_queue(sh->tiles+frame*sh->frame_tiles*16,OBJ_TILE(tile),sh->frame_tiles*32);
}
static void field_icons(void){
 int kind=r.plan.quest_kind;
 if(gRegionalSpots.has_cache){field_icon_load(HA_TOKEN);field_icon_load(HA_GOAL);}
 if(gRegionalSpots.has_npc)field_icon_load(HA_FUSER);
 if(r.plan.fusion_color==0){field_icon_load(HA_GOLD);field_icon_load(HA_GOAL);}
 if(kind==HQ_POT||kind==HQ_CARRY){field_icon_load(HA_POT);field_icon_load(HA_RECIPIENT);}
 if(kind==HQ_SCAV){field_icon_load(HA_TOKEN);field_icon_load(HA_LEAF);field_icon_load(HA_GOAL);}
 if(kind==HQ_STEALTH){for(int i=0;i<4;i++)field_icon_load(HA_WATCH_N+i);field_icon_load(HA_GOAL);}
 if(kind==HQ_COURIER)field_icon_load(HA_PARCEL);
 if(kind==HQ_BLOCKS){for(int i=HA_BLOCK_FREE;i<=HA_RESET;i++)field_icon_load(i);}
}
static void field_door_refresh(void){
 int frame;const SpriteSheet*sh;
 if(!r.door_tile)return;
 frame=gRegionalSpots.compact_door?r.door_base+(regional_content_door_open(gGame.area,gGame.cell)?1:0):r.door_base+(regional_content_door_open(gGame.area,gGame.cell)?0:3);
 if(r.door_frame==frame)return;
 sh=&sheets[r.door_sheet];vram_queue(sh->tiles+frame*sh->frame_tiles*16,OBJ_TILE(r.door_tile),sh->frame_tiles*32);
 r.door_frame=frame;r.door_pal=gRegionalSpots.compact_door?handoff_mechanisms_frame_pal[frame]:interactiveentry_frame_pal[frame];
}
static bool8 regional_door_solid(int x0,int y0,int x1,int y1){
 int px,py;
 if(!regional_scene()||!r.door_tile||!gRegionalSpots.has_door||gRegionalSpots.compact_door||regional_content_door_open(gGame.area,gGame.cell))return FALSE;
 px=sx(gRegionalSpots.door.x);py=sy(gRegionalSpots.door.y);
 return x0<=px+7&&x1>=px-8&&y0<=py-6&&y1>=py-18;
}
static bool8 field_door(bool8 walking){
 int px,py,foot;
 if(!regional_scene()||!gRegionalSpots.has_door||!r.door_tile||gPlayer->state!=PS_NORMAL)return FALSE;
 px=PX(gPlayer->x);py=PX(gPlayer->y);foot=sy(gRegionalSpots.door.y);
 if(!field_has(px/16,py/16))return FALSE;
 if(ABS(px-sx(gRegionalSpots.door.x))>(walking?12:23))return FALSE;
 if(gRegionalSpots.compact_door){if(walking||ABS(py-foot)>23)return FALSE;}
 else{
  if(py<foot-48||py>foot+32)return FALSE;
  if(walking&&(!(gKeysHeld&KEY_UP)||gPlayer->facing!=FACE_N||py>foot+8||r.door_latch))return FALSE;
 }
 r.door_latch=1;
 if(!regional_content_door_open(gGame.area,gGame.cell)){
  say(r.plan.fusion_color==1?"The blue shaped half will open this pocket entrance.":"This pocket entrance sleeps. Clear its paired portal trial elsewhere in the regions.");return TRUE;
 }
 game_open_handoff(r.plan.interior_site,r.plan.event_kind);return TRUE;
}
static void regional_enter(int area,int cell){
 HandoffQuest*q=&gHandoffState.quest;Spot start;
 if(!regional_content_get(area,cell,&r.plan))return;
 r.active=1;r.scav_dir=255;s.site=r.plan.field_site;s.kind=HS_HUB;s.board_x=7;s.board_y=8;
 s.seed=hash32(gGame.seed,0xF1E1D00u+r.plan.field_site);s.clock=0;s.clean=0;s.count=0;r.wave_site=132+(area==AREA_CREAM);rng_seed(&s.rng,s.seed);
 r.giver=gRegionalSpots.has_npc?gRegionalSpots.npc:gRegionalSpots.has_cache?gRegionalSpots.cache:(Spot){PX(gPlayer->x)/16,PX(gPlayer->y)/16};
 start=r.giver;field_component(start);
 if(!field_has(start.x,start.y)){start.x=PX(gPlayer->x)/16;start.y=PX(gPlayer->y)/16;field_component(start);r.giver=start;}
 for(int i=0;i<6;i++){Spot p;if(field_point(i,2,&p)){r.points[r.point_count++]=p;}}
 if(!r.point_count){r.points[0]=r.giver;r.point_count=1;}
 r.receiver=r.point_count?r.points[r.point_count-1]:r.giver;
 field_icons();
 if(gRegionalSpots.has_door){
  if(gRegionalSpots.compact_door){r.door_sheet=SHEET_HANDOFF_MECHANISMS;r.door_base=38;}
  else{r.door_sheet=SHEET_INTERACTIVEENTRY;r.door_base=area==AREA_FOREST?hash32(gGame.seed,cell+0x5448454du)%3:0;}
  r.door_frame=255;r.door_tile=sprite_alloc(sheets[r.door_sheet].frame_tiles);field_door_refresh();
 }
 for(int i=1;i<ACTOR_MAX;i++)if(gActors[i].kind==AK_ENEMY)handoff_track_enemy(&gActors[i],NULL);
 r.quest_ready=r.plan.quest_kind&&r.plan.quest_kind!=RC_NONE&&!HBIT(gHandoffState.completed,r.plan.field_site);
 if(regional_quest_local()&&q->state==2){
  if(q->kind==HQ_BLOCKS)field_board_setup();
  if(q->kind==HQ_POT){s.clean=q->count;s.count=q->wave;}
  if(q->kind==HQ_CARRY){q->cargo_held=q->cargo_flying=0;q->cargo_ground=1;q->cargo_x=sx(r.giver.x);q->cargo_y=sy(r.giver.y);}
 }
 if(gRegionalSpots.has_mechanism&&r.plan.fusion_color==2){
  RegionalContentRect* b=&gRegionalSpots.mechanism_rect;
  if(handoff_objects_build_fusion(s.seed,b->x,b->y,b->w,b->h))handoff_objects_enter();
 }else if(gRegionalSpots.has_mechanism&&r.plan.field_mechanism_variant!=RC_NONE){
  RegionalContentRect* b=&gRegionalSpots.mechanism_rect;
  if(handoff_objects_build_field(s.seed,r.plan.field_mechanism_variant,b->x,b->y,b->w,b->h))handoff_objects_enter();
 }
 if(r.plan.traversal_variant!=RC_NONE&&gRegionalSpots.traversal_rect.w){
  RegionalContentRect*b=&gRegionalSpots.traversal_rect;handoff_mobility_build_field(s.seed,r.plan.traversal_variant,r.plan.field_site,b->x,b->y,b->w,b->h);
 }
 if(r.plan.has_wave){s.cast_count=0;if(field_has(PX(gPlayer->x)/16,PX(gPlayer->y)/16))field_wave_begin();}
}
static bool8 regional_interact(void){
 HandoffQuest*q=&gHandoffState.quest;int site=r.plan.field_site;
 if(!regional_scene())return FALSE;
 if(field_door(FALSE))return TRUE;
 if(handoff_mobility_interact())return TRUE;
 if(!field_has(PX(gPlayer->x)/16,PX(gPlayer->y)/16))return FALSE;
 if(gHandoffState.contract_state==1&&gHandoffState.contract_kind==HC_ITEM&&gHandoffState.contract_target==site&&gRegionalSpots.has_cache&&near(sx(gRegionalSpots.cache.x),sy(gRegionalSpots.cache.y),24)){
  int item=gHandoffState.contract_item;if(gHandoffState.contract_step==4)materialize_goal();else give(item);sfx_play(SFX_CHEST);return TRUE;
 }
 if(q->state==2&&q->kind==HQ_COURIER&&q->target_area==gGame.area&&q->target_cell==gGame.cell&&near(sx(r.giver.x),sy(r.giver.y),24)){
  q->state=3;q->cargo_held=0;RegionalContentPlan origin;
  if(regional_content_get(q->origin_area,q->origin_cell,&origin))HSET(gHandoffState.completed,origin.field_site);
  gHandoffState.score+=30;refresh_rank();field_reward(1);handoff_notify(HN_QUEST,q->origin_area,q->origin_cell,0);say("A parcel between the wood and the high cliffs. Delivered safely; your reward is here.");return TRUE;
 }
 if(gRegionalSpots.has_npc&&near(sx(r.giver.x),sy(r.giver.y),24)){
  if(r.plan.fusion_color!=RC_NONE){fuse(r.plan.fusion_color);return TRUE;}
  if(r.plan.quest_kind&&r.plan.quest_kind!=RC_NONE){
   if(HBIT(gHandoffState.completed,site)){say("Your kindness left its mark on this place.");return TRUE;}
   if(q->state==1||q->state==2){say(regional_quest_local()?"The task is still before you. Its stake has not changed.":"Finish the task you already accepted; its giver is still waiting.");return TRUE;}
   field_quest_start();return TRUE;
  }
 }
 if(r.plan.fusion_color==0&&gRegionalSpots.has_cache&&near(sx(gRegionalSpots.cache.x),sy(gRegionalSpots.cache.y),24)){
  if(!(gHandoffState.fusion_flags&1)){say("The green shaped fusion opens this field cache.");return TRUE;}
  if(!(gHandoffState.remaining[site]&0x4000)){gHandoffState.remaining[site]|=0x4000;give(LI_RUPEE100);sfx_play(SFX_CHEST);}else say("The little cache is empty.");return TRUE;
 }
 if(regional_quest_local()&&q->state==2){
  if(q->kind==HQ_POT)for(int i=0;i<r.point_count;i++)if(!(s.clean&(1u<<i))&&near(sx(r.points[i].x),sy(r.points[i].y),18)){s.clean|=1u<<i;q->count=s.clean;sfx_play(SFX_HIT);if(i==s.count)field_quest_win();return TRUE;}
  if(q->kind==HQ_CARRY){
   if(q->cargo_ground&&!gPl.carry&&near(q->cargo_x,q->cargo_y,22)){q->cargo_ground=0;q->cargo_held=1;gPl.carry=CARRY_POT;gPlayer->state=PS_LIFT;gPlayer->timer=0;sfx_play(SFX_ITEM);return TRUE;}
   if(q->cargo_held&&near(q->receiver_x,q->receiver_y,24)){if(q->wave<2||field_alive()){say("Two ambushes stand between this pot and rest.");return TRUE;}q->cargo_held=0;gPl.carry=CARRY_NONE;gPlayer->state=PS_NORMAL;field_quest_win();say("Not a crack. A careful field delivery.");return TRUE;}
  }
  if(q->kind==HQ_BLOCKS&&r.board){if(near(sx(BOARD_X+2),sy(BOARD_Y+5),22)){handoff_board_reset();return TRUE;}if(handoff_board_push(gPlayer->facing))return TRUE;}
 }
 return FALSE;
}
static void regional_enemy_killed(int type,int px,int py){
 HandoffQuest*q=&gHandoffState.quest;bool8 owned=FALSE;
 if(!regional_scene())return;
 for(int i=1;i<ACTOR_MAX;i++)if(r.owned[i]&&gActors[i].kind==AK_ENEMY&&gActors[i].type==type&&PX(gActors[i].x)==px&&PX(gActors[i].y)==py){r.owned[i]=0;owned=TRUE;break;}
 if(!owned)return;
 if(r.plan.has_wave&&gHandoffState.remaining[r.wave_site])gHandoffState.remaining[r.wave_site]--;
 if(regional_quest_local()&&q->state==2&&q->kind==HQ_HUNT){q->count++;if(q->count>=q->quota)field_quest_win();}
}
static void regional_tool(int kind,int x0,int y0,int x1,int y1){
 HandoffQuest*q=&gHandoffState.quest;if(!regional_scene())return;
 handoff_objects_tool_box(kind,x0,y0,x1,y1);
 if(!regional_quest_local()||q->state!=2)return;
 if(q->kind==HQ_POT&&kind==LE_HIT_SWORD)for(int i=0;i<r.point_count;i++)if(!(s.clean&(1u<<i))&&sx(r.points[i].x)>=x0-8&&sx(r.points[i].x)<=x1+8&&sy(r.points[i].y)>=y0&&sy(r.points[i].y)<=y1+14){s.clean|=1u<<i;q->count=s.clean;sfx_play(SFX_HIT);if(i==s.count)field_quest_win();}
 if(q->kind==HQ_SCAV&&((q->mode==2&&kind==HTOOL_DIG)||(q->mode==1&&kind==LE_HIT_SWORD))&&q->cargo_x>=x0-8&&q->cargo_x<=x1+8&&q->cargo_y>=y0&&q->cargo_y<=y1+14)field_quest_win();
}
static void regional_tile(int tx,int ty){
 HandoffQuest*q=&gHandoffState.quest;if(!regional_scene())return;
 if(regional_quest_local()&&q->state==2&&q->kind==HQ_SCAV&&q->mode==1&&tx==q->cargo_x/16&&ty==q->cargo_y/16)field_quest_win();
}
static void field_scav_move(void){
 HandoffQuest*q=&gHandoffState.quest;int x=q->cargo_x,y=q->cargo_y;
 if(near(x,y,14)){field_quest_win();return;}
 if(s.clock&1)return;
 if((x&15)==8&&(y&15)==14){
  int start=(y/16)*32+x/16,head=0,tail=0;Spot goal=r.points[q->wave%r.point_count];
  if(goal.x==x/16&&goal.y==y/16){q->wave=(q->wave+1)%r.point_count;goal=r.points[q->wave];}
  clear_bytes(r.scav_path,sizeof(r.scav_path));for(int i=0;i<768;i++)r.scav_path[i]=255;
  int at=goal.y*32+goal.x;r.scav_path[at]=4;r.queue[tail++]=at;
  while(head<tail&&r.scav_path[start]==255){
   at=r.queue[head++];
   for(int d=0;d<4;d++){int nx=at%32+sDX[d],ny=at/32+sDY[d],n=ny*32+nx;
    if(!field_has(nx,ny)||r.scav_path[n]!=255)continue;
    r.scav_path[n]=(d+2)&3;r.queue[tail++]=n;
   }
  }
  r.scav_dir=r.scav_path[start]<4?r.scav_path[start]:255;
 }else if(r.scav_dir==255){
  int dx=x/16*16+8-x,dy=y/16*16+14-y;
  r.scav_dir=ABS(dx)>ABS(dy)?(dx>0?1:3):(dy>0?2:0);
 }
 if(r.scav_dir<4){int nx=x+sDX[r.scav_dir],ny=y+sDY[r.scav_dir];
  if(field_has(nx/16,ny/16)&&!room_box_solid(nx-2,ny-3,nx+1,ny)){q->cargo_x=nx;q->cargo_y=ny;}else r.scav_dir=255;
 }
}
static void regional_tick(void){
 HandoffQuest*q=&gHandoffState.quest;
 if(!regional_scene())return;
 if(!(gKeysHeld&KEY_UP))r.door_latch=0;
 if(field_door(TRUE))return;
 handoff_objects_update();handoff_mobility_update();
 if(gRegionalSpots.has_mechanism&&handoff_objects_complete()&&!(gHandoffState.remaining[r.plan.field_site]&0x8000)){
  gHandoffState.remaining[r.plan.field_site]|=0x8000;field_reward(1);handoff_notify(HN_EVENT,gGame.area,gGame.cell,0);
 }
 if(q->state==1&&!textbox_active())q->state=2;
 if(q->state==2&&q->origin_area!=AREA_HANDOFF){
  if(regional_quest_local()){
   if(q->kind==HQ_HUNT&&r.cadence==0&&field_has(PX(gPlayer->x)/16,PX(gPlayer->y)/16))field_refill(MIN(4,(int)q->quota-q->count));
   if(q->kind==HQ_SCAV&&q->mode==0&&r.point_count)field_scav_move();
   if(q->kind==HQ_STEALTH){
    for(int i=0;!near(sx(r.giver.x),sy(r.giver.y),32)&&i<MIN(3,r.point_count);i++){Spot p=r.points[i];if(watcher_sees(sx(p.x),sy(p.y),((s.clock/120)+i)&3)){quest_fail();break;}}
    if(q->state==2&&near(q->receiver_x,q->receiver_y,15))field_quest_win();
   }
   if(q->kind==HQ_CARRY){
    if(q->cargo_held&&gPl.carry!=CARRY_POT&&!q->cargo_flying){q->cargo_held=0;q->cargo_ground=1;q->cargo_x=PX(gPlayer->x);q->cargo_y=PX(gPlayer->y);}
    if(q->cargo_held&&field_has(PX(gPlayer->x)/16,PX(gPlayer->y)/16)&&((q->wave==0&&ABS(PX(gPlayer->x)-sx(r.giver.x))+ABS(PX(gPlayer->y)-sy(r.giver.y))>40)||(q->wave==1&&!field_alive()&&near(q->receiver_x,q->receiver_y,64)))){q->wave++;cast_wave();field_refill(q->wave+2);sfx_play(SFX_SPIT);}
   }
   if(q->kind==HQ_BLOCKS&&r.board&&gHandoffBoardSolved)field_quest_win();
  }
 }
 if(r.plan.has_wave&&field_has(PX(gPlayer->x)/16,PX(gPlayer->y)/16)){
  if(r.pause){if(!--r.pause)field_wave_begin();}
  else if(!gHandoffState.remaining[r.wave_site]&&!field_alive()){
   HSET(gHandoffState.won,r.plan.field_site);
   if(!HBIT(gHandoffState.completed,r.wave_site)){HSET(gHandoffState.completed,r.wave_site);field_reward(1);}
   handoff_notify(HN_WAVE,gGame.area,gGame.cell,0);
   gHandoffState.wave[r.wave_site]++;r.pause=180;
   if(gHandoffState.wave[r.wave_site]==5&&!FOOD(HF_FLEET)){give(HANDOFF_FLEET);say("Five field waves. A golden croissant grants Fleet.");}
  }else if(!r.cadence){if(!gHandoffState.remaining[r.wave_site]||!s.cast_count)field_wave_begin();else if(field_alive()<3)field_refill(MIN(3,gHandoffState.remaining[r.wave_site]));}
 }
 int x0,y0,x1,y1;
 if(player_lamp_box(&x0,&y0,&x1,&y1))regional_tool(LE_HIT_LANTERN,x0,y0,x1,y1);
 if(player_sword_box(&x0,&y0,&x1,&y1))regional_tool(LE_HIT_SWORD,x0,y0,x1,y1);
 r.cadence=(r.cadence+1)%20;
}
static void field_prop(int frame,int x,int y,int priority){
 if(frame<0||frame>=32||!r.icons[frame]||x-gCamX<-16||y-gCamY<-16||x-gCamX>256||y-gCamY>176)return;
 draw_sprite(x-8-gCamX,y-16-gCamY,SHEET_HANDOFF,r.icons[frame],0,0,priority,PAL_OBJ_FX);
}
static void regional_draw(void){
 HandoffQuest*q=&gHandoffState.quest;int site=r.plan.field_site;
 if(!regional_scene())return;
 if(gRegionalSpots.has_door&&r.door_tile){
  field_door_refresh();
  int px=sx(gRegionalSpots.door.x),py=sy(gRegionalSpots.door.y);
  draw_sprite(px-16-gCamX,py-(gRegionalSpots.compact_door?28:62)-gCamY,r.door_sheet,r.door_tile,0,0,2,r.door_pal);
 }
 handoff_objects_draw();handoff_mobility_draw();
 if((gRegionalSpots.has_npc&&(r.plan.quest_kind||r.plan.fusion_color!=RC_NONE))||(q->state==2&&q->kind==HQ_COURIER&&q->target_area==gGame.area&&q->target_cell==gGame.cell))field_prop(HA_FUSER,sx(r.giver.x),sy(r.giver.y),1);
 if(gHandoffState.contract_state==1&&gHandoffState.contract_kind==HC_ITEM&&gHandoffState.contract_target==site&&gRegionalSpots.has_cache)field_prop(HA_TOKEN,sx(gRegionalSpots.cache.x),sy(gRegionalSpots.cache.y),1);
 if(r.plan.fusion_color==0&&gRegionalSpots.has_cache&&!(gHandoffState.remaining[site]&0x4000))field_prop(gHandoffState.fusion_flags&1?HA_GOLD:HA_GOAL,sx(gRegionalSpots.cache.x),sy(gRegionalSpots.cache.y),1);
 if(r.plan.has_wave)field_prop(HA_TOKEN,sx(r.giver.x),sy(r.giver.y),1);
 if(regional_quest_local()&&(q->state==1||q->state==2)){
  if(q->kind==HQ_POT)for(int i=0;i<r.point_count;i++)if(!(s.clean&(1u<<i)))field_prop(HA_POT,sx(r.points[i].x),sy(r.points[i].y),1);
  if(q->kind==HQ_SCAV)field_prop(q->mode==0?HA_TOKEN:q->mode==1?HA_LEAF:HA_GOAL,q->cargo_x,q->cargo_y,1);
  if(q->kind==HQ_STEALTH){for(int i=0;i<MIN(3,r.point_count);i++){Spot p=r.points[i];int face=((s.clock/120)+i)&3;field_prop(HA_WATCH_N+face,sx(p.x),sy(p.y),1);for(int j=1;j<4;j++)if(field_has(p.x+sDX[face]*j,p.y+sDY[face]*j))field_prop(HA_GOAL,sx(p.x+sDX[face]*j),sy(p.y+sDY[face]*j),2);}field_prop(HA_GOAL,q->receiver_x,q->receiver_y,1);}
  if(q->kind==HQ_CARRY){if(q->cargo_ground)field_prop(HA_POT,q->cargo_x,q->cargo_y,1);field_prop(HA_RECIPIENT,q->receiver_x,q->receiver_y,1);}
  if(q->kind==HQ_COURIER)field_prop(HA_PARCEL,sx(r.giver.x),sy(r.giver.y),1);
  if(q->kind==HQ_BLOCKS&&r.board){
   const HandoffPuzzle*p=handoff_puzzle(gHandoffPuzzleIndex);
   for(int y=-1;y<=5;y++)for(int x=-1;x<=5;x++){
    int cell=y*5+x;
    if(x>=0&&x<5&&y>=0&&y<5){if(!(p->walls&(1u<<cell)))continue;}
    else if(outside_entry(x,y,p->entry)||outside_entry(x,y,p->goal))continue;
    field_prop(HA_BLOCK_H,sx(BOARD_X+x),sy(BOARD_Y+y),1);
   }
   for(int i=0;i<3;i++)field_prop(HA_BLOCK_FREE+p->axes[i],sx(BOARD_X+gHandoffBoardBlocks[i]%5),sy(BOARD_Y+gHandoffBoardBlocks[i]/5),1);
   field_prop(HA_GOAL,sx(BOARD_X+p->goal%5),sy(BOARD_Y+p->goal/5),2);field_prop(HA_RESET,sx(BOARD_X+2),sy(BOARD_Y+5),1);
  }
 }
}
