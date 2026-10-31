#!/usr/bin/env python3
from pathlib import Path
import argparse,importlib.util,json,numpy as np
p=argparse.ArgumentParser();p.add_argument('--score',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
here=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('cover_engine',here/'cover_engine.py');engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
engine.SAMPLER=here/'gm_sampler.py'
score=json.loads(a.score.read_text());audio,meta=engine.render_cover(score,32768)
a.output.parent.mkdir(parents=True,exist_ok=True);np.save(a.output,audio);a.output.with_suffix('.render.json').write_text(json.dumps(meta,indent=2))
engine.write_midi(score,a.output.with_suffix('.mid'))
print('Rendered symbolic score without source audio',a.output)
