# -*- coding: utf-8 -*-
"""Launch the one-click installer so the user only has to answer UAC."""
import ctypes, os, sys, time, hashlib

EXE = r"D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0\Continuum汉化安装器.exe"
WD = os.path.dirname(EXE)

print("exe exists:", os.path.exists(EXE), os.path.getsize(EXE))

# Use ShellExecuteEx-style "runas" through ShellExecuteW.
# The installer asks for elevation itself as well, but pre-elevating here
# gives the user a single UAC click instead of two.
rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", EXE, "", WD, 1)
print("ShellExecuteW rc =", rc, "(>32 = UAC dialog shown)")
