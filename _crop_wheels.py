from PIL import Image
from pathlib import Path
p=Path('车轮布局.jpg')
im=Image.open(p)
w,h=im.size
boxes={'A_tl':(0,0,w//2,h//2),'B_tr':(w//2,0,w,h//2),'C_bl':(0,h//2,w//2,h),'D_br':(w//2,h//2,w,h)}
out=Path('_wheel_crops'); out.mkdir(exist_ok=True)
for name,box in boxes.items():
    crop=im.crop(box)
    crop=crop.resize((crop.width*2,crop.height*2))
    crop.save(out/f'{name}.png')
print(im.size)
