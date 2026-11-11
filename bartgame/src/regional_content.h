#ifndef REGIONAL_CONTENT_H
#define REGIONAL_CONTENT_H
#include "gba.h"
#include "roomgen.h"

/* Stable extension-site namespace: existing sites and Forest save layouts
   are not reused. Interior IDs enumerate the23 non-entry/non-boss rooms in
   each region; field IDs enumerate all25 rooms in each region. */
#define RC_NONE 255
#define RC_ROOMS 50
#define RC_FIELD_BASE 32
#define RC_INTERIOR_BASE 82
#define RC_MECHANISM_PATTERNS 12
#define RC_TRAVERSAL_PATTERNS 3
enum { RC_MARK_DOOR=1, RC_MARK_QUEST=2, RC_MARK_WAVE=4,
       RC_MARK_MECHANISM=8, RC_MARK_FUSION=16, RC_MARK_CACHE=32,
       RC_MARK_COMPACT_DOOR=64 };

typedef struct {
    u8 area,cell,field_site,interior_site;
    u8 event_kind,quest_kind,mechanism_variant,traversal_variant;
    u8 fusion_color,has_wave,stage,terrace;
    u8 field_mechanism_variant;
} RegionalContentPlan;
typedef struct {u8 x,y,w,h;} RegionalContentRect;
typedef struct {
    Spot door,npc,cache,mechanism;
    u8 has_door,has_npc,has_cache,has_mechanism,terrace,compact_door;
    RegionalContentRect mechanism_rect,traversal_rect,quest_rect;
} RegionalContentSpots;
/* Captured only from actual loaded geometry. Map zooms never invent anchors;
   the extension-save owner stores this appended array alongside its state. */
typedef struct {
    Spot door,npc,mechanism,cache;
    u8 marks,terrace;
} RegionalContentDiscovery;
extern RegionalContentSpots gRegionalSpots;
extern RegionalContentDiscovery gRegionalDiscovery[RC_ROOMS];
/* Latched when the run starts, rather than changing when score or an
   optional entitlement setting changes. Stored by the v3 extension. */
extern u8 gRegionalQuestArea;

int regional_content_index(int area,int cell);
void regional_content_new_run(void);
bool8 regional_content_get(int area,int cell,RegionalContentPlan* out);
/* Uses live capabilities and actual graph edges, never grants trial facts. */
bool8 regional_content_reachable(int area,int cell);
/* One live capability query for a whole objective-selection pass. Bit n
   represents room n at its actual planned terrace, not any part of it. */
void regional_content_reach_masks(u32 out[2]);
bool8 regional_content_find(int event_kind,int after_index,bool8 reachable,RegionalContentPlan* out);
bool8 regional_content_fusion(int color,RegionalContentPlan* out);
bool8 regional_content_door_open(int area,int cell);
/* Call after geometry and player_init, before actors are spawned. Placement
   uses a canonical dry component, not the player's particular arrival. */
void regional_content_place(int area,int cell);
void regional_content_clear(void);
bool8 regional_content_reserved(int tx,int ty);
bool8 regional_content_front_reachable(Spot p);
/* Find a dry connected rectangle without moving a mandatory landmark. The
   returned footprint is reserved against all subsequently added actors. */
bool8 regional_content_rect(int w,int h,RegionalContentRect* out);
/* Bounded clearing: only ordinary grass/floor and canopy may change. It
   preserves all landmarks and refuses to connect a sealed component. */
bool8 regional_content_prepare_rect(int w,int h,RegionalContentRect* out);
bool8 regional_content_validate_routes(void);
/* A transactional field builder can reject its stamp. Do not retain a map
   marker claiming that a planned mechanism exists after that rejection. */
void regional_content_mechanism_failed(void);
/* Keep original enemy populations off added props, pools and approaches.
   The requested spot is retained when safe; replacements remain on its
   original terrace and are separated from earlier admitted spawns. */
bool8 regional_content_spawn_point(int terrace,int ordinal,Spot* point);
/* Return discovered coordinates and deterministic room-level content flags. */
u8 regional_content_marks(int area,int cell,RegionalContentDiscovery* out);
#endif
