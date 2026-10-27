"""Install the supplied item pixels across displays and Bloom's held props.

Frame dimensions and ordering retain the engine contracts. Item frames carry
one of four world palette banks; paused inventory frames use their own ramps.
"""
from PIL import Image, ImageOps
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


def held(tool,direction,phase):
    hand={'n':(23,16),'e':(26,19),'s':(23,23)}[direction]
    hx,hy=hand
    if tool=='lamp':
        return centred(R.native_image('lamp'),10,15,hx,hy-5+(0,-1,0)[phase])
    if tool=='bow':
        # The source bow is diagonal. Turn its actual pixels so the limbs
        # and released arrow face the engine's cardinal shot direction.
        bow=R.native_image('bow').rotate(45,Image.Resampling.NEAREST,expand=True)
        bow=ImageOps.mirror(cropped(bow))
        if direction=='n':bow=bow.rotate(90,Image.Resampling.NEAREST,expand=True)
        elif direction=='s':bow=bow.rotate(270,Image.Resampling.NEAREST,expand=True)
        w,h=(9,16) if direction=='e' else (16,9)
        return centred(bow,w,h,hx,hy-(phase==0))
    if tool=='cape':
        # The imported cloak opens behind Bloom, whose original flower and
        # clothing remain the foreground. Three spans follow the jump pose.
        if direction=='e':
            w,h=((11,18),(17,20),(10,19))[phase];cx,cy=10,21
        else:
            w,h=((22,22),(28,24),(20,22))[phase];cx,cy=16,20
        return centred(R.native_image('cloak'),w,h,cx,cy)
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
