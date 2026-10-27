"""Three required events in the real ROM: no free rewards, earned items,
completed event persistence, reward ownership, and no duplicate reward.

python tools/mandatory_trials.py [--seed 0xB4A7]
Debug navigation chooses generated cells; event completion uses real plate
steps and sword hits. Healing isolates logic from combat difficulty.
"""
import os
import sys
sys.path.insert(0,os.path.dirname(__file__))
import probe as P
import critical_path as C
import lift_probe as L
import myst_probe as M


def main():
    seed=int(sys.argv[sys.argv.index('--seed')+1],0) if '--seed' in sys.argv else 0xB4A7
    c=P.boot(seed=seed); P.enter_forest(c)
    w=C.world(c); results=[]
    def check(name,ok,detail=''):
        results.append(bool(ok));print(('PASS' if ok else 'FAIL'),name,detail,flush=True)
    W=P.sym('gWorld'); pl=P.sym('gPl')
    for index,cell in enumerate(w['key_cell']):
        bit=2<<index
        side=next(s for s,g in enumerate(w['cells'][cell]['gate']) if g)
        C.heal(c); L.warp(c,cell,side)
        packed=P.r8(c,W+M.MYST_OFF+cell)
        kind=M.KINDS[packed&15]
        check('a mandatory event is item-independent',kind in ('switches','waves','miniboss'),kind)
        check('the reward is not owned on arrival',not(P.r8(c,pl+8)&bit))
        check('the forest has no free progression chest',not M.tiles_of(c,lambda m:m['type']=='CHEST'))
        check('an unfinished trial permits retreat',C.enter_trial(c) and M.leave(c)==1)
        check('retreat grants no item',not(P.r8(c,pl+8)&bit))
        ok=C.earn_trial(c,claim=False)
        check('the event is completed before its reward',ok and not(P.r8(c,pl+8)&bit))
        check('won but unclaimed trial can be left',M.leave(c)==1)
        check('returning retains earned reward',C.enter_trial(c) and bool(M.tiles_of(c,lambda m:m['type']=='CHEST')))
        check('a won event does not restart its fight',C.find_actor(c,2) is None)
        check('the earned reward is claimable',M.open_chest(c))
        C.dismiss(c)
        check('claim returns to forest',M.leave(c)==1)
        check('the barrier item is owned',P.r8(c,pl+8)&bit)
        flags=P.r8(c,W+4+cell*13+11)
        mf=P.r8(c,W+M.FLAGS_OFF+cell)
        check('item and event ownership persist',flags&0x0A==0x0A and mf&5==5,'cell %02x event %02x'%(flags,mf))
        bombs=P.r8(c,pl+7)
        check('completed trial can be revisited',C.enter_trial(c))
        check('won trial does not respawn enemies',C.find_actor(c,2) is None)
        check('won trial has no new reward chest',not M.tiles_of(c,lambda m:m['type']=='CHEST'))
        check('reward cannot duplicate bombs',P.r8(c,pl+7)==bombs)
        C.dismiss(c)
        check('completed trial exit stays open',M.leave(c)==1)
    print('RESULT %s %d/%d'%('PASS' if all(results) else 'FAIL',sum(results),len(results)))
    return 0 if all(results) else 1

if __name__=='__main__':sys.exit(main())
