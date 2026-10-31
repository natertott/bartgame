from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import sys,subprocess,json
w=Path(__file__).resolve().parent;g=Path('/workspace/bartgame/bartgame');rows=[]
def run(n):
 out=w/f'pursuer-clearing/v{n}';report=out/'capture.json'
 if n!=1:
  cmd=[sys.executable,str(g/'tools/enemy_study_review.py'),'--frozen',str(w/f'v{n}'),'--out',str(out),'--clear-pursuer']
  with(w/f'pursuer-clearing-v{n}.log').open('w')as log:r=subprocess.run(cmd,cwd=g,stdout=log,stderr=subprocess.STDOUT)
  if r.returncode:return{'variant':n,'status':'failed','exit':r.returncode}
 j=json.loads(report.read_text());return{'variant':n,'status':'passed'if j['passed']==j['total']else'failed','captures':j['capture_count'],'passed':j['passed'],'total':j['total'],'frames':j['captures'][0]['frames']}
with ThreadPoolExecutor(max_workers=2)as pool:
 for f in as_completed([pool.submit(run,n)for n in range(1,11)]):
  r=f.result();rows.append(r);print(json.dumps(r),flush=True)
  (w/'pursuer-clearing-status.json').write_text(json.dumps(rows,indent=2)+'\n')
s={'source_commit':'5eedc6dae94d8c1ea21c55b8668435bcf0be884d','variants':sorted(rows,key=lambda x:x['variant']),'captures':sum(r.get('captures',0)for r in rows),'passed':sum(r.get('passed',0)for r in rows),'total':sum(r.get('total',0)for r in rows),'all_passed':all(r['status']=='passed'for r in rows)}
(w/'pursuer-clearing-summary.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s),flush=True)
raise SystemExit(not s['all_passed'])
