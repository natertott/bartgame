/* Native GBA menu studies1..5. These are presentation recipes, not game
   state: every count, item and map fact is supplied by the shared renderer.
   Main content stops at y144, leaving the common control line unobstructed. */
#include "menu_studies.h"

#define P(x,y) { (x),(y) }
#define R(x,y,w,h) { (x),(y),(w),(h) }
#define NONE R(0,0,0,0)

static const MenuLayout sLayouts[5] = {
    {
        .name = "Loadout Workbench",
        .purpose = "Ready the tools you will need",
        .mode = MS_GRID,
        .icon_size = 32,
        .flags = MS_EQUIPMENT | MS_STATUS | MS_PURPOSE,
        .map_mode = MS_MAP_TERRAIN,
        .slots = { P(8,64), P(40,64), P(72,64), P(104,64),
                   P(8,104), P(40,104), P(72,104) },
        .detail = R(144,64,88,80),
        .equipment = R(8,24,128,32),
        .status = R(144,24,88,32),
        .overview = R(8,32,144,104),
        .chamber = R(8,32,144,104),
        .map_info = R(160,32,72,104),
        .preview = NONE,
    },
    {
        .name = "Pocket Ledger",
        .purpose = "Check your tools and supplies",
        .mode = MS_LIST,
        .icon_size = 16,
        .flags = MS_EQUIPMENT | MS_STATUS | MS_PURPOSE | MS_LABELS,
        .map_mode = MS_MAP_GRAPH,
        .slots = { P(8,24), P(8,40), P(8,56), P(8,72),
                   P(8,88), P(8,104), P(8,120) },
        .detail = R(144,24,88,64),
        .equipment = R(144,96,88,24),
        .status = R(144,120,88,24),
        .overview = R(8,32,128,104),
        .chamber = R(8,32,128,104),
        .map_info = R(144,32,88,104),
        .preview = NONE,
    },
    {
        .name = "Fieldbook",
        .purpose = "Read what each tool can open",
        .mode = MS_GRID,
        .icon_size = 16,
        .flags = MS_EQUIPMENT | MS_STATUS | MS_PURPOSE,
        .map_mode = MS_MAP_PARCHMENT,
        .slots = { P(16,32), P(64,32), P(16,56), P(64,56),
                   P(16,80), P(64,80), P(16,104) },
        .detail = R(128,24,104,88),
        .equipment = R(8,120,104,24),
        .status = R(128,120,104,24),
        .overview = R(8,32,136,104),
        .chamber = R(8,32,136,104),
        .map_info = R(152,32,80,104),
        .preview = NONE,
    },
    {
        .name = "Tactical Atlas",
        .purpose = "Plan a return to a known path",
        .mode = MS_GRID,
        .icon_size = 16,
        .flags = MS_EQUIPMENT | MS_PURPOSE | MS_PREVIEW,
        .map_mode = MS_MAP_ROUTE,
        .slots = { P(8,24), P(8,40), P(8,56), P(8,72),
                   P(8,88), P(8,104), P(8,120) },
        .detail = R(48,104,184,40),
        .equipment = R(200,24,32,80),
        .status = NONE,
        .overview = R(8,32,160,104),
        .chamber = R(8,32,160,104),
        .map_info = R(176,32,56,104),
        .preview = R(48,32,144,64),
    },
    {
        .name = "Toolwheel",
        .purpose = "Choose a tool, then a button",
        .mode = MS_WHEEL,
        .icon_size = 32,
        .flags = MS_EQUIPMENT | MS_PURPOSE,
        .map_mode = MS_MAP_GRAPH,
        .slots = { P(80,24), P(120,32), P(144,72), P(112,112),
                   P(64,112), P(24,72), P(40,32) },
        .detail = R(64,64,72,40),
        .equipment = R(200,32,32,112),
        .status = NONE,
        .overview = R(8,32,144,104),
        .chamber = R(8,32,144,104),
        .map_info = R(160,32,72,104),
        .preview = NONE,
    },
};

const MenuLayout* menu_layout_a(int number) {
    return number >= 1 && number <= 5 ? &sLayouts[number - 1] : 0;
}
