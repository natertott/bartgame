"""Capture five opt-in sword studies from real mGBA runs.

Ordinary B presses on naturally generated terrain animate the complete body
and sword. Seed, safe position, facing, inventory and unrelated-actor clearing
are review fixtures. No terrain, pose or attack timer is injected. Clean
screens are separate from diagnostic overlays. Render snapshots are matched
to uploaded hardware OBJ bytes before placing an inclusive damage rectangle.
All video frames are saved locally; selected exact native frames are published.
"""
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

from PIL import Image, ImageDraw, ImageFont
import probe as P
import bloom_probe as B
import critical_path as C
import wood_probe as W
from art_reboot_review import NativeSuite
from bloom_suite_gallery import write_gif

FPS=16777216/280896
FACES=('n','e','s','w')
FIELDS=('state','age','phase','active','x0','y0','x1','y1','cam_x','cam_y',
        'foot_x','foot_y','z','facing','body_frame','fx_frame')
FONT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
BG=(12,17,25);FG=(243,227,174)


def signed16(value):return value-65536 if value&32768 else value


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def durations(count,step=1,speed=1):
    ticks=list(range(0,count,step));ends=ticks[1:]+[count]
    return [round(b/FPS*speed*100)*10-round(a/FPS*speed*100)*10 for a,b in zip(ticks,ends)]


