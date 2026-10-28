"""Keeper animation metadata for the native art reboot.

No sprite drawings live here. reboot_actors owns their native pixels; this
module supplies the small declarative acts and material pulse consumed by
build_assets and npc.c.
"""
import reboot_core as C


def _rgb(value):return tuple(int(value[i:i+2],16) for i in (1,3,5))


PEDDLER_PAL=list(zip('o123456789abcde',map(_rgb,C.PALETTES['gold'][1:])))
# The pulsing pair is deliberately reserved for the orb, never clothing.
GATEKEEPER_PAL=list(zip('oabcdefghijkvVw',map(_rgb,C.PALETTES['stone'][1:])))
ORB_GLOW=[tuple(_rgb(C.PALETTES['stone'][i]) for i in pair)
          for pair in ((12,13),(13,14),(14,15),(13,14),(12,13),(13,14),(14,15),(13,14))]
WISP_AT=(20,13) #8x8 bright centre(3,4) meets orb centre(23,17) in32x32body.

SPIN_TURN=[9,7,5,3,-5,-7,-9,-7,-5,3,5,7]


def _spin():
    steps=[('lift','down',10)]
    for hold in (3,3,4):
        for width in SPIN_TURN:
            steps.append(('spin%d%s'%(abs(width),'b' if width<0 else ''),'down',hold))
    return steps+[('slap','down',14),('slap','grin',30)]


PEDDLER_ACTS=[_spin(),[('rub0','grin',6),('rub1','grin',6)]*6,
              [('tap','open',7),('tap2','open',7)]*5]
assert len(PEDDLER_PAL)==len(GATEKEEPER_PAL)==15
assert [key for key,_ in GATEKEEPER_PAL].index('V')==[key for key,_ in GATEKEEPER_PAL].index('v')+1
