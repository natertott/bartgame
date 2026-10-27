"""Install the supplied item pixels across displays and Bloom's held props.

Frame dimensions and ordering retain the engine contracts. Item frames carry
one of four world palette banks; paused inventory frames use their own ramps.
"""
from PIL import Image, ImageDraw, ImageOps
import clean_items
import reference_items as R


def old_image(rows):
    im=Image.new('RGBA',(len(rows[0]),len(rows)))
    for y,row in enumerate(rows):
        for x,ch in enumerate(row):
            if ch not in '.0 ':
                h=clean_items.PALETTE[int(ch,16)].lstrip('#')
                im.putpixel((x,y),tuple(int(h[i:i+2],16) for i in (0,2,4))+(255,))
    return im


def cropped(im):
    box=im.getbbox()
    return im.crop(box) if box else Image.new('RGBA',(1,1))


def fit(im,width,height):
    im=cropped(im)
    factor=min(width/im.width,height/im.height)
    return im.resize((max(1,round(im.width*factor)),max(1,round(im.height*factor))),Image.Resampling.NEAREST)


def centred(im,width,height,cx,cy,frame_size=32):
    im=fit(im,width,height)
    out=Image.new('RGBA',(frame_size,frame_size))
    out.alpha_composite(im,(round(cx-im.width/2),round(cy-im.height/2)))
    return out


HELD_GRIPS = {
    # FX coordinates. Its top-left is feet(-16,-32); the hero sheet is
    # 16 pixels wider on the left. Arrow launch height includes its z=6.
    'bow': {'n':(16,9), 'e':(26,14), 's':(16,24)},
    'lamp': {'n':(23,16), 'e':(26,19), 's':(23,23)},
    'cape': {'n':(16,17), 'e':(16,17), 's':(16,17)},
}


def _hanging_lamp(direction,phase):
    """Hold the ring, with the lantern hanging below a fixed hand grip."""
    hx,hy=HELD_GRIPS['lamp'][direction]
    w,h={'n':(10,15),'e':(8,13),'s':(8,10)}[direction]
    lantern=fit(R.native_image('lamp'),w,h)
    left=round(hx-lantern.width/2);top=hy-1
    out=Image.new('RGBA',(32,32))
    for y in range(lantern.height):
        # Keep the ring motionless. Only the suspended lower body sways.
        shift=int(phase==1 and y>=lantern.height-5)
        out.alpha_composite(lantern.crop((0,y,lantern.width,y+1)),(left+shift,top+y))
    return out


def _cape_fabric(direction,phase):
    """The supplied cloak's fabric, worn from the shoulders rather than
    displaying its inventory hood and empty face opening over Bloom.
    """
    out=Image.new('RGBA',(32,32));draw=ImageDraw.Draw(out)
    dark='#080810';shadow='#083018';body='#204830';mid='#305838';light='#487840'
    if direction=='e':
        tail=(6,1,7)[phase]
        edge=[(15,16),(18,17),(18,21),(15,25),(12,29),(8,29),(6,31),
              (tail,29),(tail+2,25),(9,22),(12,18)]
        draw.polygon(edge,fill=dark)
        draw.polygon([(15,18),(17,18),(16,22),(12,26),(8,28),(tail+3,28),
                      (tail+4,26),(10,23),(13,20)],fill=body)
        draw.line([(15,18),(13,22),(tail+4,27)],fill=light,width=2)
        draw.line([(16,19),(14,23),(10,28)],fill=shadow)
        # Retain the source's pointed leaf skirt as a trailing cloth edge.
        skirt=R.native_image('cloak').crop((0,18,32,32))
        skirt=fit(skirt,(10,16,10)[phase],9)
        out.alpha_composite(skirt,(max(0,tail),23))
    else:
        half=(9,13,10)[phase]
        edge=[(14,16),(18,16),(21,20),(16+half,27),(16+half-2,30),
              (22,28),(20,31),(16,29),(12,31),(10,28),(16-half+2,30),
              (16-half,27),(11,20)]
        draw.polygon(edge,fill=dark)
        draw.polygon([(14,18),(18,18),(20,21),(15+half,27),(21,27),
                      (19,29),(16,27),(13,29),(11,27),(17-half,27),(12,21)],fill=body)
        draw.polygon([(14,18),(16,18),(14,23),(10,27),(17-half,27),(12,21)],fill=light)
        draw.polygon([(17,18),(19,21),(21,27),(18,26),(16,23)],fill=mid)
        draw.line([(16,18),(15,23),(16,28)],fill=shadow)
        # The lower source is actual cloth only: no golden front clasp or
        # dark hood opening. Its native leaf points keep the item identity.
        skirt=R.native_image('cloak').crop((0,18,32,32))
        skirt=fit(skirt,half*2,9)
        out.alpha_composite(skirt,(round(16-skirt.width/2),23))
    return out


