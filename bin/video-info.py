# pip install opencv-python

import glob
import os
import sys
import cv2
import math
from PIL import Image

class BadFormatError(Exception):
    pass
    

def get_video_info(video_path):
    if is_image_file(video_path):
        raise BadFormatError()
        
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise BadFormatError()

    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = round(cap.get(cv2.CAP_PROP_FPS), 1)
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    time   = get_time_string(frames / fps)

    cap.release()
    
    return (width, height, fps, frames, time)


def is_image_file(path):
    try:
        with Image.open(path) as img:
            return True
    except Exception as e:
        return False


def get_time_string(seconds):
    sec = int(seconds) % 60
    minute = int(seconds) // 60
    return f"{minute:02d}:{sec:02d}"


if __name__ == '__main__':
    if len(sys.argv) < 2:
        myname = os.path.basename(__file__)
        print(f"Usage: {myname} file ...")
        exit(0)
    
    paths = []
    for arg in sys.argv[1:]:
        paths.extend(glob.glob(arg))
    
    print('width height  fps frames time   video-file') 
    print('----- ----- ----- ------ -----  ----------') 
    
    for path in paths:
        try:
            (width, height, fps, frames, time) = get_video_info(path)
            print(f"{width:5} {height:5} {fps:5} {frames:6} {time:5}  {path}")
        except BadFormatError:
            # 有効な動画形式でない
            print(f"////////// not video /////////  {path}")
        except Exception as e:
            print(f"ERROR: {e}")
