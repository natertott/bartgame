"""Regression: relic collection must not move a persistent side pocket.

    python tools/revisit_probe.py

Seed 7 previously moved its relic room's candle pocket from (11,20) to
(22,20) after collection. This boots the real ROM, collects the actual relic,
then rebuilds the room with inventory cleared as after quest hand-in. Debug
navigation and an already-open pocket flag are fixtures; collection itself
uses the normal actor pickup handler.
"""
import sys
import probe as P
import critical_path as CP
import lift_probe as LP


def main():
    checks=[]
    def check(name,ok,detail=''):
        checks.append(bool(ok))
        print(('PASS' if ok else 'FAIL')+' '+name+' '+detail,flush=True)
    c=P.boot(seed=7)
    world=CP.world(c)
    cell=next(i for i,d in enumerate(world['cells']) if d['role']==8)
    side=next(i for i,g in enumerate(world['cells'][cell]['gate']) if g)
    P.enter_forest(c)
    LP.warp(c,cell,side)
    CP.clear_enemies(c); CP.heal(c)
    spots=P.sym('gSpots')
    def pocket():
        return tuple(P.r8(c,spots+i) for i in (44,45,53,55,56,57))
    before=pocket()
    check('relic room has a side pocket',before[2]==1,str(before))
    relic=CP.find_actor(c,4,5)
    check('the placed relic exists',relic is not None)
    if relic:
        CP.teleport(c,relic['x'],relic['y']+2)
        P.run(c,30)
    pl=P.sym('gPl'); state=P.sym('gWorld')+4+cell*13
    check('normal collection grants the relic',P.r8(c,pl+8)&16)
    check('collection persists on its source cell',P.r8(c,state+11)&16)
    # An already-open side pocket must stay in place when the relic disappears.
    P.w8(c,state+4,P.r8(c,state+4)|32)
    P.w8(c,pl+8,P.r8(c,pl+8)&~16)
    LP.warp(c,cell,side)
    check('pocket coordinates and kind survive revisit',pocket()==before,str(pocket()))
    check('the claimed relic does not respawn after hand-in',CP.find_actor(c,4,5) is None)
    gx,gy=before[3:5]
    R=P.sym('gRoom');mt=P.r16(c,R+2+(gy*32+gx)*2)&65535
    check('the same pocket remains open',P.r8(c,P.sym('metatile_type')+mt)==0)
    check('pedestal coordinates are stable',tuple(P.r8(c,spots+i) for i in (29,30))==
          (relic['x']//16,relic['y']//16) if relic else False)
    print('RESULT %s %d/%d'%('PASS' if all(checks) else 'FAIL',sum(checks),len(checks)))
    return 0 if all(checks) else 1


if __name__=='__main__':sys.exit(main())
