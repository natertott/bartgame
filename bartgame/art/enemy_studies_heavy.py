"""Native heavy-enemy proposals: ten mechanic-led designs per family.

All coordinates are authored directly in the legal16x32/16x16/32x64
canvases. Original frames stay first. EXTRA_FRAMES are presentation-only
poses for the original AI states; they do not create immunity or new attacks.
"""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont
import reboot_core as C

CONCEPTS={
 'knight':['Bell Washer','Walking Tureen','Censer Stilt','Molar Mason',
           'Bad Boot','Moth Confessor','Snail Porter','Broken Marionette',
           'Oyster Bailiff','Chandelier Drudge'],
 'boss':['Split Coronation Bell','Glutton Chalice','Silk Stomach',
         'Crowned Leech Coil','Funeral Peacock','Slime Banquet',
         'Choir of Molars','Wound-up Moon','Inverted Bouquet','Processional Bath'],
}
NOTES={
 'knight':[
  'A tarnished walking bell shifts its entire skirt before the clapper-blade cut. The exposed eye is identity, not an exclusive weak spot.',
  'A cracked soup tureen plants its handles and tiny feet, draws back its ladle, then pours its weight into the strike.',
  'A long-legged censer draws its chain-like arms close during preparation; the broad hot bowl pitches forward with its blade.',
  'A stained molar roots itself on two bent root-legs. Its pale crown tilts back, then the whole tooth drives the chisel forward.',
  'A sour-faced old boot winds its ankle, stamps through the cut and settles onto its heavy sole. The shoehorn is the weapon.',
  'A folded moth leans its head and wing-cape together. Unequal wing panels make its front, back and side readable.',
  'A carrying snail braces its soft lower body beneath a heavy coil. Its head recoils into the shell before swinging a reed blade.',
  'A loose wooden puppet bends at shoulder, hip and knee. Its sword and wrist keep one grip while its wooden body counter-rotates.',
  'A walking oyster opens a narrow dark mouth, shifts both shell lobes and thrusts a small shucking blade. Its shell is not a shield mechanic.',
  'A soot-stained chandelier bends its central stem and candle crown into the cut. Flame highlights remain attached to candle tips.',
 ],
 'boss':[
  'A split gilded bell swells around its filthy sounding cavity. Its seam spreads before shots; its lower lip thrusts into a lunge.',
  'A huge living chalice has a dark toothy bowl and sagging stem. The bowl fills during charge, opens for the volley and tips into pursuit.',
  'A suspended silk stomach tightens its stitches before bursting from a central vent. Loose folds sag during recovery and split on death.',
  'A ring of wet leech flesh cinches around a dark maw. The front head pulls back for a volley and stretches into a lunge.',
  'A funereal bird opens an uneven fan before firing. Its hunched breast and drooping beak move together; the fan loses its spread during dying.',
  'A serving platter carries a heaped wet body with three mouths. The pile rises before release, slumps after and tears apart during dying.',
  'A choir of giant stained teeth compresses its gum base before a shot. Dark mouths open together; no individual tooth is an exclusive weak point.',
  'A cratered face is pulled by a broken mainspring. Its jaw compresses for charge, springs open to release and leads the lunge.',
  'An inverted flower bunch hangs from a fleshy stalk. Petals fold back to reveal its mouth; one immaculate bloom remains among sick tissue.',
  'An ambulant bath carries a dripping, furious face in its scum. Its body rises over claw feet for a volley and pitches down during the lunge.',
 ],
}
EXTRA_FRAMES={
 'knight':[f'{act}_{face}' for act in ('windup','strike','recover','hurt') for face in ('n','e','s')],
 'boss':['charge1','charge2','release1','release2','spawn1','spawn2','lunge1','lunge2','dying1','dying2'],
}
SIZES={'knight':(16,32),'ksword':(16,16),'boss':(32,64)}
PALETTES={'knight':'stone','ksword':'stone','boss':'blight'}
BASE_FRAMES={
 'knight':['walk_s1','walk_s2','idle_s','atk_s','walk_n1','walk_n2','idle_n','atk_n','walk_e1','walk_e2','idle_e','atk_e'],
 'ksword':['blade_e','blade_s'], 'boss':['pulse1','pulse2','hurt'],
}

def blank(w,h):return Image.new('P',(w,h),0)

def path(d,pts,fill,width=1):
    d.line(pts,fill=1,width=width+2)
    d.line(pts,fill=fill,width=width)

def poly(d,pts,fill,edge=1):
    d.polygon(pts,fill=fill)
    if edge is not None:d.line(pts+[pts[0]],fill=edge,width=1)

def oval(d,box,fill,edge=1):
    d.ellipse(box,fill=fill,outline=edge)

def eyes(d,face,cx,cy,ink=15):
    if face=='n':return
    if face=='e':
        d.rectangle((cx+1,cy,cx+2,cy+1),fill=1);d.point((cx+2,cy),fill=ink)
    else:
        d.point((cx-2,cy),fill=1);d.point((cx+2,cy),fill=1)
        d.point((cx-2,cy-1),fill=ink);d.point((cx+2,cy-1),fill=ink)

def _state(name):
    face='n' if '_n' in name else 'e' if '_e' in name else 's'
    step=-1 if name.startswith('walk') and name.endswith('1') else 1 if name.startswith('walk') and name.endswith('2') else 0
    act=name.split('_')[0]
    if act=='atk':act='strike'
    return face,step,act

