from pathlib import Path
from PIL import Image, ImageSequence
import argparse, hashlib, json, subprocess, sys
sys.path.insert(0, 'tools')
import forest_v2_gallery as V

p=argparse.ArgumentParser();p.add_argument('--allow-current-drift',action='store_true');p.add_argument('--report',type=Path)
a=p.parse_args()
base=Path('/workspace/setup/forest-concepts-v2/gallery');r=json.loads((base/'source-manifest.json').read_text())
checks=[]
def check(value,label):
    assert value,label
    checks.append(label)
def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rgba(path):return Image.open(path).convert('RGBA')
current_drift=[]
for name,digest in r['source_sha256'].items():
    if sha(V.ROOT/name)!=digest:current_drift.append(name)
    if name!='tools/forest_v2_gallery.py':
        expected=hashlib.sha256(subprocess.check_output(['git','show',r['git_base_commit']+':bartgame/'+name])).hexdigest()
        check(expected==digest,'committed input '+name)
check(a.allow_current_drift or not current_drift,'current source/tool matches export')
check(sha(V.INVENTORY)==r['inventory_sha256'],'baseline inventory hash')
check(r['profiles']==[6,7,8,9,10] and r['total_frame_instances']==5320,'five profiles and total coverage')
for name,meta in r['files'].items():
    path=base/name;check(path.is_file() and path.stat().st_size==meta['bytes'] and sha(path)==meta['sha256'],'file '+name)
