#include "area.h"
#include "roomid.h"
#include "transitions.h"

// clang-format off

// this terminates a list of Transitions
#define TransitionListEnd { -1, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0 }

const Transition gExitList_NoExitList[] = { TransitionListEnd };
const Transition* const gExitLists_NoExit[] = {
    gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList,
    gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList,
    gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList,
    gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList,
    gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList,
    gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList,
    gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList,
    gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList,
    gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList,
    gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList,
    gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList,
    gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList,
    gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList,
};

const Transition gExitList_MinishWoods_Main[] = {
    { WARP_TYPE_AREA, 0x0138, 0x0318, 0x0078, 0x0078, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_MINISH_WOODS_BOMB, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x01c8, 0x0258, 0x00a8, 0x00d8, TRANSITION_SHAPE_AREA_12x12, AREA_DEEPWOOD_SHRINE, ROOM_DEEPWOOD_SHRINE_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x03a8, 0x0010, 0x0078, 0x0088, TRANSITION_SHAPE_AREA_28x12, AREA_BEANSTALKS, ROOM_BEANSTALKS_EASTERN_HILLS,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0210, 0x01c8, 0x0078, 0x0078, TRANSITION_SHAPE_AREA_28x12, AREA_TREE_INTERIORS,
      ROOM_TREE_INTERIORS_MINISH_WOODS_BUSINESS_SCRUB, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0070, 0x0048, 0x0078, 0x0078, TRANSITION_SHAPE_AREA_28x12, AREA_TREE_INTERIORS,
      ROOM_TREE_INTERIORS_MINISH_WOODS_GREAT_FAIRY, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x02c0, 0x0048, 0x0078, 0x0088, TRANSITION_SHAPE_AREA_28x12, AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_WITCH_HUT,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x03b8, 0x0038, 0x0078, 0x0108, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_CAVES,
      ROOM_MINISH_CAVES_MINISH_WOODS_NORTH_1, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0048, 0x0218, 0x0058, 0x0118, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_CAVES,
      ROOM_MINISH_CAVES_MINISH_WOODS_SOUTHWEST, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0068, 0x0218, 0x0138, 0x0118, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_CAVES,
      ROOM_MINISH_CAVES_MINISH_WOODS_SOUTHWEST, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0088, 0x0218, 0x0218, 0x0118, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_CAVES,
      ROOM_MINISH_CAVES_MINISH_WOODS_SOUTHWEST, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0000, 0x0000, 0x01d8, 0x0fff, TRANSITION_SHAPE_BORDER_WEST_NORTH, AREA_HYRULE_FIELD,
      ROOM_HYRULE_FIELD_EASTERN_HILLS_NORTH, 1, TRANSITION_TYPE_NORMAL, 0x06, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0000, 0x0000, 0x01d8, 0x00a0, TRANSITION_SHAPE_BORDER_WEST_SOUTH, AREA_HYRULE_FIELD,
      ROOM_HYRULE_FIELD_EASTERN_HILLS_SOUTH, 1, TRANSITION_TYPE_NORMAL, 0x06, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0000, 0x0000, 0x0fff, 0x03b8, TRANSITION_SHAPE_BORDER_NORTH_WEST, AREA_LAKE_HYLIA, ROOM_LAKE_HYLIA_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0000, 0x0000, 0x0fff, 0x03ac, TRANSITION_SHAPE_BORDER_NORTH_EAST, AREA_LAKE_HYLIA, ROOM_LAKE_HYLIA_MAIN, 1,
      TRANSITION_TYPE_INSTANT_MINISH, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_MinishWoods[] = {
    [ROOM_MINISH_WOODS_MAIN] = gExitList_MinishWoods_Main,
};

const Transition gExitList_LakeHylia_Main[] = {
    { WARP_TYPE_AREA, 0x02a0, 0x0378, 0x0078, 0x00a0, TRANSITION_SHAPE_AREA_28x12, AREA_HOUSE_INTERIORS_4,
      ROOM_HOUSE_INTERIORS_4_MAYOR_LAKE_CABIN, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0120, 0x0038, 0x0078, 0x0078, TRANSITION_SHAPE_AREA_28x12, AREA_HOUSE_INTERIORS_2,
      ROOM_HOUSE_INTERIORS_2_STOCKWELL_LAKE_HOUSE, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0100, 0x02b8, 0x0078, 0x0078, TRANSITION_SHAPE_AREA_28x12, AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_WAVEBLADE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x00c8, 0x0198, 0x0078, 0x0078, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_LAKE_HYLIA_OCARINA, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x01e8, 0x01a8, 0x0078, 0x0078, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_LIBRARI, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x02b8, 0x0058, 0x0188, 0x01a8, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_CAVES, ROOM_MINISH_CAVES_LAKE_HYLIA_NORTH,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0148, 0x0374, 0x0248, 0x01a8, TRANSITION_SHAPE_AREA_12x12, AREA_LAKE_WOODS_CAVE, ROOM_LAKE_WOODS_CAVE_MAIN,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0000, 0x0000, 0x02c8, 0x0fff, TRANSITION_SHAPE_BORDER_WEST, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH,
      1, TRANSITION_TYPE_NORMAL, 0x06, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0000, 0x0000, 0x0fff, 0x0010, TRANSITION_SHAPE_BORDER_SOUTH_WEST, AREA_MINISH_WOODS, ROOM_MINISH_WOODS_MAIN,
      1, TRANSITION_TYPE_NORMAL, 0x04, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0000, 0x0000, 0x0fff, 0x0024, TRANSITION_SHAPE_BORDER_SOUTH_EAST, AREA_MINISH_WOODS, ROOM_MINISH_WOODS_MAIN,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x04, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_LakeHylia_Beanstalk[] = {
    { WARP_TYPE_AREA, 0x0208, 0x94, 0x248, 0x88, TRANSITION_SHAPE_AREA_12x12, AREA_HYLIA_DIG_CAVES, ROOM_HYLIA_DIG_CAVES_1, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0308, 0x94, 0x308, 0x88, TRANSITION_SHAPE_AREA_12x12, AREA_HYLIA_DIG_CAVES, ROOM_HYLIA_DIG_CAVES_1, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0388, 0x64, 0x398, 0x68, TRANSITION_SHAPE_AREA_12x12, AREA_HYLIA_DIG_CAVES, ROOM_HYLIA_DIG_CAVES_1, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_LakeHylia[] = {
    [ROOM_LAKE_HYLIA_MAIN] = gExitList_LakeHylia_Main,
    [ROOM_LAKE_HYLIA_BEANSTALK] = gExitList_LakeHylia_Beanstalk,
};

const Transition gExitList_CastorWilds_Main[] = {
    { WARP_TYPE_AREA, 0x0248, 0x0032, 0x0038, 0x0078, TRANSITION_SHAPE_AREA_12x12, AREA_CASTOR_CAVES, ROOM_CASTOR_CAVES_NORTH,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0288, 0x0032, 0x0128, 0x0078, TRANSITION_SHAPE_AREA_12x12, AREA_CASTOR_CAVES, ROOM_CASTOR_CAVES_NORTH,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x01a8, 0x01a2, 0x0088, 0x0078, TRANSITION_SHAPE_AREA_12x12, AREA_CASTOR_CAVES, ROOM_CASTOR_CAVES_DARKNUT,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x02d8, 0x0382, 0x0078, 0x0098, TRANSITION_SHAPE_AREA_12x12, AREA_CASTOR_CAVES, ROOM_CASTOR_CAVES_SOUTH,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x03c8, 0x0038, 0x0078, 0x0078, TRANSITION_SHAPE_AREA_12x12, AREA_CASTOR_CAVES, ROOM_CASTOR_CAVES_HEART_PIECE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0038, 0x02d4, 0x0078, 0x0088, TRANSITION_SHAPE_AREA_12x12, AREA_DOJOS, ROOM_DOJOS_SWIFTBLADE_I, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x03b8, 0x02f8, 0x0078, 0x01f8, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_CAVES, ROOM_MINISH_CAVES_SOUTHEAST_WATER_1,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0000, 0x0000, 0x0008, 0x0fff, TRANSITION_SHAPE_BORDER_EAST_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_WESTERN_WOODS_NORTH,
      1, TRANSITION_TYPE_NORMAL, 2, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0000, 0x0000, 0x0fff, 0x0010, TRANSITION_SHAPE_BORDER_SOUTH_WEST, AREA_RUINS, ROOM_RUINS_ENTRANCE, 1, TRANSITION_TYPE_NORMAL, 4, 0x0,
      0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_CastorWilds[] = {
    [ROOM_CASTOR_WILDS_MAIN] = gExitList_CastorWilds_Main,
};

const Transition gExitList_Ruins_Entrance[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x0fff, 0x3b8, TRANSITION_SHAPE_BORDER_NORTH_WEST, AREA_CASTOR_WILDS, ROOM_CASTOR_WILDS_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xc8, 0x38, 0x0078, 0x078, TRANSITION_SHAPE_AREA_12x12, AREA_CASTOR_CAVES, ROOM_CASTOR_CAVES_WIND_RUINS,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Ruins_Beanstalk[] = {
    TransitionListEnd,
};
const Transition gExitList_Ruins_LadderToTektites[] = {
    { WARP_TYPE_AREA, 0x38, 0x08, 0x148, 0xb8, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_CAVES, ROOM_MINISH_CAVES_RUINS, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Ruins_FortressEntrance[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1d8, 0xb0, TRANSITION_SHAPE_BORDER_NORTH, AREA_OUTER_FORTRESS_OF_WINDS, ROOM_OUTER_FORTRESS_OF_WINDS_ENTRANCE_HALL,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_Ruins[] = {
    [ROOM_RUINS_ENTRANCE] = gExitList_Ruins_Entrance,
    [ROOM_RUINS_BEANSTALK] = gExitList_Ruins_Beanstalk,
    [ROOM_RUINS_TEKTITES] = gExitList_NoExitList,
    [ROOM_RUINS_LADDER_TO_TEKTITES] = gExitList_Ruins_LadderToTektites,
    [ROOM_RUINS_FORTRESS_ENTRANCE] = gExitList_Ruins_FortressEntrance,
    [ROOM_RUINS_BELOW_FORTRESS_ENTRANCE] = gExitList_NoExitList,
};

const Transition gExitList_HyruleTown_0[] = {
    { WARP_TYPE_AREA, 0x02c8, 0x0138, 0x0068, 0x0098, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_1, ROOM_HOUSE_INTERIORS_1_MAYOR,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0308, 0x0120, 0x00e8, 0x0070, TRANSITION_SHAPE_AREA_12x28, AREA_HOUSE_INTERIORS_1, ROOM_HOUSE_INTERIORS_1_MAYOR,
      1, TRANSITION_TYPE_NORMAL, 0x06, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0048, 0x00a8, 0x0078, 0x0090, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_1,
      ROOM_HOUSE_INTERIORS_1_POST_OFFICE, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0138, 0x0048, 0x0078, 0x0088, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_1,
      ROOM_HOUSE_INTERIORS_1_LIBRARY_2F, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0168, 0x00a8, 0x00e8, 0x00d8, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_1,
      ROOM_HOUSE_INTERIORS_1_LIBRARY_1F, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0388, 0x0258, 0x0068, 0x0078, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_1, ROOM_HOUSE_INTERIORS_1_INN_1F,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0368, 0x01b8, 0x0068, 0x0078, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_1,
      ROOM_HOUSE_INTERIORS_1_INN_WEST_2F, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x03a8, 0x0218, 0x0048, 0x01a8, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_1,
      ROOM_HOUSE_INTERIORS_1_INN_EAST_2F, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x02c8, 0x0098, 0x0078, 0x00c8, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_1,
      ROOM_HOUSE_INTERIORS_1_SCHOOL_WEST, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0328, 0x0068, 0x00d8, 0x0088, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_1,
      ROOM_HOUSE_INTERIORS_1_SCHOOL_EAST, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0258, 0x02e8, 0x0078, 0x00a8, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_3,
      ROOM_HOUSE_INTERIORS_3_STOCKWELL_SHOP, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0198, 0x02e8, 0x0078, 0x00a8, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_3, ROOM_HOUSE_INTERIORS_3_CAFE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0178, 0x0210, 0x00c8, 0x0060, TRANSITION_SHAPE_AREA_12x28, AREA_HOUSE_INTERIORS_3,
      ROOM_HOUSE_INTERIORS_3_REM_SHOE_SHOP, 1, TRANSITION_TYPE_NORMAL, 0x06, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0278, 0x01f0, 0x0028, 0x0090, TRANSITION_SHAPE_AREA_12x28, AREA_HOUSE_INTERIORS_3, ROOM_HOUSE_INTERIORS_3_BAKERY,
      1, TRANSITION_TYPE_NORMAL, 0x02, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0178, 0x0250, 0x00c8, 0x0070, TRANSITION_SHAPE_AREA_12x28, AREA_HOUSE_INTERIORS_3, ROOM_HOUSE_INTERIORS_3_SIMON,
      1, TRANSITION_TYPE_NORMAL, 0x06, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0178, 0x0290, 0x00c8, 0x0060, TRANSITION_SHAPE_AREA_12x28, AREA_HOUSE_INTERIORS_3,
      ROOM_HOUSE_INTERIORS_3_FIGURINE_HOUSE, 1, TRANSITION_TYPE_NORMAL, 0x06, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0138, 0x0290, 0x0028, 0x0060, TRANSITION_SHAPE_AREA_12x28, AREA_HOUSE_INTERIORS_3,
      ROOM_HOUSE_INTERIORS_3_FIGURINE_HOUSE, 1, TRANSITION_TYPE_NORMAL, 0x02, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0298, 0x0258, 0x0078, 0x0088, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_3,
      ROOM_HOUSE_INTERIORS_3_BORLOV_ENTRANCE, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0090, 0x02c8, 0x0078, 0x0098, TRANSITION_SHAPE_AREA_28x12, AREA_HOUSE_INTERIORS_4, ROOM_HOUSE_INTERIORS_4_CARPENTER,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0098, 0x0168, 0x0078, 0x0078, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_2, ROOM_HOUSE_INTERIORS_2_STRANGER,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0038, 0x0248, 0x0078, 0x0098, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_2, ROOM_HOUSE_INTERIORS_2_DR_LEFT,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x02e8, 0x02f0, 0x0078, 0x0078, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_2, ROOM_HOUSE_INTERIORS_2_ROMIO,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0348, 0x02f8, 0x0078, 0x0098, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_2, ROOM_HOUSE_INTERIORS_2_JULIETTA,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x03b8, 0x0358, 0x0078, 0x0078, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_2, ROOM_HOUSE_INTERIORS_2_CUCCO,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0138, 0x0388, 0x0078, 0x0098, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_4,
      ROOM_HOUSE_INTERIORS_4_SWIFTBLADE, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0038, 0x01a8, 0x0078, 0x0078, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_HYRULE_TOWN, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0050, 0x0378, 0x0078, 0x0078, TRANSITION_SHAPE_AREA_28x12, AREA_TREE_INTERIORS,
      ROOM_TREE_INTERIORS_STAIRS_TO_CARLOV, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x00f0, 0x0188, 0x0078, 0x0078, TRANSITION_SHAPE_AREA_28x12, AREA_CAVES, ROOM_CAVES_HYRULE_TOWN_WATERFALL,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0040, 0x01b8, 0x0078, 0x0098, TRANSITION_SHAPE_AREA_28x12, AREA_HOUSE_INTERIORS_2,
      ROOM_HOUSE_INTERIORS_2_WEST_ORACLE, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x02b8, 0x0360, 0x0078, 0x0078, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_2,
      ROOM_HOUSE_INTERIORS_2_EAST_ORACLE, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x0338, 0x0134, 0x0288, 0x0118, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_TOWN_UNDERGROUND,
      ROOM_HYRULE_TOWN_UNDERGROUND_0, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0000, 0x0000, 0x01f8, 0x0318, TRANSITION_SHAPE_BORDER_NORTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0000, 0x0000, 0x01d8, 0x0230, TRANSITION_SHAPE_BORDER_WEST_NORTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS,
      1, TRANSITION_TYPE_NORMAL, 0x06, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0000, 0x0000, 0x0008, 0x0230, TRANSITION_SHAPE_BORDER_EAST_NORTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH,
      1, TRANSITION_TYPE_NORMAL, 0x02, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0000, 0x0000, 0x01f8, 0x0010, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x04, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_HyruleTown[] = {
    [ROOM_HYRULE_TOWN_MAIN] = gExitList_HyruleTown_0,
};

const Transition gExitList_HyruleTown_1[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x318, TRANSITION_SHAPE_BORDER_NORTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_FestivalTown[] = {
    [ROOM_FESTIVAL_TOWN_MAIN] = gExitList_HyruleTown_1,
};

const Transition gExitList_MtCrenel_MountainTop[] = {
    { WARP_TYPE_AREA, 0x328, 0x34, 0x1a8, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_BLOCK_PUSHING,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x18, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_WALL_CLIMB, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MtCrenel_WallClimb[] = {
    { WARP_TYPE_AREA, 0xa8, 0x58, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_HERMIT, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x148, 0x1e8, 0x78, 0xf8, TRANSITION_SHAPE_AREA_12x12, AREA_GREAT_FAIRIES, ROOM_GREAT_FAIRIES_CRENEL, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0xd8, TRANSITION_SHAPE_BORDER_NORTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_TOP, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MtCrenel_CaveOfFlamesEntrance[] = {
    { WARP_TYPE_AREA, 0x128, 0x18, 0x58, 0x1b8, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_BLOCK_PUSHING,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x208, 0x18, 0x298, 0x1b8, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_BLOCK_PUSHING,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x1d8, 0xb8, 0xb8, 0x88, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_PILLAR_CAVE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x238, 0xb8, 0x48, 0x1c8, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_BRIDGE_SWITCH,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x188, 0xf8, 0xb8, 0x98, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_EXIT_TO_MINES,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x208, 0x148, 0x78, 0xf0, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_TO_GRAYBLADE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x1e8, 0x1d8, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_GRIP_RING,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x68, 0x72, 0x88, 0xa8, TRANSITION_SHAPE_AREA_12x12, AREA_CAVE_OF_FLAMES, ROOM_CAVE_OF_FLAMES_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MtCrenel_GustJarShortcut[] = {
    { WARP_TYPE_AREA, 0xa8, 0x48, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_FAIRY_FOUNTAIN,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x2f8, 0x28, 0x38, 0x98, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_SPINY_CHU_PUZZLE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x348, 0x58, 0xb8, 0x88, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_CHUCHU_POT_CHEST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x38, 0x108, 0x78, 0x118, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_WATER_HEART_PIECE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MtCrenel_Entrance[] = {
    { WARP_TYPE_AREA, 0x298, 0x28, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_RUPEE_FAIRY_FOUINTAIN,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x198, 0xd8, 0x1f8, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_HELMASAUR_HALLWAY,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x138, 0x138, 0xb8, 0x138, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_MUSHROOM_KEESE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x2d8, 0x188, 0x78, 0x88, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_LADDER_TO_SPRING_WATER,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xb8, 0x198, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_BOMB_BUSINESS_SCRUB,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x3b8, 0x168, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_HINT_SCRUB,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x1c8, 0x18, 0x98, 0x1a8, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_CAVES, ROOM_MINISH_CAVES_BEAN_PESTO,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x2d8, 0x154, 0x78, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_LADDER_TO_SPRING_WATER,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x8, 0xfff, TRANSITION_SHAPE_BORDER_EAST_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS,
      1, TRANSITION_TYPE_NORMAL, 0x2, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_MtCrenel[] = {
    [ROOM_MT_CRENEL_TOP] = gExitList_MtCrenel_MountainTop,
    [ROOM_MT_CRENEL_WALL_CLIMB] = gExitList_MtCrenel_WallClimb,
    [ROOM_MT_CRENEL_CAVERN_OF_FLAMES_ENTRANCE] = gExitList_MtCrenel_CaveOfFlamesEntrance,
    [ROOM_MT_CRENEL_CENTER] = gExitList_MtCrenel_GustJarShortcut,
    [ROOM_MT_CRENEL_ENTRANCE] = gExitList_MtCrenel_Entrance,
};

const Transition gExitList_HyruleField_WesternWoodSouth[] = {
    { WARP_TYPE_AREA, 0xb8, 0x28, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_HYRULE_FIELD_SOUTHWEST, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#ifdef QUICKSTART
// All 4 of this region's "? room" doors are on the vanilla-door model now:
// every one leads to its real vanilla destination and gets its randomized
// event spawned inside that room instead (game.c:
// sQuickStartRoomContentSites). Nothing in this list is retargeted anymore.
//
// Real doors work here for the reason spelled out in
// gExitList_HyruleField_NorthHyruleField's own comment below:
// UpdateDoorTransition gates only on the player's action state and the
// tile's actTile value, and actTiles are rebuilt from compiled map data on
// every room load - there's no "arrived via a real transition" prerequisite.
const Transition gExitList_HyruleField_SouthHyruleField[] = {
    // Link's House. A 2-room interior (entrance + bedroom) rather than a
    // dead end, converted anyway per the user's own call to do this "for
    // all the rooms, regardless of if they are single door rooms or
    // two-door rooms". Both rooms are content sites, and the pocket is
    // genuinely closed: the bedroom's only exit is back to the entrance,
    // and the entrance's only other exit is the border back to this field.
    { WARP_TYPE_AREA, 0x290, 0x188, 0x78, 0x78, TRANSITION_SHAPE_AREA_28x12, AREA_HOUSE_INTERIORS_2,
      ROOM_HOUSE_INTERIORS_2_LINKS_HOUSE_ENTRANCE, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    // These 3 are genuine dead-end single rooms whose only exit is a
    // WARP_TYPE_BORDER straight back here. Border transitions don't even
    // go through the actTile path real doors use - IsPosInBorderTransitionRegion
    // only checks facing and which half of the room you're in - so the
    // return leg is the most reliable kind of transition in the engine.
    { WARP_TYPE_AREA, 0x3a0, 0x228, 0x78, 0x78, TRANSITION_SHAPE_AREA_28x12, AREA_TREE_INTERIORS,
      ROOM_TREE_INTERIORS_SOUTH_HYRULE_FIELD_HEART_PIECE, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    // Behind a bombable wall in vanilla (its tile reads ACT_TILE_46 =
    // BombableWallManager, not a door actTile, until the wall is blown
    // open). Left exactly as vanilla built it - the player starts with
    // bombs, so this becomes a genuine hidden ? room rather than a door
    // that opens on touch like the old synthetic trigger box did.
    { WARP_TYPE_AREA, 0x118, 0xa8, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_SOUTH_HYRULE_FIELD_FAIRY_FOUNTAIN,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x58, 0x118, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_SOUTH_HYRULE_FIELD_RUPEE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x178, 0xd8, 0x78, 0xb8, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_CAVES, ROOM_MINISH_CAVES_OUTSIDE_LINKS_HOUSE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
#else
const Transition gExitList_HyruleField_SouthHyruleField[] = {
    { WARP_TYPE_AREA, 0x290, 0x188, 0x78, 0x78, TRANSITION_SHAPE_AREA_28x12, AREA_HOUSE_INTERIORS_2,
      ROOM_HOUSE_INTERIORS_2_LINKS_HOUSE_ENTRANCE, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x3a0, 0x228, 0x78, 0x78, TRANSITION_SHAPE_AREA_28x12, AREA_TREE_INTERIORS,
      ROOM_TREE_INTERIORS_SOUTH_HYRULE_FIELD_HEART_PIECE, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x118, 0xa8, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_SOUTH_HYRULE_FIELD_FAIRY_FOUNTAIN,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x58, 0x118, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_SOUTH_HYRULE_FIELD_RUPEE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x178, 0xd8, 0x78, 0xb8, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_CAVES, ROOM_MINISH_CAVES_OUTSIDE_LINKS_HOUSE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
#endif
    { WARP_TYPE_AREA, 0x48, 0x1c8, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_SOUTH_HYRULE_FIELD, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
#ifdef QUICKSTART
    // THE TOWN BRIDGE, north half - see the matching row in
    // gExitList_HyruleField_NorthHyruleField. Walking out SHF's north gate
    // lands at NHF's south gate, at the arrival coordinates vanilla's town
    // north exit used (endX 0x1f8, endY 0x318).
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1f8, 0x318, TRANSITION_SHAPE_BORDER_NORTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
#else
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1f8, 0x3b8, TRANSITION_SHAPE_BORDER_NORTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
#endif
    TransitionListEnd,
};
const Transition gExitList_HyruleField_EasternHillsSouth[] = {
    { WARP_TYPE_AREA, 0x38, 0x28, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_HYRULE_FIELD_EXIT, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
#ifndef QUICKSTART
    // Minish Woods is outside the seven-region ring: BLOCKED under
    // QUICKSTART, no row.
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x8, 0x3c8, TRANSITION_SHAPE_BORDER_EAST_SOUTH, AREA_MINISH_WOODS, ROOM_MINISH_WOODS_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x2, 0x0, 0x0, 0x0 },
#endif
    TransitionListEnd,
};
const Transition gExitList_HyruleField_EasternHillsCenter[] = {
    { WARP_TYPE_AREA, 0xa8, 0x98, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_HILLS_KEESE_CHEST, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HyruleField_EasternHillsNorth[] = {
    { WARP_TYPE_AREA, 0x40, 0x48, 0x78, 0x88, TRANSITION_SHAPE_AREA_28x12, AREA_HOUSE_INTERIORS_4, ROOM_HOUSE_INTERIORS_4_FARM_HOUSE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
#ifndef QUICKSTART
    // Minish Woods again: BLOCKED under QUICKSTART, no row.
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x8, 0xfff, TRANSITION_SHAPE_BORDER_EAST, AREA_MINISH_WOODS, ROOM_MINISH_WOODS_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x2, 0x0, 0x0, 0x0 },
#endif
    TransitionListEnd,
};
const Transition gExitList_HyruleField_LonLonRanch[] = {
    { WARP_TYPE_AREA, 0x158, 0x278, 0x68, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_4, ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_WEST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x188, 0x278, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_4, ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_EAST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xe8, 0x1b4, 0xa8, 0xd8, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x1f8, 0x208, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_LON_LON_RANCH_WALLET, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x88, 0x354, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_GORON_CAVE, ROOM_GORON_CAVE_STAIRS, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xb8, 0x154, 0x38, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
#ifdef QUICKSTART
    // THE TOWN BRIDGE, east half. In vanilla the ranch's west border enters
    // Hyrule Town and the town's west gate exits into Trilby Highlands; the
    // town is gone here, so this row joins those two journeys into one -
    // walking out the ranch's west side lands at Trilby's east edge, at the
    // arrival coordinates vanilla's own town west exit used (endX 0x1d8,
    // endY 0x230).
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1d8, 0x230, TRANSITION_SHAPE_BORDER_WEST_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS,
      1, TRANSITION_TYPE_NORMAL, 0x6, 0x0, 0x0, 0x0 },
    // Veil Falls (both north borders) and Lake Hylia (east) are outside the
    // ring: BLOCKED, no rows.
#else
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x3e8, TRANSITION_SHAPE_BORDER_NORTH_WEST, AREA_VEIL_FALLS, ROOM_VEIL_FALLS_MAIN, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1c8, 0x3e8, TRANSITION_SHAPE_BORDER_NORTH_EAST, AREA_VEIL_FALLS, ROOM_VEIL_FALLS_MAIN, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x8, 0xfff, TRANSITION_SHAPE_BORDER_EAST, AREA_LAKE_HYLIA, ROOM_LAKE_HYLIA_MAIN, 1, TRANSITION_TYPE_NORMAL, 0x2,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3e8, 0xf0, TRANSITION_SHAPE_BORDER_WEST_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x6, 0x0, 0x0, 0x0 },
#endif
    TransitionListEnd,
};
#ifdef QUICKSTART
// PILOT (vanilla-doors-with-randomized-contents): the 5 tree doors below
// are back on their REAL vanilla destinations. The old approach retargeted
// every one of them to Castle Garden Main and reached the "? rooms" through
// synthetic position-box teleports instead (game.c:
// sQuickStartLadderEntrances) - that was built on the belief that real
// WARP_TYPE_AREA doors can't fire under QUICKSTART's direct room load.
// That belief is wrong: UpdateDoorTransition (scroll.c) gates only on the
// player's action state and the tile's actTile value, and actTiles are
// rebuilt from compiled map data by FillActTileForLayer on EVERY room load
// - there is no "arrived via a real transition" prerequisite anywhere in
// that path. Confirmed by reading the live actTile table after a direct
// QUICKSTART warp into this room: all 5 tree doors below read ACT_TILE_40,
// i.e. fully armed. The historical "never fires" result is far better
// explained by QUICKSTART's own containment functions, which cancel any
// transition whose destination isn't allowlisted - a real door firing to
// AREA_TREE_INTERIORS would have been cancelled the same frame, which is
// indistinguishable from never firing.
//
// The transition data says these rooms are not dead ends - all 4 Boomerang
// trees list a WARP_TYPE_AREA down into a shared ROOM_CAVES_BOOMERANG hub,
// and the Fairy Fountain tree into its own cave. In practice those inner
// doors do NOT fire: probing the live actTile table shows 0x00 at each
// tree's hub door, so the trees behave as ordinary one-way-in, one-way-out
// rooms whose only working exit is the border back to this field. That is
// fine for the "? room" model (the randomization happens INSIDE each room -
// see sQuickStartRoomContentSites, game.c), but do not rely on the pocket
// being explorable; it isn't, and the hub is currently unreachable.
//
// Nothing in this list is retargeted anymore - the Heart Piece Hallway
// cave (0x138,0x1e8) was the last holdout and is back on its real vanilla
// destination too (see its own comment below). The Castle Garden
// connection (first entry) and the 3 ROOM_CAVES_TO_GRAVEYARD occurrences
// (a genuine multi-exit through-cave) are untouched in both branches, as
// before.
const Transition gExitList_HyruleField_NorthHyruleField[] = {
    { WARP_TYPE_AREA, 0x1f8, 0x38, 0x1f8, 0x208, TRANSITION_SHAPE_AREA_44x12, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x1b0, 0x128, 0x78, 0x78, TRANSITION_SHAPE_AREA_28x12, AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_BOOMERANG_NORTHWEST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x240, 0x128, 0x78, 0x78, TRANSITION_SHAPE_AREA_28x12, AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_BOOMERANG_NORTHEAST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x1b0, 0x188, 0x78, 0x78, TRANSITION_SHAPE_AREA_28x12, AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_BOOMERANG_SOUTHWEST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x240, 0x188, 0x78, 0x78, TRANSITION_SHAPE_AREA_28x12, AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_BOOMERANG_SOUTHEAST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x2f0, 0x138, 0x78, 0x78, TRANSITION_SHAPE_AREA_28x12, AREA_TREE_INTERIORS,
      ROOM_TREE_INTERIORS_NORTH_HYRULE_FIELD_FAIRY_FOUNTAIN, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    // BUG FIX (user report: "went into a tree, got the reward, but when I
    // exited I returned up a ladder in vanilla Hyrule Castle Garden and was
    // stuck"). This is the mouth of the very Boomerang cave hub the 4
    // converted trees drop into. While it stayed retargeted it also kept its
    // synthetic trigger box (entrance index 13, 480-528 x 316-364) - and the
    // hub's own vanilla exit lands the player at (0x1f8,0x138) = (504,312),
    // four pixels above that box's top edge. Before the pilot the hub was
    // unreachable (every tree led to Castle Garden), so the box never
    // mattered; once the trees opened it, walking out of the cave dropped
    // the player straight onto a teleport into a drawn pool room, whose own
    // exit is retargeted to Castle Garden Main - landing them at a Castle
    // Garden ladder return spot, exactly as reported. Retiring that box
    // (game.c, sQuickStartLadderEntrances) is what actually fixes it.
    //
    // CORRECTION, from probing the live actTile table rather than trusting
    // the transition data: this door does NOT fire (0x09 everywhere around
    // (504,340), no door-capable value), and neither does the hub's own
    // exit back to this field (0x0a at (0xa8,0xb8)), nor the trees' exits
    // down into the hub (0x00). Only the hub's two ladders up to trees
    // NW/NE are armed (ACT_TILE_241).
    //
    // So the Boomerang cave hub is effectively unreachable in play, and the
    // "walk out of the cave onto the trigger box" mechanism described above
    // could not actually have occurred. Retiring the box is still correct -
    // it removed a hazard that would bite the moment any of those doors
    // became reachable - but it is NOT a confirmed explanation of the
    // reported Castle Garden lockout, which remains undiagnosed.
    //
    // Pointing this at the real cave rather than Castle Garden is the safer
    // of the two inert options: if it ever did fire it lands inside the
    // pilot's own pocket instead of at a Castle Garden ladder spot.
    { WARP_TYPE_AREA, 0x1f8, 0x154, 0xa8, 0xd8, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_BOOMERANG, 1, TRANSITION_TYPE_NORMAL, 0x4,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x108, 0x138, 0x108, 0xd8, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_TO_GRAVEYARD, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    // The Heart Piece Hallway cave, converted to the vanilla-door model
    // (the last of this region's doors to be). Its real destination is not
    // a dead end in vanilla - ROOM_CAVES_HEART_PIECE_HALLWAY also has a
    // WARP_TYPE_AREA onward into ROOM_CAVES_TO_GRAVEYARD, a genuine
    // multi-exit through-cave that reaches Royal Valley, i.e. straight out
    // of the run. That onward door is neutralized in the room's own exit
    // list instead (gExitList_Caves_HeartPieceHallway below, QUICKSTART
    // branch), which turns the hallway into the same shape as every other
    // converted door here: one way in, one border back out.
    { WARP_TYPE_AREA, 0x138, 0x1e8, 0x78, 0xc8, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_HEART_PIECE_HALLWAY, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x88, 0xf4, 0x38, 0x58, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_TO_GRAVEYARD, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x118, 0xf4, 0x118, 0x58, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_TO_GRAVEYARD, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x208, TRANSITION_SHAPE_BORDER_NORTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
#else
const Transition gExitList_HyruleField_NorthHyruleField[] = {
    { WARP_TYPE_AREA, 0x1f8, 0x38, 0x1f8, 0x208, TRANSITION_SHAPE_AREA_44x12, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x1b0, 0x128, 0x78, 0x78, TRANSITION_SHAPE_AREA_28x12, AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_BOOMERANG_NORTHWEST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x240, 0x128, 0x78, 0x78, TRANSITION_SHAPE_AREA_28x12, AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_BOOMERANG_NORTHEAST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x1b0, 0x188, 0x78, 0x78, TRANSITION_SHAPE_AREA_28x12, AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_BOOMERANG_SOUTHWEST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x240, 0x188, 0x78, 0x78, TRANSITION_SHAPE_AREA_28x12, AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_BOOMERANG_SOUTHEAST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x2f0, 0x138, 0x78, 0x78, TRANSITION_SHAPE_AREA_28x12, AREA_TREE_INTERIORS,
      ROOM_TREE_INTERIORS_NORTH_HYRULE_FIELD_FAIRY_FOUNTAIN, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x1f8, 0x154, 0xa8, 0xd8, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_BOOMERANG, 1, TRANSITION_TYPE_NORMAL, 0x4,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x108, 0x138, 0x108, 0xd8, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_TO_GRAVEYARD, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x138, 0x1e8, 0x78, 0xc8, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_HEART_PIECE_HALLWAY, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x88, 0xf4, 0x38, 0x58, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_TO_GRAVEYARD, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x118, 0xf4, 0x118, 0x58, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_TO_GRAVEYARD, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x208, TRANSITION_SHAPE_BORDER_NORTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
#endif
#ifdef QUICKSTART
    // THE TOWN BRIDGE, south half. Hyrule Town does not exist in this mode,
    // but in vanilla it is the connective tissue of the whole ring - walk in
    // the north gate, out the south gate, and you are in South Hyrule Field.
    // This row keeps that journey and drops the town from the middle of it:
    // the south border lands directly at SHF's north gate, at the exact
    // arrival coordinates vanilla's own town south exit used
    // (gExitList_HyruleTown_Main: endX 0x1f8, endY 0x10), so the far end is
    // a spot vanilla itself vouches for.
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1f8, 0x10, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    // Veil Falls (east) and Royal Valley (west) are outside the seven-region
    // ring and BLOCKED: no border row, no crossing -
    // IsPosInBorderTransitionRegion fires only on a matching row, so walking
    // that edge simply stops at it.
#else
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1f8, 0x18, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x8, 0xfff, TRANSITION_SHAPE_BORDER_EAST_NORTH, AREA_VEIL_FALLS, ROOM_VEIL_FALLS_MAIN, 1, TRANSITION_TYPE_NORMAL, 0x2,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1d8, 0x260, TRANSITION_SHAPE_BORDER_WEST_NORTH, AREA_ROYAL_VALLEY, ROOM_ROYAL_VALLEY_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x6, 0x0, 0x0, 0x0 },
#endif
    TransitionListEnd,
};
#ifdef QUICKSTART
// Defensive fallback for the 4 doors this region contributes to the new
// single-door "? room" pool (game.c: sQuickStartLadderEntrances, entrance
// indices 15-18) - same reasoning as gExitList_HyruleField_SouthHyruleField's
// own #ifdef block above. The digging cave (AREA_DIG_CAVES - deferred, its
// own digging-specific quirks unchecked) and the 2 ROOM_CAVES_TRILBY_HIGHLANDS
// occurrences (a genuine multi-exit through-cave, deferred as a future
// "2-door" candidate) are untouched in both branches.
const Transition gExitList_HyruleField_TrilbyHighlands[] = {
    // PILOT: all 4 back on their real vanilla destinations. Every one is a
    // genuine single-room dead end whose only exit is a WARP_TYPE_BORDER
    // straight back here, which is the most reliable shape for this model
    // (borders skip the actTile path entirely).
    //
    // Two of these open on touch (Percy's Treehouse and the Rupee cave both
    // read ACT_TILE_40); the other two sit behind vanilla bombable walls -
    // the Keese Chest and Fairy Fountain cave mouths read ACT_TILE_46
    // (BombableWallManager) until blown open, so they now have to be bombed
    // to find, which is the behaviour the user asked to keep.
    { WARP_TYPE_AREA, 0x40, 0x388, 0x78, 0x78, TRANSITION_SHAPE_AREA_28x12, AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_PERCYS_TREEHOUSE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x88, 0x222, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_TRILBY_KEESE_CHEST, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x38, 0x2a8, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_TRILBY_RUPEE, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x198, 0x2b2, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_TRILBY_FAIRY_FOUNTAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x88, 0x94, 0x88, 0x68, TRANSITION_SHAPE_AREA_12x12, AREA_DIG_CAVES, ROOM_DIG_CAVES_TRILBY_HIGHLANDS, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
#else
const Transition gExitList_HyruleField_TrilbyHighlands[] = {
    { WARP_TYPE_AREA, 0x40, 0x388, 0x78, 0x78, TRANSITION_SHAPE_AREA_28x12, AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_PERCYS_TREEHOUSE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x88, 0x222, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_TRILBY_KEESE_CHEST, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x38, 0x2a8, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_TRILBY_RUPEE, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x198, 0x2b2, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_TRILBY_FAIRY_FOUNTAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x88, 0x94, 0x88, 0x68, TRANSITION_SHAPE_AREA_12x12, AREA_DIG_CAVES, ROOM_DIG_CAVES_TRILBY_HIGHLANDS, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
#endif
    { WARP_TYPE_AREA, 0x98, 0x284, 0x38, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_TRILBY_HIGHLANDS, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x118, 0x284, 0x128, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_TRILBY_HIGHLANDS, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
#ifdef QUICKSTART
    // THE TOWN BRIDGE, west half - see the matching row in
    // gExitList_HyruleField_LonLonRanch. Walking out Trilby's east edge
    // lands at the ranch's west side, at the arrival coordinates vanilla's
    // town east exit used (endX 0x8, endY 0x230).
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x8, 0x230, TRANSITION_SHAPE_BORDER_EAST_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH,
      1, TRANSITION_TYPE_NORMAL, 0x2, 0x0, 0x0, 0x0 },
    // ROYAL VALLEY, and it is open in BOTH directions on purpose (the user,
    // Aug 2026: "the player should be able to walk back and forth between
    // this seam"). Royal Valley's own SOUTH_WEST row into Trilby was never
    // blocked, so without this one the crossing was one-way - and measured,
    // that would have been a trap rather than a shortcut: the row lands the
    // player at Trilby's y=16, inside a 48-tile pocket (tx 4-16, ty 0-4)
    // that is a walkable component of its OWN. It touches neither the
    // region's 334-tile main body nor any of its other 22 components, so
    // the only way out of it is back north through this row.
    //
    // Which also means this seam does not connect Royal Valley to the
    // Trilby REGION - it connects it to an alcove on Trilby's north edge.
    // Anything routing a run through Royal Valley into Trilby needs to know
    // that; see the traversal model in tools/quickstart/overworld_paths.py.
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x3e8, TRANSITION_SHAPE_BORDER_NORTH_WEST, AREA_ROYAL_VALLEY, ROOM_ROYAL_VALLEY_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    // Mt Crenel (west) is still outside the ring: BLOCKED, no row.
#else
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x3e8, TRANSITION_SHAPE_BORDER_NORTH_WEST, AREA_ROYAL_VALLEY, ROOM_ROYAL_VALLEY_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x8, 0xf0, TRANSITION_SHAPE_BORDER_EAST_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL, 0x2,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3e8, 0xfff, TRANSITION_SHAPE_BORDER_WEST_NORTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_ENTRANCE, 1, TRANSITION_TYPE_NORMAL,
      0x6, 0x0, 0x0, 0x0 },
#endif
    TransitionListEnd,
};
const Transition gExitList_HyruleField_WesternWoodsNorth[] = {
    { WARP_TYPE_AREA, 0xa0, 0x1e8, 0x78, 0x78, TRANSITION_SHAPE_AREA_28x12, AREA_TREE_INTERIORS,
      ROOM_TREE_INTERIORS_WESTERN_WOODS_HEART_PIECE, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
#ifndef QUICKSTART
    // Castor Wilds is outside the seven-region ring: BLOCKED under
    // QUICKSTART, no row.
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3e8, 0xfff, TRANSITION_SHAPE_BORDER_WEST_NORTH, AREA_CASTOR_WILDS, ROOM_CASTOR_WILDS_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x6, 0x0, 0x0, 0x0 },
#endif
    TransitionListEnd,
};
const Transition gExitList_HyruleField_WesternWoodsCenter[] = {
    { WARP_TYPE_AREA, 0x90, 0x48, 0x78, 0x88, TRANSITION_SHAPE_AREA_28x12, AREA_HOUSE_INTERIORS_2, ROOM_HOUSE_INTERIORS_2_PERCY,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_HyruleField[] = {
    [ROOM_HYRULE_FIELD_WESTERN_WOODS_SOUTH] = gExitList_HyruleField_WesternWoodSouth,
    [ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD] = gExitList_HyruleField_SouthHyruleField,
    [ROOM_HYRULE_FIELD_EASTERN_HILLS_SOUTH] = gExitList_HyruleField_EasternHillsSouth,
    [ROOM_HYRULE_FIELD_EASTERN_HILLS_CENTER] = gExitList_HyruleField_EasternHillsCenter,
    [ROOM_HYRULE_FIELD_EASTERN_HILLS_NORTH] = gExitList_HyruleField_EasternHillsNorth,
    [ROOM_HYRULE_FIELD_LON_LON_RANCH] = gExitList_HyruleField_LonLonRanch,
    [ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD] = gExitList_HyruleField_NorthHyruleField,
    [ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS] = gExitList_HyruleField_TrilbyHighlands,
    [ROOM_HYRULE_FIELD_WESTERN_WOODS_NORTH] = gExitList_HyruleField_WesternWoodsNorth,
    [ROOM_HYRULE_FIELD_WESTERN_WOODS_CENTER] = gExitList_HyruleField_WesternWoodsCenter,
};

// TODO this is one table
const Transition gExitList_CastleGarden_Main[] = {
    // Every entry here is vanilla, untouched. The two that matter for
    // QUICKSTART are the cellar ladder and the Grimblade dojo door further
    // down - those are Castle Garden's two "? room" ladders, and they're on
    // the vanilla-door model now (their destination rooms get randomized
    // events spawned inside them; see sQuickStartRoomContentSites, game.c).
    //
    // The old comment here claimed WARP_TYPE_AREA doors can never fire
    // under QUICKSTART because the ACT_TILE they depend on isn't set up on
    // a direct room load. That is wrong: FillActTileForLayer rebuilds
    // actTiles from compiled map data on EVERY room load, and probing the
    // live table confirms both of these doors read ACT_TILE_40 (armed).
    // What actually cancelled them was QUICKSTART's own containment
    // functions, which is now handled per-destination instead.
    //
    // The remaining 3 WARP_TYPE_AREA doors (Hyrule Castle proper, and the
    // two Garden Fountains) genuinely do lead somewhere sprawling and are
    // still blocked by containment (QuickStartEnforceContainment).
    { WARP_TYPE_AREA, 0x1f8, 0x28, 0xd8, 0x208, TRANSITION_SHAPE_AREA_28x12, AREA_HYRULE_CASTLE, ROOM_HYRULE_CASTLE_0, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x308, 0x48, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_GARDEN_FOUNTAINS, ROOM_GARDEN_FOUNTAINS_EAST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xe8, 0x48, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_GARDEN_FOUNTAINS, ROOM_GARDEN_FOUNTAINS_WEST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    // "? room" ladder 1 of 2: the Great Fairy cellar. A true dead end -
    // ROOM_HYRULE_CASTLE_CELLAR_0's only exit is straight back here.
    { WARP_TYPE_AREA, 0x68, 0x74, 0x68, 0x1a8, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_CASTLE_CELLAR, ROOM_HYRULE_CASTLE_CELLAR_0,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    // "? room" ladder 2 of 2: Grimblade's dojo entrance. Also a true dead
    // end - ROOM_DOJOS_TO_GRIMBLADE's only exit is straight back here.
    { WARP_TYPE_AREA, 0x3a8, 0x184, 0x78, 0x68, TRANSITION_SHAPE_AREA_12x12, AREA_DOJOS, ROOM_DOJOS_TO_GRIMBLADE, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
    // VANILLA, in both branches, per the user's own call. This row spent most
    // of the mode's life retargeted: first to Melari's Mine (back when the
    // mine was the hub and this was how the player walked back to it), then
    // briefly as a deliberate wall once the mine left the route. Neither is
    // right now - Castle Garden and North Hyrule Field are physically
    // adjacent screens and both are regions in the same pool, so the honest
    // behaviour is the vanilla one: walking off the bottom of Castle Garden
    // puts you in North Hyrule Field, and NHF's own north border and
    // WARP_TYPE_AREA door (gExitList_HyruleField_NorthHyruleField, both
    // already vanilla in both branches) bring you back.
    //
    // Unlike the WARP_TYPE_AREA doors elsewhere in this file, a
    // WARP_TYPE_BORDER entry doesn't depend on GetActTileAtTilePos at all
    // (IsPosInBorderTransitionRegion, scroll.c, only checks facing direction
    // and room-half), so it fires reliably under QUICKSTART.
    //
    // Both containment functions need an explicit exception for this pair -
    // see QuickStartIsGardenFieldCrossing (game.c). Without it the crossing
    // would work only on the runs where this save's chain happened to put
    // the far side next, i.e. a wall on some runs and a door on others.
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1f8, 0x48, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gUnk_08134FBC[] = {
    { WARP_TYPE_AREA, 0x1f8, 0x28, 0x198, 0x1f0, TRANSITION_SHAPE_AREA_28x12, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_1F_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x308, 0x48, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_GARDEN_FOUNTAINS, ROOM_GARDEN_FOUNTAINS_EAST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xe8, 0x48, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_GARDEN_FOUNTAINS, ROOM_GARDEN_FOUNTAINS_WEST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x68, 0x74, 0x68, 0x1a8, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_CASTLE_CELLAR, ROOM_HYRULE_CASTLE_CELLAR_0,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x3a8, 0x184, 0x78, 0x68, TRANSITION_SHAPE_AREA_12x12, AREA_DOJOS, ROOM_DOJOS_TO_GRIMBLADE, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1f8, 0x48, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gUnk_08135048[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_CastleGarden[] = {
    [ROOM_CASTLE_GARDEN_MAIN] = gExitList_CastleGarden_Main,
};

const Transition gExitList_CloudTops_House[] = {
    { WARP_TYPE_AREA, 0x1e8, 0x158, 0x78, 0x138, TRANSITION_SHAPE_AREA_12x12, AREA_WIND_TRIBE_TOWER, ROOM_WIND_TRIBE_TOWER_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_CloudTops[] = {
    [ROOM_CLOUD_TOPS_CLOUD_TOPS] = gExitList_CloudTops_House,
};

const Transition gExitList_RoyalValley_Main[] = {
    { WARP_TYPE_AREA, 0xf0, 0x28, 0x88, 0x78, TRANSITION_SHAPE_AREA_28x12, AREA_ROYAL_CRYPT, ROOM_ROYAL_CRYPT_ENTRANCE, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x1a0, 0x198, 0x78, 0x78, TRANSITION_SHAPE_AREA_28x12, AREA_HOUSE_INTERIORS_2, ROOM_HOUSE_INTERIORS_2_DAMPE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x198, 0x2a8, 0x78, 0xf8, TRANSITION_SHAPE_AREA_12x12, AREA_GREAT_FAIRIES, ROOM_GREAT_FAIRIES_GRAVEYARD,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x58, 0x84, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_ROYAL_VALLEY_GRAVES, ROOM_ROYAL_VALLEY_GRAVES_HEART_PIECE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x188, 0x84, 0x78, 0x118, TRANSITION_SHAPE_AREA_12x12, AREA_ROYAL_VALLEY_GRAVES, ROOM_ROYAL_VALLEY_GRAVES_GINA,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x10, TRANSITION_SHAPE_BORDER_SOUTH_WEST, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x8, 0x50, TRANSITION_SHAPE_BORDER_EAST_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x2, 0x0, 0x0, 0x0 },
#ifndef EU
    { WARP_TYPE_AREA, 0x78, 0x28c, 0x78, 0x18, TRANSITION_SHAPE_AREA_12x12, AREA_ROYAL_VALLEY, ROOM_ROYAL_VALLEY_FOREST_MAZE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
#else
    { WARP_TYPE_AREA, 0x78, 0x288, 0x78, 0x18, TRANSITION_SHAPE_AREA_12x12, AREA_ROYAL_VALLEY, ROOM_ROYAL_VALLEY_FOREST_MAZE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
#endif
    { WARP_TYPE_AREA, 0x78, 0x328, 0x78, 0x98, TRANSITION_SHAPE_AREA_12x12, AREA_ROYAL_VALLEY, ROOM_ROYAL_VALLEY_FOREST_MAZE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_RoyalValley_ForestMaze[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x78, 0x338, TRANSITION_SHAPE_BORDER_SOUTH, AREA_ROYAL_VALLEY, ROOM_ROYAL_VALLEY_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gUnk_08135190[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x78, 0x278, TRANSITION_SHAPE_BORDER_NORTH, AREA_ROYAL_VALLEY, ROOM_ROYAL_VALLEY_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x78, 0x338, TRANSITION_SHAPE_BORDER_SOUTH, AREA_ROYAL_VALLEY, ROOM_ROYAL_VALLEY_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_RoyalValley[] = {
    [ROOM_ROYAL_VALLEY_MAIN] = gExitList_RoyalValley_Main,
    [ROOM_ROYAL_VALLEY_FOREST_MAZE] = gExitList_RoyalValley_ForestMaze,
};

const Transition gExitList_VeilFalls_Main[] = {
    { WARP_TYPE_AREA, 0xa8, 0x22, 0x38, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_VEIL_FALLS_CAVES, ROOM_VEIL_FALLS_CAVES_HALLWAY_2F,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x158, 0x22, 0x118, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_VEIL_FALLS_CAVES, ROOM_VEIL_FALLS_CAVES_HALLWAY_2F,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x118, 0x42, 0xb8, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_VEIL_FALLS_CAVES, ROOM_VEIL_FALLS_CAVES_HALLWAY_1F,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x38, 0x1e2, 0x38, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_VEIL_FALLS_CAVES, ROOM_VEIL_FALLS_CAVES_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xd8, 0x1c2, 0x98, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_VEIL_FALLS_CAVES, ROOM_VEIL_FALLS_CAVES_EXIT,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xd8, 0x142, 0x98, 0x118, TRANSITION_SHAPE_AREA_12x12, AREA_VEIL_FALLS_CAVES,
      ROOM_VEIL_FALLS_CAVES_HALLWAY_BLOCK_PUZZLE, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xa8, 0xc2, 0xb8, 0x118, TRANSITION_SHAPE_AREA_12x12, AREA_VEIL_FALLS_CAVES, ROOM_VEIL_FALLS_CAVES_HALLWAY_RUPEE_PATH,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x38, 0x28, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_VEIL_FALLS_CAVES, ROOM_VEIL_FALLS_CAVES_HALLWAY_HEART_PIECE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xc8, 0x74, 0x38, 0x108, TRANSITION_SHAPE_AREA_12x12, AREA_VEIL_FALLS_CAVES, ROOM_VEIL_FALLS_CAVES_HALLWAY_1F,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x10, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0xb8, TRANSITION_SHAPE_BORDER_NORTH, AREA_VEIL_FALLS_TOP, ROOM_VEIL_FALLS_TOP_0, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3e8, 0xfff, TRANSITION_SHAPE_BORDER_WEST, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x6, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_VeilFalls[] = {
    [ROOM_VEIL_FALLS_MAIN] = gExitList_VeilFalls_Main,
};

const Transition gExitList_Beanstalks_MountCrenel[] = {
    { WARP_TYPE_AREA, 0x58, 0x88, 0x78, 0x18, TRANSITION_SHAPE_AREA_28x12, AREA_BEANSTALKS, ROOM_BEANSTALKS_CRENEL_CLIMB, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Beanstalks_LakeHylia[] = {
    { WARP_TYPE_AREA, 0x58, 0x88, 0x78, 0x18, TRANSITION_SHAPE_AREA_28x12, AREA_BEANSTALKS, ROOM_BEANSTALKS_LAKE_HYLIA_CLIMB,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Beanstalks_Ruins[] = {
    { WARP_TYPE_AREA, 0x58, 0x88, 0x78, 0x18, TRANSITION_SHAPE_AREA_28x12, AREA_BEANSTALKS, ROOM_BEANSTALKS_RUINS_CLIMB, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Beanstalks_EasternHills[] = {
    { WARP_TYPE_AREA, 0x58, 0x88, 0x78, 0x18, TRANSITION_SHAPE_AREA_28x12, AREA_BEANSTALKS, ROOM_BEANSTALKS_EASTERN_HILLS_CLIMB,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Beanstalks_WesternWoods[] = {
    { WARP_TYPE_AREA, 0x58, 0x88, 0x78, 0x18, TRANSITION_SHAPE_AREA_28x12, AREA_BEANSTALKS, ROOM_BEANSTALKS_WESTERN_WOODS_CLIMB,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Beanstalks_MountCrenelClimb[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x58, 0x68, TRANSITION_SHAPE_BORDER_NORTH, AREA_BEANSTALKS, ROOM_BEANSTALKS_CRENEL, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x98, 0x18, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_TOP, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Beanstalks_LakeHyliaClimb[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x58, 0x68, TRANSITION_SHAPE_BORDER_NORTH, AREA_BEANSTALKS, ROOM_BEANSTALKS_LAKE_HYLIA, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x228, 0x18, TRANSITION_SHAPE_BORDER_SOUTH, AREA_LAKE_HYLIA, ROOM_LAKE_HYLIA_BEANSTALK, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Beanstalks_RuinsClimb[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x58, 0x68, TRANSITION_SHAPE_BORDER_NORTH, AREA_BEANSTALKS, ROOM_BEANSTALKS_RUINS, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x48, 0x18, TRANSITION_SHAPE_BORDER_SOUTH, AREA_RUINS, ROOM_RUINS_BEANSTALK, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0,
      0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Beanstalks_EasternHillsClimb[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x58, 0x68, TRANSITION_SHAPE_BORDER_NORTH, AREA_BEANSTALKS, ROOM_BEANSTALKS_EASTERN_HILLS, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x48, 0x18, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_EASTERN_HILLS_CENTER,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Beanstalks_WesternWoodsClimb[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x58, 0x68, TRANSITION_SHAPE_BORDER_NORTH, AREA_BEANSTALKS, ROOM_BEANSTALKS_WESTERN_WOODS, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x38, 0x18, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_WESTERN_WOODS_SOUTH,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_Beanstalks[] = {
    [ROOM_BEANSTALKS_CRENEL] = gExitList_Beanstalks_MountCrenel,
    [ROOM_BEANSTALKS_LAKE_HYLIA] = gExitList_Beanstalks_LakeHylia,
    [ROOM_BEANSTALKS_RUINS] = gExitList_Beanstalks_Ruins,
    [ROOM_BEANSTALKS_EASTERN_HILLS] = gExitList_Beanstalks_EasternHills,
    [ROOM_BEANSTALKS_WESTERN_WOODS] = gExitList_Beanstalks_WesternWoods,
    [ROOM_BEANSTALKS_5] = gExitList_NoExitList,
    [ROOM_BEANSTALKS_6] = gExitList_NoExitList,
    [ROOM_BEANSTALKS_7] = gExitList_NoExitList,
    [ROOM_BEANSTALKS_8] = gExitList_NoExitList,
    [ROOM_BEANSTALKS_9] = gExitList_NoExitList,
    [ROOM_BEANSTALKS_a] = gExitList_NoExitList,
    [ROOM_BEANSTALKS_b] = gExitList_NoExitList,
    [ROOM_BEANSTALKS_c] = gExitList_NoExitList,
    [ROOM_BEANSTALKS_d] = gExitList_NoExitList,
    [ROOM_BEANSTALKS_e] = gExitList_NoExitList,
    [ROOM_BEANSTALKS_f] = gExitList_NoExitList,
    [ROOM_BEANSTALKS_CRENEL_CLIMB] = gExitList_Beanstalks_MountCrenelClimb,
    [ROOM_BEANSTALKS_LAKE_HYLIA_CLIMB] = gExitList_Beanstalks_LakeHyliaClimb,
    [ROOM_BEANSTALKS_RUINS_CLIMB] = gExitList_Beanstalks_RuinsClimb,
    [ROOM_BEANSTALKS_EASTERN_HILLS_CLIMB] = gExitList_Beanstalks_EasternHillsClimb,
    [ROOM_BEANSTALKS_WESTERN_WOODS_CLIMB] = gExitList_Beanstalks_WesternWoodsClimb,
};

const Transition gExitList_LakeWoodsCave_Main[] = {
    { WARP_TYPE_AREA, 0x248, 0x188, 0x148, 0x358, TRANSITION_SHAPE_AREA_12x12, AREA_LAKE_HYLIA, ROOM_LAKE_HYLIA_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_LakeWoodsCave[] = {
    [ROOM_LAKE_WOODS_CAVE_MAIN] = gExitList_LakeWoodsCave_Main,
};

const Transition gExitList_HyruleDigCaves_Main[] = {
    { WARP_TYPE_AREA, 0x188, 0x218, 0x48, 0x118, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_TOWN_UNDERGROUND, ROOM_HYRULE_TOWN_UNDERGROUND_0,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_HyruleDigCaves[] = {
    [ROOM_HYRULE_DIG_CAVES_TOWN] = gExitList_HyruleDigCaves_Main,
};

const Transition gExitList_MinishVillage_Main[] = {
    { WARP_TYPE_AREA, 0x78, 0x88, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_GENTARI_MAIN, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x38, 0x70, 0x68, 0x50, TRANSITION_SHAPE_AREA_12x28, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_GENTARI_EXIT, 1, TRANSITION_TYPE_NORMAL, 0x2, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x258, 0x58, 0xe8, 0xb8, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_FESTARI,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x128, 0x228, 0x80, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_RED,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x168, 0x1d8, 0x80, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_GREEN,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x1a8, 0x208, 0x80, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_HOUSE_INTERIORS, ROOM_MINISH_HOUSE_INTERIORS_BLUE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x1e8, 0x2d8, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_SHOE_MINISH, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x48, 0x248, 0x78, 0xc8, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_POT_MINISH, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x378, 0x288, 0x78, 0x140, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_BARREL_MINISH, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x368, 0x234, 0x58, 0x100, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_BARREL_MINISH, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x78, 0x18, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MINISH_PATHS, ROOM_MINISH_PATHS_MINISH_VILLAGE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1c8, 0x338, TRANSITION_SHAPE_BORDER_NORTH_WEST, AREA_MINISH_WOODS, ROOM_MINISH_WOODS_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1a8, 0x348, TRANSITION_SHAPE_BORDER_WEST_NORTH, AREA_MINISH_WOODS, ROOM_MINISH_WOODS_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x6, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishVillage_SideHouse[] = {
    { WARP_TYPE_AREA, 0x138, 0x68, 0x80, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_SIDE_AREA, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_MinishVillage[] = {
    [ROOM_MINISH_VILLAGE_MAIN] = gExitList_MinishVillage_Main,
    [ROOM_MINISH_VILLAGE_SIDE_HOUSE_AREA] = gExitList_MinishVillage_SideHouse,
    [ROOM_MINISH_VILLAGE_2] = gExitList_NoExitList,
    [ROOM_MINISH_VILLAGE_3] = gExitList_NoExitList,
};

const Transition gExitList_MelarisMine_Main[] = {
#ifdef QUICKSTART
    // Retargeted to Castor Darknut Hall (game.c's own custom link's
    // destination for this same box) instead of the old Crenel Minish
    // Paths - this real door's own position is the exact spot that custom
    // link covers, and it was found winning the race against it in
    // practice (same class of bug the Grimblade retarget below already
    // works around), sending the player to Crenel Minish Paths instead of
    // Hall. Same destination and spawn either way now, so the race no
    // longer matters. facing_direction 0x4 (south) matches the user's
    // request that Link land facing down here.
    { WARP_TYPE_AREA, 0x78, 0x38, 0x77, 0x4a, TRANSITION_SHAPE_AREA_12x12, AREA_CASTOR_DARKNUT, ROOM_CASTOR_DARKNUT_HALL,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
#else
    { WARP_TYPE_AREA, 0x78, 0x38, 0x78, 0xa8, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_MINISH_PATHS, ROOM_CRENEL_MINISH_PATHS_MELARI,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
#endif
    { WARP_TYPE_AREA, 0x70, 0x12c, 0xbc, 0x138, TRANSITION_SHAPE_AREA_12x12, AREA_MT_CRENEL, ROOM_MT_CRENEL_CAVERN_OF_FLAMES_ENTRANCE,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x6, 0x0, 0x0, 0x0 },
    // Back on its vanilla destination. It spent one session retargeted to
    // AREA_DOJOS/ROOM_DOJOS_GRIMBLADE, from when the shop lived in that
    // dojo and this door was how the player reached it. The shop has since
    // moved out to a randomly drawn overworld door and the dojo became an
    // ordinary "? room" reached the vanilla way (down Castle Garden's
    // southeast ladder), but this retarget was never undone - so walking
    // into Melari's Mine's southwest door dropped the player in the dojo,
    // and leaving the dojo ran its own vanilla chain out to Castle Garden's
    // southeast ladder, arriving in a Castle Garden that had never been
    // through the region chain's setup. Reported by the user as being
    // trapped there. Same row as the #else branch used to hold, no
    // QUICKSTART divergence left: the room it leads to is a content site
    // now (sQuickStartRoomContentSites), like Melari's other two.
    { WARP_TYPE_AREA, 0xa8, 0x220, 0x78, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_SOUTHWEST, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x228, 0x220, 0x78, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_SOUTHEAST, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x280, 0x11c, 0x24, 0x56, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_HOUSE_INTERIORS,
      ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_EAST, 1, TRANSITION_TYPE_NORMAL, 0x2, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_MelarisMine[] = {
    [ROOM_MELARIS_MINE_MAIN] = gExitList_MelarisMine_Main,
};

#ifdef QUICKSTART
// Retargeted as a QUICKSTART "2-door ? room" pool candidate - both
// real doors now lead back to the Lon Lon Ranch cave-connector ledge
// (0xb8,0x138), same shared return spot every other 2-door pool room
// uses (see game.c: sQuickStart2DoorSmallRoomPool/LargeRoomPool). Real
// startX/startY/shape/warp_type kept as-is - only destination changes.
const Transition gExitList_MinishPaths_ToMinishVillage[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3fe, 0x3fe, TRANSITION_SHAPE_BORDER_NORTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3fd, 0x3fd, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_MinishPaths_ToMinishVillage[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x208, 0x3e0, TRANSITION_SHAPE_BORDER_NORTH, AREA_MINISH_VILLAGE, ROOM_MINISH_VILLAGE_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1d8, 0x398, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MINISH_WOODS, ROOM_MINISH_WOODS_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition gExitList_MinishPaths_CastorWilds[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x28, 0x68, TRANSITION_SHAPE_BORDER_NORTH, AREA_CASTOR_WILDS, ROOM_CASTOR_WILDS_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x28, 0xa8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTOR_WILDS, ROOM_CASTOR_WILDS_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishPaths_HyruleTown[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x398, 0x68, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishPaths_LonLonRanch[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1e0, 0x174, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishPaths_MayorsCabin[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x2a8, 0x31a, TRANSITION_SHAPE_BORDER_NORTH, AREA_LAKE_HYLIA, ROOM_LAKE_HYLIA_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH, 0x0,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xb8, 0x48, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HOUSE_INTERIORS_4, ROOM_HOUSE_INTERIORS_4_MAYOR_LAKE_CABIN,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_MinishPaths[] = {
    [ROOM_MINISH_PATHS_MINISH_VILLAGE] = gExitList_MinishPaths_ToMinishVillage,
    [ROOM_MINISH_PATHS_BOW] = gExitList_MinishPaths_CastorWilds,
    [ROOM_MINISH_PATHS_SCHOOLYARD] = gExitList_MinishPaths_HyruleTown,
    [ROOM_MINISH_PATHS_LON_LON_RANCH] = gExitList_MinishPaths_LonLonRanch,
    [ROOM_MINISH_PATHS_LAKE_HYLIA] = gExitList_MinishPaths_MayorsCabin,
};

const Transition gExitList_CrenelMinishPaths_CrenelBean[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xd2, 0x60, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_ENTRANCE, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_CrenelMinishPaths_CrenelWater[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x372, 0xf5, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_ENTRANCE, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#ifdef QUICKSTART
// Retargeted as a QUICKSTART "2-door ? room" pool candidate - both
// real doors now lead back to the Lon Lon Ranch cave-connector ledge
// (0xb8,0x138), same shared return spot every other 2-door pool room
// uses (see game.c: sQuickStart2DoorSmallRoomPool/LargeRoomPool). Real
// startX/startY/shape/warp_type kept as-is - only destination changes.
const Transition gExitList_CrenelMinishPaths_Rainfall[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3fe, 0x3fe, TRANSITION_SHAPE_BORDER_WEST, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x6, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3fd, 0x3fd, TRANSITION_SHAPE_BORDER_EAST, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x2, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_CrenelMinishPaths_Rainfall[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x2cc, 0x98, TRANSITION_SHAPE_BORDER_WEST, AREA_MT_CRENEL, ROOM_MT_CRENEL_TOP, 1, TRANSITION_TYPE_INSTANT_MINISH, 0x6,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x2f4, 0x98, TRANSITION_SHAPE_BORDER_EAST, AREA_MT_CRENEL, ROOM_MT_CRENEL_TOP, 1, TRANSITION_TYPE_INSTANT_MINISH, 0x2,
      0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
#ifdef QUICKSTART
// Retargeted as a QUICKSTART "2-door ? room" pool candidate - both
// real doors now lead back to the Lon Lon Ranch cave-connector ledge
// (0xb8,0x138), same shared return spot every other 2-door pool room
// uses (see game.c: sQuickStart2DoorSmallRoomPool/LargeRoomPool). Real
// startX/startY/shape/warp_type kept as-is - only destination changes.
const Transition gExitList_CrenelMinishPaths_MelarisMine[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3fe, 0x3fe, TRANSITION_SHAPE_BORDER_EAST, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x2, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3fd, 0x3fd, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_CrenelMinishPaths_MelarisMine[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xf4, 0x108, TRANSITION_SHAPE_BORDER_EAST, AREA_MT_CRENEL, ROOM_MT_CRENEL_CAVERN_OF_FLAMES_ENTRANCE,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x2, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x78, 0x48, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MELARIS_MINE, ROOM_MELARIS_MINE_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition* const gExitLists_CrenelMinishPaths[] = {
    [ROOM_CRENEL_MINISH_PATHS_BEAN] = gExitList_CrenelMinishPaths_CrenelBean,
    [ROOM_CRENEL_MINISH_PATHS_SPRING_WATER] = gExitList_CrenelMinishPaths_CrenelWater,
    [ROOM_CRENEL_MINISH_PATHS_RAIN] = gExitList_CrenelMinishPaths_Rainfall,
    [ROOM_CRENEL_MINISH_PATHS_MELARI] = gExitList_CrenelMinishPaths_MelarisMine,
};

#ifdef QUICKSTART
// THE TRILBY LADDER TRAP (user report, Aug 2026: "the player is able to go
// UP, but cannot go back down... the player gets stuck on this ledge").
//
// Measured, not inferred. Trilby Highlands' northwest corner holds a raised
// pocket - tiles tx 2-12, ty 7-12 - and a flood of the room's collision puts
// it in a component of its own: 44 tiles against the main room's 334, with
// nothing joining them. Walking every direction from inside the pocket keeps
// the player inside it. The Mole Mitts dig cave's mouth is IN that pocket,
// and vanilla's exit from the cave lands at (0x88,0x78) - back in the pocket
// again. So the cave was not a way out; it was the pocket's only furniture.
//
// The cave is now the way down. Its overworld exit lands at (0x98,0x268)
// instead - a spot vanilla itself uses as the landing for this region's
// ROOM_CAVES_TRILBY_HIGHLANDS exit (see gExitList_Caves_TrilbyHighlands
// below), so it is proven walkable and in the main body of the room rather
// than measured by us and hoped for.
//
// This is the general shape for a one-way overworld pocket that contains a
// cave: leave the climb alone, and make the cave's exit the descent. It
// costs one retargeted row per region and needs no new machinery, which
// matters as more regions come in - see the roadmap's Mole Mitts note.
const Transition gExitList_DigCaves1_TrilbyHighlands[] = {
    { WARP_TYPE_AREA, 0x88, 0x44, 0x98, 0x268, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD,
      ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x1a8, 0x78, 0xb8, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_TRILBY_MITTS_FAIRY_FOUNTAIN,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_DigCaves1_TrilbyHighlands[] = {
    { WARP_TYPE_AREA, 0x88, 0x44, 0x88, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x1a8, 0x78, 0xb8, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_TRILBY_MITTS_FAIRY_FOUNTAIN,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition* const gExitLists_DigCaves1[] = {
    [ROOM_DIG_CAVES_EASTERN_HILLS] = gExitList_NoExitList,
    [ROOM_DIG_CAVES_1] = gExitList_NoExitList,
    [ROOM_DIG_CAVES_2] = gExitList_NoExitList,
    [ROOM_DIG_CAVES_TRILBY_HIGHLANDS] = gExitList_DigCaves1_TrilbyHighlands,
};

#ifdef QUICKSTART
// Retargeted - see the "? room" pool comment above gExitList_MinishHouseInteriors_Red.
const Transition gExitList_MinishHouseInteriors_GentariMain[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x68, 0x90, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_MinishHouseInteriors_GentariMain[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x78, 0x98, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MINISH_VILLAGE, ROOM_MINISH_VILLAGE_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
// GENTARI_EXIT is no longer QUICKSTART's cave connector - removed entirely
// per the user's explicit request ("remove GENTARI_EXIT from the pool
// entirely and only use the rooms we just identified"), now that a real
// pool of genuine 2-door rooms exists (see game.c:
// sQuickStart2DoorSmallRoomPool/LargeRoomPool). This room was only ever a
// workaround (its single real door made bidirectional via a duplicated
// sQuickStartLinks entry) because no proper 2-door candidates had been
// surveyed yet. Reverted to pure vanilla - no #ifdef QUICKSTART override.
const Transition gExitList_MinishHouseInteriors_GentariExit[] = {
    { WARP_TYPE_AREA, 0x48, 0x50, 0x28, 0x70, TRANSITION_SHAPE_AREA_12x28, AREA_MINISH_VILLAGE, ROOM_MINISH_VILLAGE_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x6, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#ifdef QUICKSTART
// Retargeted as a QUICKSTART "2-door ? room" pool candidate - both
// real doors now lead back to the Lon Lon Ranch cave-connector ledge
// (0xb8,0x138), same shared return spot every other 2-door pool room
// uses (see game.c: sQuickStart2DoorSmallRoomPool/LargeRoomPool). Real
// startX/startY/shape/warp_type kept as-is - only destination changes.
const Transition gExitList_MinishHouseInteriors_Festari[] = {
    { WARP_TYPE_AREA, 0xe8, 0xe8, 0x3fe, 0x3fe, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xe8, 0x18, 0x3fd, 0x3fd, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_MinishHouseInteriors_Festari[] = {
    { WARP_TYPE_AREA, 0xe8, 0xe8, 0x258, 0x68, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_VILLAGE, ROOM_MINISH_VILLAGE_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xe8, 0x18, 0x1d0, 0x33c, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_WOODS, ROOM_MINISH_WOODS_MAIN, 1,
      TRANSITION_TYPE_INSTANT_MINISH, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
#ifdef QUICKSTART
// Retargeted the same way as the Tree Interiors ladder rooms further down
// this file - one of the "? room" pool's 20 candidates (game.c,
// sQuickStartQuestionRoomPool). Every pool room shares the same single
// landing spot regardless of which of the 3 ladders it ends up assigned
// to for a given save (south of ladder 0's own pot, clear of all 3
// ladders' trigger boxes - see QUICKSTART_QUESTION_ROOM_RETURN_* in
// game.c), since a static compile-time table can't otherwise vary its
// destination coordinates per save.
const Transition gExitList_MinishHouseInteriors_Red[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x68, 0x90, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_MinishHouseInteriors_Red[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x128, 0x238, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MINISH_VILLAGE, ROOM_MINISH_VILLAGE_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
#ifdef QUICKSTART
const Transition gExitList_MinishHouseInteriors_Green[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x68, 0x90, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_MinishHouseInteriors_Green[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x168, 0x1e8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MINISH_VILLAGE, ROOM_MINISH_VILLAGE_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
#ifdef QUICKSTART
const Transition gExitList_MinishHouseInteriors_Blue[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x68, 0x90, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_MinishHouseInteriors_Blue[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1a8, 0x218, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MINISH_VILLAGE, ROOM_MINISH_VILLAGE_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
#ifdef QUICKSTART
const Transition gExitList_MinishHouseInteriors_SideArea[] = {
    // Back to a plain "? room" pool entry (the shared Castle Garden return
    // point every other pool room uses) - the cave-connector's second door
    // moved to ROOM_MINISH_HOUSE_INTERIORS_GENTARI_EXIT instead, per the
    // user's own request (this room stays in the small-room pool).
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x68, 0x90, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_MinishHouseInteriors_SideArea[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x138, 0x78, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MINISH_VILLAGE, ROOM_MINISH_VILLAGE_SIDE_HOUSE_AREA,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
#ifdef QUICKSTART
const Transition gExitList_MinishHouseInteriors_ShoeMinish[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x68, 0x90, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_MinishHouseInteriors_ShoeMinish[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1e8, 0x2e8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MINISH_VILLAGE, ROOM_MINISH_VILLAGE_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
#ifdef QUICKSTART
const Transition gExitList_MinishHouseInteriors_PotMinish[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x68, 0x90, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_MinishHouseInteriors_PotMinish[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x48, 0x258, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MINISH_VILLAGE, ROOM_MINISH_VILLAGE_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition gExitList_MinishHouseInteriors_BarrelMinish[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x378, 0x298, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MINISH_VILLAGE, ROOM_MINISH_VILLAGE_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x58, 0xd0, 0x368, 0x218, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_VILLAGE, ROOM_MINISH_VILLAGE_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishHouseInteriors_NULL1[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x378, 0x290, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MINISH_VILLAGE, ROOM_MINISH_VILLAGE_SIDE_HOUSE_AREA,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishHouseInteriors_NULL2[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x138, 0x70, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MINISH_VILLAGE, ROOM_MINISH_VILLAGE_SIDE_HOUSE_AREA,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#ifdef QUICKSTART
// Retargeted (endX/endY only - area/room/shape all already correctly
// point back to Melari's Mine) so each house's own real exit lands just
// outside this file's own QuickStartLink trigger box for that same door
// (game.c, sQuickStartLinks) instead of vanilla's own landing spot - a
// symmetric "same door" round trip, same reasoning as Castle Garden's
// south border. Confirmed walkable open ground at each of these three
// spots by walking there directly from the door itself in the emulator.
const Transition gExitList_MinishHouseInteriors_MelariMinesSouthwest[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xa8, 0x20d, TRANSITION_SHAPE_BORDER_NORTH, AREA_MELARIS_MINE, ROOM_MELARIS_MINE_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishHouseInteriors_MelariMinesSoutheast[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x228, 0x20d, TRANSITION_SHAPE_BORDER_NORTH, AREA_MELARIS_MINE, ROOM_MELARIS_MINE_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishHouseInteriors_MelariMinesEast[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x26c, 0x11e, TRANSITION_SHAPE_BORDER_WEST, AREA_MELARIS_MINE, ROOM_MELARIS_MINE_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x6, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_MinishHouseInteriors_MelariMinesSouthwest[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xa8, 0x208, TRANSITION_SHAPE_BORDER_NORTH, AREA_MELARIS_MINE, ROOM_MELARIS_MINE_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishHouseInteriors_MelariMinesSoutheast[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x228, 0x208, TRANSITION_SHAPE_BORDER_NORTH, AREA_MELARIS_MINE, ROOM_MELARIS_MINE_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishHouseInteriors_MelariMinesEast[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x270, 0x11e, TRANSITION_SHAPE_BORDER_WEST, AREA_MELARIS_MINE, ROOM_MELARIS_MINE_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x6, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
// Back on its real vanilla exit (WW-South), same treatment as
// gExitList_MinishHouseInteriors_SouthHyruleField below and for the same
// reason: this room left the drawn small-room pool when it became a
// walk-in content site (the Western Wood Minish door), but its pool-era
// retarget - south border to Castle Garden at the shared ladder landing -
// was left behind, which is the user's "exit a ? room, appear at the
// cellar ladder" report. A walk-in player is minish-sized in here, so
// vanilla's INSTANT_MINISH type is the correct one again.
const Transition gExitList_MinishHouseInteriors_HyruleFieldSouthwest[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xb8, 0x35, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_WESTERN_WOODS_SOUTH,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
// Back on its real vanilla exit, and no longer a member of the ladder pool
// (game.c, sQuickStartSmallRoomPool). It is one of only two Minish-gated
// destinations in the whole five-region pool - the other is
// ROOM_MINISH_CAVES_OUTSIDE_LINKS_HOUSE - and the player now has a way in:
// South Hyrule Field's Minish portal is revealed on entry
// (QuickStartRevealHiddenLadders), so this is a real "? room" entered the
// way vanilla built it, by shrinking and walking through the tiny door at
// (72,456).
//
// The retarget it replaces sent this room's south border to Castle Garden,
// with the transition type flipped from INSTANT_MINISH to NORMAL, because
// back then the only way in was a normal-size ladder warp. Both halves of
// that have to go together: leaving INSTANT_MINISH in place while the room
// was still poolable would trap a normal-size player here, since that type
// only fires for a minish player.
const Transition gExitList_MinishHouseInteriors_SouthHyruleField[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x48, 0x1d4, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#ifdef QUICKSTART
const Transition gExitList_MinishHouseInteriors_NextToKnuckle[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x68, 0x90, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_MinishHouseInteriors_NextToKnuckle[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x28, 0x55, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
#ifdef QUICKSTART
// Retargeted - see the "? room" pool comment above
// gExitList_MinishHouseInteriors_Red (and gExitList_MinishHouseInteriors_
// HyruleFieldSouthwest just above for why this one specifically needed it
// added rather than already having it).
const Transition gExitList_MinishHouseInteriors_Librari[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x68, 0x90, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_MinishHouseInteriors_Librari[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1e8, 0x1b4, TRANSITION_SHAPE_BORDER_SOUTH, AREA_LAKE_HYLIA, ROOM_LAKE_HYLIA_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
// Back on its real vanilla exit (EH-South) - the second half of the same
// fix as gExitList_MinishHouseInteriors_HyruleFieldSouthwest above; this
// is the Eastern Hills Minish house the user's report actually named.
const Transition gExitList_MinishHouseInteriors_HyruleFieldExit[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x38, 0x35, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_EASTERN_HILLS_SOUTH,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#ifdef QUICKSTART
const Transition gExitList_MinishHouseInteriors_HyruleTown[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x68, 0x90, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_MinishHouseInteriors_HyruleTown[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x38, 0x1b5, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
#ifdef QUICKSTART
const Transition gExitList_MinishHouseInteriors_MinishWoodsBomb[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x68, 0x90, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_MinishHouseInteriors_MinishWoodsBomb[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x138, 0x325, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MINISH_WOODS, ROOM_MINISH_WOODS_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
#ifdef QUICKSTART
const Transition gExitList_MinishHouseInteriors_LakeHyliaOcarina[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x68, 0x90, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1, TRANSITION_TYPE_NORMAL, 0x4,
      0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_MinishHouseInteriors_LakeHyliaOcarina[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xc8, 0x1a4, TRANSITION_SHAPE_BORDER_SOUTH, AREA_LAKE_HYLIA, ROOM_LAKE_HYLIA_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH, 0x4,
      0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition* const gExitLists_MinishHouseInteriors[] = {
    [ROOM_MINISH_HOUSE_INTERIORS_GENTARI_MAIN] = gExitList_MinishHouseInteriors_GentariMain,
    [ROOM_MINISH_HOUSE_INTERIORS_GENTARI_EXIT] = gExitList_MinishHouseInteriors_GentariExit,
    [ROOM_MINISH_HOUSE_INTERIORS_FESTARI] = gExitList_MinishHouseInteriors_Festari,
    [ROOM_MINISH_HOUSE_INTERIORS_RED] = gExitList_MinishHouseInteriors_Red,
    [ROOM_MINISH_HOUSE_INTERIORS_GREEN] = gExitList_MinishHouseInteriors_Green,
    [ROOM_MINISH_HOUSE_INTERIORS_BLUE] = gExitList_MinishHouseInteriors_Blue,
    [ROOM_MINISH_HOUSE_INTERIORS_SIDE_AREA] = gExitList_MinishHouseInteriors_SideArea,
    [ROOM_MINISH_HOUSE_INTERIORS_SHOE_MINISH] = gExitList_MinishHouseInteriors_ShoeMinish,
    [ROOM_MINISH_HOUSE_INTERIORS_POT_MINISH] = gExitList_MinishHouseInteriors_PotMinish,
    [ROOM_MINISH_HOUSE_INTERIORS_BARREL_MINISH] = gExitList_MinishHouseInteriors_BarrelMinish,
    [ROOM_MINISH_HOUSE_INTERIORS_NULL1] = gExitList_MinishHouseInteriors_NULL1,
    [ROOM_MINISH_HOUSE_INTERIORS_NULL2] = gExitList_MinishHouseInteriors_NULL2,
    [ROOM_MINISH_HOUSE_INTERIORS_c] = gExitList_NoExitList,
    [ROOM_MINISH_HOUSE_INTERIORS_d] = gExitList_NoExitList,
    [ROOM_MINISH_HOUSE_INTERIORS_e] = gExitList_NoExitList,
    [ROOM_MINISH_HOUSE_INTERIORS_f] = gExitList_NoExitList,
    [ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_SOUTHWEST] = gExitList_MinishHouseInteriors_MelariMinesSouthwest,
    [ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_SOUTHEAST] = gExitList_MinishHouseInteriors_MelariMinesSoutheast,
    [ROOM_MINISH_HOUSE_INTERIORS_MELARI_MINES_EAST] = gExitList_MinishHouseInteriors_MelariMinesEast,
    [ROOM_MINISH_HOUSE_INTERIORS_13] = gExitList_NoExitList,
    [ROOM_MINISH_HOUSE_INTERIORS_14] = gExitList_NoExitList,
    [ROOM_MINISH_HOUSE_INTERIORS_15] = gExitList_NoExitList,
    [ROOM_MINISH_HOUSE_INTERIORS_16] = gExitList_NoExitList,
    [ROOM_MINISH_HOUSE_INTERIORS_17] = gExitList_NoExitList,
    [ROOM_MINISH_HOUSE_INTERIORS_18] = gExitList_NoExitList,
    [ROOM_MINISH_HOUSE_INTERIORS_19] = gExitList_NoExitList,
    [ROOM_MINISH_HOUSE_INTERIORS_1a] = gExitList_NoExitList,
    [ROOM_MINISH_HOUSE_INTERIORS_1b] = gExitList_NoExitList,
    [ROOM_MINISH_HOUSE_INTERIORS_1c] = gExitList_NoExitList,
    [ROOM_MINISH_HOUSE_INTERIORS_1d] = gExitList_NoExitList,
    [ROOM_MINISH_HOUSE_INTERIORS_1e] = gExitList_NoExitList,
    [ROOM_MINISH_HOUSE_INTERIORS_1f] = gExitList_NoExitList,
    [ROOM_MINISH_HOUSE_INTERIORS_HYRULE_FIELD_SOUTHWEST] = gExitList_MinishHouseInteriors_HyruleFieldSouthwest,
    [ROOM_MINISH_HOUSE_INTERIORS_SOUTH_HYRULE_FIELD] = gExitList_MinishHouseInteriors_SouthHyruleField,
    [ROOM_MINISH_HOUSE_INTERIORS_NEXT_TO_KNUCKLE] = gExitList_MinishHouseInteriors_NextToKnuckle,
    [ROOM_MINISH_HOUSE_INTERIORS_LIBRARI] = gExitList_MinishHouseInteriors_Librari,
    [ROOM_MINISH_HOUSE_INTERIORS_HYRULE_FIELD_EXIT] = gExitList_MinishHouseInteriors_HyruleFieldExit,
    [ROOM_MINISH_HOUSE_INTERIORS_HYRULE_TOWN] = gExitList_MinishHouseInteriors_HyruleTown,
    [ROOM_MINISH_HOUSE_INTERIORS_MINISH_WOODS_BOMB] = gExitList_MinishHouseInteriors_MinishWoodsBomb,
    [ROOM_MINISH_HOUSE_INTERIORS_LAKE_HYLIA_OCARINA] = gExitList_MinishHouseInteriors_LakeHyliaOcarina,
};

const Transition gExitList_OuterFortressOfWinds_EntranceHall[] = {
    { WARP_TYPE_AREA, 0x78, 0x22, 0x78, 0xb0, TRANSITION_SHAPE_AREA_12x12, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_WIZZROBE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x128, 0x22, 0x68, 0xb0, TRANSITION_SHAPE_AREA_12x12, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_WEST_STAIRS_1F,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x1d8, 0x22, 0x78, 0xb0, TRANSITION_SHAPE_AREA_12x12, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_CENTER_STAIRS_1F,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x288, 0x22, 0x68, 0xb0, TRANSITION_SHAPE_AREA_12x12, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_EAST_STAIRS_1F,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x338, 0x22, 0x88, 0xb0, TRANSITION_SHAPE_AREA_12x12, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_HEART_PIECE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x198, 0x28, TRANSITION_SHAPE_BORDER_SOUTH, AREA_RUINS, ROOM_RUINS_FORTRESS_ENTRANCE, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_OuterFortressOfWinds_2F[] = {
    { WARP_TYPE_AREA, 0x78, 0x22, 0x88, 0xb0, TRANSITION_SHAPE_AREA_12x12, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_STALFOS,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x1d8, 0x92, 0x88, 0x170, TRANSITION_SHAPE_AREA_12x12, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_MAIN_2F,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x288, 0x92, 0x88, 0xa0, TRANSITION_SHAPE_AREA_12x12, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_EAST_STAIRS_2F,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x338, 0x22, 0x28, 0xb0, TRANSITION_SHAPE_AREA_12x12, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_BOSS_KEY,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x128, 0xd8, 0x128, 0x68, TRANSITION_SHAPE_AREA_12x12, AREA_OUTER_FORTRESS_OF_WINDS, ROOM_OUTER_FORTRESS_OF_WINDS_3F,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x1d8, 0xd8, 0x1d8, 0x68, TRANSITION_SHAPE_AREA_12x12, AREA_OUTER_FORTRESS_OF_WINDS, ROOM_OUTER_FORTRESS_OF_WINDS_3F,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x288, 0xd8, 0x288, 0x68, TRANSITION_SHAPE_AREA_12x12, AREA_OUTER_FORTRESS_OF_WINDS, ROOM_OUTER_FORTRESS_OF_WINDS_3F,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x338, 0xd8, 0x338, 0x68, TRANSITION_SHAPE_AREA_12x12, AREA_OUTER_FORTRESS_OF_WINDS, ROOM_OUTER_FORTRESS_OF_WINDS_3F,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_OuterFortressOfWinds_3F[] = {
    { WARP_TYPE_AREA, 0x68, 0x22, 0x78, 0xa0, TRANSITION_SHAPE_AREA_12x12, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_PIT_PLATFORMS,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x1d8, 0x22, 0x198, 0xa0, TRANSITION_SHAPE_AREA_12x12, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_WEST_KEY_LEVER,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x2e8, 0x22, 0x198, 0x178, TRANSITION_SHAPE_AREA_12x12, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_EAST_KEY_LEVER,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x338, 0x22, 0x1f8, 0x178, TRANSITION_SHAPE_AREA_12x12, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_EAST_KEY_LEVER,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x1d8, 0x84, 0x1d8, 0xf8, TRANSITION_SHAPE_AREA_12x12, AREA_OUTER_FORTRESS_OF_WINDS, ROOM_OUTER_FORTRESS_OF_WINDS_2F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x288, 0x84, 0x288, 0xf8, TRANSITION_SHAPE_AREA_12x12, AREA_OUTER_FORTRESS_OF_WINDS, ROOM_OUTER_FORTRESS_OF_WINDS_2F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x338, 0x84, 0x338, 0xf8, TRANSITION_SHAPE_AREA_12x12, AREA_OUTER_FORTRESS_OF_WINDS, ROOM_OUTER_FORTRESS_OF_WINDS_2F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x128, 0x84, 0x128, 0xf8, TRANSITION_SHAPE_AREA_12x12, AREA_OUTER_FORTRESS_OF_WINDS, ROOM_OUTER_FORTRESS_OF_WINDS_2F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_OuterFortressOfWinds_MoleMitts[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x88, 0x22, TRANSITION_SHAPE_BORDER_SOUTH, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_ENTRANCE_MOLE_MITTS,
      2, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_OuterFortressOfWinds_SmallKey[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x78, 0x22, TRANSITION_SHAPE_BORDER_SOUTH, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_MINISH_HOLE,
      2, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_OuterFortressOfWinds[] = {
    [ROOM_OUTER_FORTRESS_OF_WINDS_ENTRANCE_HALL] = gExitList_OuterFortressOfWinds_EntranceHall,
    [ROOM_OUTER_FORTRESS_OF_WINDS_2F] = gExitList_OuterFortressOfWinds_2F,
    [ROOM_OUTER_FORTRESS_OF_WINDS_3F] = gExitList_OuterFortressOfWinds_3F,
    [ROOM_OUTER_FORTRESS_OF_WINDS_MOLE_MITTS] = gExitList_OuterFortressOfWinds_MoleMitts,
    [ROOM_OUTER_FORTRESS_OF_WINDS_SMALL_KEY] = gExitList_OuterFortressOfWinds_SmallKey,
};

const Transition gExitList_HyliaDigCaves_North[] = {
    { WARP_TYPE_AREA, 0x248, 0x62, 0x208, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_LAKE_HYLIA, ROOM_LAKE_HYLIA_BEANSTALK, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x308, 0x62, 0x308, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_LAKE_HYLIA, ROOM_LAKE_HYLIA_BEANSTALK, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x398, 0x52, 0x388, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_LAKE_HYLIA, ROOM_LAKE_HYLIA_BEANSTALK, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_HyliaDigCaves[] = {
    [ROOM_HYLIA_DIG_CAVES_0] = gExitList_NoExitList,
    [ROOM_HYLIA_DIG_CAVES_1] = gExitList_HyliaDigCaves_North,
    NULL,
    NULL,
    NULL,
};

const Transition gExitList_VeilFallsTop_Main[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x10, TRANSITION_SHAPE_BORDER_SOUTH, AREA_VEIL_FALLS, ROOM_VEIL_FALLS_MAIN, 1, TRANSITION_TYPE_NORMAL, 0x4,
      0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_VeilFallsTop[] = {
    [ROOM_VEIL_FALLS_TOP_0] = gExitList_VeilFallsTop_Main,
};

const Transition gExitList_HouseInteriors2_Stranger[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x98, 0x17c, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors2_WestOracle[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x40, 0x1cc, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors2_2[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x40, 0x1cc, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors2_3[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x40, 0x1cc, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors2_DrLeft[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x38, 0x25c, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors2_NULL1[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x40, 0x5c, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_EASTERN_HILLS_NORTH,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors2_Romio[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x2e8, 0x304, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors2_Julietta[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x348, 0x30c, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors2_Percy[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x90, 0x5c, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_WESTERN_WOODS_CENTER,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors2_EastOracle[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x2b8, 0x374, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors2_A[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x2b8, 0x374, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors2_B[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x2b8, 0x374, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors2_Cucco[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3b8, 0x36c, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#ifdef QUICKSTART
// Link's House is a "? room" now (game.c: sQuickStartRoomContentSites), so
// this room is entered through its own real vanilla front door from South
// Hyrule Field, holds a randomized event, and is left the same way.
//
// The stairs up to the bedroom are neutralized, and only the stairs: the
// bedroom room itself does not load correctly outside vanilla's own opening
// sequence. Confirmed empirically - warping straight into
// ROOM_HOUSE_INTERIORS_2_LINKS_HOUSE_BEDROOM, and walking up these stairs,
// both land the player in South Hyrule Field at (1384,472) within a second,
// nowhere near the house. That isn't a softlock, but it is a silent
// teleport into the middle of a field from a spot the player has no reason
// to expect one, so the stairs are pointed back into this room instead
// (arriving at (0x58,0x38), a clear 32px below the stairs tile so the door
// can't immediately re-fire). Walking up now simply reads as "nothing up
// there". Same treatment, and same reasoning, as the Heart Piece Hallway's
// onward door to ROOM_CAVES_TO_GRAVEYARD.
//
// The border below is vanilla's own, untouched - that is the exit the
// player actually uses. It needs the front door to be openable at all,
// which is a separate fix in game.c (QuickStartRevealHiddenLadders):
// this house's HOUSE_DOOR_INT ships with unk7d = 1, so it never opens by
// being walked into, and without that fix this room is a trap.
// The stairs lead upstairs again, exactly as vanilla. They were looped back
// into this same room because the bedroom did not survive being entered
// outside the opening sequence - it ran script_PlayerIntro and spat the
// player out into South Hyrule Field, which read in play as "the stairs do
// nothing". That was a symptom of the global START flag never being set,
// which GameTask_Transition now does; with it set the bedroom loads
// normally (verified: the player stays in (34,21) and its content site
// spawns there). So this row is vanilla's again.
const Transition gExitList_HouseInteriors2_LinksHouseEntrance[] = {
    { WARP_TYPE_AREA, 0x58, 0x18, 0x58, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_2, ROOM_HOUSE_INTERIORS_2_LINKS_HOUSE_BEDROOM,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x290, 0x19c, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_HouseInteriors2_LinksHouseEntrance[] = {
    { WARP_TYPE_AREA, 0x58, 0x18, 0x58, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_2, ROOM_HOUSE_INTERIORS_2_LINKS_HOUSE_BEDROOM,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x290, 0x19c, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition gExitList_HouseInteriors2_Dampe[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1a0, 0x1ac, TRANSITION_SHAPE_BORDER_SOUTH, AREA_ROYAL_VALLEY, ROOM_ROYAL_VALLEY_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors2_NULL2[] = {
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors2_StockwellLakeHouse[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x120, 0x4c, TRANSITION_SHAPE_BORDER_SOUTH, AREA_LAKE_HYLIA, ROOM_LAKE_HYLIA_MAIN, 1, TRANSITION_TYPE_NORMAL, 0x4,
      0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors2_LinksHouseBedroom[] = {
    { WARP_TYPE_AREA, 0x58, 0x18, 0x58, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_2,
      ROOM_HOUSE_INTERIORS_2_LINKS_HOUSE_ENTRANCE, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_HouseInteriors2[] = {
    [ROOM_HOUSE_INTERIORS_2_STRANGER] = gExitList_HouseInteriors2_Stranger,
    [ROOM_HOUSE_INTERIORS_2_WEST_ORACLE] = gExitList_HouseInteriors2_WestOracle,
    [ROOM_HOUSE_INTERIORS_2_2] = gExitList_HouseInteriors2_2,
    [ROOM_HOUSE_INTERIORS_2_3] = gExitList_HouseInteriors2_3,
    [ROOM_HOUSE_INTERIORS_2_DR_LEFT] = gExitList_HouseInteriors2_DrLeft,
    [ROOM_HOUSE_INTERIORS_2_5] = gExitList_HouseInteriors2_NULL1,
    [ROOM_HOUSE_INTERIORS_2_ROMIO] = gExitList_HouseInteriors2_Romio,
    [ROOM_HOUSE_INTERIORS_2_JULIETTA] = gExitList_HouseInteriors2_Julietta,
    [ROOM_HOUSE_INTERIORS_2_PERCY] = gExitList_HouseInteriors2_Percy,
    [ROOM_HOUSE_INTERIORS_2_EAST_ORACLE] = gExitList_HouseInteriors2_EastOracle,
    [ROOM_HOUSE_INTERIORS_2_a] = gExitList_HouseInteriors2_A,
    [ROOM_HOUSE_INTERIORS_2_b] = gExitList_HouseInteriors2_B,
    [ROOM_HOUSE_INTERIORS_2_CUCCO] = gExitList_HouseInteriors2_Cucco,
    [ROOM_HOUSE_INTERIORS_2_d] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_e] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_f] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_LINKS_HOUSE_ENTRANCE] = gExitList_HouseInteriors2_LinksHouseEntrance,
    [ROOM_HOUSE_INTERIORS_2_LINKS_HOUSE_SMITH] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_DAMPE] = gExitList_HouseInteriors2_Dampe,
    [ROOM_HOUSE_INTERIORS_2_13] = gExitList_HouseInteriors2_NULL2,
    [ROOM_HOUSE_INTERIORS_2_STOCKWELL_LAKE_HOUSE] = gExitList_HouseInteriors2_StockwellLakeHouse,
    [ROOM_HOUSE_INTERIORS_2_LINKS_HOUSE_BEDROOM] = gExitList_HouseInteriors2_LinksHouseBedroom,
    [ROOM_HOUSE_INTERIORS_2_16] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_17] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_18] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_19] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_1a] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_1b] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_1c] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_1d] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_1e] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_1f] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_20] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_21] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_22] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_23] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_24] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_25] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_26] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_27] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_28] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_29] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_2a] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_2b] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_2c] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_2d] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_2e] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_2_2f] = gExitList_NoExitList,
};

const Transition gExitList_HouseInteriors4_Carpenter[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x90, 0x2dc, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors4_Swiftblade[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x138, 0x39c, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors4_RanchHouseWest[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x158, 0x28c, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors4_RanchHouseEast[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x188, 0x28c, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors4_FarmHouse[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x40, 0x5c, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_EASTERN_HILLS_NORTH,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors4_MayorLakeCabin[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x2a0, 0x38c, TRANSITION_SHAPE_BORDER_SOUTH, AREA_LAKE_HYLIA, ROOM_LAKE_HYLIA_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_HouseInteriors4[] = {
    [ROOM_HOUSE_INTERIORS_4_CARPENTER] = gExitList_HouseInteriors4_Carpenter,
    [ROOM_HOUSE_INTERIORS_4_SWIFTBLADE] = gExitList_HouseInteriors4_Swiftblade,
    [ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_WEST] = gExitList_HouseInteriors4_RanchHouseWest,
    [ROOM_HOUSE_INTERIORS_4_RANCH_HOUSE_EAST] = gExitList_HouseInteriors4_RanchHouseEast,
    [ROOM_HOUSE_INTERIORS_4_FARM_HOUSE] = gExitList_HouseInteriors4_FarmHouse,
    [ROOM_HOUSE_INTERIORS_4_MAYOR_LAKE_CABIN] = gExitList_HouseInteriors4_MayorLakeCabin,
    [ROOM_HOUSE_INTERIORS_4_6] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_4_7] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_4_8] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_4_9] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_4_a] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_4_b] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_4_c] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_4_d] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_4_e] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_4_f] = gExitList_NoExitList,
};

const Transition gExitList_GreatFairies_Graveyard[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x198, 0x2b8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_ROYAL_VALLEY, ROOM_ROYAL_VALLEY_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#ifdef QUICKSTART
// Retargeted - see the "? room" pool comment above gExitList_MinishHouseInteriors_Red.
const Transition gExitList_GreatFairies_MinishWoods[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x68, 0x90, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_GreatFairies_MinishWoods[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x78, 0x58, TRANSITION_SHAPE_BORDER_SOUTH, AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_MINISH_WOODS_GREAT_FAIRY,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition gExitList_GreatFairies_MtCrenel[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x148, 0x1f8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_WALL_CLIMB, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_GreatFairies[] = {
    [ROOM_GREAT_FAIRIES_GRAVEYARD] = gExitList_GreatFairies_Graveyard,
    [ROOM_GREAT_FAIRIES_MINISH_WOODS] = gExitList_GreatFairies_MinishWoods,
    [ROOM_GREAT_FAIRIES_CRENEL] = gExitList_GreatFairies_MtCrenel,
    [ROOM_GREAT_FAIRIES_NOT_IMPLEMENTED] = gExitList_NoExitList,
};

#ifdef QUICKSTART
// Stockwell's shop, vanilla's own general store, is QUICKSTART's shop room
// now (game.c: QuickStartSetupShopRoom). It was picked against the user's
// own three constraints: currently unused by this mode, and - the part that
// actually matters - its single vanilla connection is to Hyrule Town, which
// is NOT one of the overworld regions in this run's pool. So nothing the
// player can already reach opens onto it, and it can be attached to
// whichever overworld door the save's own draw picks without colliding with
// a real connection.
//
// The destination here is a placeholder. Which door the shop hangs off
// varies per save, so the real return leg is written at transition time by
// QuickStartFixupShopReturn (game.c), the same way every other
// per-save-variable return in this file is handled. North Hyrule Field is
// used as the placeholder rather than Hyrule Town purely so a missed fixup
// lands inside the run instead of escaping it.
const Transition gExitList_HouseInteriors3_StockwellShop[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1f8, 0x1f8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD,
      ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_HouseInteriors3_StockwellShop[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x258, 0x2fc, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition gExitList_HouseInteriors3_Cafe[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x198, 0x2fc, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors3_RemShoeShop[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x188, 0x210, TRANSITION_SHAPE_BORDER_EAST, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x2, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors3_Bakery[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x268, 0x1f0, TRANSITION_SHAPE_BORDER_WEST, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x6, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors3_Simon[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x188, 0x250, TRANSITION_SHAPE_BORDER_EAST, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x2, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors3_FigurineHouse[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x188, 0x290, TRANSITION_SHAPE_BORDER_EAST, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x2, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x128, 0x290, TRANSITION_SHAPE_BORDER_WEST, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x6, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors3_BorlovEntrance[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x298, 0x26c, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xb8, 0x78, TRANSITION_SHAPE_BORDER_NORTH, AREA_HOUSE_INTERIORS_3, ROOM_HOUSE_INTERIORS_3_BORLOV,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors3_Carlov[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x78, 0x60, TRANSITION_SHAPE_BORDER_SOUTH, AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_STAIRS_TO_CARLOV,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors3_Borlov[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x78, 0x68, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HOUSE_INTERIORS_3, ROOM_HOUSE_INTERIORS_3_BORLOV_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_HouseInteriors3[] = {
    [ROOM_HOUSE_INTERIORS_3_STOCKWELL_SHOP] = gExitList_HouseInteriors3_StockwellShop,
    [ROOM_HOUSE_INTERIORS_3_CAFE] = gExitList_HouseInteriors3_Cafe,
    [ROOM_HOUSE_INTERIORS_3_REM_SHOE_SHOP] = gExitList_HouseInteriors3_RemShoeShop,
    [ROOM_HOUSE_INTERIORS_3_BAKERY] = gExitList_HouseInteriors3_Bakery,
    [ROOM_HOUSE_INTERIORS_3_SIMON] = gExitList_HouseInteriors3_Simon,
    [ROOM_HOUSE_INTERIORS_3_FIGURINE_HOUSE] = gExitList_HouseInteriors3_FigurineHouse,
    [ROOM_HOUSE_INTERIORS_3_BORLOV_ENTRANCE] = gExitList_HouseInteriors3_BorlovEntrance,
    [ROOM_HOUSE_INTERIORS_3_CARLOV] = gExitList_HouseInteriors3_Carlov,
    [ROOM_HOUSE_INTERIORS_3_BORLOV] = gExitList_HouseInteriors3_Borlov,
    [ROOM_HOUSE_INTERIORS_3_9] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_3_a] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_3_b] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_3_c] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_3_d] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_3_e] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_3_f] = gExitList_NoExitList,
};

const Transition gExitList_HouseInteriors1_Mayor[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x2c8, 0x14c, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x318, 0x120, TRANSITION_SHAPE_BORDER_EAST, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x2, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors1_PostOffice[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x48, 0xb8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#ifdef QUICKSTART
// Retargeted as a QUICKSTART "2-door ? room" pool candidate - both
// real doors now lead back to the Lon Lon Ranch cave-connector ledge
// (0xb8,0x138), same shared return spot every other 2-door pool room
// uses (see game.c: sQuickStart2DoorSmallRoomPool/LargeRoomPool). Real
// startX/startY/shape/warp_type kept as-is - only destination changes.
const Transition gExitList_HouseInteriors1_Library2F[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3fe, 0x3fe, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 2, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x78, 0x18, 0x3fd, 0x3fd, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_HouseInteriors1_Library2F[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x138, 0x58, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 2, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x78, 0x18, 0x68, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_1, ROOM_HOUSE_INTERIORS_1_LIBRARY_1F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
#ifdef QUICKSTART
// Retargeted as a QUICKSTART "2-door ? room" pool candidate - both
// real doors now lead back to the Lon Lon Ranch cave-connector ledge
// (0xb8,0x138), same shared return spot every other 2-door pool room
// uses (see game.c: sQuickStart2DoorSmallRoomPool/LargeRoomPool). Real
// startX/startY/shape/warp_type kept as-is - only destination changes.
const Transition gExitList_HouseInteriors1_Library1F[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3fe, 0x3fe, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x68, 0x18, 0x3fd, 0x3fd, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_HouseInteriors1_Library1F[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x168, 0xb8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x68, 0x18, 0x78, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_1, ROOM_HOUSE_INTERIORS_1_LIBRARY_2F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition gExitList_HouseInteriors1_Inn1F[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x388, 0x268, TRANSITION_SHAPE_BORDER_SOUTH_WEST, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x78, 0x18, 0x98, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_1, ROOM_HOUSE_INTERIORS_1_INN_WEST_ROOM,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xb8, 0x18, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_1, ROOM_HOUSE_INTERIORS_1_INN_MIDDLE_ROOM,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xf8, 0x18, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_1, ROOM_HOUSE_INTERIORS_1_INN_EAST_ROOM,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x118, 0x38, 0xb8, 0x168, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_1, ROOM_HOUSE_INTERIORS_1_INN_EAST_2F,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors1_InnWestRoom[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x78, 0x28, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HOUSE_INTERIORS_1, ROOM_HOUSE_INTERIORS_1_INN_1F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors1_InnMiddleRoom[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xb8, 0x28, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HOUSE_INTERIORS_1, ROOM_HOUSE_INTERIORS_1_INN_1F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors1_InnEastRoom[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xf8, 0x28, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HOUSE_INTERIORS_1, ROOM_HOUSE_INTERIORS_1_INN_1F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HouseInteriors1_InnWest2F[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x368, 0x1c8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#ifdef QUICKSTART
// Retargeted as a QUICKSTART "2-door ? room" pool candidate - both
// real doors now lead back to the Lon Lon Ranch cave-connector ledge
// (0xb8,0x138), same shared return spot every other 2-door pool room
// uses (see game.c: sQuickStart2DoorSmallRoomPool/LargeRoomPool). Real
// startX/startY/shape/warp_type kept as-is - only destination changes.
const Transition gExitList_HouseInteriors1_InnEast2F[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3fe, 0x3fe, TRANSITION_SHAPE_BORDER_SOUTH_WEST, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 2, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xb8, 0x178, 0x3fd, 0x3fd, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_HouseInteriors1_InnEast2F[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3a8, 0x230, TRANSITION_SHAPE_BORDER_SOUTH_WEST, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 2, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xb8, 0x178, 0x118, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_1, ROOM_HOUSE_INTERIORS_1_INN_1F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
#ifdef QUICKSTART
// Retargeted as a QUICKSTART "2-door ? room" pool candidate - both
// real doors now lead back to the Lon Lon Ranch cave-connector ledge
// (0xb8,0x138), same shared return spot every other 2-door pool room
// uses (see game.c: sQuickStart2DoorSmallRoomPool/LargeRoomPool). Real
// startX/startY/shape/warp_type kept as-is - only destination changes.
const Transition gExitList_HouseInteriors1_SchoolWest[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3fe, 0x3fe, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x78, 0x48, 0x3fd, 0x3fd, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_HouseInteriors1_SchoolWest[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x2c8, 0xa8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x78, 0x48, 0x168, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_TOWN_UNDERGROUND, ROOM_HYRULE_TOWN_UNDERGROUND_0,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition gExitList_HouseInteriors1_SchoolEast[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x328, 0x78, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_HouseInteriors1[] = {
    [ROOM_HOUSE_INTERIORS_1_MAYOR] = gExitList_HouseInteriors1_Mayor,
    [ROOM_HOUSE_INTERIORS_1_POST_OFFICE] = gExitList_HouseInteriors1_PostOffice,
    [ROOM_HOUSE_INTERIORS_1_LIBRARY_2F] = gExitList_HouseInteriors1_Library2F,
    [ROOM_HOUSE_INTERIORS_1_LIBRARY_1F] = gExitList_HouseInteriors1_Library1F,
    [ROOM_HOUSE_INTERIORS_1_INN_1F] = gExitList_HouseInteriors1_Inn1F,
    [ROOM_HOUSE_INTERIORS_1_INN_WEST_ROOM] = gExitList_HouseInteriors1_InnWestRoom,
    [ROOM_HOUSE_INTERIORS_1_INN_MIDDLE_ROOM] = gExitList_HouseInteriors1_InnMiddleRoom,
    [ROOM_HOUSE_INTERIORS_1_INN_EAST_ROOM] = gExitList_HouseInteriors1_InnEastRoom,
    [ROOM_HOUSE_INTERIORS_1_INN_WEST_2F] = gExitList_HouseInteriors1_InnWest2F,
    [ROOM_HOUSE_INTERIORS_1_INN_EAST_2F] = gExitList_HouseInteriors1_InnEast2F,
    [ROOM_HOUSE_INTERIORS_1_INN_MINISH_HEART_PIECE] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_1_SCHOOL_WEST] = gExitList_HouseInteriors1_SchoolWest,
    [ROOM_HOUSE_INTERIORS_1_SCHOOL_EAST] = gExitList_HouseInteriors1_SchoolEast,
    [ROOM_HOUSE_INTERIORS_1_d] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_1_e] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_1_f] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_1_10] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_1_11] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_1_12] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_1_13] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_1_14] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_1_15] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_1_16] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_1_17] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_1_18] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_1_19] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_1_1a] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_1_1b] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_1_1c] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_1_1d] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_1_1e] = gExitList_NoExitList,
    [ROOM_HOUSE_INTERIORS_1_1f] = gExitList_NoExitList,
};

const Transition gExitList_TreeInteriors_WitchHut[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x2c0, 0x58, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MINISH_WOODS, ROOM_MINISH_WOODS_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TreeInteriors_StairsToCarlov[] = {
    { WARP_TYPE_AREA, 0x78, 0x48, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_3, ROOM_HOUSE_INTERIORS_3_CARLOV,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x50, 0x388, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TreeInteriors_PercysTreehouse[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x40, 0x398, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
// PILOT: no longer retargeted. This room is now a ? room in place, reached
// through South Hyrule Field's own real tree door, so its real vanilla exit
// back to South Hyrule Field is exactly what's wanted - identical in both
// builds now.
const Transition gExitList_TreeInteriors_HeartPiece[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3a0, 0x238, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TreeInteriors_Waveblade[] = {
    { WARP_TYPE_AREA, 0x78, 0x48, 0x78, 0x98, TRANSITION_SHAPE_AREA_12x12, AREA_DOJOS, ROOM_DOJOS_WAVEBLADE, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0,
      0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x100, 0x2c8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_LAKE_HYLIA, ROOM_LAKE_HYLIA_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#ifdef QUICKSTART
// Retargeted (this room is otherwise never reached as a destination by any
// real transition - see game.c's Castle Garden hidden-ladder feature) so
// its one real exit returns to Castle Garden Main, landing south of ladder
// 0's own pot spot (104,104 - one of the garden's own real, pre-existing
// HIDDEN_LADDER_DOWN fixtures, per game.c) and clear of that ladder's
// trigger box (game.c, QuickStartProcessLadderLinks: +/-16px around the
// pot) so arriving here doesn't immediately re-trigger the ladder.
const Transition gExitList_TreeInteriors_14[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x68, 0x90, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_TreeInteriors_14[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x210, 0x1d8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MINISH_WOODS, ROOM_MINISH_WOODS_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition gExitList_TreeInteriors_BoomerangNorthwest[] = {
    { WARP_TYPE_AREA, 0x78, 0x54, 0x48, 0x88, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_BOOMERANG, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0,
      0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1b0, 0x138, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TreeInteriors_BoomerangNortheast[] = {
    { WARP_TYPE_AREA, 0x78, 0x54, 0x108, 0x88, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_BOOMERANG, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x240, 0x138, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TreeInteriors_BoomerangSouthwest[] = {
    { WARP_TYPE_AREA, 0x78, 0x54, 0x48, 0xf8, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_BOOMERANG, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0,
      0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1b0, 0x198, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TreeInteriors_BoomerangSoutheast[] = {
    { WARP_TYPE_AREA, 0x78, 0x54, 0x108, 0xf8, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_BOOMERANG, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x240, 0x198, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
// Back on its real vanilla exit (WW-North) - third room of the same fix
// as the two Minish houses above: promoted to a walk-in content site (the
// Western Wood heart-piece tree door) but still carrying its pool-era
// retarget to Castle Garden's shared ladder landing.
const Transition gExitList_TreeInteriors_WesternWoodsHeartPiece[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xa0, 0x1f8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_WESTERN_WOODS_NORTH,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TreeInteriors_NorthHyruleFieldFairyFountain[] = {
    { WARP_TYPE_AREA, 0x78, 0x48, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_NORTH_HYRULE_FIELD_FAIRY_FOUNTAIN,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x2f0, 0x148, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TreeInteriors_MinishWoodsGreatFairy[] = {
    { WARP_TYPE_AREA, 0x78, 0x48, 0x78, 0xf8, TRANSITION_SHAPE_AREA_12x12, AREA_GREAT_FAIRIES, ROOM_GREAT_FAIRIES_MINISH_WOODS,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x70, 0x58, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MINISH_WOODS, ROOM_MINISH_WOODS_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#ifdef QUICKSTART
// Retargeted the same way as gExitList_TreeInteriors_14 above, for ladder 1
// (pot at 936,376 - the garden's other real HIDDEN_LADDER_DOWN fixture) -
// landing south of it, clear of its own trigger box.
const Transition gExitList_TreeInteriors_1C[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3a8, 0x1a0, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_TreeInteriors_1C[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x50, 0x298, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition gExitList_TreeInteriors_MinishWoodsBusinessScrub[] = {
    { WARP_TYPE_AREA, 0x78, 0x48, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_KINSTONE_BUSINESS_SCRUB, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x210, 0x1d8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MINISH_WOODS, ROOM_MINISH_WOODS_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TreeInteriors_1E[] = {
    TransitionListEnd,
};
#ifdef QUICKSTART
// Retargeted the same way as gExitList_TreeInteriors_14 above, for ladder 2
// (bush at 650,310) - landing south of it, clear of its own trigger box.
const Transition gExitList_TreeInteriors_UnusedHeartContainer[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x28a, 0x15e, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_TreeInteriors_UnusedHeartContainer[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1e0, 0x1b8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_LAKE_HYLIA, ROOM_LAKE_HYLIA_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition* const gExitLists_TreeInteriors[] = {
    [ROOM_TREE_INTERIORS_WITCH_HUT] = gExitList_TreeInteriors_WitchHut,
    [ROOM_TREE_INTERIORS_1] = gExitList_NoExitList,
    [ROOM_TREE_INTERIORS_2] = gExitList_NoExitList,
    [ROOM_TREE_INTERIORS_3] = gExitList_NoExitList,
    [ROOM_TREE_INTERIORS_4] = gExitList_NoExitList,
    [ROOM_TREE_INTERIORS_5] = gExitList_NoExitList,
    [ROOM_TREE_INTERIORS_6] = gExitList_NoExitList,
    [ROOM_TREE_INTERIORS_7] = gExitList_NoExitList,
    [ROOM_TREE_INTERIORS_8] = gExitList_NoExitList,
    [ROOM_TREE_INTERIORS_9] = gExitList_NoExitList,
    [ROOM_TREE_INTERIORS_a] = gExitList_NoExitList,
    [ROOM_TREE_INTERIORS_b] = gExitList_NoExitList,
    [ROOM_TREE_INTERIORS_c] = gExitList_NoExitList,
    [ROOM_TREE_INTERIORS_d] = gExitList_NoExitList,
    [ROOM_TREE_INTERIORS_e] = gExitList_NoExitList,
    [ROOM_TREE_INTERIORS_f] = gExitList_NoExitList,
    [ROOM_TREE_INTERIORS_STAIRS_TO_CARLOV] = gExitList_TreeInteriors_StairsToCarlov,
    [ROOM_TREE_INTERIORS_PERCYS_TREEHOUSE] = gExitList_TreeInteriors_PercysTreehouse,
    [ROOM_TREE_INTERIORS_SOUTH_HYRULE_FIELD_HEART_PIECE] = gExitList_TreeInteriors_HeartPiece,
    [ROOM_TREE_INTERIORS_WAVEBLADE] = gExitList_TreeInteriors_Waveblade,
    [ROOM_TREE_INTERIORS_14] = gExitList_TreeInteriors_14,
    [ROOM_TREE_INTERIORS_BOOMERANG_NORTHWEST] = gExitList_TreeInteriors_BoomerangNorthwest,
    [ROOM_TREE_INTERIORS_BOOMERANG_NORTHEAST] = gExitList_TreeInteriors_BoomerangNortheast,
    [ROOM_TREE_INTERIORS_BOOMERANG_SOUTHWEST] = gExitList_TreeInteriors_BoomerangSouthwest,
    [ROOM_TREE_INTERIORS_BOOMERANG_SOUTHEAST] = gExitList_TreeInteriors_BoomerangSoutheast,
    [ROOM_TREE_INTERIORS_WESTERN_WOODS_HEART_PIECE] = gExitList_TreeInteriors_WesternWoodsHeartPiece,
    [ROOM_TREE_INTERIORS_NORTH_HYRULE_FIELD_FAIRY_FOUNTAIN] = gExitList_TreeInteriors_NorthHyruleFieldFairyFountain,
    [ROOM_TREE_INTERIORS_MINISH_WOODS_GREAT_FAIRY] = gExitList_TreeInteriors_MinishWoodsGreatFairy,
    [ROOM_TREE_INTERIORS_1c] = gExitList_TreeInteriors_1C,
    [ROOM_TREE_INTERIORS_MINISH_WOODS_BUSINESS_SCRUB] = gExitList_TreeInteriors_MinishWoodsBusinessScrub,
    [ROOM_TREE_INTERIORS_1e] = gExitList_TreeInteriors_1E,
    [ROOM_TREE_INTERIORS_UNUSED_HEART_CONTAINER] = gExitList_TreeInteriors_UnusedHeartContainer,
};

#ifdef QUICKSTART
// Retargeted - see the "? room" pool comment above gExitList_MinishHouseInteriors_Red.
const Transition gExitList_Dojos_Grayblade[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x68, 0x90, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_Dojos_Grayblade[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x78, 0x20, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_TO_GRAYBLADE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
#ifdef QUICKSTART
const Transition gExitList_Dojos_Swiftblade[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x68, 0x90, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_Dojos_Swiftblade[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x38, 0x2e8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTOR_WILDS, ROOM_CASTOR_WILDS_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
#ifdef QUICKSTART
const Transition gExitList_Dojos_Waveblade[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x68, 0x90, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_Dojos_Waveblade[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x78, 0x58, TRANSITION_SHAPE_BORDER_SOUTH, AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_WAVEBLADE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition gExitList_Dojos_ToGrimblade[] = {
    { WARP_TYPE_AREA, 0x78, 0x48, 0x3a8, 0x168, TRANSITION_SHAPE_AREA_12x12, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Dojos_ToSplitblade[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xf8, 0x358, TRANSITION_SHAPE_BORDER_SOUTH, AREA_VEIL_FALLS, ROOM_VEIL_FALLS_MAIN, 1, TRANSITION_TYPE_NORMAL, 0x4,
      0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Dojos_ToGreatblade[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xc8, 0x1f8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Dojos_ToScarblade[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x398, 0x48, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTOR_WILDS, ROOM_CASTOR_WILDS_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_Dojos[] = {
    [ROOM_DOJOS_GRAYBLADE] = gExitList_Dojos_Grayblade,
    [ROOM_DOJOS_SPLITBLADE] = gExitList_NoExitList,
    [ROOM_DOJOS_GREATBLADE] = gExitList_NoExitList,
    [ROOM_DOJOS_SCARBLADE] = gExitList_NoExitList,
    [ROOM_DOJOS_SWIFTBLADE_I] = gExitList_Dojos_Swiftblade,
    [ROOM_DOJOS_GRIMBLADE] = gExitList_NoExitList,
    [ROOM_DOJOS_WAVEBLADE] = gExitList_Dojos_Waveblade,
    [ROOM_DOJOS_7] = gExitList_NoExitList,
    [ROOM_DOJOS_8] = gExitList_NoExitList,
    [ROOM_DOJOS_9] = gExitList_NoExitList,
    [ROOM_DOJOS_TO_GRIMBLADE] = gExitList_Dojos_ToGrimblade,
    [ROOM_DOJOS_TO_SPLITBLADE] = gExitList_Dojos_ToSplitblade,
    [ROOM_DOJOS_TO_GREATBLADE] = gExitList_Dojos_ToGreatblade,
    [ROOM_DOJOS_TO_SCARBLADE] = gExitList_Dojos_ToScarblade,
    [ROOM_DOJOS_e] = gExitList_NoExitList,
    [ROOM_DOJOS_f] = gExitList_NoExitList,
};

const Transition gExitList_MinishCracks_LonLonRanchNorth[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x232, 0x18, TRANSITION_SHAPE_BORDER_NORTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x6, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishCracks_LakeHyliaEast[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x2d8, 0x114, TRANSITION_SHAPE_BORDER_NORTH, AREA_LAKE_HYLIA, ROOM_LAKE_HYLIA_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH, 0x4,
      0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishCracks_HyruleCastleGarden[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3a8, 0x40, TRANSITION_SHAPE_BORDER_NORTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishCracks_MtCrenel[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x158, 0x54, TRANSITION_SHAPE_BORDER_NORTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_ENTRANCE, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x2, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishCracks_EastHyruleCastle[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3c8, 0x184, TRANSITION_SHAPE_BORDER_NORTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishCracks_5[] = {
    TransitionListEnd,
};
const Transition gExitList_MinishCracks_CastorWildsBow[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x28, 0x54, TRANSITION_SHAPE_BORDER_NORTH, AREA_CASTOR_WILDS, ROOM_CASTOR_WILDS_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishCracks_RuinsEntrance[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x48, 0x17c, TRANSITION_SHAPE_BORDER_NORTH, AREA_RUINS, ROOM_RUINS_ENTRANCE, 1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0,
      0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishCracks_MinishWoodsSouth[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x218, 0x3c4, TRANSITION_SHAPE_BORDER_NORTH, AREA_MINISH_WOODS, ROOM_MINISH_WOODS_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishCracks_CastorWildsNorth[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xc8, 0x44, TRANSITION_SHAPE_BORDER_NORTH, AREA_CASTOR_WILDS, ROOM_CASTOR_WILDS_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishCracks_CastorWildsWest[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x38, 0x134, TRANSITION_SHAPE_BORDER_NORTH, AREA_CASTOR_WILDS, ROOM_CASTOR_WILDS_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishCracks_CastorWildsMiddle[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x168, 0x2d4, TRANSITION_SHAPE_BORDER_NORTH, AREA_CASTOR_WILDS, ROOM_CASTOR_WILDS_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishCracks_RuinsTektite[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xc8, 0x54, TRANSITION_SHAPE_BORDER_NORTH, AREA_RUINS, ROOM_RUINS_TEKTITES, 1, TRANSITION_TYPE_INSTANT_MINISH, 0x0, 0x0,
      0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishCracks_CastorWildsNextToBow[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x18, 0x54, TRANSITION_SHAPE_BORDER_NORTH, AREA_CASTOR_WILDS, ROOM_CASTOR_WILDS_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishCracks_11[] = {
    TransitionListEnd,
};
const Transition* const gExitLists_MinishCracks[] = {
    [ROOM_MINISH_CRACKS_LON_LON_RANCH_NORTH] = gExitList_MinishCracks_LonLonRanchNorth,
    [ROOM_MINISH_CRACKS_LAKE_HYLIA_EAST] = gExitList_MinishCracks_LakeHyliaEast,
    [ROOM_MINISH_CRACKS_HYRULE_CASTLE_GARDEN] = gExitList_MinishCracks_HyruleCastleGarden,
    [ROOM_MINISH_CRACKS_MT_CRENEL] = gExitList_MinishCracks_MtCrenel,
    [ROOM_MINISH_CRACKS_EAST_HYRULE_CASTLE] = gExitList_MinishCracks_EastHyruleCastle,
    [ROOM_MINISH_CRACKS_5] = gExitList_MinishCracks_5,
    [ROOM_MINISH_CRACKS_CASTOR_WILDS_BOW] = gExitList_MinishCracks_CastorWildsBow,
    [ROOM_MINISH_CRACKS_RUINS_ENTRANCE] = gExitList_MinishCracks_RuinsEntrance,
    [ROOM_MINISH_CRACKS_MINISH_WOODS_SOUTH] = gExitList_MinishCracks_MinishWoodsSouth,
    [ROOM_MINISH_CRACKS_CASTOR_WILDS_NORTH] = gExitList_MinishCracks_CastorWildsNorth,
    [ROOM_MINISH_CRACKS_CASTOR_WILDS_WEST] = gExitList_MinishCracks_CastorWildsWest,
    [ROOM_MINISH_CRACKS_CASTOR_WILDS_MIDDLE] = gExitList_MinishCracks_CastorWildsMiddle,
    [ROOM_MINISH_CRACKS_RUINS_TEKTITE] = gExitList_MinishCracks_RuinsTektite,
    [ROOM_MINISH_CRACKS_CASTOR_WILDS_NEXT_TO_BOW] = gExitList_MinishCracks_CastorWildsNextToBow,
    [ROOM_MINISH_CRACKS_e] = gExitList_NoExitList,
    [ROOM_MINISH_CRACKS_f] = gExitList_NoExitList,
    [ROOM_MINISH_CRACKS_10] = gExitList_NoExitList,
    [ROOM_MINISH_CRACKS_11] = gExitList_MinishCracks_11,
    [ROOM_MINISH_CRACKS_12] = gExitList_NoExitList,
    [ROOM_MINISH_CRACKS_13] = gExitList_NoExitList,
    [ROOM_MINISH_CRACKS_14] = gExitList_NoExitList,
    [ROOM_MINISH_CRACKS_15] = gExitList_NoExitList,
    [ROOM_MINISH_CRACKS_16] = gExitList_NoExitList,
    [ROOM_MINISH_CRACKS_17] = gExitList_NoExitList,
};

const Transition gExitList_CrenelCaves_BlockPushing[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x328, 0x18, TRANSITION_SHAPE_BORDER_NORTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_TOP, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x128, 0x28, TRANSITION_SHAPE_BORDER_SOUTH_WEST, AREA_MT_CRENEL, ROOM_MT_CRENEL_CAVERN_OF_FLAMES_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x208, 0x28, TRANSITION_SHAPE_BORDER_SOUTH_EAST, AREA_MT_CRENEL, ROOM_MT_CRENEL_CAVERN_OF_FLAMES_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x238, 0xb8, 0x38, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_BRIDGE_SWITCH,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_CrenelCaves_PillarCave[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1d8, 0xc8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_CAVERN_OF_FLAMES_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x38, 0x28, 0xb8, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_EXIT_TO_MINES,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#ifdef QUICKSTART
// Retargeted as a QUICKSTART "2-door ? room" pool candidate - both
// real doors now lead back to the Lon Lon Ranch cave-connector ledge
// (0xb8,0x138), same shared return spot every other 2-door pool room
// uses (see game.c: sQuickStart2DoorSmallRoomPool/LargeRoomPool). Real
// startX/startY/shape/warp_type kept as-is - only destination changes.
const Transition gExitList_CrenelCaves_BridgeSwitch[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3fe, 0x3fe, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x38, 0x28, 0x3fd, 0x3fd, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_CrenelCaves_BridgeSwitch[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x238, 0xc8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_CAVERN_OF_FLAMES_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x38, 0x28, 0x238, 0xc8, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_BLOCK_PUSHING,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition gExitList_CrenelCaves_ExitToMines[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x188, 0x108, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_CAVERN_OF_FLAMES_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xb8, 0x38, 0x38, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_PILLAR_CAVE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_CrenelCaves_GripRing[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1e8, 0x1e8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_CAVERN_OF_FLAMES_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_CrenelCaves_FairyFountain[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xa8, 0x58, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_CENTER, 1, TRANSITION_TYPE_NORMAL, 0x4,
      0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_CrenelCaves_SpinyChuPuzzle[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x2f8, 0x38, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_CENTER, 1, TRANSITION_TYPE_NORMAL, 0x4,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xb8, 0x38, 0x38, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_CHUCHU_POT_CHEST,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#ifdef QUICKSTART
// Retargeted as a QUICKSTART "2-door ? room" pool candidate - both
// real doors now lead back to the Lon Lon Ranch cave-connector ledge
// (0xb8,0x138), same shared return spot every other 2-door pool room
// uses (see game.c: sQuickStart2DoorSmallRoomPool/LargeRoomPool). Real
// startX/startY/shape/warp_type kept as-is - only destination changes.
const Transition gExitList_CrenelCaves_ChuchuPotChest[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3fe, 0x3fe, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x38, 0x28, 0x3fd, 0x3fd, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_CrenelCaves_ChuchuPotChest[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x348, 0x68, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_CENTER, 1, TRANSITION_TYPE_NORMAL, 0x4,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x38, 0x28, 0xb8, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_SPINY_CHU_PUZZLE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition gExitList_CrenelCaves_WaterHeartPiece[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x38, 0x118, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_CENTER, 1, TRANSITION_TYPE_NORMAL, 0x4,
      0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_CrenelCaves_RupeeFairyFountain[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x298, 0x38, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_ENTRANCE, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#ifdef QUICKSTART
// Retargeted as a QUICKSTART "2-door ? room" pool candidate - both
// real doors now lead back to the Lon Lon Ranch cave-connector ledge
// (0xb8,0x138), same shared return spot every other 2-door pool room
// uses (see game.c: sQuickStart2DoorSmallRoomPool/LargeRoomPool). Real
// startX/startY/shape/warp_type kept as-is - only destination changes.
const Transition gExitList_CrenelCaves_HelmasaurHallway[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3fe, 0x3fe, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x68, 0x18, 0x3fd, 0x3fd, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_CrenelCaves_HelmasaurHallway[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x198, 0xe8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_ENTRANCE, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x68, 0x18, 0xb8, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_MUSHROOM_KEESE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition gExitList_CrenelCaves_MushroomKeese[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x138, 0x148, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_ENTRANCE, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xb8, 0x38, 0x68, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_CRENEL_CAVES, ROOM_CRENEL_CAVES_HELMASAUR_HALLWAY,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#ifdef QUICKSTART
// Retargeted as a QUICKSTART "2-door ? room" pool candidate - both
// real doors now lead back to the Lon Lon Ranch cave-connector ledge
// (0xb8,0x138), same shared return spot every other 2-door pool room
// uses (see game.c: sQuickStart2DoorSmallRoomPool/LargeRoomPool). Real
// startX/startY/shape/warp_type kept as-is - only destination changes.
const Transition gExitList_CrenelCaves_LadderToSpringWater[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3fe, 0x3fe, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3fd, 0x3fd, TRANSITION_SHAPE_BORDER_NORTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_CrenelCaves_LadderToSpringWater[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x2d8, 0x198, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_ENTRANCE, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x2d8, 0x138, TRANSITION_SHAPE_BORDER_NORTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_ENTRANCE, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition gExitList_CrenelCaves_BombBusinessScrub[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xb8, 0x1a8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_ENTRANCE, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_CrenelCaves_Hermit[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xa8, 0x68, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_WALL_CLIMB, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_CrenelCaves_HintScrub[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3b8, 0x178, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_ENTRANCE, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_CrenelCaves_ToGrayblade[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x78, 0xa0, TRANSITION_SHAPE_BORDER_NORTH, AREA_DOJOS, ROOM_DOJOS_GRAYBLADE, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0,
      0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x208, 0x158, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_CAVERN_OF_FLAMES_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_CrenelCaves[] = {
    [ROOM_CRENEL_CAVES_BLOCK_PUSHING] = gExitList_CrenelCaves_BlockPushing,
    [ROOM_CRENEL_CAVES_PILLAR_CAVE] = gExitList_CrenelCaves_PillarCave,
    [ROOM_CRENEL_CAVES_BRIDGE_SWITCH] = gExitList_CrenelCaves_BridgeSwitch,
    [ROOM_CRENEL_CAVES_EXIT_TO_MINES] = gExitList_CrenelCaves_ExitToMines,
    [ROOM_CRENEL_CAVES_GRIP_RING] = gExitList_CrenelCaves_GripRing,
    [ROOM_CRENEL_CAVES_FAIRY_FOUNTAIN] = gExitList_CrenelCaves_FairyFountain,
    [ROOM_CRENEL_CAVES_SPINY_CHU_PUZZLE] = gExitList_CrenelCaves_SpinyChuPuzzle,
    [ROOM_CRENEL_CAVES_CHUCHU_POT_CHEST] = gExitList_CrenelCaves_ChuchuPotChest,
    [ROOM_CRENEL_CAVES_WATER_HEART_PIECE] = gExitList_CrenelCaves_WaterHeartPiece,
    [ROOM_CRENEL_CAVES_RUPEE_FAIRY_FOUINTAIN] = gExitList_CrenelCaves_RupeeFairyFountain,
    [ROOM_CRENEL_CAVES_HELMASAUR_HALLWAY] = gExitList_CrenelCaves_HelmasaurHallway,
    [ROOM_CRENEL_CAVES_MUSHROOM_KEESE] = gExitList_CrenelCaves_MushroomKeese,
    [ROOM_CRENEL_CAVES_LADDER_TO_SPRING_WATER] = gExitList_CrenelCaves_LadderToSpringWater,
    [ROOM_CRENEL_CAVES_BOMB_BUSINESS_SCRUB] = gExitList_CrenelCaves_BombBusinessScrub,
    [ROOM_CRENEL_CAVES_HERMIT] = gExitList_CrenelCaves_Hermit,
    [ROOM_CRENEL_CAVES_HINT_SCRUB] = gExitList_CrenelCaves_HintScrub,
    [ROOM_CRENEL_CAVES_TO_GRAYBLADE] = gExitList_CrenelCaves_ToGrayblade,
};

const Transition gExitList_CastorCaves_South[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x2d8, 0x398, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTOR_WILDS, ROOM_CASTOR_WILDS_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_CastorCaves_North[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x248, 0x48, TRANSITION_SHAPE_BORDER_SOUTH_WEST, AREA_CASTOR_WILDS, ROOM_CASTOR_WILDS_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x288, 0x48, TRANSITION_SHAPE_BORDER_SOUTH_EAST, AREA_CASTOR_WILDS, ROOM_CASTOR_WILDS_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_CastorCaves_WindRuins[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xc8, 0x48, TRANSITION_SHAPE_BORDER_SOUTH, AREA_RUINS, ROOM_RUINS_ENTRANCE, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0,
      0x0, 0x0 },
    TransitionListEnd,
};
#ifdef QUICKSTART
// Retargeted as a QUICKSTART "2-door ? room" pool candidate - both
// real doors now lead back to the Lon Lon Ranch cave-connector ledge
// (0xb8,0x138), same shared return spot every other 2-door pool room
// uses (see game.c: sQuickStart2DoorSmallRoomPool/LargeRoomPool). Real
// startX/startY/shape/warp_type kept as-is - only destination changes.
const Transition gExitList_CastorCaves_Darknut[] = {
    { WARP_TYPE_AREA, 0x68, 0x18, 0x3fe, 0x3fe, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3fd, 0x3fd, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_CastorCaves_Darknut[] = {
    { WARP_TYPE_AREA, 0x68, 0x18, 0x188, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_CASTOR_DARKNUT, ROOM_CASTOR_DARKNUT_HALL, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1a8, 0x1b8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTOR_WILDS, ROOM_CASTOR_WILDS_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition gExitList_CastorCaves_HeartPiece[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3c8, 0x48, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTOR_WILDS, ROOM_CASTOR_WILDS_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_CastorCaves[] = {
    [ROOM_CASTOR_CAVES_SOUTH] = gExitList_CastorCaves_South,
    [ROOM_CASTOR_CAVES_NORTH] = gExitList_CastorCaves_North,
    [ROOM_CASTOR_CAVES_WIND_RUINS] = gExitList_CastorCaves_WindRuins,
    [ROOM_CASTOR_CAVES_DARKNUT] = gExitList_CastorCaves_Darknut,
    [ROOM_CASTOR_CAVES_HEART_PIECE] = gExitList_CastorCaves_HeartPiece,
    [ROOM_CASTOR_CAVES_5] = gExitList_NoExitList,
    [ROOM_CASTOR_CAVES_6] = gExitList_NoExitList,
    [ROOM_CASTOR_CAVES_7] = gExitList_NoExitList,
};

const Transition gExitList_CastorDarknut_Main[] = {
    TransitionListEnd,
};
const Transition gExitList_CastorDarknut_Hall[] = {
#ifdef QUICKSTART
    // Retargeted to Melari's Mine (game.c's own custom link's destination
    // for this same box) instead of the old Castor Caves - same race
    // concern as the Melari's Mine side of this pair (see
    // gExitList_MelarisMine_Main above): this real door's position is the
    // exact spot that custom link covers. Spawn (120,120) - see that link's
    // own comment (game.c, sQuickStartLinks) for why this is further from
    // the door than it first looks: a passive drift near the door pulls the
    // player back into the return trigger box from anywhere closer.
    { WARP_TYPE_AREA, 0x188, 0x18, 0x78, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_MELARIS_MINE, ROOM_MELARIS_MINE_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
#else
    { WARP_TYPE_AREA, 0x188, 0x18, 0x68, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_CASTOR_CAVES, ROOM_CASTOR_CAVES_DARKNUT, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
#endif
    TransitionListEnd,
};
const Transition* const gExitLists_CastorDarknut[] = {
    [ROOM_CASTOR_DARKNUT_MAIN] = gExitList_CastorDarknut_Main,
    [ROOM_CASTOR_DARKNUT_HALL] = gExitList_CastorDarknut_Hall,
    NULL,
    NULL,
};

const Transition gExitList_ArmosInteriors_RuinsEntranceNorth[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x78, 0xf8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_RUINS, ROOM_RUINS_ENTRANCE, 1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0,
      0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_ArmosInteriors_RuinsEntranceSouth[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x88, 0x1a8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_RUINS, ROOM_RUINS_ENTRANCE, 1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0,
      0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_ArmosInteriors_RuinsLeft[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x48, 0x68, TRANSITION_SHAPE_BORDER_SOUTH, AREA_RUINS, ROOM_RUINS_BELOW_FORTRESS_ENTRANCE, 1,
      TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_ArmosInteriors_RuinsMiddleLeft[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x78, 0x68, TRANSITION_SHAPE_BORDER_SOUTH, AREA_RUINS, ROOM_RUINS_BELOW_FORTRESS_ENTRANCE, 1,
      TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_ArmosInteriors_RuinsMiddleRight[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xa8, 0x68, TRANSITION_SHAPE_BORDER_SOUTH, AREA_RUINS, ROOM_RUINS_BELOW_FORTRESS_ENTRANCE, 1,
      TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_ArmosInteriors_RuinsRight[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xd8, 0x68, TRANSITION_SHAPE_BORDER_SOUTH, AREA_RUINS, ROOM_RUINS_BELOW_FORTRESS_ENTRANCE, 1,
      TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_ArmosInteriors_6[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x108, 0x68, TRANSITION_SHAPE_BORDER_SOUTH, AREA_RUINS, ROOM_RUINS_BELOW_FORTRESS_ENTRANCE, 1,
      TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_ArmosInteriors_RuinsGrassPath[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xa8, 0xa8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_RUINS, ROOM_RUINS_FORTRESS_ENTRANCE, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_ArmosInteriors_8[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xc8, 0x58, TRANSITION_SHAPE_BORDER_SOUTH, AREA_RUINS, ROOM_RUINS_ENTRANCE, 1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0,
      0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_ArmosInteriors_FortressOfWindsLeft[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xc8, 0x58, TRANSITION_SHAPE_BORDER_SOUTH, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_EAST_KEY_LEVER,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_ArmosInteriors_FortressOfWindsRight[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xc8, 0x58, TRANSITION_SHAPE_BORDER_SOUTH, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_EAST_KEY_LEVER,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_ArmosInteriors[] = {
    [ROOM_ARMOS_INTERIORS_RUINS_ENTRANCE_NORTH] = gExitList_ArmosInteriors_RuinsEntranceNorth,
    [ROOM_ARMOS_INTERIORS_RUINS_ENTRANCE_SOUTH] = gExitList_ArmosInteriors_RuinsEntranceSouth,
    [ROOM_ARMOS_INTERIORS_RUINS_LEFT] = gExitList_ArmosInteriors_RuinsLeft,
    [ROOM_ARMOS_INTERIORS_RUINS_MIDDLE_LEFT] = gExitList_ArmosInteriors_RuinsMiddleLeft,
    [ROOM_ARMOS_INTERIORS_RUINS_MIDDLE_RIGHT] = gExitList_ArmosInteriors_RuinsMiddleRight,
    [ROOM_ARMOS_INTERIORS_RUINS_RIGHT] = gExitList_ArmosInteriors_RuinsRight,
    [ROOM_ARMOS_INTERIORS_6] = gExitList_ArmosInteriors_6,
    [ROOM_ARMOS_INTERIORS_RUINS_GRASS_PATH] = gExitList_ArmosInteriors_RuinsGrassPath,
    [ROOM_ARMOS_INTERIORS_8] = gExitList_ArmosInteriors_8,
    [ROOM_ARMOS_INTERIORS_FORTRESS_LEFT] = gExitList_ArmosInteriors_FortressOfWindsLeft,
    [ROOM_ARMOS_INTERIORS_FORTRESS_RIGHT] = gExitList_ArmosInteriors_FortressOfWindsRight,
};

const Transition gExitList_TownMinishHoles_MayorsHouse[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x38, 0x2c, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HOUSE_INTERIORS_1, ROOM_HOUSE_INTERIORS_1_MAYOR,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TownMinishHoles_WestOracle[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xc, 0x38, TRANSITION_SHAPE_BORDER_EAST, AREA_HOUSE_INTERIORS_2, ROOM_HOUSE_INTERIORS_2_WEST_ORACLE,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x2, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TownMinishHoles_DrLeft[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xa8, 0x44, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HOUSE_INTERIORS_2, ROOM_HOUSE_INTERIORS_2_DR_LEFT,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TownMinishHoles_Carpenter[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xc, 0x68, TRANSITION_SHAPE_BORDER_EAST, AREA_HOUSE_INTERIORS_4, ROOM_HOUSE_INTERIORS_4_CARPENTER,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x2, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TownMinishHoles_Cafe[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xcc, 0x48, TRANSITION_SHAPE_BORDER_WEST, AREA_HOUSE_INTERIORS_3, ROOM_HOUSE_INTERIORS_3_CAFE,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x6, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TownMinishHoles_LibraryBookshelf[] = {
    { WARP_TYPE_AREA, 0x100, 0xc8, 0x78, 0xc0, TRANSITION_SHAPE_AREA_12x12, AREA_TOWN_MINISH_HOLES,
      ROOM_TOWN_MINISH_HOLES_LIBRARY_BOOKS_HOUSE, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3e, 0x3c, TRANSITION_SHAPE_BORDER_SOUTH_WEST, AREA_HOUSE_INTERIORS_1, ROOM_HOUSE_INTERIORS_1_LIBRARY_2F,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x54, 0x3c, TRANSITION_SHAPE_BORDER_SOUTH_EAST, AREA_HOUSE_INTERIORS_1, ROOM_HOUSE_INTERIORS_1_LIBRARY_2F,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TownMinishHoles_LibrariBookHouse[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xf8, 0xd8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_TOWN_MINISH_HOLES, ROOM_TOWN_MINISH_HOLES_LIBRARY_BOOKSHELF,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TownMinishHoles_RemShoeShop[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x74, 0x64, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HOUSE_INTERIORS_3, ROOM_HOUSE_INTERIORS_3_REM_SHOE_SHOP,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_TownMinishHoles[] = {
    [ROOM_TOWN_MINISH_HOLES_MAYORS_HOUSE] = gExitList_TownMinishHoles_MayorsHouse,
    [ROOM_TOWN_MINISH_HOLES_WEST_ORACLE] = gExitList_TownMinishHoles_WestOracle,
    [ROOM_TOWN_MINISH_HOLES_DR_LEFT] = gExitList_TownMinishHoles_DrLeft,
    [ROOM_TOWN_MINISH_HOLES_CARPENTER] = gExitList_TownMinishHoles_Carpenter,
    [ROOM_TOWN_MINISH_HOLES_CAFE] = gExitList_TownMinishHoles_Cafe,
    [ROOM_TOWN_MINISH_HOLES_5] = gExitList_NoExitList,
    [ROOM_TOWN_MINISH_HOLES_6] = gExitList_NoExitList,
    [ROOM_TOWN_MINISH_HOLES_7] = gExitList_NoExitList,
    [ROOM_TOWN_MINISH_HOLES_8] = gExitList_NoExitList,
    [ROOM_TOWN_MINISH_HOLES_9] = gExitList_NoExitList,
    [ROOM_TOWN_MINISH_HOLES_a] = gExitList_NoExitList,
    [ROOM_TOWN_MINISH_HOLES_b] = gExitList_NoExitList,
    [ROOM_TOWN_MINISH_HOLES_c] = gExitList_NoExitList,
    [ROOM_TOWN_MINISH_HOLES_d] = gExitList_NoExitList,
    [ROOM_TOWN_MINISH_HOLES_e] = gExitList_NoExitList,
    [ROOM_TOWN_MINISH_HOLES_f] = gExitList_NoExitList,
    [ROOM_TOWN_MINISH_HOLES_LIBRARY_BOOKSHELF] = gExitList_TownMinishHoles_LibraryBookshelf,
    [ROOM_TOWN_MINISH_HOLES_LIBRARY_BOOKS_HOUSE] = gExitList_TownMinishHoles_LibrariBookHouse,
    [ROOM_TOWN_MINISH_HOLES_REM_SHOE_SHOP] = gExitList_TownMinishHoles_RemShoeShop,
    [ROOM_TOWN_MINISH_HOLES_13] = gExitList_NoExitList,
};

const Transition gExitList_MinishRafters_Cafe[] = {
    { WARP_TYPE_AREA, 0x38, 0x18, 0x48, 0x2c, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_3, ROOM_HOUSE_INTERIORS_3_CAFE,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1bc, 0x2b4, TRANSITION_SHAPE_BORDER_EAST, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 2, TRANSITION_TYPE_INSTANT_MINISH,
      0x2, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishRafters_Stockwell[] = {
    { WARP_TYPE_AREA, 0x198, 0x18, 0xac, 0x2c, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_3, ROOM_HOUSE_INTERIORS_3_STOCKWELL_SHOP,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x238, 0x2b4, TRANSITION_SHAPE_BORDER_WEST, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 2, TRANSITION_TYPE_INSTANT_MINISH,
      0x6, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishRafters_DrLeft[] = {
    { WARP_TYPE_AREA, 0xe8, 0x18, 0x88, 0x2c, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_2, ROOM_HOUSE_INTERIORS_2_DR_LEFT,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishRafters_Bakery[] = {
    { WARP_TYPE_AREA, 0x48, 0x18, 0x48, 0x2c, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_3, ROOM_HOUSE_INTERIORS_3_BAKERY,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x148, 0x18, 0x88, 0x2c, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_3, ROOM_HOUSE_INTERIORS_3_BAKERY,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_MinishRafters[] = {
    [ROOM_MINISH_RAFTERS_CAFE] = gExitList_MinishRafters_Cafe,
    [ROOM_MINISH_RAFTERS_STOCKWELL] = gExitList_MinishRafters_Stockwell,
    [ROOM_MINISH_RAFTERS_DR_LEFT] = gExitList_MinishRafters_DrLeft,
    [ROOM_MINISH_RAFTERS_BAKERY] = gExitList_MinishRafters_Bakery,
};

const Transition gExitList_GoronCave_Stairs[] = {
    { WARP_TYPE_AREA, 0x78, 0x38, 0x78, 0x278, TRANSITION_SHAPE_AREA_12x12, AREA_GORON_CAVE, ROOM_GORON_CAVE_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x88, 0x368, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_GoronCave_Main[] = {
    { WARP_TYPE_AREA, 0x78, 0x288, 0x78, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_GORON_CAVE, ROOM_GORON_CAVE_STAIRS, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_GoronCave[] = {
    [ROOM_GORON_CAVE_STAIRS] = gExitList_GoronCave_Stairs,
    [ROOM_GORON_CAVE_MAIN] = gExitList_GoronCave_Main,
};

const Transition gExitList_WindTribeTower_Entrance[] = {
    { WARP_TYPE_AREA, 0x88, 0xe8, 0xb8, 0xf8, TRANSITION_SHAPE_AREA_12x12, AREA_WIND_TRIBE_TOWER, ROOM_WIND_TRIBE_TOWER_FLOOR_1,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1e8, 0x168, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CLOUD_TOPS, ROOM_CLOUD_TOPS_CLOUD_TOPS, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_WindTribeTower_Floor2[] = {
    { WARP_TYPE_AREA, 0xb8, 0xe8, 0x88, 0xf8, TRANSITION_SHAPE_AREA_12x12, AREA_WIND_TRIBE_TOWER, ROOM_WIND_TRIBE_TOWER_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x88, 0xe8, 0xb8, 0xf8, TRANSITION_SHAPE_AREA_12x12, AREA_WIND_TRIBE_TOWER, ROOM_WIND_TRIBE_TOWER_FLOOR_2,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_WindTribeTower_Floor3[] = {
    { WARP_TYPE_AREA, 0xb8, 0xe8, 0x88, 0xf8, TRANSITION_SHAPE_AREA_12x12, AREA_WIND_TRIBE_TOWER, ROOM_WIND_TRIBE_TOWER_FLOOR_1,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x88, 0xe8, 0xb8, 0xf8, TRANSITION_SHAPE_AREA_12x12, AREA_WIND_TRIBE_TOWER, ROOM_WIND_TRIBE_TOWER_FLOOR_3,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_WindTribeTower_Floor4[] = {
    { WARP_TYPE_AREA, 0xb8, 0xe8, 0x88, 0xf8, TRANSITION_SHAPE_AREA_12x12, AREA_WIND_TRIBE_TOWER, ROOM_WIND_TRIBE_TOWER_FLOOR_2,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x88, 0xe8, 0xb8, 0x148, TRANSITION_SHAPE_AREA_12x12, AREA_WIND_TRIBE_TOWER_ROOF, ROOM_WIND_TRIBE_TOWER_ROOF_0,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_WindTribeTower[] = {
    [ROOM_WIND_TRIBE_TOWER_ENTRANCE] = gExitList_WindTribeTower_Entrance,
    [ROOM_WIND_TRIBE_TOWER_FLOOR_1] = gExitList_WindTribeTower_Floor2,
    [ROOM_WIND_TRIBE_TOWER_FLOOR_2] = gExitList_WindTribeTower_Floor3,
    [ROOM_WIND_TRIBE_TOWER_FLOOR_3] = gExitList_WindTribeTower_Floor4,
};

const Transition gExitList_WindTribeTowerRoof_Main[] = {
    { WARP_TYPE_AREA, 0xb8, 0x138, 0x88, 0xf8, TRANSITION_SHAPE_AREA_12x12, AREA_WIND_TRIBE_TOWER, ROOM_WIND_TRIBE_TOWER_FLOOR_3,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_WindTribeTowerRoof[] = {
    [ROOM_WIND_TRIBE_TOWER_ROOF_0] = gExitList_WindTribeTowerRoof_Main,
};

const Transition gExitList_Caves_Boomerang[] = {
#ifdef QUICKSTART
    // Arrival in each tree hollow moved from (0x78,0x38) to (0x78,0x68) -
    // from just NORTH of the hollow's ladder to just SOUTH of it.
    //
    // Vanilla can put the player north of the ladder because vanilla only
    // ever runs this trip once: the chamber is a one-time prize room and
    // its ladders exist because the Boomerang chest event drew them. Here
    // the hollows are ? rooms the player comes and goes from, and the
    // ladder is a live door in both directions (game.c opens its collision
    // so the vanilla door can fire at all). North of it, the only way out
    // of the hollow - its south border to the field - crosses the ladder,
    // so leaving would send the player straight back down. (120,104) is
    // open floor on the field side of it, so both ways out are a walk.
    { WARP_TYPE_AREA, 0x48, 0x68, 0x78, 0x68, TRANSITION_SHAPE_AREA_12x12, AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_BOOMERANG_NORTHWEST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x108, 0x68, 0x78, 0x68, TRANSITION_SHAPE_AREA_12x12, AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_BOOMERANG_NORTHEAST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x48, 0xd8, 0x78, 0x68, TRANSITION_SHAPE_AREA_12x12, AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_BOOMERANG_SOUTHWEST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x108, 0xd8, 0x78, 0x68, TRANSITION_SHAPE_AREA_12x12, AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_BOOMERANG_SOUTHEAST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
#else
    { WARP_TYPE_AREA, 0x48, 0x68, 0x78, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_BOOMERANG_NORTHWEST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x108, 0x68, 0x78, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_BOOMERANG_NORTHEAST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x48, 0xd8, 0x78, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_BOOMERANG_SOUTHWEST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x108, 0xd8, 0x78, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_TREE_INTERIORS, ROOM_TREE_INTERIORS_BOOMERANG_SOUTHEAST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
#endif
    { WARP_TYPE_AREA, 0xa8, 0xb8, 0x1f8, 0x138, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Caves_ToGraveyard[] = {
    { WARP_TYPE_AREA, 0x38, 0x38, 0x88, 0xd8, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x118, 0x38, 0x118, 0xd8, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x138, 0x98, 0x78, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_HEART_PIECE_HALLWAY, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x108, 0x148, TRANSITION_SHAPE_BORDER_SOUTH_EAST, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Caves_2[] = {
    { WARP_TYPE_AREA, 0x48, 0x28, 0x308, 0x98, TRANSITION_SHAPE_AREA_12x12, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Caves_3[] = {
    TransitionListEnd,
};
const Transition gExitList_Caves_4[] = {
    TransitionListEnd,
};
const Transition gExitList_Caves_5[] = {
    TransitionListEnd,
};
const Transition gExitList_Caves_TrilbyKeeseChest[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x88, 0x238, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Caves_TrilbyFairyFountain[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x198, 0x2c8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
// PILOT: no longer retargeted, same reasoning as
// gExitList_TreeInteriors_HeartPiece above - this cave is a ? room in place
// now, reached through South Hyrule Field's own (bombable) cave mouth.
const Transition gExitList_Caves_SouthHyruleFieldFairyFountain[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x118, 0xb8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Caves_A[] = {
    TransitionListEnd,
};
const Transition gExitList_Caves_HyruleTownWaterfall[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xf0, 0x198, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Caves_LonLonRanch[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xe8, 0x1c8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xb8, 0x138, TRANSITION_SHAPE_BORDER_NORTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Caves_TrilbyHighlands[] = {
    { WARP_TYPE_AREA, 0x38, 0x18, 0x98, 0x268, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x128, 0x18, 0x118, 0x268, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
// VANILLA, in both branches again. This is the cave under Lon Lon Ranch's
// shallow water - the one a Kinstone fusion reveals a staircase down into.
//
// It spent a long time retargeted at Castle Garden Main, which is the landing
// spot every room in the old "? room" pool shared. The room was never actually
// added to that pool, though (nothing in game.c so much as named it), so the
// retarget was all cost and no benefit: the player fused the Kinstone, walked
// down the revealed stairs into an empty cave, and its only exit deposited
// them in Castle Garden. Reported by the user as "this staircase leads
// nowhere, the player just warps back to the overworld map" - the warp they
// saw was this exit firing.
//
// Back on vanilla, it returns to Lon Lon Ranch at (0x1f8,0x218), just south of
// the staircase it came from, and the room is a content site now
// (sQuickStartRoomContentSites, game.c) so there is something down there.
const Transition gExitList_Caves_LonLonRanchWallet[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1f8, 0x218, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Caves_SouthHyruleFieldRupee[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x58, 0x128, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
// PILOT: no longer retargeted - this cave is a ? room in place now, reached
// through Trilby Highlands' own real cave mouth, so its real vanilla exit
// back to Trilby is exactly what's wanted. Identical in both builds.
const Transition gExitList_Caves_TrilbyRupee[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x38, 0x2b8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_TRILBY_HIGHLANDS,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Caves_TrilbyMittsFairyFountain[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1a8, 0x68, TRANSITION_SHAPE_BORDER_NORTH, AREA_DIG_CAVES, ROOM_DIG_CAVES_TRILBY_HIGHLANDS, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Caves_HillsKeeseChest[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xa8, 0xa8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_EASTERN_HILLS_CENTER,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Caves_BottleBusinessScrub[] = {
    TransitionListEnd,
};
#ifdef QUICKSTART
// This room is North Hyrule Field's Heart Piece Hallway cave on the
// vanilla-door model now (gExitList_HyruleField_NorthHyruleField above):
// entered through its own real vanilla cave mouth, with a randomized event
// spawned inside it (game.c: sQuickStartRoomContentSites). It is no longer
// a 2-door pool room, so the old "both doors lead back to the Lon Lon
// Ranch connector ledge" retarget is gone.
//
// CORRECTION. The first entry used to be pointed back at this cave's own
// mouth, on the belief that vanilla's destination - ROOM_CAVES_TO_GRAVEYARD
// - was a through-cave reaching Royal Valley and so escaping the run. That
// is wrong, and reading its exit list settles it: all four of its doors are
// two mouths back into North Hyrule Field, a border south into the same
// field, and one back into this hallway. The two caves are a closed pocket
// between them, and always were.
//
// So this entry is vanilla again, and the pair connects the way the map
// suggests it should. ROOM_CAVES_TO_GRAVEYARD is blessed past containment
// in game.c (QuickStartIsPocketInteriorRoom) and hosts its own ? event.
const Transition gExitList_Caves_HeartPieceHallway[] = {
    { WARP_TYPE_AREA, 0x78, 0x38, 0x138, 0x88, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_TO_GRAVEYARD, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x138, 0x1f8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD,
      ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_Caves_HeartPieceHallway[] = {
    { WARP_TYPE_AREA, 0x78, 0x38, 0x138, 0x88, TRANSITION_SHAPE_AREA_12x12, AREA_CAVES, ROOM_CAVES_TO_GRAVEYARD, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x138, 0x1f8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_NORTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition gExitList_Caves_NorthHyruleFieldFairyFountain[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x78, 0x58, TRANSITION_SHAPE_BORDER_SOUTH, AREA_TREE_INTERIORS,
      ROOM_TREE_INTERIORS_NORTH_HYRULE_FIELD_FAIRY_FOUNTAIN, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Caves_KinstoneBusinessScrub[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x78, 0x58, TRANSITION_SHAPE_BORDER_SOUTH, AREA_TREE_INTERIORS,
      ROOM_TREE_INTERIORS_MINISH_WOODS_BUSINESS_SCRUB, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_Caves[] = {
    [ROOM_CAVES_BOOMERANG] = gExitList_Caves_Boomerang,
    [ROOM_CAVES_TO_GRAVEYARD] = gExitList_Caves_ToGraveyard,
    [ROOM_CAVES_2] = gExitList_Caves_2,
    [ROOM_CAVES_3] = gExitList_Caves_3,
    [ROOM_CAVES_4] = gExitList_Caves_4,
    [ROOM_CAVES_5] = gExitList_Caves_5,
    [ROOM_CAVES_6] = gExitList_NoExitList,
    [ROOM_CAVES_TRILBY_KEESE_CHEST] = gExitList_Caves_TrilbyKeeseChest,
    [ROOM_CAVES_TRILBY_FAIRY_FOUNTAIN] = gExitList_Caves_TrilbyFairyFountain,
    [ROOM_CAVES_SOUTH_HYRULE_FIELD_FAIRY_FOUNTAIN] = gExitList_Caves_SouthHyruleFieldFairyFountain,
    [ROOM_CAVES_a] = gExitList_Caves_A,
    [ROOM_CAVES_HYRULE_TOWN_WATERFALL] = gExitList_Caves_HyruleTownWaterfall,
    [ROOM_CAVES_LON_LON_RANCH] = gExitList_Caves_LonLonRanch,
    [ROOM_CAVES_LON_LON_RANCH_SECRET] = gExitList_NoExitList,
    [ROOM_CAVES_TRILBY_HIGHLANDS] = gExitList_Caves_TrilbyHighlands,
    [ROOM_CAVES_LON_LON_RANCH_WALLET] = gExitList_Caves_LonLonRanchWallet,
    [ROOM_CAVES_SOUTH_HYRULE_FIELD_RUPEE] = gExitList_Caves_SouthHyruleFieldRupee,
    [ROOM_CAVES_TRILBY_RUPEE] = gExitList_Caves_TrilbyRupee,
    [ROOM_CAVES_TRILBY_MITTS_FAIRY_FOUNTAIN] = gExitList_Caves_TrilbyMittsFairyFountain,
    [ROOM_CAVES_HILLS_KEESE_CHEST] = gExitList_Caves_HillsKeeseChest,
    [ROOM_CAVES_BOTTLE_BUSINESS_SCRUB] = gExitList_Caves_BottleBusinessScrub,
    [ROOM_CAVES_HEART_PIECE_HALLWAY] = gExitList_Caves_HeartPieceHallway,
    [ROOM_CAVES_NORTH_HYRULE_FIELD_FAIRY_FOUNTAIN] = gExitList_Caves_NorthHyruleFieldFairyFountain,
    [ROOM_CAVES_KINSTONE_BUSINESS_SCRUB] = gExitList_Caves_KinstoneBusinessScrub,
};

const Transition gExitList_VeilFallsCaves_Hallway2F[] = {
    { WARP_TYPE_AREA, 0xd8, 0x28, 0x78, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_VEIL_FALLS_CAVES, ROOM_VEIL_FALLS_CAVES_HALLWAY_1F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xa8, 0x38, TRANSITION_SHAPE_BORDER_SOUTH_WEST, AREA_VEIL_FALLS, ROOM_VEIL_FALLS_MAIN, 1, TRANSITION_TYPE_NORMAL, 0x4,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x158, 0x38, TRANSITION_SHAPE_BORDER_SOUTH_EAST, AREA_VEIL_FALLS, ROOM_VEIL_FALLS_MAIN, 1, TRANSITION_TYPE_NORMAL, 0x4,
      0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_VeilFallsCaves_Hallway1F[] = {
    { WARP_TYPE_AREA, 0x38, 0x18, 0x98, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_VEIL_FALLS_CAVES, ROOM_VEIL_FALLS_CAVES_HALLWAY_RUPEE_PATH,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x78, 0x18, 0xd8, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_VEIL_FALLS_CAVES, ROOM_VEIL_FALLS_CAVES_HALLWAY_2F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xb8, 0x8c, 0x118, 0x58, TRANSITION_SHAPE_AREA_12x12, AREA_VEIL_FALLS, ROOM_VEIL_FALLS_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x38, 0xe8, 0xc8, 0x58, TRANSITION_SHAPE_AREA_12x12, AREA_VEIL_FALLS, ROOM_VEIL_FALLS_MAIN, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_VeilFallsCaves_Entrance[] = {
    { WARP_TYPE_AREA, 0x128, 0x18, 0x58, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_VEIL_FALLS_CAVES, ROOM_VEIL_FALLS_CAVES_EXIT,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x38, 0x1f8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_VEIL_FALLS, ROOM_VEIL_FALLS_MAIN, 1, TRANSITION_TYPE_NORMAL, 0x4,
      0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#ifdef QUICKSTART
// Retargeted as a QUICKSTART "2-door ? room" pool candidate - both
// real doors now lead back to the Lon Lon Ranch cave-connector ledge
// (0xb8,0x138), same shared return spot every other 2-door pool room
// uses (see game.c: sQuickStart2DoorSmallRoomPool/LargeRoomPool). Real
// startX/startY/shape/warp_type kept as-is - only destination changes.
const Transition gExitList_VeilFallsCaves_Exit[] = {
    { WARP_TYPE_AREA, 0x58, 0x18, 0x3fe, 0x3fe, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3fd, 0x3fd, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_VeilFallsCaves_Exit[] = {
    { WARP_TYPE_AREA, 0x58, 0x18, 0x128, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_VEIL_FALLS_CAVES, ROOM_VEIL_FALLS_CAVES_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xd8, 0x1d8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_VEIL_FALLS, ROOM_VEIL_FALLS_MAIN, 1, TRANSITION_TYPE_NORMAL, 0x4,
      0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition gExitList_VeilFallsCaves_SecretChest[] = {
    { WARP_TYPE_AREA, 0x58, 0x38, 0x98, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_VEIL_FALLS_CAVES,
      ROOM_VEIL_FALLS_CAVES_HALLWAY_SECRET_STAIRCASE, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#ifdef QUICKSTART
// Retargeted as a QUICKSTART "2-door ? room" pool candidate - both
// real doors now lead back to the Lon Lon Ranch cave-connector ledge
// (0xb8,0x138), same shared return spot every other 2-door pool room
// uses (see game.c: sQuickStart2DoorSmallRoomPool/LargeRoomPool). Real
// startX/startY/shape/warp_type kept as-is - only destination changes.
const Transition gExitList_VeilFallsCaves_SecretStaircases[] = {
    { WARP_TYPE_AREA, 0x58, 0x38, 0x3fe, 0x3fe, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x98, 0x38, 0x3fd, 0x3fd, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_VeilFallsCaves_SecretStaircases[] = {
    { WARP_TYPE_AREA, 0x58, 0x38, 0x98, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_VEIL_FALLS_CAVES, ROOM_VEIL_FALLS_CAVES_HALLWAY_BLOCK_PUZZLE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x98, 0x38, 0x58, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_VEIL_FALLS_CAVES, ROOM_VEIL_FALLS_CAVES_SECRET_CHEST,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition gExitList_VeilFallsCaves_BlockPuzzle[] = {
    { WARP_TYPE_AREA, 0x98, 0x38, 0x58, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_VEIL_FALLS_CAVES,
      ROOM_VEIL_FALLS_CAVES_HALLWAY_SECRET_STAIRCASE, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xd8, 0x158, TRANSITION_SHAPE_BORDER_SOUTH, AREA_VEIL_FALLS, ROOM_VEIL_FALLS_MAIN, 1, TRANSITION_TYPE_NORMAL, 0x4,
      0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#ifdef QUICKSTART
// Retargeted as a QUICKSTART "2-door ? room" pool candidate - both
// real doors now lead back to the Lon Lon Ranch cave-connector ledge
// (0xb8,0x138), same shared return spot every other 2-door pool room
// uses (see game.c: sQuickStart2DoorSmallRoomPool/LargeRoomPool). Real
// startX/startY/shape/warp_type kept as-is - only destination changes.
const Transition gExitList_VeilFallsCaves_RupeePath[] = {
    { WARP_TYPE_AREA, 0x98, 0x18, 0x3fe, 0x3fe, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3fd, 0x3fd, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_VeilFallsCaves_RupeePath[] = {
    { WARP_TYPE_AREA, 0x98, 0x18, 0x38, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_VEIL_FALLS_CAVES, ROOM_VEIL_FALLS_CAVES_HALLWAY_1F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xa8, 0xd8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_VEIL_FALLS, ROOM_VEIL_FALLS_MAIN, 1, TRANSITION_TYPE_NORMAL, 0x4,
      0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
#ifdef QUICKSTART
// Retargeted - see the "? room" pool comment above
// gExitList_MinishHouseInteriors_Red - this room is a small-pool member too
// (per the user's own room survey), its real exit otherwise leading
// somewhere entirely outside the QUICKSTART loop (Veil Falls proper) rather
// than back into it.
const Transition gExitList_VeilFallsCaves_HeartPiece[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x68, 0x90, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_VeilFallsCaves_HeartPiece[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x38, 0x38, TRANSITION_SHAPE_BORDER_SOUTH, AREA_VEIL_FALLS, ROOM_VEIL_FALLS_MAIN, 1, TRANSITION_TYPE_NORMAL, 0x4,
      0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition* const gExitLists_VeilFallsCaves[] = {
    [ROOM_VEIL_FALLS_CAVES_HALLWAY_2F] = gExitList_VeilFallsCaves_Hallway2F,
    [ROOM_VEIL_FALLS_CAVES_HALLWAY_1F] = gExitList_VeilFallsCaves_Hallway1F,
    [ROOM_VEIL_FALLS_CAVES_HALLWAY_SECRET_ROOM] = gExitList_NoExitList,
    [ROOM_VEIL_FALLS_CAVES_ENTRANCE] = gExitList_VeilFallsCaves_Entrance,
    [ROOM_VEIL_FALLS_CAVES_EXIT] = gExitList_VeilFallsCaves_Exit,
    [ROOM_VEIL_FALLS_CAVES_SECRET_CHEST] = gExitList_VeilFallsCaves_SecretChest,
    [ROOM_VEIL_FALLS_CAVES_HALLWAY_SECRET_STAIRCASE] = gExitList_VeilFallsCaves_SecretStaircases,
    [ROOM_VEIL_FALLS_CAVES_HALLWAY_BLOCK_PUZZLE] = gExitList_VeilFallsCaves_BlockPuzzle,
    [ROOM_VEIL_FALLS_CAVES_HALLWAY_RUPEE_PATH] = gExitList_VeilFallsCaves_RupeePath,
    [ROOM_VEIL_FALLS_CAVES_HALLWAY_HEART_PIECE] = gExitList_VeilFallsCaves_HeartPiece,
    [ROOM_VEIL_FALLS_CAVES_a] = gExitList_NoExitList,
    [ROOM_VEIL_FALLS_CAVES_b] = gExitList_NoExitList,
    [ROOM_VEIL_FALLS_CAVES_c] = gExitList_NoExitList,
    [ROOM_VEIL_FALLS_CAVES_d] = gExitList_NoExitList,
    [ROOM_VEIL_FALLS_CAVES_e] = gExitList_NoExitList,
    [ROOM_VEIL_FALLS_CAVES_f] = gExitList_NoExitList,
};

const Transition gExitList_RoyalValleyGraves_HeartPiece[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x58, 0x98, TRANSITION_SHAPE_BORDER_SOUTH, AREA_ROYAL_VALLEY, ROOM_ROYAL_VALLEY_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#ifdef QUICKSTART
// Retargeted - see the "? room" pool comment above gExitList_MinishHouseInteriors_Red.
const Transition gExitList_RoyalValleyGraves_Gina[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x68, 0x90, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_RoyalValleyGraves_Gina[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x188, 0x98, TRANSITION_SHAPE_BORDER_SOUTH, AREA_ROYAL_VALLEY, ROOM_ROYAL_VALLEY_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition* const gExitLists_RoyalValleyGraves[] = {
    [ROOM_ROYAL_VALLEY_GRAVES_HEART_PIECE] = gExitList_RoyalValleyGraves_HeartPiece,
    [ROOM_ROYAL_VALLEY_GRAVES_GINA] = gExitList_RoyalValleyGraves_Gina,
};

const Transition gExitList_MinishCaves_BeanPesto[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1c8, 0x28, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_ENTRANCE, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishCaves_SoutheastWater1[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3b8, 0x308, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTOR_WILDS, ROOM_CASTOR_WILDS_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishCaves_Ruins[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x38, 0x14, TRANSITION_SHAPE_BORDER_SOUTH, AREA_RUINS, ROOM_RUINS_LADDER_TO_TEKTITES, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishCaves_OutsideLinksHouse[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x178, 0xe8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_SOUTH_HYRULE_FIELD,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishCaves_MinishWoodsNorth1[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3b8, 0x48, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MINISH_WOODS, ROOM_MINISH_WOODS_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishCaves_LakeHyliaNorth[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x2b8, 0x68, TRANSITION_SHAPE_BORDER_SOUTH, AREA_LAKE_HYLIA, ROOM_LAKE_HYLIA_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH, 0x4,
      0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishCaves_LakeHyliaLibrari[] = {
    { WARP_TYPE_AREA, 0x48, 0x38, 0x98, 0x204, TRANSITION_SHAPE_AREA_12x12, AREA_LAKE_HYLIA, ROOM_LAKE_HYLIA_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x378, 0x38, 0x1b8, 0x1c4, TRANSITION_SHAPE_AREA_12x12, AREA_LAKE_HYLIA, ROOM_LAKE_HYLIA_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_MinishCaves_MinishWoodsSouthwest[] = {
    { WARP_TYPE_AREA, 0x58, 0x138, 0x48, 0x224, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_WOODS, ROOM_MINISH_WOODS_MAIN, 1,
      TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x138, 0x138, 0x68, 0x224, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_WOODS, ROOM_MINISH_WOODS_MAIN, 1,
      TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x218, 0x138, 0x88, 0x224, TRANSITION_SHAPE_AREA_12x12, AREA_MINISH_WOODS, ROOM_MINISH_WOODS_MAIN, 1,
      TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_MinishCaves[] = {
    [ROOM_MINISH_CAVES_BEAN_PESTO] = gExitList_MinishCaves_BeanPesto,
    [ROOM_MINISH_CAVES_SOUTHEAST_WATER_1] = gExitList_MinishCaves_SoutheastWater1,
    [ROOM_MINISH_CAVES_2] = gExitList_NoExitList,
    [ROOM_MINISH_CAVES_RUINS] = gExitList_MinishCaves_Ruins,
    [ROOM_MINISH_CAVES_OUTSIDE_LINKS_HOUSE] = gExitList_MinishCaves_OutsideLinksHouse,
    [ROOM_MINISH_CAVES_MINISH_WOODS_NORTH_1] = gExitList_MinishCaves_MinishWoodsNorth1,
    [ROOM_MINISH_CAVES_6] = gExitList_NoExitList,
    [ROOM_MINISH_CAVES_LAKE_HYLIA_NORTH] = gExitList_MinishCaves_LakeHyliaNorth,
    [ROOM_MINISH_CAVES_LAKE_HYLIA_LIBRARI] = gExitList_MinishCaves_LakeHyliaLibrari,
    [ROOM_MINISH_CAVES_MINISH_WOODS_SOUTHWEST] = gExitList_MinishCaves_MinishWoodsSouthwest,
};

const Transition gExitList_CastleGardenMinishHoles_East[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x308, 0x2c, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1,
      TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_CastleGardenMinishHoles_West[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xe8, 0x2c, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_CastleGardenMinishHoles[] = {
    [ROOM_CASTLE_GARDEN_MINISH_HOLES_0] = gExitList_CastleGardenMinishHoles_East,
    [ROOM_CASTLE_GARDEN_MINISH_HOLES_1] = gExitList_CastleGardenMinishHoles_West,
};

const Transition gExitList_37_0[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x308, 0x2c, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1,
      TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_37_1[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xe8, 0x2c, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_37[] = {
    [ROOM_37_0] = gExitList_37_0,
    [ROOM_37_1] = gExitList_37_1,
};

const Transition gExitList_HyruleTownUnderground_Main[] = {
    { WARP_TYPE_AREA, 0x288, 0xf8, 0x338, 0x118, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x168, 0x18, 0x78, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_HOUSE_INTERIORS_1, ROOM_HOUSE_INTERIORS_1_SCHOOL_WEST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x48, 0xf8, 0x188, 0x208, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_DIG_CAVES, ROOM_HYRULE_DIG_CAVES_TOWN,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x138, 0x238, 0x88, 0x50, TRANSITION_SHAPE_AREA_12x28, AREA_HYRULE_TOWN_UNDERGROUND, ROOM_HYRULE_TOWN_UNDERGROUND_1,
      1, TRANSITION_TYPE_NORMAL, 0x6, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HyruleTownUnderground_Well[] = {
    { WARP_TYPE_AREA, 0x98, 0x50, 0x148, 0x23c, TRANSITION_SHAPE_AREA_12x28, AREA_HYRULE_TOWN_UNDERGROUND, ROOM_HYRULE_TOWN_UNDERGROUND_0,
      1, TRANSITION_TYPE_NORMAL, 0x2, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x78, 0x28, 0x2f8, 0x26c, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_HyruleTownUnderground[] = {
    [ROOM_HYRULE_TOWN_UNDERGROUND_0] = gExitList_HyruleTownUnderground_Main,
    [ROOM_HYRULE_TOWN_UNDERGROUND_1] = gExitList_HyruleTownUnderground_Well,
};

const Transition gExitList_HyruleTownMinishCaves_Entrance[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x174, 0x196, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HyruleTownMinishCaves_Entrance2[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xe2, 0x58, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_TOWN, ROOM_HYRULE_TOWN_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_HyruleTownMinishCaves[] = {
    gExitList_HyruleTownMinishCaves_Entrance,
    gExitList_NoExitList,
    gExitList_NoExitList,
    gExitList_NoExitList,
    gExitList_NoExitList,
    gExitList_NoExitList,
    gExitList_NoExitList,
    gExitList_NoExitList,
    gExitList_NoExitList,
    gExitList_NoExitList,
    gExitList_NoExitList,
    gExitList_NoExitList,
    gExitList_NoExitList,
    gExitList_NoExitList,
    gExitList_NoExitList,
    gExitList_NoExitList,
    gExitList_NoExitList,
    gExitList_NoExitList,
    gExitList_NoExitList,
    gExitList_NoExitList,
    gExitList_NoExitList,
    gExitList_HyruleTownMinishCaves_Entrance2,
    gExitList_NoExitList,
    gExitList_NoExitList,
};

const Transition gExitList_GardenFountains_East[] = {
    { WARP_TYPE_AREA, 0x78, 0x88, 0x308, 0x58, TRANSITION_SHAPE_AREA_12x12, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_GardenFountains_West[] = {
    { WARP_TYPE_AREA, 0x78, 0x88, 0xe8, 0x58, TRANSITION_SHAPE_AREA_12x12, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_GardenFountains[] = {
    [ROOM_GARDEN_FOUNTAINS_EAST] = gExitList_GardenFountains_East,
    [ROOM_GARDEN_FOUNTAINS_WEST] = gExitList_GardenFountains_West,
};

const Transition gExitList_GreatFairies_Entrance[] = {
    { WARP_TYPE_AREA, 0x68, 0x188, 0x68, 0x58, TRANSITION_SHAPE_AREA_12x12, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_GreatFairies_Exit[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x52, 0x29c, TRANSITION_SHAPE_BORDER_EAST, AREA_HYRULE_CASTLE, ROOM_HYRULE_CASTLE_3, 1, TRANSITION_TYPE_NORMAL,
      0x2, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_HyruleCastleCellar[] = {
    [ROOM_HYRULE_CASTLE_CELLAR_0] = gExitList_GreatFairies_Entrance,
    [ROOM_HYRULE_CASTLE_CELLAR_1] = gExitList_GreatFairies_Exit,
};

const Transition* const gExitLists_40[] = {
    gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList,
    gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList, gExitList_NoExitList,
};

const Transition gExitList_DeepwoodShrine_StairsToB1[] = {
    { WARP_TYPE_AREA, 0xc8, 0x28, 0xc8, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_DEEPWOOD_SHRINE, ROOM_DEEPWOOD_SHRINE_COMPASS,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DeepwoodShrine_BluePortal[] = {
#ifdef EU
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x38, TRANSITION_SHAPE_BORDER_SOUTH, AREA_DEEPWOOD_SHRINE, ROOM_DEEPWOOD_SHRINE_BARREL,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
#endif
    TransitionListEnd,
};
const Transition gExitList_DeepwoodShrine_Map[] = {
#ifdef EU
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x18, 0xfff, TRANSITION_SHAPE_BORDER_EAST, AREA_DEEPWOOD_SHRINE, ROOM_DEEPWOOD_SHRINE_BARREL,
      1, TRANSITION_TYPE_NORMAL, 0x2, 0x0, 0x0, 0x0 },
#endif
    TransitionListEnd,
};
const Transition gExitList_DeepwoodShrine_Button[] = {
#ifdef EU
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1b8, 0xfff, TRANSITION_SHAPE_BORDER_WEST, AREA_DEEPWOOD_SHRINE, ROOM_DEEPWOOD_SHRINE_BARREL,
      1, TRANSITION_TYPE_NORMAL, 0x6, 0x0, 0x0, 0x0 },
#endif
    TransitionListEnd,
};
const Transition gExitList_DeepwoodShrine_Lever[] = {
#ifdef EU
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x168, TRANSITION_SHAPE_BORDER_NORTH, AREA_DEEPWOOD_SHRINE, ROOM_DEEPWOOD_SHRINE_BARREL,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
#endif
    TransitionListEnd,
};
const Transition gExitList_DeepwoodShrine_Barrel[] = {
    { WARP_TYPE_AREA, 0xb8, 0x88, 0x50, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_DEEPWOOD_SHRINE, ROOM_DEEPWOOD_SHRINE_INSIDE_BARREL,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x118, 0x88, 0xa0, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_DEEPWOOD_SHRINE, ROOM_DEEPWOOD_SHRINE_INSIDE_BARREL,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xb8, 0x108, 0x50, 0x70, TRANSITION_SHAPE_AREA_12x12, AREA_DEEPWOOD_SHRINE, ROOM_DEEPWOOD_SHRINE_INSIDE_BARREL,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x118, 0x108, 0xa0, 0x70, TRANSITION_SHAPE_AREA_12x12, AREA_DEEPWOOD_SHRINE, ROOM_DEEPWOOD_SHRINE_INSIDE_BARREL,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
#ifdef EU
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0xc8, TRANSITION_SHAPE_BORDER_NORTH, AREA_DEEPWOOD_SHRINE, ROOM_DEEPWOOD_SHRINE_BLUE_PORTAL,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x28, 0xfff, TRANSITION_SHAPE_BORDER_EAST, AREA_DEEPWOOD_SHRINE, ROOM_DEEPWOOD_SHRINE_BUTTON,
      1, TRANSITION_TYPE_NORMAL, 0x2, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x38, TRANSITION_SHAPE_BORDER_SOUTH, AREA_DEEPWOOD_SHRINE, ROOM_DEEPWOOD_SHRINE_LEVER,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xe8, 0xfff, TRANSITION_SHAPE_BORDER_WEST, AREA_DEEPWOOD_SHRINE, ROOM_DEEPWOOD_SHRINE_MAP, 1,
      TRANSITION_TYPE_NORMAL, 0x6, 0x0, 0x0, 0x0 },
#endif
    TransitionListEnd,
};
const Transition gExitList_DeepwoodShrine_Entrance[] = {
    { WARP_TYPE_AREA, 0x48, 0x68, 0x48, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_DEEPWOOD_SHRINE, ROOM_DEEPWOOD_SHRINE_BOSS_DOOR,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x108, 0x68, 0x108, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_DEEPWOOD_SHRINE, ROOM_DEEPWOOD_SHRINE_BOSS_DOOR,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x78, 0x64, TRANSITION_SHAPE_BORDER_SOUTH, AREA_DEEPWOOD_SHRINE_ENTRY, ROOM_DEEPWOOD_SHRINE_ENTRY_MAIN,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DeepwoodShrine_Compass[] = {
    { WARP_TYPE_AREA, 0xc8, 0x28, 0xc8, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_DEEPWOOD_SHRINE, ROOM_DEEPWOOD_SHRINE_STAIRS_TO_B1,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DeepwoodShrineBoss_Main[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xa8, 0x8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_DEEPWOOD_SHRINE, ROOM_DEEPWOOD_SHRINE_BOSS_DOOR,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DeepwoodShrine_PreBoss[] = {
    { WARP_TYPE_AREA, 0x48, 0x68, 0x48, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_DEEPWOOD_SHRINE, ROOM_DEEPWOOD_SHRINE_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x108, 0x68, 0x108, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_DEEPWOOD_SHRINE, ROOM_DEEPWOOD_SHRINE_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x88, 0xd8, TRANSITION_SHAPE_BORDER_NORTH, AREA_DEEPWOOD_SHRINE_BOSS, ROOM_DEEPWOOD_SHRINE_BOSS_MAIN,
      1, TRANSITION_TYPE_INSTANT, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_DeepwoodShrine[] = {
    [ROOM_DEEPWOOD_SHRINE_MADDERPILLAR] = gExitList_NoExitList,
    [ROOM_DEEPWOOD_SHRINE_BLUE_PORTAL] = gExitList_DeepwoodShrine_BluePortal,
    [ROOM_DEEPWOOD_SHRINE_STAIRS_TO_B1] = gExitList_DeepwoodShrine_StairsToB1,
    [ROOM_DEEPWOOD_SHRINE_POT_BRIDGE] = gExitList_NoExitList,
    [ROOM_DEEPWOOD_SHRINE_DOUBLE_STATUE] = gExitList_NoExitList,
    [ROOM_DEEPWOOD_SHRINE_MAP] = gExitList_DeepwoodShrine_Map,
    [ROOM_DEEPWOOD_SHRINE_BARREL] = gExitList_DeepwoodShrine_Barrel,
    [ROOM_DEEPWOOD_SHRINE_BUTTON] = gExitList_DeepwoodShrine_Button,
    [ROOM_DEEPWOOD_SHRINE_MULLDOZER] = gExitList_NoExitList,
    [ROOM_DEEPWOOD_SHRINE_PILLARS] = gExitList_NoExitList,
    [ROOM_DEEPWOOD_SHRINE_LEVER] = gExitList_DeepwoodShrine_Lever,
    [ROOM_DEEPWOOD_SHRINE_ENTRANCE] = gExitList_DeepwoodShrine_Entrance,
    [ROOM_DEEPWOOD_SHRINE_c] = gExitList_NoExitList,
    [ROOM_DEEPWOOD_SHRINE_d] = gExitList_NoExitList,
    [ROOM_DEEPWOOD_SHRINE_e] = gExitList_NoExitList,
    [ROOM_DEEPWOOD_SHRINE_f] = gExitList_NoExitList,
    [ROOM_DEEPWOOD_SHRINE_TORCHES] = gExitList_NoExitList,
    [ROOM_DEEPWOOD_SHRINE_BOSS_KEY] = gExitList_NoExitList,
    [ROOM_DEEPWOOD_SHRINE_COMPASS] = gExitList_DeepwoodShrine_Compass,
    [ROOM_DEEPWOOD_SHRINE_13] = gExitList_NoExitList,
    [ROOM_DEEPWOOD_SHRINE_LILY_PAD_WEST] = gExitList_NoExitList,
    [ROOM_DEEPWOOD_SHRINE_LILY_PAD_EAST] = gExitList_NoExitList,
    [ROOM_DEEPWOOD_SHRINE_16] = gExitList_NoExitList,
    [ROOM_DEEPWOOD_SHRINE_BOSS_DOOR] = gExitList_DeepwoodShrine_PreBoss,
    [ROOM_DEEPWOOD_SHRINE_18] = gExitList_NoExitList,
    [ROOM_DEEPWOOD_SHRINE_19] = gExitList_NoExitList,
    [ROOM_DEEPWOOD_SHRINE_1a] = gExitList_NoExitList,
    [ROOM_DEEPWOOD_SHRINE_1b] = gExitList_NoExitList,
    [ROOM_DEEPWOOD_SHRINE_1c] = gExitList_NoExitList,
    [ROOM_DEEPWOOD_SHRINE_1d] = gExitList_NoExitList,
    [ROOM_DEEPWOOD_SHRINE_1e] = gExitList_NoExitList,
    [ROOM_DEEPWOOD_SHRINE_1f] = gExitList_NoExitList,
    [ROOM_DEEPWOOD_SHRINE_INSIDE_BARREL] = gExitList_NoExitList,
};

const Transition* const gExitLists_DeepwoodShrineBoss[] = {
    [ROOM_DEEPWOOD_SHRINE_BOSS_MAIN] = gExitList_DeepwoodShrineBoss_Main,
};

const Transition gExitList_DeepwoodShrineEntry_Main[] = {
    { WARP_TYPE_AREA, 0x78, 0x58, 0xa8, 0xd8, TRANSITION_SHAPE_AREA_12x12, AREA_DEEPWOOD_SHRINE, ROOM_DEEPWOOD_SHRINE_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x188, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1c8, 0x272, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MINISH_WOODS, ROOM_MINISH_WOODS_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1d8, 0x272, TRANSITION_SHAPE_BORDER_EAST, AREA_MINISH_WOODS, ROOM_MINISH_WOODS_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x2, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1b8, 0x272, TRANSITION_SHAPE_BORDER_WEST, AREA_MINISH_WOODS, ROOM_MINISH_WOODS_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x6, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_DeepwoodShrineEntry[] = {
    [ROOM_DEEPWOOD_SHRINE_ENTRY_MAIN] = gExitList_DeepwoodShrineEntry_Main,
};

const Transition gExitList_CaveOfFlames_AfterCane[] = {
    { WARP_TYPE_AREA, 0x88, 0x38, 0x1a8, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_CAVE_OF_FLAMES, ROOM_CAVE_OF_FLAMES_MINISH_SPIKES,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_CaveOfFlames_Entrance[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x68, 0x88, TRANSITION_SHAPE_BORDER_SOUTH, AREA_MT_CRENEL, ROOM_MT_CRENEL_CAVERN_OF_FLAMES_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_CaveOfFlames_MainCart[] = {
    { WARP_TYPE_AREA, 0x1f8, 0x38, 0x88, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_CAVE_OF_FLAMES, ROOM_CAVE_OF_FLAMES_NORTH_ENTRANCE,
      2, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_CaveOfFlames_NorthEntrance[] = {
    { WARP_TYPE_AREA, 0x88, 0x18, 0x1f8, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_CAVE_OF_FLAMES, ROOM_CAVE_OF_FLAMES_MAIN_CART,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_CaveOfFlames_MinishSpikes[] = {
    { WARP_TYPE_AREA, 0x1a8, 0x28, 0x88, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_CAVE_OF_FLAMES, ROOM_CAVE_OF_FLAMES_AFTER_CANE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_CaveOfFlames_BeforeGleerok[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x28, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CAVE_OF_FLAMES, ROOM_CAVE_OF_FLAMES_BOSS_DOOR,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_CaveOfFlames_BossDoor[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0xc0, TRANSITION_SHAPE_BORDER_NORTH_WEST, AREA_CAVE_OF_FLAMES, ROOM_CAVE_OF_FLAMES_BEFORE_GLEEROK,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_CaveOfFlames[] = {
    [ROOM_CAVE_OF_FLAMES_AFTER_CANE] = gExitList_CaveOfFlames_AfterCane,
    [ROOM_CAVE_OF_FLAMES_SPINY_CHU] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_CART_TO_SPINY_CHU] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_ENTRANCE] = gExitList_CaveOfFlames_Entrance,
    [ROOM_CAVE_OF_FLAMES_MAIN_CART] = gExitList_CaveOfFlames_MainCart,
    [ROOM_CAVE_OF_FLAMES_NORTH_ENTRANCE] = gExitList_CaveOfFlames_NorthEntrance,
    [ROOM_CAVE_OF_FLAMES_CART_WEST] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_HELMASAUR_FIGHT] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_ROLLOBITE_LAVA_ROOM] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_MINISH_LAVA_ROOM] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_a] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_b] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_c] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_d] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_e] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_f] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_MINISH_SPIKES] = gExitList_CaveOfFlames_MinishSpikes,
    [ROOM_CAVE_OF_FLAMES_TOMPAS_DOOM] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_BEFORE_GLEEROK] = gExitList_CaveOfFlames_BeforeGleerok,
    [ROOM_CAVE_OF_FLAMES_BOSSKEY_PATH1] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_BOSSKEY_PATH2] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_COMPASS] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_BOB_OMB_WALL] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_BOSS_DOOR] = gExitList_CaveOfFlames_BossDoor,
    [ROOM_CAVE_OF_FLAMES_18] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_19] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_1a] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_1b] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_1c] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_1d] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_1e] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_1f] = gExitList_NoExitList,
    [ROOM_CAVE_OF_FLAMES_20] = gExitList_NoExitList,
};

const Transition gExitList_FortressOfWinds_BeforeMazaal[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x18, TRANSITION_SHAPE_BORDER_SOUTH, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_WEST_KEY_LEVER,
      1, TRANSITION_TYPE_INSTANT, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_FortressOfWinds_EastKeyLever[] = {
    { WARP_TYPE_AREA, 0x198, 0x198, 0x2e8, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_OUTER_FORTRESS_OF_WINDS, ROOM_OUTER_FORTRESS_OF_WINDS_3F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x1f8, 0x198, 0x338, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_OUTER_FORTRESS_OF_WINDS, ROOM_OUTER_FORTRESS_OF_WINDS_3F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_FortressOfWinds_PitPlatforms[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x68, 0x38, TRANSITION_SHAPE_BORDER_SOUTH, AREA_OUTER_FORTRESS_OF_WINDS, ROOM_OUTER_FORTRESS_OF_WINDS_3F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_FortressOfWinds_WestKeyLever[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0xc8, TRANSITION_SHAPE_BORDER_NORTH, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_BEFORE_MAZAAL,
      1, TRANSITION_TYPE_INSTANT, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1d8, 0x38, TRANSITION_SHAPE_BORDER_SOUTH, AREA_OUTER_FORTRESS_OF_WINDS, ROOM_OUTER_FORTRESS_OF_WINDS_3F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_FortressOfWinds_Mazaal[] = {
    { WARP_TYPE_AREA, 0xb8, 0x18, 0xa0, 0x18c, TRANSITION_SHAPE_AREA_12x12, AREA_FORTRESS_OF_WINDS_TOP, ROOM_FORTRESS_OF_WINDS_TOP_MAIN,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_FortressOfWinds_Stalfos[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x78, 0x38, TRANSITION_SHAPE_BORDER_SOUTH, AREA_OUTER_FORTRESS_OF_WINDS, ROOM_OUTER_FORTRESS_OF_WINDS_2F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_FortressOfWinds_EntranceMoleMitts[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x88, 0xb0, TRANSITION_SHAPE_BORDER_NORTH, AREA_OUTER_FORTRESS_OF_WINDS,
      ROOM_OUTER_FORTRESS_OF_WINDS_MOLE_MITTS, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_FortressOfWinds_Main2F[] = {
    { WARP_TYPE_AREA, 0x88, 0xf8, 0x78, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_CENTER_STAIRS_1F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1d8, 0xa8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_OUTER_FORTRESS_OF_WINDS, ROOM_OUTER_FORTRESS_OF_WINDS_2F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_FortressOfWinds_MinishHole[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x68, 0xb0, TRANSITION_SHAPE_BORDER_NORTH, AREA_OUTER_FORTRESS_OF_WINDS, ROOM_OUTER_FORTRESS_OF_WINDS_SMALL_KEY,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_FortressOfWinds_BossKey[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x338, 0x38, TRANSITION_SHAPE_BORDER_SOUTH, AREA_OUTER_FORTRESS_OF_WINDS, ROOM_OUTER_FORTRESS_OF_WINDS_2F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_FortressOfWinds_WestStairs2F[] = {
    { WARP_TYPE_AREA, 0x88, 0x28, 0x68, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_WEST_STAIRS_1F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_FortressOfWinds_EastStairs2F[] = {
    { WARP_TYPE_AREA, 0x88, 0x28, 0x68, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_EAST_STAIRS_1F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x288, 0xa8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_OUTER_FORTRESS_OF_WINDS, ROOM_OUTER_FORTRESS_OF_WINDS_2F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_FortressOfWinds_WestStairs1F[] = {
    { WARP_TYPE_AREA, 0x68, 0x28, 0x88, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_WEST_STAIRS_2F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x128, 0x38, TRANSITION_SHAPE_BORDER_SOUTH, AREA_OUTER_FORTRESS_OF_WINDS,
      ROOM_OUTER_FORTRESS_OF_WINDS_ENTRANCE_HALL, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_FortressOfWinds_CenterStairs1F[] = {
    { WARP_TYPE_AREA, 0x78, 0x28, 0x88, 0x108, TRANSITION_SHAPE_AREA_12x12, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_MAIN_2F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1d8, 0x38, TRANSITION_SHAPE_BORDER_SOUTH, AREA_OUTER_FORTRESS_OF_WINDS,
      ROOM_OUTER_FORTRESS_OF_WINDS_ENTRANCE_HALL, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_FortressOfWinds_EastStairs1F[] = {
    { WARP_TYPE_AREA, 0x68, 0x28, 0x88, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_EAST_STAIRS_2F,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x288, 0x38, TRANSITION_SHAPE_BORDER_SOUTH, AREA_OUTER_FORTRESS_OF_WINDS,
      ROOM_OUTER_FORTRESS_OF_WINDS_ENTRANCE_HALL, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_FortressOfWinds_Wizzrobe[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x78, 0x38, TRANSITION_SHAPE_BORDER_SOUTH, AREA_OUTER_FORTRESS_OF_WINDS,
      ROOM_OUTER_FORTRESS_OF_WINDS_ENTRANCE_HALL, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_FortressOfWinds_HeartPiece[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x338, 0x38, TRANSITION_SHAPE_BORDER_SOUTH, AREA_OUTER_FORTRESS_OF_WINDS,
      ROOM_OUTER_FORTRESS_OF_WINDS_ENTRANCE_HALL, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_FortressOfWinds[] = {
    [ROOM_FORTRESS_OF_WINDS_DOUBLE_EYEGORE] = gExitList_NoExitList,
    [ROOM_FORTRESS_OF_WINDS_BEFORE_MAZAAL] = gExitList_FortressOfWinds_BeforeMazaal,
    [ROOM_FORTRESS_OF_WINDS_EAST_KEY_LEVER] = gExitList_FortressOfWinds_EastKeyLever,
    [ROOM_FORTRESS_OF_WINDS_PIT_PLATFORMS] = gExitList_FortressOfWinds_PitPlatforms,
    [ROOM_FORTRESS_OF_WINDS_WEST_KEY_LEVER] = gExitList_FortressOfWinds_WestKeyLever,
    [ROOM_FORTRESS_OF_WINDS_5] = gExitList_NoExitList,
    [ROOM_FORTRESS_OF_WINDS_6] = gExitList_NoExitList,
    [ROOM_FORTRESS_OF_WINDS_7] = gExitList_NoExitList,
    [ROOM_FORTRESS_OF_WINDS_8] = gExitList_NoExitList,
    [ROOM_FORTRESS_OF_WINDS_9] = gExitList_NoExitList,
    [ROOM_FORTRESS_OF_WINDS_a] = gExitList_NoExitList,
    [ROOM_FORTRESS_OF_WINDS_b] = gExitList_NoExitList,
    [ROOM_FORTRESS_OF_WINDS_c] = gExitList_NoExitList,
    [ROOM_FORTRESS_OF_WINDS_d] = gExitList_NoExitList,
    [ROOM_FORTRESS_OF_WINDS_e] = gExitList_NoExitList,
    [ROOM_FORTRESS_OF_WINDS_f] = gExitList_NoExitList,
    [ROOM_FORTRESS_OF_WINDS_DARKNUT_ROOM] = gExitList_NoExitList,
    [ROOM_FORTRESS_OF_WINDS_ARROW_EYE_BRIDGE] = gExitList_NoExitList,
    [ROOM_FORTRESS_OF_WINDS_NORTH_SPLIT_PATH_PIT] = gExitList_NoExitList,
    [ROOM_FORTRESS_OF_WINDS_WALLMASTER_MINISH_PORTAL] = gExitList_NoExitList,
    [ROOM_FORTRESS_OF_WINDS_PILLAR_CLONE_BUTTONS] = gExitList_NoExitList,
    [ROOM_FORTRESS_OF_WINDS_ROTATING_SPIKE_TRAPS] = gExitList_NoExitList,
    [ROOM_FORTRESS_OF_WINDS_MAZAAL] = gExitList_FortressOfWinds_Mazaal,
    [ROOM_FORTRESS_OF_WINDS_STALFOS] = gExitList_FortressOfWinds_Stalfos,
    [ROOM_FORTRESS_OF_WINDS_ENTRANCE_MOLE_MITTS] = gExitList_FortressOfWinds_EntranceMoleMitts,
    [ROOM_FORTRESS_OF_WINDS_MAIN_2F] = gExitList_FortressOfWinds_Main2F,
    [ROOM_FORTRESS_OF_WINDS_MINISH_HOLE] = gExitList_FortressOfWinds_MinishHole,
    [ROOM_FORTRESS_OF_WINDS_BOSS_KEY] = gExitList_FortressOfWinds_BossKey,
    [ROOM_FORTRESS_OF_WINDS_WEST_STAIRS_2F] = gExitList_FortressOfWinds_WestStairs2F,
    [ROOM_FORTRESS_OF_WINDS_EAST_STAIRS_2F] = gExitList_FortressOfWinds_EastStairs2F,
    [ROOM_FORTRESS_OF_WINDS_1e] = gExitList_NoExitList,
    [ROOM_FORTRESS_OF_WINDS_1f] = gExitList_NoExitList,
    [ROOM_FORTRESS_OF_WINDS_WEST_STAIRS_1F] = gExitList_FortressOfWinds_WestStairs1F,
    [ROOM_FORTRESS_OF_WINDS_CENTER_STAIRS_1F] = gExitList_FortressOfWinds_CenterStairs1F,
    [ROOM_FORTRESS_OF_WINDS_EAST_STAIRS_1F] = gExitList_FortressOfWinds_EastStairs1F,
    [ROOM_FORTRESS_OF_WINDS_WIZZROBE] = gExitList_FortressOfWinds_Wizzrobe,
    [ROOM_FORTRESS_OF_WINDS_HEART_PIECE] = gExitList_FortressOfWinds_HeartPiece,
    [ROOM_FORTRESS_OF_WINDS_25] = gExitList_NoExitList,
    [ROOM_FORTRESS_OF_WINDS_26] = gExitList_NoExitList,
    [ROOM_FORTRESS_OF_WINDS_27] = gExitList_NoExitList,
};

const Transition gExitList_FortressOfWindsTop_Main[] = {
    { WARP_TYPE_AREA, 0xa0, 0x1a0, 0xb8, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_MAZAAL,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_FortressOfWindsTop[] = {
    [ROOM_FORTRESS_OF_WINDS_TOP_MAIN] = gExitList_FortressOfWindsTop_Main,
};

const Transition gExitList_InnerMazaal_Main[] = {
    { WARP_TYPE_AREA, 0x88, 0x11c, 0xb8, 0x5c, TRANSITION_SHAPE_AREA_12x12, AREA_FORTRESS_OF_WINDS, ROOM_FORTRESS_OF_WINDS_MAZAAL,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_InnerMazaal[] = {
    [ROOM_INNER_MAZAAL_MAIN] = gExitList_InnerMazaal_Main,
    [ROOM_INNER_MAZAAL_PHASE_1] = gExitList_InnerMazaal_Main,
};

const Transition gExitList_TempleOfDroplets_WestHole[] = {
    { WARP_TYPE_AREA, 0x58, 0x28, 0x58, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_TEMPLE_OF_DROPLETS, ROOM_TEMPLE_OF_DROPLETS_BOSS_KEY,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TempleOfDroplets_EastHole[] = {
    { WARP_TYPE_AREA, 0xd8, 0x28, 0xd8, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_TEMPLE_OF_DROPLETS, ROOM_TEMPLE_OF_DROPLETS_NORTH_SMALL_KEY,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TempleOfDroplets_HoleToBlueChuchu[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x208, 0xfff, TRANSITION_SHAPE_BORDER_WEST, AREA_TEMPLE_OF_DROPLETS, ROOM_TEMPLE_OF_DROPLETS_ELEMENT,
      1, TRANSITION_TYPE_NORMAL, 0x6, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xc8, 0x28, 0x88, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_TEMPLE_OF_DROPLETS,
      ROOM_TEMPLE_OF_DROPLETS_BLUE_CHU_KEY_LEVER, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TempleOfDroplets_BigBlueChuchu[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0xb8, TRANSITION_SHAPE_BORDER_NORTH, AREA_TEMPLE_OF_DROPLETS, ROOM_TEMPLE_OF_DROPLETS_TO_BLUE_CHU,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TempleOfDroplets_BigBlueChuchuKey[] = {
    { WARP_TYPE_AREA, 0x58, 0x28, 0xc8, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_TEMPLE_OF_DROPLETS,
      ROOM_TEMPLE_OF_DROPLETS_BLUE_CHU_KEY_LEVER, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TempleOfDroplets_BossKey[] = {
    { WARP_TYPE_AREA, 0x58, 0x28, 0x58, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_TEMPLE_OF_DROPLETS, ROOM_TEMPLE_OF_DROPLETS_WEST_HOLE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TempleOfDroplets_NorthSmallKey[] = {
    { WARP_TYPE_AREA, 0xd8, 0x28, 0xd8, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_TEMPLE_OF_DROPLETS, ROOM_TEMPLE_OF_DROPLETS_EAST_HOLE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TempleOfDroplets_BlueChuchuKeyLever[] = {
    { WARP_TYPE_AREA, 0x88, 0x18, 0xc8, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_TEMPLE_OF_DROPLETS,
      ROOM_TEMPLE_OF_DROPLETS_HOLE_TO_BLUE_CHU_KEY, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xc8, 0x18, 0x58, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_TEMPLE_OF_DROPLETS, ROOM_TEMPLE_OF_DROPLETS_BLUE_CHU_KEY,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TempleOfDroplets_Entrance[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x18, TRANSITION_SHAPE_BORDER_SOUTH, AREA_TEMPLE_OF_DROPLETS, ROOM_TEMPLE_OF_DROPLETS_ELEMENT,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TempleOfDroplets_WaterfallNortheast[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x18, 0xfff, TRANSITION_SHAPE_BORDER_EAST, AREA_TEMPLE_OF_DROPLETS, ROOM_TEMPLE_OF_DROPLETS_ELEMENT,
      1, TRANSITION_TYPE_NORMAL, 0x2, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TempleOfDroplets_Element[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xf8, 0xfff, TRANSITION_SHAPE_BORDER_WEST, AREA_TEMPLE_OF_DROPLETS,
      ROOM_TEMPLE_OF_DROPLETS_WATERFALL_NORTHEAST, 1, TRANSITION_TYPE_NORMAL, 0x6, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x8, 0xfff, TRANSITION_SHAPE_BORDER_EAST_NORTH, AREA_TEMPLE_OF_DROPLETS, ROOM_TEMPLE_OF_DROPLETS_ICE_CORNER,
      1, TRANSITION_TYPE_NORMAL, 0x2, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x8, 0xfff, TRANSITION_SHAPE_BORDER_EAST_SOUTH, AREA_TEMPLE_OF_DROPLETS,
      ROOM_TEMPLE_OF_DROPLETS_HOLE_TO_BLUE_CHU_KEY, 1, TRANSITION_TYPE_NORMAL, 0x2, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x178, TRANSITION_SHAPE_BORDER_NORTH, AREA_TEMPLE_OF_DROPLETS, ROOM_TEMPLE_OF_DROPLETS_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x28, TRANSITION_SHAPE_BORDER_SOUTH, AREA_TEMPLE_OF_DROPLETS, ROOM_TEMPLE_OF_DROPLETS_BIG_OCTO,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TempleOfDroplets_IceCorner[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x208, 0xfff, TRANSITION_SHAPE_BORDER_WEST, AREA_TEMPLE_OF_DROPLETS, ROOM_TEMPLE_OF_DROPLETS_ELEMENT,
      1, TRANSITION_TYPE_NORMAL, 0x6, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TempleOfDroplets_BigOcto[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x178, TRANSITION_SHAPE_BORDER_NORTH, AREA_TEMPLE_OF_DROPLETS, ROOM_TEMPLE_OF_DROPLETS_ELEMENT,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TempleOfDroplets_NorthwestStairs[] = {
    { WARP_TYPE_AREA, 0x88, 0x18, 0x88, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_TEMPLE_OF_DROPLETS,
      ROOM_TEMPLE_OF_DROPLETS_BLOCK_CLONE_ICE_BRIDGE, 2, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TempleOfDroplets_ScissorsMiniboss[] = {
    { WARP_TYPE_AREA, 0xc8, 0x18, 0xc8, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_TEMPLE_OF_DROPLETS,
      ROOM_TEMPLE_OF_DROPLETS_STAIRS_TO_SCISSORS_MINIBOSS, 2, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TempleOfDroplets_WaterfallSouthwest[] = {
    { WARP_TYPE_AREA, 0x38, 0x170, 0x38, 0x18, TRANSITION_SHAPE_AREA_12x12, AREA_TEMPLE_OF_DROPLETS, ROOM_TEMPLE_OF_DROPLETS_LILYPAD_B2_WEST,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TempleOfDroplets_ToBigBlueChuchu[] = {
    { WARP_TYPE_AREA, 0x58, 0x58, 0x58, 0x68, TRANSITION_SHAPE_AREA_12x12, AREA_TEMPLE_OF_DROPLETS, ROOM_TEMPLE_OF_DROPLETS_COMPASS,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_TEMPLE_OF_DROPLETS, ROOM_TEMPLE_OF_DROPLETS_BLUE_CHU,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TempleOfDroplets_BlockCloneIceBridge[] = {
    { WARP_TYPE_AREA, 0x88, 0x18, 0x88, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_TEMPLE_OF_DROPLETS, ROOM_TEMPLE_OF_DROPLETS_NORTHWEST_STAIRS,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TempleOfDroplets_StairsToScissorsMiniboss[] = {
    { WARP_TYPE_AREA, 0xc8, 0x18, 0xc8, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_TEMPLE_OF_DROPLETS, ROOM_TEMPLE_OF_DROPLETS_SCISSORS_MINIBOSS,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TempleOfDroplets_LilypadWestB2[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x38, 0x168, TRANSITION_SHAPE_BORDER_NORTH, AREA_TEMPLE_OF_DROPLETS,
      ROOM_TEMPLE_OF_DROPLETS_WEST_WATERFALL_SOUTHWEST, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_TempleOfDroplets_CompassRoom[] = {
    { WARP_TYPE_AREA, 0x58, 0x58, 0x58, 0x68, TRANSITION_SHAPE_AREA_12x12, AREA_TEMPLE_OF_DROPLETS, ROOM_TEMPLE_OF_DROPLETS_TO_BLUE_CHU,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_TempleOfDroplets[] = {
    [ROOM_TEMPLE_OF_DROPLETS_WEST_HOLE] = gExitList_TempleOfDroplets_WestHole,
    [ROOM_TEMPLE_OF_DROPLETS_NORTH_SPLIT_ROOM] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_EAST_HOLE] = gExitList_TempleOfDroplets_EastHole,
    [ROOM_TEMPLE_OF_DROPLETS_ENTRANCE] = gExitList_TempleOfDroplets_Entrance,
    [ROOM_TEMPLE_OF_DROPLETS_NORTHWEST_STAIRS] = gExitList_TempleOfDroplets_NorthwestStairs,
    [ROOM_TEMPLE_OF_DROPLETS_SCISSORS_MINIBOSS] = gExitList_TempleOfDroplets_ScissorsMiniboss,
    [ROOM_TEMPLE_OF_DROPLETS_WATERFALL_NORTHWEST] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_WATERFALL_NORTHEAST] = gExitList_TempleOfDroplets_WaterfallNortheast,
    [ROOM_TEMPLE_OF_DROPLETS_ELEMENT] = gExitList_TempleOfDroplets_Element,
    [ROOM_TEMPLE_OF_DROPLETS_ICE_CORNER] = gExitList_TempleOfDroplets_IceCorner,
    [ROOM_TEMPLE_OF_DROPLETS_ICE_PIT_MAZE] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_HOLE_TO_BLUE_CHU_KEY] = gExitList_TempleOfDroplets_HoleToBlueChuchu,
    [ROOM_TEMPLE_OF_DROPLETS_WEST_WATERFALL_SOUTHEAST] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_WEST_WATERFALL_SOUTHWEST] = gExitList_TempleOfDroplets_WaterfallSouthwest,
    [ROOM_TEMPLE_OF_DROPLETS_BIG_OCTO] = gExitList_TempleOfDroplets_BigOcto,
    [ROOM_TEMPLE_OF_DROPLETS_TO_BLUE_CHU] = gExitList_TempleOfDroplets_ToBigBlueChuchu,
    [ROOM_TEMPLE_OF_DROPLETS_BLUE_CHU] = gExitList_TempleOfDroplets_BigBlueChuchu,
    [ROOM_TEMPLE_OF_DROPLETS_BLUE_CHU_KEY] = gExitList_TempleOfDroplets_BigBlueChuchuKey,
    [ROOM_TEMPLE_OF_DROPLETS_12] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_13] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_14] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_15] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_16] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_17] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_18] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_19] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_1a] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_1b] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_1c] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_1d] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_1e] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_1f] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_BOSS_KEY] = gExitList_TempleOfDroplets_BossKey,
    [ROOM_TEMPLE_OF_DROPLETS_NORTH_SMALL_KEY] = gExitList_TempleOfDroplets_NorthSmallKey,
    [ROOM_TEMPLE_OF_DROPLETS_BLOCK_CLONE_BUTTON_PUZZLE] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_BLOCK_CLONE_PUZZLE] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_BLOCK_CLONE_ICE_BRIDGE] = gExitList_TempleOfDroplets_BlockCloneIceBridge,
    [ROOM_TEMPLE_OF_DROPLETS_STAIRS_TO_SCISSORS_MINIBOSS] = gExitList_TempleOfDroplets_StairsToScissorsMiniboss,
    [ROOM_TEMPLE_OF_DROPLETS_SPIKE_BAR_FLIPPER_ROOM] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_9_LANTERNS] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_LILYPAD_ICE_BLOCKS] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_29] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_MULLDOZERS_FIRE_BARS] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_DARK_MAZE] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_TWIN_MADDERPILLARS] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_AFTER_TWIN_MADDERPILLARS] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_BLUE_CHU_KEY_LEVER] = gExitList_TempleOfDroplets_BlueChuchuKeyLever,
    [ROOM_TEMPLE_OF_DROPLETS_MULLDOZER_KEY] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_BEFORE_TWIN_MADDERPILLARS] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_LILYPAD_B2_WEST] = gExitList_TempleOfDroplets_LilypadWestB2,
    [ROOM_TEMPLE_OF_DROPLETS_COMPASS] = gExitList_TempleOfDroplets_CompassRoom,
    [ROOM_TEMPLE_OF_DROPLETS_DARK_SCISSOR_BEETLES] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_LILYPAD_B2_MIDDLE] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_ICE_MADDERPILLAR] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_FLAMEBAR_BLOCK_PUZZLE] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_37] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_38] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_39] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_3a] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_3b] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_3c] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_3d] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_3e] = gExitList_NoExitList,
    [ROOM_TEMPLE_OF_DROPLETS_3f] = gExitList_NoExitList,
};

#ifdef QUICKSTART
// Retargeted as a QUICKSTART "2-door ? room" pool candidate - both
// real doors now lead back to the Lon Lon Ranch cave-connector ledge
// (0xb8,0x138), same shared return spot every other 2-door pool room
// uses (see game.c: sQuickStart2DoorSmallRoomPool/LargeRoomPool). Real
// startX/startY/shape/warp_type kept as-is - only destination changes.
const Transition gExitList_61_0[] = {
    { WARP_TYPE_AREA, 0x78, 0x58, 0x3fe, 0x3fe, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3fd, 0x3fd, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_61_0[] = {
    { WARP_TYPE_AREA, 0x78, 0x58, 0xa8, 0xd8, TRANSITION_SHAPE_AREA_12x12, AREA_DEEPWOOD_SHRINE, ROOM_DEEPWOOD_SHRINE_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x118, 0x174, TRANSITION_SHAPE_BORDER_SOUTH, AREA_LAKE_HYLIA, ROOM_LAKE_HYLIA_MAIN, 1, TRANSITION_TYPE_INSTANT_MINISH,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition* const gExitLists_61[] = {
    [ROOM_NULL_61_0] = gExitList_61_0,
};

const Transition gExitList_RoyalCrypt_WaterRope[] = {
    TransitionListEnd,
};
const Transition gExitList_RoyalCrypt_Gibdo[] = {
    { WARP_TYPE_AREA, 0xa8, 0x12e, 0x128, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_ROYAL_CRYPT, ROOM_ROYAL_CRYPT_KEY_BLOCK, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_RoyalCrypt_KeyBlock[] = {
    { WARP_TYPE_AREA, 0x128, 0x38, 0xa8, 0x118, TRANSITION_SHAPE_AREA_12x12, AREA_ROYAL_CRYPT, ROOM_ROYAL_CRYPT_GIBDO, 1, TRANSITION_TYPE_NORMAL,
      0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x128, 0x16e, 0x88, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_ROYAL_CRYPT, ROOM_ROYAL_CRYPT_MUSHROOM_PIT,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_RoyalCrypt_MushroomPit[] = {
    { WARP_TYPE_AREA, 0x88, 0x38, 0x128, 0x158, TRANSITION_SHAPE_AREA_12x12, AREA_ROYAL_CRYPT, ROOM_ROYAL_CRYPT_KEY_BLOCK, 1,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_RoyalCrypt_Entrance[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xf0, 0x3c, TRANSITION_SHAPE_BORDER_SOUTH, AREA_ROYAL_VALLEY, ROOM_ROYAL_VALLEY_MAIN, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_RoyalCrypt[] = {
    [ROOM_ROYAL_CRYPT_0] = gExitList_NoExitList,
    [ROOM_ROYAL_CRYPT_WATER_ROPE] = gExitList_RoyalCrypt_WaterRope,
    [ROOM_ROYAL_CRYPT_GIBDO] = gExitList_RoyalCrypt_Gibdo,
    [ROOM_ROYAL_CRYPT_3] = gExitList_NoExitList,
    [ROOM_ROYAL_CRYPT_KEY_BLOCK] = gExitList_RoyalCrypt_KeyBlock,
    [ROOM_ROYAL_CRYPT_5] = gExitList_NoExitList,
    [ROOM_ROYAL_CRYPT_6] = gExitList_NoExitList,
    [ROOM_ROYAL_CRYPT_MUSHROOM_PIT] = gExitList_RoyalCrypt_MushroomPit,
    [ROOM_ROYAL_CRYPT_ENTRANCE] = gExitList_RoyalCrypt_Entrance,
};

const Transition gExitList_PalaceOfWinds_GyorgTornado[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x18, TRANSITION_SHAPE_BORDER_SOUTH, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_GYORG_BOSS_DOOR,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_PalaceOfWinds_GyorgBossDoor[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x1c8, TRANSITION_SHAPE_BORDER_NORTH, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_GYORG_TORNADO,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_PalaceOfWinds_BallAndChainSoldiers[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x18, TRANSITION_SHAPE_BORDER_SOUTH, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_HOLE_TO_DARKNUT,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_PalaceOfWinds_BombarossaPath[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x18, TRANSITION_SHAPE_BORDER_SOUTH, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_TO_BOMBAROSSA_PATH,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_PalaceOfWinds_HoleToDarknut[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x128, TRANSITION_SHAPE_BORDER_NORTH, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_BALL_AND_CHAIN_SOLDIERS,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_PalaceOfWinds_ToBombarossaPath[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x88, TRANSITION_SHAPE_BORDER_NORTH, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_BOMBAROSSA_PATH,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x18, 0xfff, TRANSITION_SHAPE_BORDER_EAST, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_BOMB_WALL_OUTSIDE,
      1, TRANSITION_TYPE_NORMAL, 0x2, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_PalaceOfWinds_BombWallInside[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x18, 0xfff, TRANSITION_SHAPE_BORDER_EAST, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_BOMB_WALL_OUTSIDE,
      1, TRANSITION_TYPE_NORMAL, 0x2, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x38, 0x38, 0x218, 0xe8, TRANSITION_SHAPE_AREA_12x12, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_RED_WARP_HALL,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_PalaceOfWinds_BombWallOutside[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xc8, 0xfff, TRANSITION_SHAPE_BORDER_WEST_NORTH, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_TO_BOMBAROSSA_PATH,
      1, TRANSITION_TYPE_NORMAL, 0x6, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xc8, 0xfff, TRANSITION_SHAPE_BORDER_WEST_SOUTH, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_BOMB_WALL_INSIDE,
      1, TRANSITION_TYPE_NORMAL, 0x6, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_PalaceOfWinds_BlockMazeToBossDoor[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x18, TRANSITION_SHAPE_BORDER_SOUTH, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_RED_WARP_HALL,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_PalaceOfWinds_HeartPieceBridge[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x18, TRANSITION_SHAPE_BORDER_SOUTH, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_RED_WARP_HALL,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_PalaceOfWinds_RedWarpHall[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x88, TRANSITION_SHAPE_BORDER_NORTH_WEST, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_HEART_PIECE_BRIDGE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x1c8, TRANSITION_SHAPE_BORDER_NORTH_EAST, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_BLOCK_MAZE_TO_BOSS_DOOR,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xb8, 0xd8, 0xb8, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_PALACE_OF_WINDS,
      ROOM_PALACE_OF_WINDS_STAIRS_AFTER_FLOORMASTER, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x218, 0xd8, 0x38, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_BOMB_WALL_INSIDE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_PalaceOfWinds_PitCornerAfterKey[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xd8, 0xfff, TRANSITION_SHAPE_BORDER_WEST, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_KEY_ARROW_BUTTON,
      1, TRANSITION_TYPE_NORMAL, 0x6, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_PalaceOfWinds_PotPush[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x78, TRANSITION_SHAPE_BORDER_NORTH_WEST, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_KEY_ARROW_BUTTON,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_PalaceOfWinds_StairsAfterFloormaster[] = {
    { WARP_TYPE_AREA, 0xb8, 0x38, 0xb8, 0xe8, TRANSITION_SHAPE_AREA_12x12, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_RED_WARP_HALL,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_PalaceOfWinds_KeyArrowButton[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x10, 0xfff, TRANSITION_SHAPE_BORDER_EAST, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_PIT_CORNER_AFTER_KEY,
      1, TRANSITION_TYPE_NORMAL, 0x2, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x28, TRANSITION_SHAPE_BORDER_SOUTH, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_POT_PUSH,
      1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x38, 0x38, 0x38, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_GIBDO_STAIRS,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_PalaceOfWinds_PeahatSwitch[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x88, TRANSITION_SHAPE_BORDER_NORTH, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_TO_PEAHAT_SWITCH,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_PalaceOfWinds_WhirlwindBombarossa[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x88, TRANSITION_SHAPE_BORDER_NORTH, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_GIBDO_STAIRS,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_PalaceOfWinds_ToPeahatSwitch[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x18, TRANSITION_SHAPE_BORDER_SOUTH, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_PEAHAT_SWITCH,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xb8, 0x38, 0xb8, 0xe8, TRANSITION_SHAPE_AREA_12x12, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_DARK_COMPASS_HALL,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_PalaceOfWinds_GibdoStairs[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xfff, 0x18, TRANSITION_SHAPE_BORDER_SOUTH, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_WHIRLWIND_BOMBAROSSA,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x38, 0x38, 0x38, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_KEY_ARROW_BUTTON,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_PalaceOfWinds_BridgeAfterDarknut[] = {
    { WARP_TYPE_AREA, 0x78, 0x18, 0x168, 0x118, TRANSITION_SHAPE_AREA_12x12, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_DARK_COMPASS_HALL,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_PalaceOfWinds_DarkCompassHall[] = {
    { WARP_TYPE_AREA, 0x168, 0x130, 0x78, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_BRIDGE_AFTER_DARKNUT,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xb8, 0xd8, 0xb8, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_PALACE_OF_WINDS, ROOM_PALACE_OF_WINDS_TO_PEAHAT_SWITCH,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_PalaceOfWinds[] = {
    [ROOM_PALACE_OF_WINDS_GYORG_TORNADO] = gExitList_PalaceOfWinds_GyorgTornado,
    [ROOM_PALACE_OF_WINDS_BOSS_KEY] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_BEFORE_BALL_AND_CHAIN_SOLDIERS] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_GYORG_BOSS_DOOR] = gExitList_PalaceOfWinds_GyorgBossDoor,
    [ROOM_PALACE_OF_WINDS_EAST_CHEST_FROM_GYORG_BOSS_DOOR] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_MOBLIN_AND_WIZZROBE_FIGHT] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_FOUR_BUTTON_STALFOS] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_FAN_AND_KEY_TO_BOSS_KEY] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_BALL_AND_CHAIN_SOLDIERS] = gExitList_PalaceOfWinds_BallAndChainSoldiers,
    [ROOM_PALACE_OF_WINDS_BOMBAROSSA_PATH] = gExitList_PalaceOfWinds_BombarossaPath,
    [ROOM_PALACE_OF_WINDS_HOLE_TO_DARKNUT] = gExitList_PalaceOfWinds_HoleToDarknut,
    [ROOM_PALACE_OF_WINDS_TO_BOMBAROSSA_PATH] = gExitList_PalaceOfWinds_ToBombarossaPath,
    [ROOM_PALACE_OF_WINDS_DARKNUT_MINIBOSS] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_BOMB_WALL_INSIDE] = gExitList_PalaceOfWinds_BombWallInside,
    [ROOM_PALACE_OF_WINDS_BOMB_WALL_OUTSIDE] = gExitList_PalaceOfWinds_BombWallOutside,
    [ROOM_PALACE_OF_WINDS_CLOUD_JUMPS] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_BLOCK_MAZE_TO_BOSS_DOOR] = gExitList_PalaceOfWinds_BlockMazeToBossDoor,
    [ROOM_PALACE_OF_WINDS_CRACKED_FLOOR_LAKITU] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_HEART_PIECE_BRIDGE] = gExitList_PalaceOfWinds_HeartPieceBridge,
    [ROOM_PALACE_OF_WINDS_FAN_BRIDGE] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_TO_FAN_BRIDGE] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_RED_WARP_HALL] = gExitList_PalaceOfWinds_RedWarpHall,
    [ROOM_PALACE_OF_WINDS_PLATFORM_CLONE_RIDE] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_PIT_CORNER_AFTER_KEY] = gExitList_PalaceOfWinds_PitCornerAfterKey,
    [ROOM_PALACE_OF_WINDS_PLATFORM_CROW_RIDE] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_GRATE_PLATFORM_RIDE] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_POT_PUSH] = gExitList_PalaceOfWinds_PotPush,
    [ROOM_PALACE_OF_WINDS_FLOORMASTER_LEVER] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_MAP] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_CORNER_TO_MAP] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_STAIRS_AFTER_FLOORMASTER] = gExitList_PalaceOfWinds_StairsAfterFloormaster,
    [ROOM_PALACE_OF_WINDS_HOLE_TO_KINSTONE_WIZZROBE] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_KEY_ARROW_BUTTON] = gExitList_PalaceOfWinds_KeyArrowButton,
    [ROOM_PALACE_OF_WINDS_GRATES_TO_3F] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_SPINY_FIGHT] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_PEAHAT_SWITCH] = gExitList_PalaceOfWinds_PeahatSwitch,
    [ROOM_PALACE_OF_WINDS_WHIRLWIND_BOMBAROSSA] = gExitList_PalaceOfWinds_WhirlwindBombarossa,
    [ROOM_PALACE_OF_WINDS_DOOR_TO_STALFOS_FIREBAR] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_STALFOS_FIREBAR_HOLE] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_SHORTCUT_DOOR_BUTTONS] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_TO_PEAHAT_SWITCH] = gExitList_PalaceOfWinds_ToPeahatSwitch,
    [ROOM_PALACE_OF_WINDS_KINSTONE_WIZZROBE_FIGHT] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_GIBDO_STAIRS] = gExitList_PalaceOfWinds_GibdoStairs,
    [ROOM_PALACE_OF_WINDS_SPIKE_BAR_SMALL_KEY] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_ROC_CAPE] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_FIRE_BAR_GRATES] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_PLATFORM_RIDE_BOMBAROSSAS] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_BRIDGE_AFTER_DARKNUT] = gExitList_PalaceOfWinds_BridgeAfterDarknut,
    [ROOM_PALACE_OF_WINDS_BRIDGE_SWITCHES_CLONE_BLOCK] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_ENTRANCE_ROOM] = gExitList_NoExitList,
    [ROOM_PALACE_OF_WINDS_DARK_COMPASS_HALL] = gExitList_PalaceOfWinds_DarkCompassHall,
    [ROOM_PALACE_OF_WINDS_33] = gExitList_NoExitList,
};

const Transition gExitList_Unused1[] = {
    TransitionListEnd,
};

const Transition gExitList_DarkHyruleCastle_1FEntrance[] = {
    { WARP_TYPE_AREA, 0x108, 0xd8, 0x108, 0xe8, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_B1_MAP,
      2, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x228, 0xd8, 0x228, 0xe8, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_B1_MAP,
      2, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x198, 0x220, 0x1f8, 0x38, TRANSITION_SHAPE_AREA_28x12, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_3FTopLeftTower[] = {
    { WARP_TYPE_AREA, 0xa8, 0x38, 0x68, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_2F_TOP_LEFT_TOWER,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_3FTopRightTower[] = {
    { WARP_TYPE_AREA, 0xa8, 0x38, 0x68, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE,
      ROOM_DARK_HYRULE_CASTLE_2F_TOP_RIGHT_TOWER, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_3FBottomLeftTower[] = {
    { WARP_TYPE_AREA, 0xa8, 0x38, 0x68, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE,
      ROOM_DARK_HYRULE_CASTLE_2F_BOTTOM_LEFT_TOWER, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_3FBottomRightTower[] = {
    { WARP_TYPE_AREA, 0xa8, 0x38, 0x68, 0x118, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE,
      ROOM_DARK_HYRULE_CASTLE_2F_BOTTOM_RIGHT_TOWER, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_3FKeatonHallToVaati[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xa8, 0xe8, TRANSITION_SHAPE_BORDER_NORTH, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_3F_TRIPLE_DARKNUT,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xa8, 0x190, 0x88, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE_BRIDGE,
      ROOM_DARK_HYRULE_CASTLE_BRIDGE_MAIN, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#ifdef QUICKSTART
// Retargeted as a QUICKSTART "2-door ? room" pool candidate - both
// real doors now lead back to the Lon Lon Ranch cave-connector ledge
// (0xb8,0x138), same shared return spot every other 2-door pool room
// uses (see game.c: sQuickStart2DoorSmallRoomPool/LargeRoomPool). Real
// startX/startY/shape/warp_type kept as-is - only destination changes.
const Transition gExitList_DarkHyruleCastle_3FTripleDarknut[] = {
    { WARP_TYPE_AREA, 0xa8, 0x28, 0x3fe, 0x3fe, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3fd, 0x3fd, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_DarkHyruleCastle_3FTripleDarknut[] = {
    { WARP_TYPE_AREA, 0xa8, 0x28, 0x78, 0x168, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE_OUTSIDE,
      ROOM_DARK_HYRULE_CASTLE_OUTSIDE_ZELDA_STATUE_PLATFORM, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xb8, 0x18, TRANSITION_SHAPE_BORDER_SOUTH, AREA_DARK_HYRULE_CASTLE,
      ROOM_DARK_HYRULE_CASTLE_3F_KEATON_HALL_TO_VAATI, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition gExitList_DarkHyruleCastle_2FTopLeftTower[] = {
    { WARP_TYPE_AREA, 0x68, 0x38, 0xa8, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_3F_TOP_LEFT_TOWER,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xa8, 0x38, 0x68, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_1F_TOP_LEFT_TOWER,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x88, 0xc0, 0x88, 0xd8, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE_OUTSIDE,
      ROOM_DARK_HYRULE_CASTLE_OUTSIDE_NORTHWEST, 2, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_2FTopRightTower[] = {
    { WARP_TYPE_AREA, 0x68, 0x38, 0xa8, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE,
      ROOM_DARK_HYRULE_CASTLE_3F_TOP_RIGHT_TOWER, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xa8, 0x38, 0x68, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE,
      ROOM_DARK_HYRULE_CASTLE_1F_TOP_RIGHT_TOWER, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x88, 0xc0, 0x88, 0xd8, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE_OUTSIDE,
      ROOM_DARK_HYRULE_CASTLE_OUTSIDE_NORTHEAST, 2, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_2FRight[] = {
    { WARP_TYPE_AREA, 0xf0, 0x5c, 0x44, 0x5e, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE_OUTSIDE,
      ROOM_DARK_HYRULE_CASTLE_OUTSIDE_EAST, 2, TRANSITION_TYPE_NORMAL, 0x2, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xf0, 0xec, 0x44, 0xee, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE_OUTSIDE,
      ROOM_DARK_HYRULE_CASTLE_OUTSIDE_EAST, 2, TRANSITION_TYPE_NORMAL, 0x2, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_2FBossDoor[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x88, 0x118, TRANSITION_SHAPE_BORDER_NORTH, AREA_DARK_HYRULE_CASTLE_BRIDGE, ROOM_DARK_HYRULE_CASTLE_BRIDGE_MAIN,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_2FEntrance[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x198, 0xd8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_DARK_HYRULE_CASTLE_OUTSIDE,
      ROOM_DARK_HYRULE_CASTLE_OUTSIDE_SOUTH, 2, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_2FBottomLeftTower[] = {
    { WARP_TYPE_AREA, 0x68, 0x38, 0xa8, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE,
      ROOM_DARK_HYRULE_CASTLE_3F_BOTTOM_LEFT_TOWER, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xa8, 0x38, 0x68, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE,
      ROOM_DARK_HYRULE_CASTLE_1F_BOTTOM_LEFT_TOWER, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x88, 0xc0, 0x78, 0xe8, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE_OUTSIDE,
      ROOM_DARK_HYRULE_CASTLE_OUTSIDE_SOUTHWEST, 2, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_2FBottomLeftGhini[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x88, 0xd8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_DARK_HYRULE_CASTLE_OUTSIDE,
      ROOM_DARK_HYRULE_CASTLE_OUTSIDE_SOUTH, 2, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_B1Entrance[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x88, 0x188, TRANSITION_SHAPE_BORDER_NORTH, AREA_DARK_HYRULE_CASTLE_OUTSIDE,
      ROOM_DARK_HYRULE_CASTLE_OUTSIDE_GARDEN, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_2FBottomRightTower[] = {
    { WARP_TYPE_AREA, 0x68, 0x108, 0xa8, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE,
      ROOM_DARK_HYRULE_CASTLE_3F_BOTTOM_RIGHT_TOWER, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0xa8, 0x108, 0x68, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE,
      ROOM_DARK_HYRULE_CASTLE_1F_BOTTOM_RIGHT_TOWER, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x88, 0x190, 0x88, 0x288, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE_OUTSIDE,
      ROOM_DARK_HYRULE_CASTLE_OUTSIDE_SOUTHEAST, 2, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_1FTopLeftTower[] = {
    { WARP_TYPE_AREA, 0x68, 0x38, 0xa8, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_2F_TOP_LEFT_TOWER,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_1FThroneRoom[] = {
    { WARP_TYPE_AREA, 0x88, 0x48, 0x88, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_B1_BELOW_THRONE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_1FCompass[] = {
    { WARP_TYPE_AREA, 0xb8, 0x38, 0xb8, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_B1_BELOW_COMPASS,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_1FTopRightTower[] = {
    { WARP_TYPE_AREA, 0x68, 0x38, 0xa8, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE,
      ROOM_DARK_HYRULE_CASTLE_2F_TOP_RIGHT_TOWER, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_1FBeforeThrone[] = {
    { WARP_TYPE_AREA, 0x88, 0x68, 0x88, 0x78, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_B1_BEFORE_THRONE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_1FBottomLeftTower[] = {
    { WARP_TYPE_AREA, 0x68, 0x38, 0xa8, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE,
      ROOM_DARK_HYRULE_CASTLE_2F_BOTTOM_LEFT_TOWER, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_1FBottomRightTower[] = {
    { WARP_TYPE_AREA, 0x68, 0x38, 0xa8, 0x118, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE,
      ROOM_DARK_HYRULE_CASTLE_2F_BOTTOM_RIGHT_TOWER, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_B1BelowThrone[] = {
    { WARP_TYPE_AREA, 0x88, 0x48, 0x88, 0x58, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_1F_THRONE_ROOM,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_B1BelowCompass[] = {
    { WARP_TYPE_AREA, 0xb8, 0x38, 0xb8, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_1F_COMPASS,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_B1BeforeThrone[] = {
    { WARP_TYPE_AREA, 0x88, 0x68, 0x88, 0x58, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_1F_BEFORE_THRONE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_B1ToPrison[] = {
    { WARP_TYPE_AREA, 0x58, 0x28, 0x58, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_B2_TO_PRISON,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_B1Map[] = {
    { WARP_TYPE_AREA, 0x108, 0xd8, 0x108, 0xe8, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_1F_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x228, 0xd8, 0x228, 0xe8, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_1F_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastle_B2ToPrison[] = {
    { WARP_TYPE_AREA, 0x58, 0x18, 0x58, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_B1_TO_PRISON,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_DarkHyruleCastle[] = {
    [ROOM_DARK_HYRULE_CASTLE_1F_ENTRANCE] = gExitList_DarkHyruleCastle_1FEntrance,
    [ROOM_DARK_HYRULE_CASTLE_3F_TOP_LEFT_TOWER] = gExitList_DarkHyruleCastle_3FTopLeftTower,
    [ROOM_DARK_HYRULE_CASTLE_3F_TOP_RIGHT_TOWER] = gExitList_DarkHyruleCastle_3FTopRightTower,
    [ROOM_DARK_HYRULE_CASTLE_3F_BOTTOM_LEFT_TOWER] = gExitList_DarkHyruleCastle_3FBottomLeftTower,
    [ROOM_DARK_HYRULE_CASTLE_3F_BOTTOM_RIGHT_TOWER] = gExitList_DarkHyruleCastle_3FBottomRightTower,
    [ROOM_DARK_HYRULE_CASTLE_3F_KEATON_HALL_TO_VAATI] = gExitList_DarkHyruleCastle_3FKeatonHallToVaati,
    [ROOM_DARK_HYRULE_CASTLE_3F_TRIPLE_DARKNUT] = gExitList_DarkHyruleCastle_3FTripleDarknut,
    [ROOM_DARK_HYRULE_CASTLE_2F_TOP_LEFT_TOWER] = gExitList_DarkHyruleCastle_2FTopLeftTower,
    [ROOM_DARK_HYRULE_CASTLE_2F_TOP_LEFT_CORNER] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_2F_BOSS_KEY] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_2F_BLUE_WARP] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_2F_TOP_RIGHT_CORNER_GHINI] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_2F_TOP_RIGHT_CORNER_TORCHES] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_2F_TOP_RIGHT_TOWER] = gExitList_DarkHyruleCastle_2FTopRightTower,
    [ROOM_DARK_HYRULE_CASTLE_2F_TOP_LEFT_DARKNUT] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_2F_SPARKS] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_2F_TOP_RIGHT_DARKNUTS] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_2F_LEFT] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_2F_RIGHT] = gExitList_DarkHyruleCastle_2FRight,
    [ROOM_DARK_HYRULE_CASTLE_2F_BOTTOM_LEFT_DARKNUTS] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_2F_BOSS_DOOR] = gExitList_DarkHyruleCastle_2FBossDoor,
    [ROOM_DARK_HYRULE_CASTLE_2F_BOTTOM_RIGHT_DARKNUT] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_2F_BOTTOM_LEFT_CORNER_PUZZLE] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_2F_ENTRANCE] = gExitList_DarkHyruleCastle_2FEntrance,
    [ROOM_DARK_HYRULE_CASTLE_2F_BOTTOM_RIGHT_CORNER] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_2F_BOTTOM_LEFT_TOWER] = gExitList_DarkHyruleCastle_2FBottomLeftTower,
    [ROOM_DARK_HYRULE_CASTLE_2F_BOTTOM_LEFT_GHINI] = gExitList_DarkHyruleCastle_2FBottomLeftGhini,
    [ROOM_DARK_HYRULE_CASTLE_1b] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_B1_ENTRANCE] = gExitList_DarkHyruleCastle_B1Entrance,
    [ROOM_DARK_HYRULE_CASTLE_2F_BOTTOM_RIGHT_TOWER] = gExitList_DarkHyruleCastle_2FBottomRightTower,
    [ROOM_DARK_HYRULE_CASTLE_1F_TOP_LEFT_TOWER] = gExitList_DarkHyruleCastle_1FTopLeftTower,
    [ROOM_DARK_HYRULE_CASTLE_1F_THRONE_ROOM] = gExitList_DarkHyruleCastle_1FThroneRoom,
    [ROOM_DARK_HYRULE_CASTLE_1F_COMPASS] = gExitList_DarkHyruleCastle_1FCompass,
    [ROOM_DARK_HYRULE_CASTLE_1F_TOP_RIGHT_TOWER] = gExitList_DarkHyruleCastle_1FTopRightTower,
    [ROOM_DARK_HYRULE_CASTLE_1F_BEFORE_THRONE] = gExitList_DarkHyruleCastle_1FBeforeThrone,
    [ROOM_DARK_HYRULE_CASTLE_1F_LOOP_TOP_LEFT] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_1F_LOOP_TOP] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_1F_LOOP_TOP_RIGHT] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_1F_LOOP_LEFT] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_1F_LOOP_RIGHT] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_1F_LOOP_BOTTOM_LEFT] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_1F_LOOP_BOTTOM] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_1F_LOOP_BOTTOM_RIGHT] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_1F_BOTTOM_LEFT_TOWER] = gExitList_DarkHyruleCastle_1FBottomLeftTower,
    [ROOM_DARK_HYRULE_CASTLE_1F_BOTTOM_RIGHT_TOWER] = gExitList_DarkHyruleCastle_1FBottomRightTower,
    [ROOM_DARK_HYRULE_CASTLE_B1_BELOW_THRONE] = gExitList_DarkHyruleCastle_B1BelowThrone,
    [ROOM_DARK_HYRULE_CASTLE_B1_BELOW_COMPASS] = gExitList_DarkHyruleCastle_B1BelowCompass,
    [ROOM_DARK_HYRULE_CASTLE_B1_BEFORE_THRONE] = gExitList_DarkHyruleCastle_B1BeforeThrone,
    [ROOM_DARK_HYRULE_CASTLE_B1_TO_PRISON] = gExitList_DarkHyruleCastle_B1ToPrison,
    [ROOM_DARK_HYRULE_CASTLE_B1_BOMB_WALL] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_B1_KEATONS] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_B1_TO_PRISON_FIREBAR] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_B1_CANNONS] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_B1_LEFT] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_B1_RIGHT] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_B1_MAP] = gExitList_DarkHyruleCastle_B1Map,
    [ROOM_DARK_HYRULE_CASTLE_B2_TO_PRISON] = gExitList_DarkHyruleCastle_B2ToPrison,
    [ROOM_DARK_HYRULE_CASTLE_B2_PRISON] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_B2_DROPDOWN] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_3b] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_3c] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_3d] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_3e] = gExitList_NoExitList,
    [ROOM_DARK_HYRULE_CASTLE_3f] = gExitList_NoExitList,
};

const Transition gExitList_Unused2[] = {
    TransitionListEnd,
};

const Transition gExitList_DarkHyruleCastleOutside_ZeldaStatuePlatform[] = {
    { WARP_TYPE_AREA, 0x78, 0x178, 0xa8, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE,
      ROOM_DARK_HYRULE_CASTLE_3F_TRIPLE_DARKNUT, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastleOutside_Garden[] = {
    { WARP_TYPE_AREA, 0x88, 0x38, 0xc8, 0x1e8, TRANSITION_SHAPE_AREA_12x12, AREA_SANCTUARY, ROOM_SANCTUARY_HALL, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x88, 0x18, TRANSITION_SHAPE_BORDER_SOUTH, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_B1_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastleOutside_OutsideNorthwest[] = {
    { WARP_TYPE_AREA, 0x88, 0xc8, 0x88, 0xa8, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_2F_TOP_LEFT_TOWER,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastleOutside_OutsideNortheast[] = {
    { WARP_TYPE_AREA, 0x88, 0xc8, 0x88, 0xb0, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE,
      ROOM_DARK_HYRULE_CASTLE_2F_TOP_RIGHT_TOWER, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastleOutside_OutsideEast[] = {
    { WARP_TYPE_AREA, 0x38, 0x5c, 0xde, 0x5e, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_2F_RIGHT,
      1, TRANSITION_TYPE_NORMAL, 0x6, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x38, 0xec, 0xde, 0xee, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_2F_RIGHT,
      1, TRANSITION_TYPE_NORMAL, 0x6, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastleOutside_OutsideSouthwest[] = {
    { WARP_TYPE_AREA, 0x78, 0xd8, 0x88, 0xb0, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE,
      ROOM_DARK_HYRULE_CASTLE_2F_BOTTOM_LEFT_TOWER, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastleOutside_OutsideSouth[] = {
    { WARP_TYPE_AREA, 0x198, 0xc8, 0x88, 0x170, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_2F_ENTRANCE,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x88, 0xc8, 0x88, 0xa0, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE,
      ROOM_DARK_HYRULE_CASTLE_2F_BOTTOM_LEFT_GHINI, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_DarkHyruleCastleOutside_OutsideSoutheast[] = {
    { WARP_TYPE_AREA, 0x88, 0x278, 0x88, 0x178, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE,
      ROOM_DARK_HYRULE_CASTLE_2F_BOTTOM_RIGHT_TOWER, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_DarkHyruleCastleOutside[] = {
    [ROOM_DARK_HYRULE_CASTLE_OUTSIDE_ZELDA_STATUE_PLATFORM] = gExitList_DarkHyruleCastleOutside_ZeldaStatuePlatform,
    [ROOM_DARK_HYRULE_CASTLE_OUTSIDE_GARDEN] = gExitList_DarkHyruleCastleOutside_Garden,
    [ROOM_DARK_HYRULE_CASTLE_OUTSIDE_NORTHWEST] = gExitList_DarkHyruleCastleOutside_OutsideNorthwest,
    [ROOM_DARK_HYRULE_CASTLE_OUTSIDE_NORTHEAST] = gExitList_DarkHyruleCastleOutside_OutsideNortheast,
    [ROOM_DARK_HYRULE_CASTLE_OUTSIDE_EAST] = gExitList_DarkHyruleCastleOutside_OutsideEast,
    [ROOM_DARK_HYRULE_CASTLE_OUTSIDE_SOUTHWEST] = gExitList_DarkHyruleCastleOutside_OutsideSouthwest,
    [ROOM_DARK_HYRULE_CASTLE_OUTSIDE_SOUTH] = gExitList_DarkHyruleCastleOutside_OutsideSouth,
    [ROOM_DARK_HYRULE_CASTLE_OUTSIDE_SOUTHEAST] = gExitList_DarkHyruleCastleOutside_OutsideSoutheast,
};

const Transition gExitList_VaatisArms_First[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xb0, 0x88, TRANSITION_SHAPE_BORDER_SOUTH, AREA_VAATI_3, ROOM_VAATI_3_0, 1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0,
      0x0 },
    TransitionListEnd,
};
const Transition gExitList_VaatisArms_Second[] = {
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xb0, 0x88, TRANSITION_SHAPE_BORDER_SOUTH, AREA_VAATI_3, ROOM_VAATI_3_0, 1, TRANSITION_TYPE_INSTANT_MINISH, 0x4, 0x0, 0x0,
      0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_VaatisArms[] = {
    [ROOM_VAATIS_ARMS_FIRST] = gExitList_VaatisArms_First,
    [ROOM_VAATIS_ARMS_SECOND] = gExitList_VaatisArms_Second,
};

#ifdef QUICKSTART
// Retargeted as a QUICKSTART "2-door ? room" pool candidate - both
// real doors now lead back to the Lon Lon Ranch cave-connector ledge
// (0xb8,0x138), same shared return spot every other 2-door pool room
// uses (see game.c: sQuickStart2DoorSmallRoomPool/LargeRoomPool). Real
// startX/startY/shape/warp_type kept as-is - only destination changes.
const Transition gExitList_DarkHyruleCastleBridge_Main[] = {
    { WARP_TYPE_AREA, 0x88, 0x18, 0x3fe, 0x3fe, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3fd, 0x3fd, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_DarkHyruleCastleBridge_Main[] = {
    { WARP_TYPE_AREA, 0x88, 0x18, 0xa8, 0x178, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE,
      ROOM_DARK_HYRULE_CASTLE_3F_KEATON_HALL_TO_VAATI, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x88, 0x28, TRANSITION_SHAPE_BORDER_SOUTH, AREA_DARK_HYRULE_CASTLE, ROOM_DARK_HYRULE_CASTLE_2F_BOSS_DOOR,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition* const gExitLists_DarkHyruleCastleBridge[] = {
    [ROOM_DARK_HYRULE_CASTLE_BRIDGE_MAIN] = gExitList_DarkHyruleCastleBridge_Main,
};

const Transition gExitList_HyruleCastle_0[] = {
    { WARP_TYPE_AREA, 0x48, 0xd8, 0x88, 0x288, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_CASTLE, ROOM_HYRULE_CASTLE_3, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x1f8, 0x38, TRANSITION_SHAPE_BORDER_SOUTH, AREA_CASTLE_GARDEN, ROOM_CASTLE_GARDEN_MAIN, 1,
      TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HyruleCastle_1[] = {
    { WARP_TYPE_AREA, 0x58, 0x28, 0x68, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_CASTLE, ROOM_HYRULE_CASTLE_3, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x198, 0x28, 0x1c8, 0x28, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_CASTLE, ROOM_HYRULE_CASTLE_3, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_HyruleCastle_3[] = {
    { WARP_TYPE_AREA, 0x68, 0x18, 0x58, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_CASTLE, ROOM_HYRULE_CASTLE_1, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x1c8, 0x18, 0x198, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_CASTLE, ROOM_HYRULE_CASTLE_1, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x88, 0x278, 0x48, 0xe8, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_CASTLE, ROOM_HYRULE_CASTLE_0, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    { WARP_TYPE_AREA, 0x118, 0x1c8, 0x88, 0x180, TRANSITION_SHAPE_AREA_12x12, AREA_SANCTUARY_ENTRANCE, ROOM_SANCTUARY_ENTRANCE_MAIN,
      1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0xd2, 0x5c, TRANSITION_SHAPE_BORDER_WEST, AREA_HYRULE_CASTLE_CELLAR, ROOM_HYRULE_CASTLE_CELLAR_1,
      1, TRANSITION_TYPE_NORMAL, 0x6, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_HyruleCastle[] = {
    [ROOM_HYRULE_CASTLE_0] = gExitList_HyruleCastle_0,
    [ROOM_HYRULE_CASTLE_1] = gExitList_HyruleCastle_1,
    [ROOM_HYRULE_CASTLE_2] = gExitList_NoExitList,
    [ROOM_HYRULE_CASTLE_3] = gExitList_HyruleCastle_3,
    [ROOM_HYRULE_CASTLE_4] = gExitList_NoExitList,
    [ROOM_HYRULE_CASTLE_5] = gExitList_NoExitList,
    [ROOM_HYRULE_CASTLE_6] = gExitList_NoExitList,
    [ROOM_HYRULE_CASTLE_7] = gExitList_NoExitList,
};

#ifdef QUICKSTART
// Retargeted as a QUICKSTART "2-door ? room" pool candidate - both
// real doors now lead back to the Lon Lon Ranch cave-connector ledge
// (0xb8,0x138), same shared return spot every other 2-door pool room
// uses (see game.c: sQuickStart2DoorSmallRoomPool/LargeRoomPool). Real
// startX/startY/shape/warp_type kept as-is - only destination changes.
const Transition gExitList_SanctuaryEntrance_Main[] = {
    { WARP_TYPE_AREA, 0x88, 0x38, 0x3fe, 0x3fe, TRANSITION_SHAPE_AREA_12x12, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x3fd, 0x3fd, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_FIELD, ROOM_HYRULE_FIELD_LON_LON_RANCH, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#else
const Transition gExitList_SanctuaryEntrance_Main[] = {
    { WARP_TYPE_AREA, 0x88, 0x38, 0xc8, 0x1e8, TRANSITION_SHAPE_AREA_12x12, AREA_SANCTUARY, ROOM_SANCTUARY_HALL, 1, TRANSITION_TYPE_NORMAL, 0x0,
      0x0, 0x0, 0x0 },
    { WARP_TYPE_BORDER, 0x0, 0x0, 0x118, 0x1e8, TRANSITION_SHAPE_BORDER_SOUTH, AREA_HYRULE_CASTLE, ROOM_HYRULE_CASTLE_3, 1, TRANSITION_TYPE_NORMAL,
      0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
#endif
const Transition* const gExitLists_SanctuaryEntrance[] = {
    [ROOM_SANCTUARY_ENTRANCE_MAIN] = gExitList_SanctuaryEntrance_Main,
};

const Transition gExitList_Sanctuary_Hall[] = {
    { WARP_TYPE_AREA, 0xc8, 0x1fc, 0x88, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_SANCTUARY_ENTRANCE, ROOM_SANCTUARY_ENTRANCE_MAIN,
      1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gUnk_0813A76C[] = {
    { WARP_TYPE_AREA, 0xc8, 0x1fc, 0x88, 0x48, TRANSITION_SHAPE_AREA_12x12, AREA_DARK_HYRULE_CASTLE_OUTSIDE,
      ROOM_DARK_HYRULE_CASTLE_OUTSIDE_GARDEN, 1, TRANSITION_TYPE_NORMAL, 0x4, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Sanctuary_Main[] = {
    { WARP_TYPE_AREA, 0xe8, 0x28, 0x98, 0x130, TRANSITION_SHAPE_AREA_12x12, AREA_SANCTUARY, ROOM_SANCTUARY_STAINED_GLASS, 2,
      TRANSITION_TYPE_NORMAL, 0x0, 0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition gExitList_Sanctuary_StainedGlass[] = {
    { WARP_TYPE_AREA, 0x98, 0x140, 0xe8, 0x38, TRANSITION_SHAPE_AREA_12x12, AREA_SANCTUARY, ROOM_SANCTUARY_MAIN, 2, TRANSITION_TYPE_NORMAL, 0x4,
      0x0, 0x0, 0x0 },
    TransitionListEnd,
};
const Transition* const gExitLists_Sanctuary[] = {
    [ROOM_SANCTUARY_HALL] = gExitList_Sanctuary_Hall,
    [ROOM_SANCTUARY_MAIN] = gExitList_Sanctuary_Main,
    [ROOM_SANCTUARY_STAINED_GLASS] = gExitList_Sanctuary_StainedGlass,
};

const Transition* const* const gExitLists[] = {
    /*AREA_MINISH_WOODS*/ gExitLists_MinishWoods,
    /*AREA_MINISH_VILLAGE*/ gExitLists_MinishVillage,
    /*AREA_HYRULE_TOWN*/ gExitLists_HyruleTown,
    /*AREA_HYRULE_FIELD*/ gExitLists_HyruleField,
    /*AREA_CASTOR_WILDS*/ gExitLists_CastorWilds,
    /*AREA_RUINS*/ gExitLists_Ruins,
    /*AREA_MT_CRENEL*/ gExitLists_MtCrenel,
    /*AREA_CASTLE_GARDEN*/ gExitLists_CastleGarden,
    /*AREA_CLOUD_TOPS*/ gExitLists_CloudTops,
    /*AREA_ROYAL_VALLEY*/ gExitLists_RoyalValley,
    /*AREA_VEIL_FALLS*/ gExitLists_VeilFalls,
    /*AREA_LAKE_HYLIA*/ gExitLists_LakeHylia,
    /*AREA_LAKE_WOODS_CAVE*/ gExitLists_LakeWoodsCave,
    /*AREA_BEANSTALKS*/ gExitLists_Beanstalks,
    /*AREA_EMPTY*/ gExitLists_NoExit,
    /*AREA_HYRULE_DIG_CAVES*/ gExitLists_HyruleDigCaves,
    /*AREA_MELARIS_MINE*/ gExitLists_MelarisMine,
    /*AREA_MINISH_PATHS*/ gExitLists_MinishPaths,
    /*AREA_CRENEL_MINISH_PATHS*/ gExitLists_CrenelMinishPaths,
    /*AREA_DIG_CAVES*/ gExitLists_DigCaves1,
    /*AREA_CRENEL_DIG_CAVE*/ gExitLists_NoExit,
    /*AREA_FESTIVAL_TOWN*/ gExitLists_FestivalTown,
    /*AREA_VEIL_FALLS_DIG_CAVE*/ gExitLists_NoExit,
    /*AREA_CASTOR_WILDS_DIG_CAVE*/ gExitLists_NoExit,
    /*AREA_OUTER_FORTRESS_OF_WINDS*/ gExitLists_OuterFortressOfWinds,
    /*AREA_HYLIA_DIG_CAVES*/ gExitLists_HyliaDigCaves,
    /*AREA_VEIL_FALLS_TOP*/ gExitLists_VeilFallsTop,
    /*AREA_NULL_1B*/ gExitLists_NoExit,
    /*AREA_NULL_1C*/ gExitLists_NoExit,
    /*AREA_NULL_1D*/ gExitLists_NoExit,
    /*AREA_NULL_1E*/ gExitLists_NoExit,
    /*AREA_NULL_1F*/ gExitLists_NoExit,
    /*AREA_MINISH_HOUSE_INTERIORS*/ gExitLists_MinishHouseInteriors,
    /*AREA_HOUSE_INTERIORS_1*/ gExitLists_HouseInteriors1,
    /*AREA_HOUSE_INTERIORS_2*/ gExitLists_HouseInteriors2,
    /*AREA_HOUSE_INTERIORS_3*/ gExitLists_HouseInteriors3,
    /*AREA_TREE_INTERIORS*/ gExitLists_TreeInteriors,
    /*AREA_DOJOS*/ gExitLists_Dojos,
    /*AREA_CRENEL_CAVES*/ gExitLists_CrenelCaves,
    /*AREA_MINISH_CRACKS*/ gExitLists_MinishCracks,
    /*AREA_HOUSE_INTERIORS_4*/ gExitLists_HouseInteriors4,
    /*AREA_GREAT_FAIRIES*/ gExitLists_GreatFairies,
    /*AREA_CASTOR_CAVES*/ gExitLists_CastorCaves,
    /*AREA_CASTOR_DARKNUT*/ gExitLists_CastorDarknut,
    /*AREA_ARMOS_INTERIORS*/ gExitLists_ArmosInteriors,
    /*AREA_TOWN_MINISH_HOLES*/ gExitLists_TownMinishHoles,
    /*AREA_MINISH_RAFTERS*/ gExitLists_MinishRafters,
    /*AREA_GORON_CAVE*/ gExitLists_GoronCave,
    /*AREA_WIND_TRIBE_TOWER*/ gExitLists_WindTribeTower,
    /*AREA_WIND_TRIBE_TOWER_ROOF*/ gExitLists_WindTribeTowerRoof,
    /*AREA_CAVES*/ gExitLists_Caves,
    /*AREA_VEIL_FALLS_CAVES*/ gExitLists_VeilFallsCaves,
    /*AREA_ROYAL_VALLEY_GRAVES*/ gExitLists_RoyalValleyGraves,
    /*AREA_MINISH_CAVES*/ gExitLists_MinishCaves,
    /*AREA_CASTLE_GARDEN_MINISH_HOLES*/ gExitLists_CastleGardenMinishHoles,
    /*AREA_37*/ gExitLists_37,
    /*AREA_EZLO_CUTSCENE*/ gExitLists_NoExit,
    /*AREA_NULL_39*/ gExitLists_NoExit,
    /*AREA_NULL_3A*/ gExitLists_NoExit,
    /*AREA_NULL_3B*/ gExitLists_NoExit,
    /*AREA_NULL_3C*/ gExitLists_NoExit,
    /*AREA_NULL_3D*/ gExitLists_NoExit,
    /*AREA_NULL_3E*/ gExitLists_NoExit,
    /*AREA_NULL_3F*/ gExitLists_NoExit,
    /*AREA_40*/ gExitLists_40,
    /*AREA_HYRULE_TOWN_UNDERGROUND*/ gExitLists_HyruleTownUnderground,
    /*AREA_GARDEN_FOUNTAINS*/ gExitLists_GardenFountains,
    /*AREA_HYRULE_CASTLE_CELLAR*/ gExitLists_HyruleCastleCellar,
    /*AREA_SIMONS_SIMULATION*/ gExitLists_NoExit,
    /*AREA_45*/ gExitLists_NoExit,
    /*AREA_NULL_46*/ gExitLists_40,
    /*AREA_47*/ gExitLists_NoExit,
    /*AREA_DEEPWOOD_SHRINE*/ gExitLists_DeepwoodShrine,
    /*AREA_DEEPWOOD_SHRINE_BOSS*/ gExitLists_DeepwoodShrineBoss,
    /*AREA_DEEPWOOD_SHRINE_ENTRY*/ gExitLists_DeepwoodShrineEntry,
    /*AREA_NULL_4B*/ gExitLists_NoExit,
    /*AREA_NULL_4C*/ gExitLists_NoExit,
    /*AREA_4D*/ gExitLists_NoExit,
    /*AREA_NULL_4E*/ gExitLists_NoExit,
    /*AREA_NULL_4F*/ gExitLists_NoExit,
    /*AREA_CAVE_OF_FLAMES*/ gExitLists_CaveOfFlames,
    /*AREA_CAVE_OF_FLAMES_BOSS*/ gExitLists_NoExit,
    /*AREA_NULL_52*/ gExitLists_NoExit,
    /*AREA_NULL_53*/ gExitLists_NoExit,
    /*AREA_NULL_54*/ gExitLists_NoExit,
    /*AREA_NULL_55*/ gExitLists_NoExit,
    /*AREA_NULL_56*/ gExitLists_NoExit,
    /*AREA_57*/ gExitLists_NoExit,
#ifndef DEMO_USA
    /*AREA_FORTRESS_OF_WINDS*/ gExitLists_FortressOfWinds,
    /*AREA_FORTRESS_OF_WINDS_TOP*/ gExitLists_FortressOfWindsTop,
    /*AREA_INNER_MAZAAL*/ gExitLists_InnerMazaal,
    /*AREA_NULL_5B*/ gExitLists_NoExit,
    /*AREA_NULL_5C*/ gExitLists_NoExit,
    /*AREA_NULL_5D*/ gExitLists_NoExit,
    /*AREA_NULL_5E*/ gExitLists_NoExit,
    /*AREA_5F*/ gExitLists_NoExit,
#endif
    /*AREA_TEMPLE_OF_DROPLETS*/ gExitLists_TempleOfDroplets,
    /*AREA_NULL_61*/ gExitLists_61,
    /*AREA_HYRULE_TOWN_MINISH_CAVES*/ gExitLists_HyruleTownMinishCaves,
    /*AREA_NULL_63*/ gExitLists_NoExit,
    /*AREA_NULL_64*/ gExitLists_NoExit,
    /*AREA_NULL_65*/ gExitLists_NoExit,
    /*AREA_NULL_66*/ gExitLists_NoExit,
    /*AREA_67*/ gExitLists_NoExit,
    /*AREA_ROYAL_CRYPT*/ gExitLists_RoyalCrypt,
    /*AREA_NULL_69*/ gExitLists_NoExit,
    /*AREA_NULL_6A*/ gExitLists_NoExit,
    /*AREA_NULL_6B*/ gExitLists_NoExit,
    /*AREA_NULL_6C*/ gExitLists_NoExit,
    /*AREA_NULL_6D*/ gExitLists_NoExit,
    /*AREA_NULL_6E*/ gExitLists_NoExit,
    /*AREA_6F*/ gExitLists_NoExit,
    /*AREA_PALACE_OF_WINDS*/ gExitLists_PalaceOfWinds,
    /*AREA_PALACE_OF_WINDS_BOSS*/ gExitLists_NoExit,
    /*AREA_NULL_72*/ gExitLists_NoExit,
    /*AREA_NULL_73*/ gExitLists_NoExit,
    /*AREA_NULL_74*/ gExitLists_NoExit,
    /*AREA_NULL_75*/ gExitLists_NoExit,
    /*AREA_NULL_76*/ gExitLists_NoExit,
    /*AREA_77*/ gExitLists_NoExit,
    /*AREA_SANCTUARY*/ gExitLists_Sanctuary,
    /*AREA_NULL_79*/ gExitLists_NoExit,
    /*AREA_NULL_7A*/ gExitLists_NoExit,
    /*AREA_NULL_7B*/ gExitLists_NoExit,
    /*AREA_NULL_7C*/ gExitLists_NoExit,
    /*AREA_NULL_7D*/ gExitLists_NoExit,
    /*AREA_NULL_7E*/ gExitLists_NoExit,
    /*AREA_7F*/ gExitLists_NoExit,
    /*AREA_HYRULE_CASTLE*/ gExitLists_HyruleCastle,
    /*AREA_SANCTUARY_ENTRANCE*/ gExitLists_SanctuaryEntrance,
    /*AREA_NULL_82*/ gExitLists_NoExit,
    /*AREA_NULL_83*/ gExitLists_NoExit,
    /*AREA_NULL_84*/ gExitLists_NoExit,
    /*AREA_NULL_85*/ gExitLists_NoExit,
    /*AREA_NULL_86*/ gExitLists_NoExit,
    /*AREA_87*/ gExitLists_NoExit,
    /*AREA_DARK_HYRULE_CASTLE*/ gExitLists_DarkHyruleCastle,
    /*AREA_DARK_HYRULE_CASTLE_OUTSIDE*/ gExitLists_DarkHyruleCastleOutside,
    /*AREA_VAATIS_ARMS*/ gExitLists_VaatisArms,
    /*AREA_VAATI_3*/ gExitLists_NoExit,
    /*AREA_VAATI_2*/ gExitLists_NoExit,
    /*AREA_DARK_HYRULE_CASTLE_BRIDGE*/ gExitLists_DarkHyruleCastleBridge,
    /*AREA_NULL_8E*/ gExitLists_NoExit,
    /*AREA_8F*/ gExitLists_NoExit,
    /*AREA_90*/ gExitLists_NoExit,
    /*AREA_91*/ gExitLists_NoExit,
    /*AREA_92*/ gExitLists_NoExit,
    /*AREA_93*/ gExitLists_NoExit,
    /*AREA_94*/ gExitLists_NoExit,
    /*AREA_95*/ gExitLists_NoExit,
    /*AREA_96*/ gExitLists_NoExit,
    /*AREA_97*/ gExitLists_NoExit,
    /*AREA_98*/ gExitLists_NoExit,
};
// clang-format on