def held(tool,direction,phase):
    if tool=='lamp':
        return _hanging_lamp(direction,phase)
    if tool=='bow':
        # The source bow is diagonal. Turn its actual pixels so the limbs
        # and released arrow face the engine's cardinal shot direction.
        bow=R.native_image('bow').rotate(45,Image.Resampling.NEAREST,expand=True)
        bow=ImageOps.mirror(cropped(bow))
        if direction=='n':bow=bow.rotate(90,Image.Resampling.NEAREST,expand=True)
        elif direction=='s':bow=bow.rotate(270,Image.Resampling.NEAREST,expand=True)
        hx,hy=HELD_GRIPS['bow'][direction]
        w,h={'n':(28,16),'e':(11,20),'s':(24,14)}[direction]
        # Gameplay releases on the button frame. Keep the grip pinned
        # through release/settle/recovery instead of moving the whole bow
        # after the arrow has already left it.
        return centred(bow,w,h,hx,hy)
    if tool=='cape':
        return _cape_fabric(direction,phase)
    raise KeyError(tool)


def arrow(direction):
    im=R.native_image('arrow1').rotate(45,Image.Resampling.NEAREST,expand=True)
    im=cropped(im)
    if direction=='e':im=im.rotate(-90,Image.Resampling.NEAREST,expand=True)
    elif direction=='s':im=im.rotate(180,Image.Resampling.NEAREST,expand=True)
    return centred(im,14,14,8,8,16)


def apply(sheets):
    for sh in sheets:
        name=sh['name']
        if name in ('items','pick32','icon32'):
            if name=='icon32':sh['frames']['shield_upgraded']=['.'*32]*32
            banks={};exact={}
            for frame in sh['frames']:
                item='shield' if frame=='shield_upgraded' else frame
                variant=int(frame=='shield_upgraded')
                rows,bank=R.world_frame(item,sh['w'],variant)
                sh['frames'][frame]=rows;banks[frame]=bank
                if name=='icon32':exact[frame]=R.menu_frame(item,variant)
            sh['frame_pal']=banks
            if exact:sh['exact_frames']=exact
        elif name=='shield':
            sources=(('front','shield',0),('side','shield_side',0),('back','shield_back',0),
                     ('upgraded_front','shield',1),('upgraded_side','shield_side',1),('upgraded_back','shield_back',1))
            sh['frames']={};sh['frame_pal']={}
            for frame,item,variant in sources:
                rows,bank=R.world_frame(item,16,variant)
                sh['frames'][frame]=rows;sh['frame_pal'][frame]=bank
        elif name=='sword':
            sh['frames']={n:R.world_quantize(old_image(rows),'gear') for n,rows in sh['frames'].items()}
        elif name=='arrow':
            sh['pal']='icons'
            sh['frames']={n:R.world_quantize(arrow(n),'icons') for n in sh['frames']}
        elif name=='bloomfx':
            banks={}
            for frame,rows in sh['frames'].items():
                tool=frame.split('_')[0]
                if tool=='sword':image=old_image(rows);bank='gear'
                else:
                    direction,phase=frame[-2],int(frame[-1])
                    image=held(tool,direction,phase)
                    bank='items' if tool=='lamp' else 'icons'
                sh['frames'][frame]=R.world_quantize(image,bank);banks[frame]=bank
            sh['frame_pal']=banks
        if name in ('items','pick32','icon32','sword','shield','arrow','bloomfx'):
            for frame,rows in sh['frames'].items():
                assert len(rows)==sh['h'] and all(len(row)==sh['w'] for row in rows),(name,frame)
