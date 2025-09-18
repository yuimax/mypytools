import sys
import math

if len(sys.argv) < 2:
    print('Usage: ksan.py 計算式')

else:
    try:
        exp = ' '.join(map(str, sys.argv[1:]))
        print(eval(exp))

    except Exception as e:
        print(f"ERROR: {e}")
