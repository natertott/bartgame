"""Native reboot metatiles: one painter, stable gameplay contracts."""
import json
from pathlib import Path
import reboot_terrain

CONTRACTS=json.loads((Path(__file__).with_name('reboot_contracts.json')).read_text())
TYPES=CONTRACTS['types']
SOLID_TYPES={'SOLID','THORN','CRACK','WEB','DOOR','TORCH','TORCH_LIT','CHEST','CHEST_OPEN',
             'LIFT1','LIFT2','LEDGE_N','LEDGE_E','LEDGE_S','LEDGE_W'}

def default_coll(kind):
    return 15 if kind in SOLID_TYPES else 0

METATILES=reboot_terrain.build()
assert len(METATILES)==len(CONTRACTS['tiles'])
COVERAGE=[]
for expected,painted in zip(CONTRACTS['tiles'],METATILES):
    assert painted['name']==expected['name'],(expected['name'],painted['name'])
    for field in ('type','coll','prop'):
        actual=painted.get(field,default_coll(painted['type']) if field=='coll' else 0)
        assert actual==expected[field],(painted['name'],field,actual,expected[field])
    frames=painted.get('frames') or [painted['art']]
    assert len(frames)==expected['frames'],painted['name']
    COVERAGE.append({'name':painted['name'],'owner':'reboot_terrain','frames':len(frames),
                     'material':painted['pal'],'glitter':bool(painted.get('glitter'))})