def video(directory,out):
    command=['ffmpeg','-y','-loglevel','error','-framerate',str(FPS),'-i',str(directory/'frame-%03d.png'),
             '-vf','scale=720:480:flags=neighbor','-an','-c:v','libx264','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
    subprocess.run(command,check=True,stdout=subprocess.DEVNULL)


class Capture:
    def __init__(self,args):
        self.args=args;self.frozen=Path(args.frozen);self.out=Path(args.out);self.out.mkdir(parents=True,exist_ok=True)
        self.coverage=json.loads((self.frozen/'coverage.json').read_text());self.meta=self.coverage['sword_study'];self.rows=[]
        self.config=SimpleNamespace(rom=str(self.frozen/'bartgame.gba'),map=str(self.frozen/'bartgame.map'),
             assets_header=str(self.frozen/'assets.h'),out=str(self.out),seed='0xB4A7',only=None,match=None)
        P.ROM=self.config.rom;self.suite=NativeSuite(self.config);self.rom_sha=digest(P.ROM)

    def prepare(self,background):
        self.suite.seed=11 if background=='cave' else 0xB4A7;self.suite.enter(background)
        self.c=self.suite.c;self.point=self.suite.spot(0,0)
        self.snapshot_at=P.sym('gSwordStudyRender');self.sequence_at=P.sym('gSwordStudyRenderSequence')
        self.action_tile=P.r16(self.c,B.static_symbol('sActionTile'))&65535
        self.body=B.sheet_metadata(self.c,self.suite.defs['SHEET_HERO'])
        self.fx=B.sheet_metadata(self.c,self.suite.defs['SHEET_BLOOMFX'])
        self.body_blobs={i:B.bytes_at(self.c,self.body['source']+i*512,512) for i in range(self.suite.defs['SHEET_HERO_FRAMES'])}
        self.fx_blobs={i:B.bytes_at(self.c,self.fx['source']+i*512,512) for i in range(self.suite.defs['SHEET_BLOOMFX_FRAMES'])}

    def snapshot(self):
        values=[signed16(P.r16(self.c,self.snapshot_at+i*2)&65535) for i in range(16)]
        row=dict(zip(FIELDS,values));row['sequence']=P.r32(self.c,self.sequence_at)
        row['box']=[row[k] for k in ('x0','y0','x1','y1')];row['camera']=[row['cam_x'],row['cam_y']]
        row['position']=[row['foot_x'],row['foot_y']]
        return row

    def aligned(self,history):
        c=self.c;body=B.bytes_at(c,0x06010000,512);fx=B.bytes_at(c,0x06010000+self.action_tile*32,512)
        entries=B.oam(c);hero=B.hero_oam(c);effect=next((o for o in entries if o['tile']==self.action_tile),None)
        assert hero is not None,'hardware Bloom missing'
        # Usually the previous prepared snapshot is displayed. Match source
        # bytes and actual OAM instead of presuming a fixed delay.
        prior=list(history)[:-1];candidates=list(reversed(prior))+[history[-1]]
        for row in candidates:
            if self.body_blobs[row['body_frame']]!=body:continue
            if hero['x']!=row['foot_x']-16-row['cam_x'] or hero['y']!=row['foot_y']-32-row['z']-row['cam_y']:continue
            if row['state']==2:
                if not effect or self.fx_blobs.get(row['fx_frame'])!=fx:continue
                origin=self.meta['geometry']['origins'][row['facing']][row['phase']]
                if [effect['x'],effect['y']]!=[row['foot_x']+origin[0]-row['cam_x'],row['foot_y']+origin[1]-row['z']-row['cam_y']]:continue
            elif effect:continue
            return {**row,'hardware_body_frame_verified':True,'hardware_fx_frame_verified':row['state']==2,
                    'hero_oam':hero,'effect_oam':effect}
        raise AssertionError(('no matching prepared body/FX snapshot',[(r['state'],r['age'],r['phase']) for r in history]))

    def record(self,background,facing):
        if self.args.target_demo:self.point=self.suite.spot(facing,32)
        self.suite.reset(self.point,facing,1);c=self.c;name=background+'-'+FACES[facing]
        self.action_tile=P.r16(c,B.static_symbol('sActionTile'))&65535
        target=None;target_at=None
        if self.args.target_demo:
            dx,dy=((0,-29),(24,-5),(0,19),(-24,-5))[facing]
            tx,ty=self.point[0]+dx,self.point[1]+dy
            index=W.spawn_enemy(c,0,tx,ty)
            target_at=P.sym('gActors')+index*64
            # Pause AI with zero-speed knockback, as in the contact probe.
            # Merely extending ES_IDLE's timer does not stop nearby beetles
            # from immediately chasing during the pre-roll.
            P.w8(c,target_at+29,200);P.w16(c,target_at+32,0)
            target={'slot':index,'position':[tx,ty],'native_hp':P.actor(c,index)['hp'],
                    'fixture':'Ordinary debug-spawned beetle; AI paused with zero-speed knockback, position fixture, native HP untouched.'}
            assert target['native_hp']==2
        directory=self.out/name;directory.mkdir(exist_ok=True)
        all_frames=self.out.parent.parent/'all-frames'/self.out.parent.name/('v'+str(self.meta['id']))/name;all_frames.mkdir(parents=True,exist_ok=True)
        history=deque([self.snapshot()],maxlen=8);images=[];overlays=[];trace=[];total=72
        for tick in range(total):
            c.clear_keys(*range(10))
            if 16<=tick<18:c.set_keys(P.key(c,'B'))
            c.run_frame();now=self.snapshot();history.append(now);display=self.aligned(history)
            image=c.bg_video.to_pil().convert('RGB').copy();images.append(image)
            image.save(all_frames/f'frame-{tick:03}.png')
            label='LIVE / actual damage box' if display['active'] else 'READY / harmless'
            if display['state']==2 and not display['active']:
                label='WINDUP / harmless' if display['age']<self.meta['age_active'].index(1) else 'RECOVERY / harmless'
            diagnostic=image.copy();draw=ImageDraw.Draw(diagnostic)
            if display['active']:
                x0,y0,x1,y1=display['box'];cx,cy=display['camera']
                draw.rectangle((x0-cx,y0-cy,x1-cx,y1-cy),outline=(105,250,247),width=1)
            panel=Image.new('RGB',(240,180),BG);panel.paste(diagnostic,(0,20));ImageDraw.Draw(panel).text((3,3),label,font=FONT,fill=(105,250,247) if display['active'] else FG)
            overlays.append(panel)
            row={'tick':tick,'logic':now,'display':display,'game_updates':P.r32(c,P.sym('gGame')+8),
                 'vblanks':P.r32(c,P.sym('gFrame'))}
            if target_at is not None:
                row['target']={'kind':P.r8(c,target_at),'hp':signed16(P.r16(c,target_at+26)&65535)}
            trace.append(row)
        c.clear_keys(*range(10))
        seen={r['display']['phase'] for r in trace if r['display']['state']==2}
        assert seen==set(range(8)),(name,'not all eight poses displayed',seen)
        logic=[r['logic'] for r in trace if r['logic']['state']==2]
        assert [r['age'] for r in logic]==list(range(sum(self.meta['durations']))),(name,'one predictable attack',[(r['age'],r['phase']) for r in logic])
        assert all(r['active']==self.meta['age_active'][r['age']] for r in logic)
        if target is not None:
            impacts=[r for r in trace if r['target']['kind']!=2 or r['target']['hp']<target['native_hp']]
            assert impacts,(name,'complete swing missed actual forward beetle')
            first=impacts[0];assert first['logic']['active'],(name,'damage outside declared interval')
            target['first_hit']={'video_tick':first['tick'],'age':first['logic']['age'],'phase':first['logic']['phase']}
        selected={0,total-1,15}
        for phase in range(8):selected.add(next(i for i,r in enumerate(trace) if r['display']['state']==2 and r['display']['phase']==phase))
        for i in sorted(selected):images[i].save(directory/f'frame-{i:03}.png')
        clean_name=name+'.gif';slow_name=name+'-slow.gif';overlay_name=name+'-hitbox.gif'
        clean=write_gif([im.resize((480,320),Image.Resampling.NEAREST) for im in images[::2]],durations(total,2),self.out/clean_name)
        slow=write_gif([im.resize((480,320),Image.Resampling.NEAREST) for im in images],durations(total,1,3),self.out/slow_name)
        overlay=write_gif([im.resize((480,360),Image.Resampling.NEAREST) for im in overlays],durations(total,1,3),self.out/overlay_name)
        if not self.args.no_video:video(all_frames,self.out/(name+'.mp4'))
        # Consistent actor-centred crop includes the entire native swing.
        foot=trace[0]['display'];px=foot['foot_x']-foot['cam_x'];py=foot['foot_y']-foot['cam_y']
        crop=[max(0,min(160,px-40)),max(24,min(80,py-56)),0,0];crop[2]=crop[0]+80;crop[3]=crop[1]+80
        film=Image.new('RGB',(8*160,210),BG);draw=ImageDraw.Draw(film)
        for phase in range(8):
            i=next(i for i,r in enumerate(trace) if r['display']['state']==2 and r['display']['phase']==phase)
            film.paste(images[i].crop(crop).resize((160,160),Image.Resampling.NEAREST),(phase*160,25))
            draw.text((phase*160+3,5),f'Pose{phase} age{trace[i]["display"]["age"]}',font=FONT,fill=FG)
            draw.text((phase*160+3,187),'LIVE' if self.meta['active_flags'][phase] else 'harmless',font=FONT,fill=(105,250,247) if self.meta['active_flags'][phase] else FG)
        film.save(self.out/(name+'-poses.png'))
        row={'name':name,'variant':self.meta['id'],'background':background,'facing':FACES[facing],
             'seed':hex(self.suite.seed),'cell':self.suite.cell,'position':list(self.point),'camera':trace[0]['display']['camera'],
             'input':{'B_down':16,'B_up':18},'video_frames':total,'fps':FPS,'crop':crop,
             'clean_gif':clean_name,'slow_gif':slow_name,'overlay_gif':overlay_name,'video':None if self.args.no_video else name+'.mp4',
             'native_frames':[name+f'/frame-{i:03}.png' for i in sorted(selected)],'filmstrip':name+'-poses.png','target':target,
             'full_frame_paths':[str(all_frames/f'frame-{i:03}.png') for i in range(total)],
             'gif':{'clean':clean,'slow':slow,'overlay':overlay},'trace':trace,
             'checks':{'all_eight_poses_displayed':True,'exactly_one_complete_attack':True,'active_window_matches_clock':True,'all_hardware_frames_matched':True,
                       'forward_enemy_hit':target is not None if self.args.target_demo else None}}
        self.rows.append(row);self.save();print('CAPTURE',self.meta['id'],name,'PASS',flush=True)

    def save(self):
        report={'rom_sha256':self.rom_sha,'variant':self.meta['id'],'profile':self.meta,'emulator':'mGBA0.10.5','fps':FPS,
                'method':__doc__.strip(),'captures':self.rows,'count':len(self.rows),'failures':[]}
        (self.out/'capture.json').write_text(json.dumps(report,indent=2)+'\n')

    def run(self):
        for background in self.args.backgrounds.split(','):
            self.prepare(background)
            for face in self.args.faces.split(','):self.record(background,FACES.index(face))
        assert digest(self.config.rom)==self.rom_sha


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--frozen',required=True);ap.add_argument('--out',required=True)
    ap.add_argument('--backgrounds',default='forest,drain,blight,cave');ap.add_argument('--faces',default='n,e,s,w');ap.add_argument('--no-video',action='store_true')
    ap.add_argument('--target-demo',action='store_true',help='Disclosed forward beetle fixture, native HP unchanged')
    Capture(ap.parse_args()).run()


if __name__=='__main__':main()
