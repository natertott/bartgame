"""Every current sprite family is authored by the native reboot painters.

The contract file supplies identifiers and ordering, never reference pixels.
Missing families or frames are errors rather than old-art fallbacks.
"""
import json
import os
from pathlib import Path
import reboot_actors
import reboot_items
import reboot_ui

CONTRACTS=json.loads((Path(__file__).with_name('reboot_contracts.json')).read_text())
VALID_SHAPES={(8,8),(16,16),(32,32),(64,64),(16,8),(32,8),(32,16),(64,32),
              (8,16),(8,32),(16,32),(32,64)}
SHEETS=[]
COVERAGE=[]
owned={}
for module in (reboot_actors,reboot_items,reboot_ui):
    provided=module.build_sheets(CONTRACTS)
    assert isinstance(provided,dict),module.__name__
    for name,sheet in provided.items():
        assert name not in owned,('two sprite owners',name)
        owned[name]=(module.__name__,sheet)

def take(name,order=None):
    owner,sheet=owned.pop(name)
    assert sheet['name']==name
    assert (sheet['w'],sheet['h']) in VALID_SHAPES,(name,sheet['w'],sheet['h'])
    if order is not None:
        assert set(sheet['frames'])==set(order),(name,set(sheet['frames'])^set(order))
        sheet['frames']={frame:sheet['frames'][frame] for frame in order}
    for frame,rows in sheet['frames'].items():
        assert len(rows)==sheet['h'] and all(len(row)==sheet['w'] for row in rows),(name,frame)
        assert set(''.join(rows))<=set('.0123456789abcdef'),(name,frame)
        COVERAGE.append({'sheet':name,'frame':frame,'owner':owner,'canvas':[sheet['w'],sheet['h']]})
    SHEETS.append(sheet)

for contract in CONTRACTS['sheets']:
    assert contract['name'] in owned,('unpainted family',contract['name'])
    take(contract['name'],contract['frames'])
for name in ('huditems','glitter'):
    assert name in owned,('missing new family',name)
    take(name)
assert not owned,('unregistered new families',sorted(owned))

# Sword studies are opt-in comparison builds. All original frame identifiers
# and the default painter path remain untouched until a study is selected.
SWING_VARIANT=int(os.environ.get('BART_SWING','0'))
assert 0<=SWING_VARIANT<=5,('BART_SWING must be 0..5',SWING_VARIANT)
SWING_PROFILE=None
SWING_GEOMETRY=None
if SWING_VARIANT:
    import sword_studies
    SWING_PROFILE=sword_studies.profile(SWING_VARIANT)
    SWING_GEOMETRY=sword_studies.geometry(SWING_VARIANT)
    for sheet_name,painter,palette in (('hero',sword_studies.body_frame,'hero'),
                                       ('bloomfx',sword_studies.fx_frame,'iron')):
        sheet=next(s for s in SHEETS if s['name']==sheet_name)
        for face in ('n','e','s','w'):
            for phase in range(8):
                frame='study_%s%d'%(face,phase)
                assert frame not in sheet['frames']
                image=painter(SWING_VARIANT,face,phase)
                assert image.size==(32,32),(sheet_name,frame,image.size)
                sheet['frames'][frame]=sword_studies.ink_rows(image)
                if 'frame_pal' in sheet:
                    sheet['frame_pal'][frame]=palette
                COVERAGE.append({'sheet':sheet_name,'frame':frame,'owner':'sword_studies',
                                 'canvas':[32,32],'study':SWING_VARIANT})