def _knight(v,name):
    im=blank(16,32);d=ImageDraw.Draw(im);face,step,act=_state(name)
    # Shoulders/hips move around an invariant hand anchor; feet alternate contact.
    lean=-1 if act=='windup' else 1 if act=='strike' else 0
    if face=='n':lean=-lean
    if face=='e':lean=1 if act=='strike' else -1 if act=='windup' else 0
    squat=1 if act in ('recover','hurt') else 0
    cx=8+lean;upper=0 if not step else (0 if step<0 else 1)
    y=upper+squat
    lf=(3 if step>=0 else 1,31 if step<=0 else 29)
    rf=(13 if step<=0 else 15,31 if step>=0 else 29)
    # The stance does not rely on a translated idle frame.
    legink=10 if v in (2,5,8) else 4
    if v==7:
        poly(d,[(4,24),(10,24),(13,28),(15,30),(14,31),(8,30),(4,31),(1,31),(1,29)],5)
        d.line([(3,29),(6,28),(12,29)],fill=7)
        path(d,[(5,25),(5,29),lf],4,2);path(d,[(10,25),(11,29),rf],4,2)
    else:
        path(d,[(cx-3,23+squat),(5-lean,27),lf],legink,2)
        path(d,[(cx+2,23+squat),(11+lean,27),rf],legink,2)
    # Arm placement leaves a physically connected grip at the runtime anchor.
    hand={'n':(13,15),'e':(15,16),'s':(12,19)}[face]
    off=(1,19+squat) if face!='e' else (3,21+squat)
    if v not in (3,10):
        path(d,[(cx-3,15+y),(cx-5,18+y),off],4 if v!=8 else 11,2)
    # Individual anatomy/material silhouette, not a shared body recolor.
    if v==1: # rolled bell lip, black hanging cavity
        poly(d,[(cx-3,8+y),(cx+2,8+y),(cx+4,13+y),(cx+4,20+y),(14,24),(1,24),(cx-5,20+y),(cx-4,13+y)],11)
        poly(d,[(cx-3,10+y),(cx,9+y),(cx+1,17+y),(cx-3,21+y),(3,22)],13,None)
        poly(d,[(cx+2,11+y),(cx+3,18+y),(12,22),(8,21)],10,None)
        d.line([(2,23),(13,23)],fill=14);d.line([(3,25),(12,25)],fill=9)
        oval(d,(cx-2,12+y,cx+2,17+y),2);eyes(d,face,cx,15+y,15)
        path(d,[(cx,7+y),(cx,5+y),(cx+1,4+y)],12,1)
        d.line([(cx-2,9+y),(cx,9+y)],fill=15)
    elif v==2: # ceramic tureen with independent lid and handles
        path(d,[(2,15+y),(0,17+y),(2,20+y)],6,1)
        poly(d,[(3,12+y),(12,12+y),(14,17+y),(12,23+y),(9,25+y),(5,25+y),(2,22+y),(1,17+y)],5)
        poly(d,[(3,14+y),(8,14+y),(9,21+y),(6,23+y),(3,21+y)],7,None)
        d.line([(4,15+y),(7,15+y)],fill=8)
        poly(d,[(2,12+y),(4,9+y),(11,9+y),(13,12+y)],6)
        d.line([(4,10+y),(10,10+y)],fill=8);oval(d,(6,6+y,9,9+y),13)
        d.line([(10,14+y),(9,17+y),(11,20+y)],fill=2)
        eyes(d,face,cx,17+y,15)
        if face!='n':d.line([(6,20+y),(9,20+y)],fill=1)
    elif v==3: # censer bowl on a long-legged frame
        path(d,[(4,14+y),(1,11+y),(2,7+y)],12,1)
        path(d,[(11,14+y),(14,11+y),(13,7+y)],11,1)
        poly(d,[(3,13+y),(12,13+y),(13,18+y),(10,24+y),(5,24+y),(2,18+y)],11)
        poly(d,[(4,14+y),(7,14+y),(7,21+y),(5,21+y)],13,None)
        d.line([(3,13+y),(12,13+y)],fill=14)
        d.line([(4,16+y),(11,16+y)],fill=9)
        for x in (5,8,10):d.line([(x,18+y),(x,20+y)],fill=1)
        poly(d,[(4,10+y),(6,6+y),(9,6+y),(11,10+y)],4)
        eyes(d,face,8,9+y,15)
        path(d,[(6,7+y),(7,4+y),(10,3+y)],6,1)
        path(d,[(2,15+y),(2,19+y),off],12,1)
    elif v==4: # a chunky tooth with a cleft crown and root knees
        poly(d,[(2,8+y),(4,5+y),(7,5+y),(8,8+y),(10,5+y),(13,6+y),(14,11+y),(12,21+y),(10,25+y),(7,22+y),(4,25+y),(2,20+y),(1,13+y)],6)
        poly(d,[(3,9+y),(5,7+y),(6,8+y),(6,16+y),(4,20+y),(3,17+y)],8,None)
        poly(d,[(9,9+y),(11,7+y),(12,9+y),(11,16+y),(9,19+y)],7,None)
        d.line([(8,10+y),(7,14+y),(9,16+y),(8,20+y)],fill=5)
        eyes(d,face,cx,13+y,15)
        if face!='n':d.line([(5,17+y),(10,17+y)],fill=1)
        d.line([(3,19+y),(4,21+y)],fill=11)
    elif v==5: # shaft, folded cuff, heel and sour face
        poly(d,[(3,5+y),(11,5+y),(12,9+y),(10,17+y),(12,21+y),(14,22+y),(15,25+y),(14,27+y),(3,27+y),(1,25+y),(2,19+y)],10)
        poly(d,[(4,8+y),(7,8+y),(6,19+y),(4,23+y),(3,23+y)],12,None)
        poly(d,[(3,5+y),(11,5+y),(11,8+y),(3,9+y)],13)
        d.line([(4,6+y),(9,6+y)],fill=14)
        d.line([(2,25+y),(14,25+y)],fill=2,width=2)
        d.line([(8,10+y),(10,11+y),(8,12+y),(10,13+y),(8,14+y)],fill=7)
        eyes(d,face,6 if face=='e' else 8,17+y,15)
        if face!='n':d.line([(6,20+y),(9,21+y)],fill=1)
    elif v==6: # ragged folded wings, pale moth collar and dark head
        poly(d,[(7,12+y),(4,10+y),(1,13+y),(0,23+y),(3,21+y),(3,26+y),(7,23+y),(10,26+y),(14,24+y),(15,15+y),(12,10+y)],3)
        poly(d,[(3,13+y),(5,14+y),(7,23+y),(3,22+y),(2,20+y)],6,None)
        poly(d,[(10,13+y),(13,13+y),(12,22+y),(10,24+y)],4,None)
        d.line([(4,16+y),(5,18+y),(4,20+y)],fill=8)
        d.line([(11,16+y),(11,20+y)],fill=7)
        oval(d,(4,5+y,11,14+y),2)
        poly(d,[(5,12+y),(7,10+y),(10,12+y),(9,15+y),(6,15+y)],7)
        path(d,[(5,6+y),(3,3+y),(2,3+y)],6,1)
        path(d,[(10,6+y),(12,3+y),(13,3+y)],6,1)
        eyes(d,face,8,9+y,15)
    elif v==7: # asymmetrical coiled load with a projecting head
        oval(d,(2,8+y,14,25+y),10)
        poly(d,[(4,10+y),(8,8+y),(12,11+y),(12,20+y),(9,23+y),(5,20+y),(4,16+y)],12,None)
        d.line([(8,11+y),(11,13+y),(11,18+y),(8,20+y),(6,18+y),(6,14+y),(8,13+y),(9,15+y),(8,17+y)],fill=9,width=1)
        d.line([(4,11+y),(6,10+y)],fill=14)
        poly(d,[(3,20+y),(1,17+y),(2,12+y),(5,12+y),(6,18+y),(7,22+y)],5)
        path(d,[(2,13+y),(1,9+y)],6,1);path(d,[(5,13+y),(6,9+y)],6,1)
        if face!='n':d.point((1,9+y),fill=15);d.point((6,9+y),fill=15)
    elif v==8: # jointed marionette with one stiff knee
        path(d,[(cx-3,16+y),(cx-4,20+y),(cx-3,25+y)],11,2)
        path(d,[(cx+2,16+y),(cx+3,21+y),(cx+2,25+y)],10,2)
        poly(d,[(cx-3,14+y),(cx+2,14+y),(cx+3,22+y),(cx,25+y),(cx-3,22+y)],11)
        d.line([(cx-2,15+y),(cx-1,21+y)],fill=13)
        oval(d,(cx-1,20+y,cx+1,22+y),2)
        poly(d,[(3+lean,4+y),(10+lean,4+y),(12+lean,7+y),(11+lean,12+y),(7+lean,14+y),(3+lean,11+y)],11)
        poly(d,[(4+lean,5+y),(7+lean,5+y),(7+lean,10+y),(5+lean,12+y),(4+lean,10+y)],14,None)
        d.line([(4+lean,9+y),(10+lean,9+y)],fill=10)
        eyes(d,face,cx,8+y,15)
        if face=='e':poly(d,[(11,8+y),(15,10+y),(11,10+y)],12)
        elif face!='n':d.line([(5+lean,11+y),(9+lean,11+y)],fill=1)
    elif v==9: # paired shell flutes around a clearly animate pearl
        poly(d,[(7,7+y),(3,8+y),(0,14+y),(1,20+y),(4,25+y),(8,24+y),(12,25+y),(15,18+y),(14,12+y),(11,8+y)],5)
        for x0,xt in [(2,5),(5,7),(8,9),(11,11)]:
            d.line([(x0,14+y),(xt,9+y)],fill=8 if x0<8 else 6)
        poly(d,[(2,18+y),(6,14+y),(10,14+y),(13,18+y),(10,22+y),(5,22+y)],2)
        oval(d,(5,15+y,10,21+y),7)
        d.line([(6,16+y),(8,16+y)],fill=15)
        eyes(d,face,8,18+y,8)
        d.line([(3,23+y),(6,24+y),(10,24+y),(12,22+y)],fill=7)
    else: # an ambulant chandelier, filth attached under the bowl
        path(d,[(8,13+y),(8,23+y)],11,3)
        poly(d,[(3,19+y),(12,19+y),(11,23+y),(8,25+y),(4,23+y)],10)
        d.line([(4,20+y),(10,20+y)],fill=13)
        path(d,[(4,18+y),(1,14+y),(2,11+y)],12,1)
        path(d,[(10,18+y),(14,13+y),(13,11+y)],11,1)
        for x,yy in ((3,8+y),(8,5+y),(12,8+y)):
            d.rectangle((x-1,yy,x+1,yy+5),fill=1);d.line([(x,yy),(x,yy+3)],fill=7)
            poly(d,[(x,yy-4),(x-1,yy-2),(x,yy-1),(x+1,yy-2)],14)
            d.point((x,yy-2),fill=15)
        eyes(d,face,8,17+y,15)
        d.line([(5,23+y),(4,26+y)],fill=3)
    # The striking arm is keyed to the engine's exact grip in all facings.
    shoulder=(min(12,max(4,cx+2)),14+y)
    elbow=(min(14,cx+4),12+y) if act=='windup' else (min(14,cx+3),17+y)
    armink=12 if v in (1,2,3,8,10) else 6
    path(d,[shoulder,elbow,hand],armink,2)
    d.point(hand,fill=14 if v in (1,2,3,8,10) else 8)
    # North uses structural backs; no stray front-facing eyes are copied.
    if face=='n':
        d.line([(7+lean,13+y),(8+lean,18+y),(7+lean,22+y)],fill=3)
        if v in (1,2,4,8,9):d.line([(5+lean,10+y),(8+lean,9+y)],fill=6)
    if act=='hurt':
        d.line([(4,13+y),(6,12+y),(8,14+y)],fill=15)
        d.line([(9,22+y),(11,21+y)],fill=14)
    return im