actual_files={str(q.relative_to(base)) for q in base.rglob('*') if q.is_file()}
check(actual_files==set(r['files'])|{'source-manifest.json'},'complete output fileset')
inv=read(V.INVENTORY);original={t['name']:t for t in inv['tiles']};need=set(inv['required']['bg_names'])
by_profile={};gif_count=0;pulse_states=0;blob_samples=0;alpha_cases=0;clearance_cases=0;roll_panels=0
hero_hashes={};minimum_canopy=[]
for profile in r['profiles']:
    folder=base/f'variant-{profile-5:02}';v=read(folder/'source-manifest.json')
    check((v['profile'],v['local_variant'])==(profile,profile-5),'profile mapping')
    check((v['bg_metatile_count'],v['bg_frame_count'],v['sprite_frame_count'],v['frame_count'])==(920,1034,30,1064),'complete per-profile scope')
    frames={tuple((e['kind'],e.get('sheet',''),e['name'],e['phase'])):e for e in v['frames']};by_profile[profile]=frames
    keys=[tuple(k) for album in v['atlases'] for k in album['frame_keys']]
    check(len(keys)==len(set(keys))==1064 and set(keys)==set(frames),'complete category atlas coverage')
    check(len(v['atlases'])==20,'practical album count')
    by_name={}
    for key,e in frames.items():
        pic=Image.open(folder/e['native_indexed_png']);out=rgba(folder/e['native_rgba_png'])
        check(pic.mode=='P' and pic.size==tuple(e['canvas']) and pic.convert('RGBA').tobytes()==out.tobytes(),'native PNG roundtrip '+str(key))
        check(set(pic.tobytes())<=set(range(16)) and hashlib.sha256(pic.tobytes()).hexdigest()==e['index_sha256'],'native4bpp index/hash '+str(key))
        check(set(out.getchannel('A').tobytes())<={0,255} and hashlib.sha256(out.tobytes()).hexdigest()==e['rgba_sha256'],'binary alpha/RGBA hash '+str(key))
        check(len(e['colors_rgb555'])==16 and all(all(c%8==0 for c in V.G.rgb(color)) for color in e['colors_rgb555']),'RGB555 bank '+str(key))
        if e['kind']=='tile':
            by_name.setdefault(e['name'],[]).append(e)
            if e['name'] in need:
                check(e['id']==original[e['name']]['id'] and all(e[k]==original[e['name']][k] for k in ('type','coll','prop')),'original semantic contract '+str(key))
    check(need<=set(by_name),'all463 original forest/myst IDs')
    check(len(v['topology'])==457,'all appended topology aliases')
    family_counts={}
    for spec in v['topology']:
        family_counts[spec['family']]=family_counts.get(spec['family'],0)+1
        source=by_name[spec['name']][0];parent=by_name[spec['parent']][0]
        check(source['semantic_parent_id']==parent['id'] and all(source[k]==parent[k] for k in ('type','coll','prop')),'alias parent physical metadata '+spec['name'])
    check(family_counts=={'canopy':376,'fringe':30,'water':47,'isolated_water':2,'overhead_root_arch':2},'topology family coverage')
    for name in ('f2_water_f0','f2_water_lily_isolated','f2_water_foam_isolated'):
        for e in by_name[name]:
            data=Image.open(folder/e['native_indexed_png']).tobytes()
            perimeter=[data[y*16+x] for y in range(16) for x in range(16) if x in (0,15) or y in (0,15)]
            check(set(perimeter)=={0},'entire isolated-water perimeter alpha0 '+name);alpha_cases+=1
    check(v['pulse_indices']=={'blight':[5,6,7,13,14]},'only authored glow-ink indices')
    phases=v['pulse_palettes']['blight']
    check(len(phases)==4 and all(len(q)==16 for q in phases),'four literal BG bank phases')
    for colors in phases:
        check(all(colors[i]==phases[0][i] for i in range(16) if i not in (5,6,7,13,14)),'material inks invariant across pulse')
    for group in v['native_palette_phase_groups']:
        raw=None
        for phase in group['phases']:
            pic=Image.open(folder/phase['native_indexed_png']);out=rgba(folder/phase['native_rgba_png'])
            check(pic.convert('RGBA').tobytes()==out.tobytes() and sha(folder/phase['native_indexed_png']) is not None,'native palette-state PNG roundtrip')
            check(raw is None or pic.tobytes()==raw,'palette pulse keeps literal source indices fixed')
            raw=pic.tobytes();check(hashlib.sha256(raw).hexdigest()==group['index_sha256']==phase['index_sha256'],'native phase group index identity')
            check(phase['colors_rgb555']==phases[phase['phase']],'native phase uses authored bank state');pulse_states+=1
    for animation in v['animations']:
        check(not animation.get('omitted'),'exact GIF available')
        path=folder/animation['path'];prefix=path.name.removesuffix('-source.gif')
        with Image.open(path) as gif:decoded=[(f.convert('RGB').copy(),f.info['duration']) for f in ImageSequence.Iterator(gif)]
        check(len(decoded)==animation['frames'],'GIF frame count')
        for n,(frame,duration) in enumerate(decoded):
            expected=Image.open(folder/f'{prefix}-phase{n:02}-source.png').convert('RGB')
            check(frame.tobytes()==expected.tobytes() and duration==180,'GIF exact RGB/fixed hold')
        gif_count+=1
    def native(e):return rgba(folder/e['native_rgba_png'])
    def field(size,name):
        out=Image.new('RGB',size);tile=native(by_name[name][0])
        for y in range(0,size[1],16):
            for x in range(0,size[0],16):out.paste(tile,(x,y),tile)
        return out
    topo={(e['topology']['family'],e['topology'].get('kind'),e['topology'].get('quadrant'),e['topology'].get('mask'),e['topology'].get('corners',0),e['phase']):e for e in v['frames'] if e.get('topology')}
    allcases=read(folder/'all47-cases-source.json')
    for family,records in allcases.items():
        check(len(records)==47 and len({(q['mask'],q['corners']) for q in records})==47,'all47 unique cases '+family)
        board=Image.open(folder/f'all47-{family}-cases-source.png').convert('RGB')
        for n,case in enumerate(records):
            mask,corners=case['mask'],case['corners'];sides=(9,3,6,12)
            check(all(not(corners&(1<<q)) or not(mask&sides[q]) for q in range(4)),'legal concave case')
            check(case['parent_coll']==(0 if family=='water' else 15),'parent collider preserved despite visual rounding')
            for q in range(2 if family=='water' else 4):
                e=topo[('water',None,None,mask,corners,q)] if family=='water' else topo[('canopy',2 if family=='blight' else 1,q,mask,corners,0)]
                expected=field((24,24) if family=='water' else (20,20),'blight_floor' if family=='blight' else 'moss0')
                pic=native(e);offset=4 if family=='water' else 2;expected.paste(pic,(offset,offset),pic)
                xx=n%6*206+6+(q*30 if family=='water' else q%2*24);yy=68+n//6*136+23+(0 if family=='water' else q//2*24)
                check(board.crop((xx,yy,xx+expected.width,yy+expected.height)).tobytes()==expected.tobytes(),'47-case panel exact native composite');blob_samples+=1
    for shape in read(folder/'adjacency-islands-source.json'):
        for cell in shape['cells']:
            wx,wy=cell['world_cell'];check(cell['macro_quadrant']==(wx&1)|((wy&1)<<1),'shape macro parity')
    clearance=read(folder/'standing-roll-clearance-source.json')
    check(len(clearance['north_fringe_alpha_cases'])==16,'all north-touching fringe source cases')
    for case in clearance['north_fringe_alpha_cases']:
        e=by_name[case['alias']][0];data=Image.open(folder/e['native_indexed_png']).tobytes()
        check(case['clear_rectangle']==[2,2,14,16] and all(data[y*16+x]==0 for y in range(2,16) for x in range(2,14)),'literal12x14 source-clearance lane');clearance_cases+=1
    check(len(clearance['poses'])==28,'standing and13 source roll poses on two source families')
    for pose in clearance['poses']:
        check(pose['source_only'] and pose['not_runtime_or_physical_clearance_proof'] and 0<pose['visible_after_source_foreground']<=pose['actor_scene_opaque_pixels'],'honest source-only pose occlusion')
        prior=hero_hashes.setdefault(pose['pose'],pose['protected_actor_index_sha256'])
        check(prior==pose['protected_actor_index_sha256'],'protected Bloom pose indices consistent');roll_panels+=1
    for e in v['frames']:
        if e.get('topology',{}).get('family')=='canopy':
            minimum_canopy.append(sum(bool(v) for v in Image.open(folder/e['native_indexed_png']).tobytes()))
    check(min(minimum_canopy)>0,'no invisible full-solid canopy alias')
