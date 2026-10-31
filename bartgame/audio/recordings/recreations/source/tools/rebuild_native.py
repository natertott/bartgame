#!/usr/bin/env python3
from pathlib import Path
import argparse,importlib.util,json,sys
p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
here=Path(__file__).resolve().parent
source=json.loads((here.parent/'source_manifest.json').read_text())
for row in source['sources']:
 row['source_path']=str((a.inputs/row['file_name']).resolve())
 if not Path(row['source_path']).is_file():raise FileNotFoundError(row['source_path'])
a.output.mkdir(parents=True,exist_ok=True);(a.output/'source_manifest.json').write_text(json.dumps(source))
spec=importlib.util.spec_from_file_location('export_pcm',here/'export_pcm.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.ROOT=a.output.resolve()
sys.argv=['export_pcm.py','--native'];module.main()