def _weapon(v,name):
    im=blank(16,16);d=ImageDraw.Draw(im)
    # Horizontal authored once. Vertical is an exact integer clockwise turn,
    # mapping the physical grip(2,8) to(8,2), not a filtered sprite reduction.
    # Every tool reaches the same native endpoint as the original blade.
    if v==1: # broad clapper blade
        path(d,[(0,8),(4,8)],11,2)
        poly(d,[(4,7),(11,5),(15,7),(15,9),(11,11),(4,9)],6)
        d.line([(5,7),(11,6),(14,7)],fill=8);d.line([(3,5),(3,11)],fill=13)
    elif v==2: # open ladle silhouette with a sharpened rim
        path(d,[(0,8),(10,8)],11,1)
        oval(d,(10,5,15,11),7);oval(d,(12,7,14,9),2)
        d.line([(11,6),(14,6)],fill=15)
    elif v==3: # chain-suspended incense knife
        path(d,[(0,8),(6,8)],12,1)
        poly(d,[(6,7),(10,5),(15,7),(13,10),(7,10)],6)
        d.line([(8,7),(13,6)],fill=8);d.point((2,7),fill=14)
    elif v==4: # masonry chisel
        path(d,[(0,8),(5,8)],11,2)
        poly(d,[(5,6),(14,6),(15,8),(13,10),(5,10)],6)
        d.line([(6,6),(13,6)],fill=8);d.line([(4,5),(4,11)],fill=10)
    elif v==5: # worn metal shoehorn
        path(d,[(0,8),(6,8)],10,1)
        poly(d,[(6,7),(12,5),(15,6),(15,9),(11,11),(6,9)],5)
        d.line([(7,7),(12,6),(14,6)],fill=8)
    elif v==6: # narrow thorn-tine
        path(d,[(0,8),(5,8)],11,1)
        poly(d,[(5,7),(10,7),(15,5),(13,8),(15,10),(9,9),(5,9)],7)
        d.line([(6,7),(10,7),(13,6)],fill=8);d.line([(3,6),(3,10)],fill=12)
    elif v==7: # reed cutter wrapped at the grip
        path(d,[(0,8),(7,8)],10,1)
        poly(d,[(6,7),(14,6),(15,7),(12,9),(6,9)],6)
        d.line([(7,7),(13,6)],fill=8);d.point((3,7),fill=14)
    elif v==8: # a thin toy saber with a chipped broad point
        path(d,[(0,8),(4,8)],11,1)
        poly(d,[(4,7),(12,7),(15,5),(14,9),(10,10),(4,9)],7)
        d.line([(5,7),(12,7)],fill=8);d.line([(3,5),(3,11)],fill=13)
    elif v==9: # triangular shucking blade
        path(d,[(0,8),(5,8)],11,2)
        poly(d,[(5,6),(15,8),(5,10)],6)
        d.line([(6,6),(13,8)],fill=8);d.line([(4,5),(4,11)],fill=13)
    else: # dripping wax-edged candle sword, same damaging reach
        path(d,[(0,8),(4,8)],11,1)
        poly(d,[(4,6),(12,6),(15,8),(12,10),(4,10)],7)
        d.line([(5,6),(12,6)],fill=15);d.line([(7,9),(7,11)],fill=6)
        d.line([(3,5),(3,11)],fill=13)
    if name=='blade_s':
        # Matrix transpose swaps axes: grip(2,8)->(8,2) and endpointE->S.
        im=im.transpose(Image.Transpose.TRANSPOSE)
    return im


