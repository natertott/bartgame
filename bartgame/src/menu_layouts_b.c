/* Five native layout studies: spatial hierarchy is independent of UI skin.
   Coordinates describe 240x160 pixels. The shared runtime owns live inventory,
   assignment controls, truthful map state, text wrapping and sprite uploads. */
#include "menu_studies.h"

#define POINT(x,y) { (x), (y) }
#define RECT(x,y,w,h) { (x), (y), (w), (h) }
#define NONE RECT(0,0,0,0)

static const MenuLayout sTwinAtlas = {
    .name = "Twin Atlas",
    .purpose = "Keep your bearings while inspecting a chamber.",
    .mode = MS_LIST,
    .icon_size = 16,
    .flags = MS_LABELS | MS_PREVIEW,
    .map_mode = MS_MAP_DUAL,
    .slots = {
        POINT(8,24), POINT(8,40), POINT(8,56), POINT(8,72),
        POINT(8,88), POINT(8,104), POINT(8,120)
    },
    .detail = RECT(128,96,104,48),
    .equipment = NONE,
    .status = NONE,
    /* Region left, selected room right: inspection never loses its context. */
    .overview = RECT(8,32,96,96),
    .chamber = RECT(112,32,120,96),
    .map_info = RECT(8,128,224,16),
    /* Pack/key pages retain a smaller map above the selected-item text. */
    .preview = RECT(128,24,104,64)
};

static const MenuLayout sExpeditionDashboard = {
    .name = "Expedition Dashboard",
    .purpose = "Review your pack, loadout and known expedition state.",
    .mode = MS_GRID,
    .icon_size = 16,
    .flags = MS_EQUIPMENT | MS_STATUS | MS_PURPOSE,
    .map_mode = MS_MAP_ROUTE,
    .slots = {
        POINT(16,32), POINT(48,32), POINT(80,32), POINT(112,32),
        POINT(16,72), POINT(48,72), POINT(80,72)
    },
    .detail = RECT(144,80,88,64),
    .equipment = RECT(8,104,128,40),
    .status = RECT(144,24,88,48),
    .overview = RECT(8,24,128,112),
    .chamber = RECT(8,24,128,112),
    .map_info = RECT(144,24,88,112),
    .preview = NONE
};

static const MenuLayout sFocusCards = {
    .name = "Focus Cards",
    .purpose = "Understand one tool before assigning it.",
    .mode = MS_FOCUS,
    .icon_size = 16,
    .flags = MS_PURPOSE,
    .map_mode = MS_MAP_PARCHMENT,
    .slots = {
        POINT(8,112), POINT(40,112), POINT(72,112), POINT(104,112),
        POINT(136,112), POINT(168,112), POINT(200,112)
    },
    /* FOCUS gives the selected tool a native32px illustration in this card. */
    .detail = RECT(8,24,224,80),
    .equipment = NONE,
    .status = NONE,
    .overview = RECT(8,24,144,112),
    .chamber = RECT(8,24,144,112),
    .map_info = RECT(160,24,72,112),
    .preview = NONE
};

static const MenuLayout sBarrierIndex = {
    .name = "Barrier Index",
    .purpose = "Choose the tool by what it does.",
    .mode = MS_GRID,
    .icon_size = 16,
    .flags = MS_LABELS | MS_PURPOSE,
    .map_mode = MS_MAP_GRAPH,
    .slots = {
        POINT(16,32), POINT(72,32), POINT(128,32), POINT(184,32),
        POINT(16,72), POINT(72,72), POINT(128,72)
    },
    /* Short role labels accompany icons; the selected card keeps its name. */
    .detail = RECT(8,104,224,40),
    .equipment = NONE,
    .status = NONE,
    .overview = RECT(8,24,152,112),
    .chamber = RECT(8,24,152,112),
    .map_info = RECT(168,24,64,112),
    .preview = NONE
};

static const MenuLayout sQuickRibbon = {
    .name = "Quick Ribbon",
    .purpose = "Compare and assign tools in one direct row.",
    .mode = MS_RIBBON,
    .icon_size = 32,
    .flags = 0,
    .map_mode = MS_MAP_TERRAIN,
    .slots = {
        POINT(8,32), POINT(40,32), POINT(72,32), POINT(104,32),
        POINT(136,32), POINT(168,32), POINT(200,32)
    },
    .detail = RECT(8,80,224,64),
    .equipment = NONE,
    .status = NONE,
    .overview = RECT(8,32,224,96),
    .chamber = RECT(8,32,224,96),
    .map_info = RECT(8,128,224,16),
    .preview = NONE
};

const MenuLayout* menu_layout_b(int number) {
    switch (number) {
        case 6: return &sTwinAtlas;
        case 7: return &sExpeditionDashboard;
        case 8: return &sFocusCards;
        case 9: return &sBarrierIndex;
        case 10: return &sQuickRibbon;
        default: return 0;
    }
}
