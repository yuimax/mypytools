# pip install opencv-python

import glob
import os
import sys
import cv2

def get_video_info(video_path):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise Exception(f"Can't read video '{video_path}'")

    width   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height  = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps     = round(cap.get(cv2.CAP_PROP_FPS), 1)
    nframes = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    cap.release()
    return (width, height, fps, nframes)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        myname = os.path.basename(__file__)
        print(f"Usage: {myname} file ...")
        exit(0)
    
    paths = []
    for arg in sys.argv[1:]:
        paths.extend(glob.glob(arg))
    
    print('width height  fps frames  video-file') 
    print('----- ----- ----- ------  ----------') 
    
    for path in paths:
        try:
            (width, height, fps, nframes) = get_video_info(path)
            print(f"{width:5} {height:5} {fps:5} {nframes:6}  {path}")
        except Exception as e:
            print(f"ERROR: {e}")
