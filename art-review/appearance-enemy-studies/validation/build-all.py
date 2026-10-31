from pathlib import Path
import hashlib,json,shutil,subprocess
r=Path('/workspace/bartgame/bartgame');w=Path('/workspace/setup/appearance-enemy-studies')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()
art=sorted([*r.glob('art/*.py'),*r.glob('art/*.json')])
code=sorted([*r.glob('src/*.c'),*r.glob('src/*.h'),*r.glob('src/*.s'),*r.glob('src/*.inc'),r/'Makefile',r/'gba.ld',r/'tools/build_assets.py'])
art_hash={str(p.relative_to(r)):sha(p) for p in art};code_hash={str(p.relative_to(r)):sha(p) for p in code}
for p in art+code:
 committed=subprocess.check_output(['git','show',source+':bartgame/'+str(p.relative_to(r))],cwd=r)
 assert hashlib.sha256(committed).hexdigest()==sha(p),('Uncommitted game/art input',p)
rows=[]
for number in range(11):
 b=w/f'build-{number}'
 cmd=['make','-j4',f'BUILD={b}','TARGET=bartgame','BART_SEWER=9','BART_UI=6','BART_MENU=1',f'BART_ENEMY={number}']
 with (w/f'build-{number}.log').open('w') as f:res=subprocess.run(cmd,cwd=r,stdout=f,stderr=subprocess.STDOUT)
 if res.returncode:print((w/f'build-{number}.log').read_text()[-6000:],flush=True);raise SystemExit(res.returncode)
 assert art_hash=={str(p.relative_to(r)):sha(p) for p in art},'Art source changed during freeze'
 assert code_hash=={str(p.relative_to(r)):sha(p) for p in code},'Code source changed during freeze'
 d=w/f'v{number}';d.mkdir(exist_ok=True)
 for s,n in [(r/'bartgame.gba','bartgame.gba'),(b/'bartgame.map','bartgame.map'),(b/'gen/assets.h','assets.h'),(b/'gen/art-reboot-coverage.json','coverage.json')]:shutil.copy2(s,d/n)
 record={'variant':number,'enemy':number,'kind':'production' if not number else 'enemy-study','label':'Selected interface and current enemies' if not number else f'Enemy alternative {number:02}','ui':6,'menu':1,'sewer':9,'source_commit':source,'rom_sha256':sha(d/'bartgame.gba'),'rom_bytes':(d/'bartgame.gba').stat().st_size,'command':cmd,'source_file_sha256':art_hash,'code_file_sha256':code_hash}
 (d/'freeze.json').write_text(json.dumps(record,indent=2)+'\n');rows.append(record)
 print(f'BUILT {number}: {record["rom_bytes"]} bytes {record["rom_sha256"]}',flush=True)
with (w/'default-restore.log').open('w') as f:subprocess.run(['make','-j4','-B'],cwd=r,stdout=f,stderr=subprocess.STDOUT,check=True)
assert sha(r/'bartgame.gba')==rows[0]['rom_sha256']
(w/'builds.json').write_text(json.dumps(rows,indent=2)+'\n')
print('Restored default Winebound HUD, Options, Workbench/graph map, enemy0. Eleven frozen builds complete.',flush=True)
