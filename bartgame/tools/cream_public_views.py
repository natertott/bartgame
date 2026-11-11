#!/usr/bin/env python3
"""Capture settled Cream cave/terrace and both atlas levels in actual mGBA.

Uses the qualified progression harness until its real Lamp gate, then waits for
normal camera easing and operates the actual pause/atlas controls. The wrapper
and complete executed program are retained alongside untouched240x160 frames.
This gallery is separate from the full native-win qualification.
"""
from pathlib import Path
import sys

base=Path(__file__).with_name('cream_runtime_review.py')
source=base.read_text()
needle="def shot(c,name):P.snap(c,str(out/(name+'.png')))"
replacement='''def shot(c,name):
 P.snap(c,str(out/(name+'.png')))
 if name=='opened-gate-45':
  P.run(c,80)
  while P.r32(c,P.sym('gFrame'))&2:P.run(c,1)
  images=['cave-and-terrace']
  P.snap(c,str(out/'cave-and-terrace.png'))
  P.press(c,'START',2,5);P.press(c,'SELECT',2,5);P.press(c,'R',2,8)
  P.snap(c,str(out/'atlas-upper-overview.png'));images.append('atlas-upper-overview')
  P.press(c,'A',2,8);P.snap(c,str(out/'atlas-upper-room.png'));images.append('atlas-upper-room')
  P.press(c,'L',2,8);P.snap(c,str(out/'atlas-lower-room.png'));images.append('atlas-lower-room')
  P.press(c,'B',2,8);P.snap(c,str(out/'atlas-lower-overview.png'));images.append('atlas-lower-overview')
  P.press(c,'START',2,6)
  (out/'source-used.py').write_text(_gallery_source)
  (out/'public-views.json').write_text(json.dumps(dict(scope='Settled public gallery only; full win proof is a separate run.',source_commit=(bundle/'source-commit.txt').read_text().strip(),rom_sha256=hashlib.sha256((bundle/'bartgame.gba').read_bytes()).hexdigest(),wrapper_sha256=hashlib.sha256(Path(_gallery_wrapper).read_bytes()).hexdigest(),executed_source_sha256=hashlib.sha256(_gallery_source.encode()).hexdigest(),camera=[P.r16(c,P.sym('gCamX')),P.r16(c,P.sym('gCamY'))],fixtures=fixtures,images=[dict(file=n+'.png',size=[240,160],sha256=hashlib.sha256((out/(n+'.png')).read_bytes()).hexdigest()) for n in images]),indent=2))
  print('PASS public cave and upper/lower atlas gallery',flush=True)
  raise SystemExit(0)
'''
if needle not in source:raise RuntimeError('qualified capture hook changed')
source=source.replace(needle,replacement).replace('atexit.register(save_report)','')
sys.path.insert(0,str(base.parent))
namespace={'__name__':'__main__','__file__':str(base),'_gallery_wrapper':str(Path(__file__).resolve()),'_gallery_source':source}
exec(compile(source,str(base),'exec'),namespace)