def _boss(v,name):
    im=blank(32,64);d=ImageDraw.Draw(im)
    pulse=1 if name in ('pulse2','charge2','release2','spawn2','lunge2','dying2') else 0
    charge=name.startswith('charge');release=name.startswith('release');spawn=name.startswith('spawn');lunge=name.startswith('lunge');dying=name.startswith('dying')
    hurt=name=='hurt';sag=(2 if dying else 1 if name=='release2' else 0)
    spread=(2+pulse) if charge or release else pulse
    top=(-2-pulse) if charge else (1+pulse) if dying else -pulse
    # Dark structural mass is concentrated inside HB_HEART x2..29,y22..62.
    # Top flourishes are thinner; no bright emblem claims a gated weakness.
    if v==1: # cracked coronation bell
        poly(d,[(12,22+top),(21,22+top),(24,27),(26,38),(27+spread,49),(30,53+sag),(28,57+sag),(3,57+sag),(1,53+sag),(5-spread,49),(7,34),(9,27)],9)
        poly(d,[(11,26),(16,25+top),(18,33),(16,47),(7,51),(8,36)],11,None)
        poly(d,[(19,28),(22,30),(23,43),(26,51),(19,48)],4,None)
        d.line([(4,53+sag),(28,53+sag)],fill=11,width=2)
        d.line([(5,52+sag),(16,51+sag)],fill=15)
        poly(d,[(12,36),(16,33),(20,35),(23,43),(21,49),(17,51),(11,48),(9,42)],1)
        oval(d,(12,38,20,47+(1 if release else 0)),3)
        if release:oval(d,(13,37,20,48),1);d.line([(14,38),(18,38)],fill=14)
        else:d.line([(13,40),(19,40)],fill=14);d.point((16,44),fill=15)
        path(d,[(10,24),(8,20),(10,17),(14,19),(18,17),(21,20),(20,24)],10,2)
        d.line([(10,19),(13,20)],fill=15)
        d.line([(19,26),(17,31),(19,35),(17,40)],fill=12,width=2)
        for x in (7,24):path(d,[(x,56),(x-2,60),(x+1,62)],8,1)
    elif v==2: # a monstrous holy vessel, clearly a body not a pickup
        poly(d,[(2,26+top),(29,26+top),(28,38),(24,46),(19,51),(18,56),(24,60),(24,62),(6,62),(6,60),(12,56),(12,51),(7,46),(3,37)],9)
        poly(d,[(4,28+top),(13,28+top),(13,42),(16,49),(11,46),(7,41)],11,None)
        d.line([(4,27+top),(28,27+top)],fill=15,width=2)
        poly(d,[(6,30),(24,30),(23,38+spread),(20,42+spread),(11,42+spread),(7,38+spread)],1)
        for x in (9,14,20):poly(d,[(x,31),(x+2,31),(x+1,35)],15)
        if release:oval(d,(10,34,21,45),1)
        else:d.line([(9,36),(12,37)],fill=14);d.line([(20,36),(23,35)],fill=14)
        d.line([(13,48),(14,55),(11,59)],fill=13)
        for x in (4,25):path(d,[(x,38),(x-2 if x<16 else x+2,43),(x,48)],4,2)
        d.line([(7,61),(18,61)],fill=15)
        d.line([(24,39),(25,44),(24,47)],fill=12)
    elif v==3: # stitched, hanging stomach/cocoon
        path(d,[(12,24),(9,18),(10,14)],8,2);path(d,[(20,24),(24,19),(23,15)],9,2)
        poly(d,[(12,22+top),(21,23+top),(27,30),(29,42),(25,53+sag),(20,59+sag),(11,59+sag),(4,52+sag),(2,40),(5,30)],4)
        poly(d,[(10,25+top),(15,25+top),(14,34),(9,38),(7,47),(5,44),(5,34)],7,None)
        poly(d,[(20,28),(24,33),(25,44),(21,52),(18,54),(17,45)],12,None)
        seam=[(15,27),(16,33),(14,39),(17,45),(15,53),(17,58)]
        d.line(seam,fill=1,width=2)
        for x,y in seam[1:-1]:d.line([(x-2,y-1),(x+2,y+1)],fill=15)
        oval(d,(9-spread,36,21+spread,45+spread),1)
        d.line([(10,37),(14,36)],fill=14)
        if not release:d.line([(11,40),(19,40)],fill=8)
        for x,y in ((5,50),(24,47),(20,57)):
            path(d,[(x,y),(x-2,y+5),(x,y+7)],8,1)
        d.line([(9,28),(11,27)],fill=15)
    elif v==4: # a wet coil with a fanged front head
        poly(d,[(8,24+top),(18,22+top),(26,27),(29,35),(28,46),(24,55),(18,60+sag),(9,60+sag),(3,53),(1,42),(3,31)],3)
        poly(d,[(8,27+top),(17,25+top),(23,29),(25,36),(22,47),(18,53),(9,54),(5,47),(5,36)],6,None)
        oval(d,(8-spread,31,24+spread,52+sag),1)
        oval(d,(11,34,22,48),8)
        oval(d,(12-spread,37,22+spread,47+(2 if release else 0)),1)
        d.line([(11,35),(14,34),(18,34)],fill=15)
        for x,y in ((12,38),(17,36),(21,40),(15,46)):
            poly(d,[(x,y),(x+2,y),(x+1,y+3)],15)
        path(d,[(8,28),(6,22),(8,19)],12,2)
        path(d,[(19,26),(23,20),(25,22)],12,2)
        for y in (31,41,51):d.line([(4,y),(6,y-1)],fill=14)
        d.line([(22,53),(20,55),(17,56)],fill=13)
    elif v==5: # torn fan and drooping beak, not a huge winged pickup
        fan=[(2,35),(1,26),(4,21),(7,26),(9,19),(13,27),(17,18),(20,26),(25,20),(27,29),(30,24),(30,38),(26,46),(5,46)]
        if dying:fan=[(x, y+5 if y<30 else y) for x,y in fan]
        poly(d,fan,3)
        for x,y in ((4,25),(9,24),(17,23),(24,26),(28,31)):
            path(d,[(16,43),(x,y+top)],5,2)
            oval(d,(x-2,y-2+top,x+2,y+2+top),12)
            d.point((x-1,y-1+top),fill=15)
        poly(d,[(12,33+top),(20,32+top),(24,39),(23,49+sag),(19,57+sag),(11,56+sag),(7,47),(9,39)],4)
        poly(d,[(12,35),(16,34),(16,45),(13,51),(10,46)],7,None)
        path(d,[(13,53),(11,59),(7,62)],8,2);path(d,[(20,54),(22,59),(26,62)],8,2)
        oval(d,(12,27+top,21,38+top),6)
        d.line([(14,28+top),(17,28+top)],fill=15)
        oval(d,(17,31+top,20,34+top),1)
        poly(d,[(17,36+top),(24+(1 if lunge else 0),38),(19,44+spread),(18,40)],11)
        d.line([(19,38),(22,38)],fill=15)
        if release:d.line([(19,40),(23,40),(20,44)],fill=1,width=2)
    elif v==6: # a banquet pile on a crooked platter
        poly(d,[(1,51),(30,51),(29,57+sag),(24,60+sag),(7,60+sag),(2,57+sag)],9)
        d.line([(3,52),(26,52)],fill=15,width=2)
        for box,fill in [((6,35+top,24,55+sag),4),((2,32+top,16,48),6),((13,25+top,28,46),5),((8,22+top,21,37),7)]:oval(d,box,fill)
        poly(d,[(7,39),(11,37),(15,40),(17,48),(14,53),(7,52),(5,46)],12,None)
        for x,y in ((9,36+top),(21,34+top),(16,47)):
            oval(d,(x-3-spread//2,y-2,x+3+spread//2,y+3+(2 if release else 0)),1)
            d.line([(x-2,y-1),(x,y-1)],fill=15)
        for x,y in ((8,27+top),(17,24+top),(25,31)):
            d.line([(x,y),(x+2,y)],fill=15)
        path(d,[(7,59),(5,62)],8,1);path(d,[(24,59),(27,62)],8,1)
    elif v==7: # grinning molar chorus in a sagging gum base
        poly(d,[(3,44),(7,38),(25,38),(29,46),(28,56+sag),(22,61+sag),(8,61+sag),(3,56+sag)],12)
        poly(d,[(5,45),(10,43),(12,50),(9,57),(5,54)],14,None)
        teeth=[(2,29+top,12,49),(11,22+top,22,49),(21,31+top,30,51)]
        for k,(x0,y0,x1,y1) in enumerate(teeth):
            poly(d,[(x0,y0+3),(x0+2,y0),(x0+4,y0),(x0+5,y0+2),(x1-2,y0),(x1,y0+3),(x1-1,y1-3),(x1-4,y1),(x0+2,y1-1)],7)
            poly(d,[(x0+2,y0+4),(x0+4,y0+3),(x0+4,y1-7),(x0+2,y1-5)],15,None)
            mx=(x0+x1)//2;my=y0+11
            oval(d,(mx-3,my-2,mx+3,my+3+(2 if release else 0)),1)
            d.line([(mx-2,my-1),(mx,my-1)],fill=14)
            d.line([(x1-3,y1-9),(x1-4,y1-6),(x1-2,y1-3)],fill=8)
        path(d,[(8,58),(5,62)],8,2);path(d,[(23,58),(27,62)],8,2)
    elif v==8: # a cracked moon-mask carried by its mainspring
        oval(d,(2,23+top,29,54+sag),6)
        poly(d,[(8,25+top),(15,24+top),(16,31),(11,37),(8,47),(5,43),(5,32)],7,None)
        poly(d,[(21,29),(26,34),(25,45),(20,50),(18,43)],4,None)
        for x,y,r in ((8,33,3),(24,40,3),(11,47,2)):
            oval(d,(x-r,y-r,x+r,y+r),3);d.line([(x-r+1,y-r+1),(x,y-r)],fill=5)
        oval(d,(10-spread,35,23+spread,45+(2 if release else 0)),1)
        for x in (12,17,21):poly(d,[(x,36),(x+1,39),(x+2,36)],15)
        d.line([(18,24),(16,29),(18,32),(16,35)],fill=1,width=2)
        path(d,[(12,52),(8,55),(22,57),(10,60),(19,62)],10,2)
        d.line([(10,55),(19,56)],fill=15)
        path(d,[(7,25),(6,19),(9,16)],8,2);path(d,[(25,27),(27,20),(25,18)],8,2)
    elif v==9: # inverted bloom around a grub face
        path(d,[(16,25),(18,17),(15,12)],8,3)
        petals=[[(14,22),(7,21),(2,27),(5,36),(12,37),(15,31)],[(18,22),(25,22),(30,30),(26,38),(20,36),(16,30)],[(12,34),(4,35),(1,43),(7,49),(14,45),(17,38)],[(21,34),(28,37),(31,45),(24,51),(18,45),(16,38)]]
        for k,p in enumerate(petals):
            poly(d,p,5 if k%2 else 12)
            d.line([p[1],p[2]],fill=14 if k%2==0 else 7,width=2)
        poly(d,[(12,31+top),(21,31+top),(25,39),(24,51+sag),(21,58+sag),(12,60+sag),(7,53+sag),(7,41)],4)
        poly(d,[(11,35),(15,33),(15,43),(12,50),(10,47)],7,None)
        oval(d,(10-spread,39,22+spread,49+(2 if release else 0)),1)
        d.line([(12,40),(16,40)],fill=15)
        for x in (13,18):poly(d,[(x,41),(x+2,41),(x+1,44)],14)
        path(d,[(12,56),(8,61),(4,62)],8,2);path(d,[(21,56),(24,61),(28,62)],8,2)
        for p in [[(4,24),(4,21),(6,20),(8,22),(7,24)],[(6,24),(9,23),(11,25),(9,27),(7,26)]]:poly(d,p,15)
    else: # a claw-foot bath filled with diseased living water
        path(d,[(6,52),(5,59),(2,62)],8,2);path(d,[(24,52),(26,59),(30,62)],8,2)
        poly(d,[(1,34),(30,34),(28,48+sag),(23,55+sag),(10,56+sag),(4,50+sag)],6)
        poly(d,[(4,37),(12,38),(13,49),(9,52),(5,48)],7,None)
        poly(d,[(1,33),(5,30),(27,30),(31,33),(28,37),(4,37)],8)
        oval(d,(5-spread//2,26+top,28,36),3)
        poly(d,[(9,30),(10,25+top),(14,22+top),(18,23+top),(22,29),(25,33),(19,35),(13,33)],12)
        d.line([(12,26+top),(14,25+top)],fill=15)
        oval(d,(12,28+top,16,30+top),1);oval(d,(20,29,23,31),1)
        oval(d,(14-spread//2,32,24+spread//2,39+(2 if release else 0)),1)
        d.line([(15,33),(18,33)],fill=15)
        path(d,[(5,32),(5,23),(8,20),(11,21)],10,2)
        d.line([(6,23),(8,21),(10,21)],fill=15)
        d.line([(25,36),(26,42),(24,45)],fill=12,width=2)
        d.line([(8,39),(10,38),(13,39)],fill=15)
    # Motion changes the broad body, not isolated ornamental dust. A lunge
    # shifts upper mass forward within its native canvas, keeping the lower
    # contact mass close to the original collision footprint.
    if lunge:
        src=im.copy();im=blank(32,64)
        a=Image.new('1',src.size);a.putdata([bool(x) for x in src.tobytes()])
        # Lower mass stays planted; upper mass stretches2px toward viewer.
        upper=src.crop((0,0,32,43));mask=a.crop((0,0,32,43));im.paste(upper,(0,2),mask)
        lower=src.crop((0,43,32,64));im.paste(lower,(0,43),a.crop((0,43,32,64)))
        d=ImageDraw.Draw(im)
        d.line([(10,44),(13,45),(18,45),(21,44)],fill=12,width=2)
    if spawn:
        # Distinct small exit vents, not new invulnerable damage targets.
        oval(d,(3,44,10,51+2*pulse),1);oval(d,(23,45,29,52+2*pulse),1)
        d.line([(5,45),(8,45)],fill=14);d.line([(24,46),(27,46)],fill=14)
    if hurt:
        # Attached irregular stress split, not an all-white invulnerability rim.
        d.line([(10,29),(13,33),(12,38),(16,42),(14,47),(18,52)],fill=15,width=2)
        d.line([(11,30),(14,34)],fill=14)
    if dying:
        # Body collapses inside the same canvas; black negative spaces widen.
        d.polygon([(12,33),(15,39),(13,45),(17,50),(16,59),(19,55),(18,47),(21,41),(17,35)],fill=1)
        if pulse:
            d.line([(5,51),(10,54),(15,55),(20,54),(25,51)],fill=8,width=2)
            d.line([(13,39),(15,44),(14,49)],fill=14)
    elif charge:
        d.line([(10,30),(12,27),(15,26)],fill=15)
        d.line([(23,46),(23,49)],fill=14)
    elif release:
        d.line([(9,39),(11,37)],fill=15);d.line([(23,41),(24,43)],fill=14)
    return im


def frame(family,variant,name):
    assert family in SIZES,(family,variant,name)
    assert 1<=variant<=10,(family,variant,name)
    valid=BASE_FRAMES[family]+EXTRA_FRAMES.get(family,[])
    assert name in valid,(family,variant,name)
    im=_knight(variant,name) if family=='knight' else _weapon(variant,name) if family=='ksword' else _boss(variant,name)
    assert im.mode=='P' and im.size==SIZES[family]
    assert set(im.tobytes())<=set(range(16))
    return im


def preview(out):
    """Source-only context/complete-pose boards, never emulator evidence."""
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
    for family in ('knight','boss'):
        w,h=SIZES[family];cellw=200;cellh=156 if family=='knight' else 244
        overview=Image.new('RGB',(5*cellw,28+2*cellh),'#101820');od=ImageDraw.Draw(overview);od.fontmode='1'
        od.text((8,7),'SOURCE ART / native pixels and3x nearest-neighbour / not emulator output',font=font,fill='#f0d898')
        for v in range(1,11):
            x=(v-1)%5*cellw;y=28+(v-1)//5*cellh
            im=C.rgba(frame(family,v,'idle_s' if family=='knight' else 'pulse1'),C.PALETTES[PALETTES[family]])
            overview.paste(im.resize((w*3,h*3),Image.Resampling.NEAREST),(x+10,y+8),im.resize((w*3,h*3),Image.Resampling.NEAREST))
            overview.paste(im,(x+126,y+h*2),im)
            od.text((x+7,y+cellh-25),f'{v}. {CONCEPTS[family][v-1]}',font=font,fill='#f0d898')
            # Every pose, with base and appended action frames explicitly named.
            names=BASE_FRAMES[family]+EXTRA_FRAMES.get(family,[])
            cw=max(112,w*3+12);ch=h*3+30;cols=6
            sheet=Image.new('RGB',(cw*cols,34+((len(names)+cols-1)//cols)*ch),'#203038');sd=ImageDraw.Draw(sheet);sd.fontmode='1'
            sd.text((6,6),f'SOURCE / {v}. {CONCEPTS[family][v-1]} / all {len(names)} poses',font=font,fill='#f0d898')
            for n,nm in enumerate(names):
                px=n%cols*cw+6;py=34+n//cols*ch
                a=C.rgba(frame(family,v,nm),C.PALETTES[PALETTES[family]]);big=a.resize((w*3,h*3),Image.Resampling.NEAREST)
                sheet.paste(big,(px,py),big);sd.text((px,py+h*3+5),nm,font=font,fill='#d0d8c0')
            sheet.save(out/f'{family}-{v:02}-all-frames.png')
        overview.save(out/f'{family}-ten-concepts.png')
    # Per-option guard body+weapon in actual origin conventions, source only.
    context=Image.new('RGB',(800,28+10*92),'#101820');cd=ImageDraw.Draw(context);cd.fontmode='1'
    cd.text((8,6),'SOURCE / silhouettes over quiet sewer, green, blight and cave swatches / not game output',font=font,fill='#f0d898')
    backgrounds=['#485858','#385038','#483048','#303840']
    for v in range(1,11):
        for col,bg in enumerate(backgrounds):
            xx=col*200;yy=28+(v-1)*92;cd.rectangle((xx,yy,xx+199,yy+91),fill=bg)
            for pos,nm in enumerate(('idle_s','windup_s','strike_s','recover_s')):
                b=C.rgba(frame('knight',v,nm),C.PALETTES['stone']);context.paste(b,(xx+8+pos*42,yy+16),b)
            cd.text((xx+5,yy+64),f'{v}. {CONCEPTS["knight"][v-1]}',font=font,fill='#f0d898')
    context.save(out/'knight-native-context.png')
    checks=[]
    for fam in SIZES:
        for v in range(1,11):
            imgs=[frame(fam,v,n) for n in BASE_FRAMES[fam]+EXTRA_FRAMES.get(fam,[])]
            checks.append({'family':fam,'variant':v,'frames':len(imgs),'unique':len(set(im.tobytes() for im in imgs)),'bounds':[im.getbbox() for im in imgs]})
    (out/'native-validation.json').write_text(json.dumps({'method':'Direct native canvas/index/frame-count checks; no visual quality score.','checks':checks,'source_only':True},indent=2)+'\n')
    # Direct native pose cycles: labelled SOURCE, never mGBA footage.
    for family in ('knight','boss'):
        steps=[]
        if family=='knight':
            for face in ('s','e','n','w'):
                srcface='e' if face=='w' else face
                for action,hold in [('idle',10),('walk1',8),('walk2',8),('walk1',8),('walk2',8),('windup',16),('strike',14),('recover',24),('hurt',12)]:
                    nm=('walk_'+srcface+action[-1]) if action.startswith('walk') else action+'_'+srcface
                    steps.append((nm,hold,face,action))
        else:
            for nm,hold in [('pulse1',16),('pulse2',16),('charge1',10),('charge2',10),('release1',8),('release2',8),('pulse1',16),('spawn1',10),('spawn2',10),('lunge1',12),('lunge2',12),('hurt',12),('dying1',20),('dying2',20)]:steps.append((nm,hold,'s',nm))
        frames=[];durations=[]
        for nm,hold,face,action in steps:
            board=Image.new('RGB',(800,28+2*172),'#182028');bd=ImageDraw.Draw(board);bd.fontmode='1'
            bd.text((8,6),f'SOURCE animation / {family}: {nm} / native +2x / not emulator output',font=font,fill='#f0d898')
            for v in range(1,11):
                xx=(v-1)%5*160;yy=28+(v-1)//5*172
                scene=Image.new('RGBA',(64,72),(0,0,0,0))
                a=frame(family,v,nm)
                if face=='w':a=a.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                a=C.rgba(a,C.PALETTES[PALETTES[family]])
                if family=='knight':
                    scene.alpha_composite(a,(24,36))
                    if action in ('windup','strike'):
                        vertical=action=='windup' or face in ('n','s');weapon=frame('ksword',v,'blade_s' if vertical else 'blade_e')
                        flipx=face=='w';flipy=vertical and (action=='windup' or face=='n')
                        gx,gy=(8,2) if vertical else (2,8)
                        if flipx:weapon=weapon.transpose(Image.Transpose.FLIP_LEFT_RIGHT);gx=15-gx
                        if flipy:weapon=weapon.transpose(Image.Transpose.FLIP_TOP_BOTTOM);gy=15-gy
                        hx,hy={'n':(5,-17),'e':(7,-16),'s':(4,-13),'w':(-8,-16)}[face]
                        weapon=C.rgba(weapon,C.PALETTES['stone'])
                        scene.alpha_composite(weapon,(32+hx-gx,68+hy-gy))
                else:scene.alpha_composite(a,(16,4))
                big=scene.resize((128,144),Image.Resampling.NEAREST)
                board.paste(big,(xx+10,yy),big)
                bd.text((xx+5,yy+148),f'{v}. {CONCEPTS[family][v-1]}',font=font,fill='#f0d898')
            frames.append(board);durations.append(round(hold*1000/60))
        frames[0].save(out/f'{family}-ten-source-animation.gif',save_all=True,append_images=frames[1:],duration=durations,loop=0,optimize=False,disposal=2)
    return out

if __name__=='__main__':
    import sys
    preview(sys.argv[1] if len(sys.argv)>1 else '/workspace/setup/appearance-enemy-studies/heavy')
