import ctypes, sys

BAT = r"D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0\Install-Chinese.bat"
WORKDIR = r"D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0"

rc = ctypes.windll.shell32.ShellExecuteW(
    None, "runas", r"C:\Windows\System32\cmd.exe", '/k ""%s""' % BAT, WORKDIR, 1
)
print("ShellExecuteW rc =", rc, "(>32 means the UAC dialog was shown)")
print("WAIT FOR THE USER TO CLICK YES IN THE WINDOW THAT APPEARED.")
