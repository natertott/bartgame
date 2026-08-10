"""Does every content site actually put something in its room?

Boots once per content-site room, lands the player DELIBERATELY AWAY from the
site's content spot (landing on it means the player collects the reward on the
spawn frame, which looks like a bug and is not), and reports whether the room
holds a ground item.

Written for the open "item-drop ? rooms appear empty" bug - see section 5 of
docs/QUICKSTART_ROADMAP.md. Run from the repo root.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu import boot, warp, here, GENT, MAX_ENT, STRIDE, SAVE_FLAGS, QS_BIT0, room_dims
import parse_tables as P
KIND={0:'CHEST',1:'MINIBOSS',2:'NPC',3:'WAVES',4:'POT_LOT',5:'CHEST_LOT',6:'FAIRY'}
def qs(c,n):
    b=QS_BIT0+n; return (c.memory.u8[SAVE_FLAGS+(b>>3)]>>(b&7))&1
def items(c):
    out=[]
    for i in range(MAX_ENT):
        b=GENT+i*STRIDE
        if c.memory.u8[b+0]==6 and c.memory.u8[b+1]==0:
            out.append(c.memory.u8[b+2])
    return out
sites=P.content_sites()
rooms={}
for idx,(_k,_l,a,r,cx,cy) in enumerate(sites):
    rooms.setdefault((a,r),[]).append((idx,cx,cy))
bad=ok=0
for (a,r),m in list(rooms.items()):
    idx,cx,cy=m[0]
    c=boot('tmc.gba'); c.memory.u8[0x03000bf0+4]=0
    # Land well away from the content spot so the player cannot collect it.
    warp(c,a,r,cx,cy,frames=60)
    W,H=room_dims(c)
    px = 24 if cx > 80 else max(W-24, cx+80)
    py = 24 if cy > 80 else max(H-24, cy+80)
    warp(c,a,r,px,py,frames=240)
    if here(c)!=(a,r): print(f'area {a} room {r}: did not land'); continue
    st=[(qs(c,266+i*13+12), sum(qs(c,266+i*13+1+b)<<b for b in range(3))) for i,_,_ in m]
    it=items(c)
    chest=[k for (_d,k) in st if k==0]
    verdict='OK' if (not chest or it) else 'EMPTY'
    if verdict=='EMPTY': bad+=1
    else: ok+=1
    print(f'area {a:3d} room {r:3d} kinds={[KIND.get(k,k) for (_d,k) in st]} done={[d for (d,_k) in st]} items={it} -> {verdict}')
print(f'\n{ok} OK / {bad} EMPTY')
