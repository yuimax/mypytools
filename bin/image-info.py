# pip install Pillow

import glob
import os
import sys
import PIL
from PIL import Image

def get_image_info(image_path):
    with Image.open(image_path) as img:
        return (img.format, img.mode, img.width, img.height)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        myname = os.path.basename(__file__)
        print(f"Usage: {myname} file ...")
        exit(0)
    
    paths = []
    for arg in sys.argv[1:]:
        paths.extend(glob.glob(arg))
    
    print('format mode  width height  image-file') 
    print('------ ----- ----- ------  ----------') 
    
    for path in paths:
        try:
            (fmt, mode, width, height) = get_image_info(path)
            print(f"{fmt:6} {mode:5} {width:5} {height:6}  {path}")
        except PIL.UnidentifiedImageError:
            # 有効な画像形式でない場合は無視
            pass
        except Exception as e:
            print(f"ERROR: {e}")
