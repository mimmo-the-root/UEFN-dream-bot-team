import os, re
h = os.path.join(os.path.dirname(__file__), "..", "project-template", "Claude", "hooks")
py = open(os.path.join(h, "agent-console-server.py"), encoding="utf-8").read()
ps = open(os.path.join(h, "agent-console-server.ps1"), encoding="utf-8").read()
a = py[py.index("DOC_FILES = {"):]; a = a[:a.index("}")]
b = ps[ps.index("$docFiles = @{"):]; b = b[:b.index("\n}")]
pk = dict(re.findall(r'"([\w]+)":\s*"([^"]+)"', a))
sk = dict(re.findall(r'"([\w]+)"\s*=\s*"([^"]+)"', b))
miss = {k: v for k, v in pk.items() if sk.get(k) != v}
assert not miss, "the PowerShell server lacks or differs on doc keys: %s" % miss
print("server doc parity OK")