proof=read(base/'complete-native-source.json');matrix=Image.open(base/'complete-native-source.png').convert('RGB')
check(len(proof['panels'])==5320,'all native matrix panels')
for panel in proof['panels']:
    e=by_profile[panel['profile']][tuple(panel['key'])];pic=rgba(base/f'variant-{panel["local_variant"]:02}'/e['native_rgba_png'])
    expected=Image.new('RGB',pic.size,tuple(panel['context_rgb']));expected.paste(pic,(0,0),pic)
    check(matrix.crop(panel['rectangle']).tobytes()==expected.tobytes(),'native matrix exact composite')
old=Path('/workspace/setup/forest-concepts-v2/source-gallery-0dce-pixel-hashes.json');images_identical=None
if old.exists():
    previous=read(old);images_identical=all(name in r['files'] and r['files'][name]['sha256']==data['sha256'] for name,data in previous['files'].items())
    check(images_identical,'image bytes match held0dce art checkpoint')
matrix.convert('L').save('/workspace/setup/forest-concepts-v2/source-native-value-review.png')
report={'source_commit':r['git_base_commit'],'passed':len(checks),'total':len(checks),'failures':[],
 'current_source_matches':not current_drift,'current_drift':current_drift,'files':len(r['files']),
 'native_frames':5320,'native_matrix_panels':5320,'exact_gifs':gif_count,'native_palette_group_states':pulse_states,
 'blob_panel_native_composites':blob_samples,'isolated_water_entire_alpha_perimeters':alpha_cases,
 'north_fringe_source_alpha_cases':clearance_cases,'source_standing_roll_panels':roll_panels,
 'minimum_canopy_opaque_pixels':min(minimum_canopy),'image_bytes_identical_to_held0dce':images_identical,
 'limits':['Source diagrams and fixed-foot pose composites are not real gameplay or collision runs.','Pulse GIFs use authored BG bank phases with fixed180ms inspection holds; no real clock/OBJ pulse claimed.']}
(a.report or Path('/workspace/setup/forest-concepts-v2/source-gallery-verification.json')).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
