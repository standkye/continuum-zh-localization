
import ctypes, sys
p = sys.argv[1]
try:
    h = ctypes.WinDLL(p, mode=0)
    print("OK   loaded handle=%s" % h._handle)
except OSError as e:
    print("FAIL err=%s msg=%s" % (getattr(e, 'winerror', '?'), e))
except Exception as e:
    print("FAIL %s" % e)
