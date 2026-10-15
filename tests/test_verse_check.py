"""verse_check: three honest states against a fake Verse Workflow Server."""
import os, sys, json, socket, threading, importlib.util
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
spec = importlib.util.spec_from_file_location("verse_check", os.path.join(root, "project-template", "Claude", "hooks", "verse_check.py"))
vc = importlib.util.module_from_spec(spec); spec.loader.exec_module(vc)
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))

def serve(reply, noise=True, silent=False):
    s = socket.socket(); s.bind(("127.0.0.1", 0)); s.listen(1)
    def run():
        c, _ = s.accept()
        with c:
            data = c.recv(65536)
            if silent:
                import time; time.sleep(3); return
            if noise:
                c.sendall(vc.frame({"seq": 1, "type": 0, "command": "updateBuildState", "params": 3}))
                c.sendall(vc.frame({"seq": 2, "type": 0, "command": "logMessage", "params": {"type": 3, "message": "x"}}))
            c.sendall(vc.frame(reply(json.loads(data.split(b"\r\n\r\n", 1)[1]))))
        s.close()
    threading.Thread(target=run, daemon=True).start()
    return s.getsockname()[1]

resp = lambda result=None, error=None: (lambda req: dict({"seq": req["seq"], "type": 2, "command": req["command"]}, **({"result": result} if error is None else {"error": error})))
p = serve(resp({"message": "ok", "numWarnings": 2, "numErrors": 0}))
r = vc.check(port=p, timeout=5)
ok(r["state"] == "clean" and r["warnings"] == 2, "0 errors -> clean (warnings counted, notifications ignored)")
p = serve(resp({"message": "MapCode.verse(3,1): error 3502", "numWarnings": 0, "numErrors": 1}))
r = vc.check(port=p, timeout=5)
ok(r["state"] == "errors" and r["errors"] == 1 and "3502" in r["message"], "errors -> errors with the build log")
p = serve(resp(error="no project"))
ok(vc.check(port=p, timeout=5)["state"] == "not_analyzed", "refused request -> not analyzed")
p = serve(resp({"hello": 1}))
ok(vc.check(port=p, timeout=5)["state"] == "not_analyzed", "odd reply -> not analyzed, never 'clean'")
p = serve(resp(), silent=True)
ok(vc.check(port=p, timeout=1)["state"] == "not_analyzed", "no answer in time -> not analyzed")
s = socket.socket(); s.bind(("127.0.0.1", 0)); dead = s.getsockname()[1]; s.close()
ok(vc.check(port=dead, timeout=2)["state"] == "not_analyzed", "UEFN closed -> not analyzed")
ok(vc.main(["--port", str(dead)]) == 2, "exit code 2 when not analyzed")
