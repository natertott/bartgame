#include "menu_studies.h"
const char* const menu_study_names[11]={"Original","Loadout Workbench","Pocket Ledger","Fieldbook","Tactical Atlas","Toolwheel","Twin Atlas","Expedition Dashboard","Focus Cards","Barrier Index","Quick Ribbon"};
u8 gMenuStudyPage,gMenuStudyCursor,gMenuStudyMapCell,gMenuStudyZoom;
const MenuLayout* menu_study_layout(int n){return n<=5?menu_layout_a(n):menu_layout_b(n);}
