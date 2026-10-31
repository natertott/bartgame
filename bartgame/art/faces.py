"""Six native48×48 dialogue busts, matching the rebooted world characters."""
from reboot_ui import FACES as BASE_FACES
import sewer_concepts as SC
import forest_concepts as FC
FACES=list(BASE_FACES)
W=H=48
if SC.VARIANT:
    import sewer_concepts_npcs as SCN
    for i,(name,palette,rows) in enumerate(FACES):
        if name not in ('peddler','gatekeeper'):
            continue
        style=SC.RECIPE['peddler' if name=='peddler' else 'wizard']
        image=SCN.portrait(style,name)
        assert image.mode=='P' and image.size==(48,48),(name,image.mode,image.size)
        colors=SCN.peddler_palette(style) if name=='peddler' else SCN.wizard_palette(style)
        rgb=lambda color:tuple(int(color[j:j+2],16) for j in (1,3,5))
        palette=[(format(k,'x'),rgb(colors[k])) for k in range(1,16)]
        rows=[''.join('.' if image.getpixel((x,y))==0 else format(image.getpixel((x,y)),'x')
                      for x in range(48)) for y in range(48)]
        FACES[i]=(name,palette,rows)
if FC.VARIANT:
    import forest_concepts_folk as FCF
    for i,(name,palette,rows) in enumerate(FACES):
        if name not in ('hermit','nun','gardener'):
            continue
        image=FCF.portrait(name,FC.VARIANT)
        assert image.mode=='P' and image.size==(48,48),name
        colors=FCF.portrait_palette(name,FC.VARIANT)
        rgb=lambda color:tuple(int(color[j:j+2],16) for j in (1,3,5))
        palette=[(format(k,'x'),rgb(colors[k])) for k in range(1,16)]
        rows=[''.join('.' if image.getpixel((x,y))==0 else format(image.getpixel((x,y)),'x')
                      for x in range(48)) for y in range(48)]
        FACES[i]=(name,palette,rows)
