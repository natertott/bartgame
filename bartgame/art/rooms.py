"""Room layout metadata only; all native pixels come from reboot_terrain."""
import json
from pathlib import Path
from copy import deepcopy
import sewer_concepts as SC

OBJ_NPC,OBJ_EXIT,OBJ_SPAWN,OBJ_SHOP,OBJ_SIGN=range(1,6)
ROOMS=deepcopy(json.loads((Path(__file__).parent/'reboot_contracts.json').read_text())['rooms'])
if SC.VARIANT == 9:
    from sewer_final_contracts import ROOM
    ROOMS[0] = deepcopy(ROOM)
LEGEND={'  ':None}


def expand(rows,w,h,mt_names):
    assert len(rows)==h,(len(rows),h)
    out=[]
    for row in rows:
        assert not isinstance(row,str) and len(row)==w,'Native room uses explicit metatile names'
        out.extend(0xffff if name is None else mt_names[name] for name in row)
    return out
