"""Two process-isolated final mGBA reviewers, frozen inputs, no builds or mutations."""
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import hashlib,json,subprocess,sys
W=Path(__file__).resolve().parent;G=Path('/workspace/bartgame/bartgame');EXPECTED='5eedc6dae94d8c1ea21c55b8668435bcf0be884d'

def run(n):
 freeze=W/f'v{n}';f=json.loads((freeze/'freeze.json').read_text())
 assert f['source_commit']==EXPECTED and f['enemy']==n
 assert hashlib.sha256((freeze/'bartgame.gba').read_bytes()).hexdigest()==f['rom_sha256']
 out=W/f'enemy-reviews/v{n}';out.mkdir(parents=True,exist_ok=True)
 cmd=[sys.executable,str(G/'tools/enemy_study_review.py'),'--frozen',str(freeze),'--out',str(out),'--include-cave']
 with(W/f'enemy-review-v{n}.log').open('w')as log:result=subprocess.run(cmd,cwd=G,stdout=log,stderr=subprocess.STDOUT)
 if result.returncode:return{'variant':n,'status':'failed','exit_code':result.returncode}
 r=json.loads((out/'capture.json').read_text())
 return{'variant':n,'status':'passed'if r['passed']==r['total']else'failed','captures':r['capture_count'],'passed':r['passed'],'total':r['total'],'rom_sha256':r['rom_sha256']}

def main():
 progress=[]
 with ThreadPoolExecutor(max_workers=2)as pool:
  for f in as_completed([pool.submit(run,n)for n in range(11)]):
   row=f.result();progress.append(row);print(json.dumps(row),flush=True);(W/'enemy-review-status.json').write_text(json.dumps(progress,indent=2)+'\n')
 summary={'source_commit':EXPECTED,'variants':sorted(progress,key=lambda r:r['variant']),'captures':sum(r.get('captures',0)for r in progress),'passed':sum(r.get('passed',0)for r in progress),'total':sum(r.get('total',0)for r in progress),'all_passed':all(r['status']=='passed'for r in progress)}
 (W/'enemy-review-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
 return int(not summary['all_passed'])
if __name__=='__main__':raise SystemExit(main())
