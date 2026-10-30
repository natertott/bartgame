"""Native reboot metatiles: one painter, stable gameplay contracts."""
import json
from pathlib import Path
import reboot_terrain
import sewer_concepts as SC

CONTRACTS=json.loads((Path(__file__).with_name('reboot_contracts.json')).read_text())
TYPES=CONTRACTS['types']
SOLID_TYPES={'SOLID','THORN','CRACK','WEB','DOOR','TORCH','TORCH_LIT','CHEST','CHEST_OPEN',
             'LIFT1','LIFT2','LEDGE_N','LEDGE_E','LEDGE_S','LEDGE_W'}

def default_coll(kind):
    return 15 if kind in SOLID_TYPES else 0

METATILES=reboot_terrain.build()
if SC.VARIANT and SC.VARIANT != 9:
    import sewer_concepts_terrain as SCT
    for mt in METATILES:
        if not mt['name'].startswith(('sw_', 'swh_')):
            continue
        count=len(mt['frames']) if 'frames' in mt else 1
        frames=[]
        for phase in range(count):
            image=SCT.paint(mt['name'],phase,SC.RECIPE)
            assert image.mode=='P' and image.size==(16,16),(mt['name'],image.mode,image.size)
            assert set(image.getdata())<=set(range(16)),mt['name']
            frames.append(reboot_terrain.rows(image))
        if 'frames' in mt:mt['frames']=frames
        else:mt['art']=frames[0]
        mt['pal']='drain'
assert len(METATILES)==len(CONTRACTS['tiles'])
COVERAGE=[]
for expected,painted in zip(CONTRACTS['tiles'],METATILES):
    assert painted['name']==expected['name'],(expected['name'],painted['name'])
    for field in ('type','coll','prop'):
        actual=painted.get(field,default_coll(painted['type']) if field=='coll' else 0)
        assert actual==expected[field],(painted['name'],field,actual,expected[field])
    frames=painted.get('frames') or [painted['art']]
    assert len(frames)==expected['frames'],painted['name']
    owner='sewer_concepts_terrain' if SC.VARIANT and SC.VARIANT != 9 and painted['name'].startswith(('sw_','swh_')) else 'reboot_terrain'
    COVERAGE.append({'name':painted['name'],'owner':owner,'frames':len(frames),
                     'material':painted['pal'],'glitter':bool(painted.get('glitter'))})

# Final room pictures have placement-specific identities. Their physical
# metadata remains the source cell's metadata, and original IDs stay stable.
if SC.VARIANT == 9:
    import sewer_final as SF
    import sewer_final_contracts as SFC
    original = {mt['name']: mt for mt in METATILES}
    for clone in SFC.CLONES:
        mt = dict(original[clone['source']])
        mt['name'] = clone['name']
        mt['pal'] = 'drain'
        mt.pop('qpals', None)
        mt.pop('art', None)
        mt.pop('frames', None)
        count, speed = SF.frame_spec(clone['layer'], clone['x'], clone['y'])
        assert 1 <= count <= 255 and 1 <= speed <= 255, (clone['name'], count, speed)
        frames = []
        for phase in range(count):
            image = SF.paint(clone['name'], phase)
            assert image.mode == 'P' and image.size == (16, 16), clone['name']
            assert set(image.getdata()) <= set(range(16)), clone['name']
            frames.append(reboot_terrain.rows(image))
        if count > 1:
            mt['frames'] = frames
            mt['anim_speed'] = speed
        else:
            mt['art'] = frames[0]
        for field in ('type', 'coll', 'prop'):
            actual = mt.get(field, default_coll(mt['type']) if field == 'coll' else 0)
            assert actual == clone[field], (clone['name'], field, actual, clone[field])
        METATILES.append(mt)
        COVERAGE.append({'name': mt['name'], 'owner': 'sewer_final', 'frames': count,
                         'material': 'drain', 'glitter': bool(mt.get('glitter')),
                         'source': clone['source'], 'placement': [clone['layer'], clone['x'], clone['y']]})
