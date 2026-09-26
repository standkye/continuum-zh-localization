# -*- coding: utf-8 -*-
"""以管理员身份启动安装器。

必须用 DETACHED_PROCESS 分离出去：ShellExecuteW(runas) 在用户点「是」之前
不返回，Bash 工具会超时 SIGTERM 把整个调用杀掉（表现为 exit=1 / 无输出），
UAC 窗口也随之消失。分离后主进程立刻返回，我们再轮询 sha256。
"""
import subprocess, sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

EXE = r"D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0\Continuum汉化安装器.exe"
LOG = r"D:\Programming project\插件汉化\_work\_launch_log.txt"

code = (
    "import sys,ctypes;"
    "rc=ctypes.windll.shell32.ShellExecuteW(None,'runas',sys.argv[1],None,None,1);"
    "open(sys.argv[2],'w').write('ShellExecuteW rc=%d'%rc)"
)
p = subprocess.Popen(
    [sys.executable, "-c", code, EXE, LOG],
    creationflags=0x00000008,      # DETACHED_PROCESS
    close_fds=True,
)
print("已分离启动, pid =", p.pid)
print("等待 UAC，随后轮询 sha256")
