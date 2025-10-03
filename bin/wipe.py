# pip install send2trash

import sys
import os
import glob
from send2trash import send2trash

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: wipe.py <file1> ...")
        exit(0)

    for pattern in sys.argv[1:]:
        for file_path in glob.glob(pattern):
            if os.path.isdir(file_path):
                continue

            try:
                send2trash(file_path)
                with open(file_path, 'w') as f:
                    pass
                print(f"WIPED OUT: {file_path}")

            except Exception as e:
                print(f"ERROR: {file_path}: {e}")
    