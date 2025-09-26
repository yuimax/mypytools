import os
import sys
import urllib.parse

if len(sys.argv) < 2:
    myname = os.path.basename(__file__)
    print(f"Usage: {myname} URL-encoded-string")
    sys.exit(1)

try:
    print(urllib.parse.unquote(sys.argv[1]))
except Exception as e:
    print(f"ERROR: {e}")
