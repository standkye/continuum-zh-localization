# -*- coding: utf-8 -*-
"""在桌面创建指向安装器的快捷方式（.lnk），用户双击即可触发 UAC 安装。
用 COM 创建，避免手写 .lnk 二进制格式。"""
import os, subprocess, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

EXE = r"D:\Programming project\插件汉化\Continuum 汉化组件 v19.0.0\Continuum汉化安装器.exe"
DESK = os.path.join(os.path.expanduser('~'), 'Desktop')
LNK = os.path.join(DESK, "安装 Continuum 汉化（右键管理员）.lnk")

# 用一个临时 ps1 执行，规避 bash 内联 powershell 被拦。
# ⚠️ 两个坑：
#   1. ps1 必须用 **UTF-8 带 BOM**（utf-8-sig）写。PowerShell 5.1 读无 BOM 的
#      UTF-8 会按本地代码页(GBK)解释，中文字符串被截断 → "字符串缺少终止符"。
#   2. 也别图省事写纯 ASCII：快捷方式路径本身常含中文（桌面 + 中文文件名），
#      encoding='ascii' 会直接 UnicodeEncodeError（我在这儿栽了一次）。
ps1 = os.path.join(os.environ.get('TEMP', '.'), '_mklnk.ps1')
script = (
    "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%s');"
    "$s.TargetPath='%s';"
    "$s.WorkingDirectory='%s';"
    "$s.Description='BorisFX Continuum 2026 Hanhua Installer';"
    "$s.Save()" % (LNK, EXE, os.path.dirname(EXE))
)
open(ps1, 'w', encoding='utf-8-sig').write(script)

r = subprocess.run(
    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1],
    capture_output=True
)
o = []
o.append("ps1 rc: %s" % r.returncode)
o.append("stdout: " + r.stdout.decode('utf-8', 'replace').strip())
o.append("stderr: " + r.stderr.decode('utf-8', 'replace').strip()[:800])
o.append("")
o.append("快捷方式存在: %s  %s" % (os.path.exists(LNK),
                                  os.path.getsize(LNK) if os.path.exists(LNK) else ''))
o.append("目标 exe 存在: %s  %s" % (os.path.exists(EXE),
                                    os.path.getsize(EXE) if os.path.exists(EXE) else ''))
try:
    os.remove(ps1)
except OSError:
    pass

open(r"D:\Programming project\插件汉化\_work\_mklnk.txt", 'w', encoding='utf-8').write("\n".join(o))
print("done")
