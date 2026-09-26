import subprocess
r = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True)
out = r.stdout.decode("gbk", errors="ignore")
keys = ["cmd.exe", "consent", "AfterFX", "WindowsTerminal", "wextract", "iexpress"]
for l in out.splitlines():
    if any(k.lower() in l.lower() for k in keys):
        print(l)
