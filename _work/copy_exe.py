# -*- coding: utf-8 -*-
import os, shutil

PROJ = r"D:\Programming project\插件汉化"
built = r"C:\Users\Jinna\.workbuddy\pyinstaller_stage6\dist\Continuum汉化安装器.exe"
dst_dir = os.path.join(PROJ, "Continuum 汉化组件 v19.0.0")

dst = os.path.join(dst_dir, "Continuum汉化安装器.exe")
shutil.copy2(built, dst)
print("copied ->", dst, os.path.getsize(dst))

# restore launcher
lb = os.path.join(PROJ, "_work", "launch_restore.bat")
d2 = os.path.join(dst_dir, "还原英文（双击这个）.bat")
shutil.copy2(lb, d2)
print("copied ->", d2, os.path.getsize(d2))
