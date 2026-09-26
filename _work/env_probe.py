import os, subprocess, sys, glob

print("python:", sys.version)
cands = [
    r"C:\Users\Jinna\.workbuddy\binaries\python\envs\default\Scripts\pip.exe",
    r"C:\Users\Jinna\.workbuddy\binaries\python\versions\3.13.12\Scripts\pip.exe",
    r"C:\Python314\Scripts\pip.exe",
]
for c in cands:
    print("pip:", c, os.path.exists(c))

r = subprocess.run([sys.executable, "-m", "pip", "list"], capture_output=True, text=True)
lines = [l for l in r.stdout.splitlines() if "yinstaller" in l.lower() or "setuptools" in l.lower()]
print("current interp pyinstaller/setuptools:", lines)

# check venv presence
v = r"C:\Users\Jinna\.workbuddy\binaries\python\envs\default"
print("venv exists:", os.path.exists(v))
if os.path.exists(v):
    print("venv scripts:", os.listdir(os.path.join(v, "Scripts"))[:20])
