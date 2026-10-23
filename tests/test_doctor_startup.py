"""kit_doctor: tells when UEFN opens on the home screen, so a relaunch after a crash cannot reopen the project."""
import os, sys, tempfile
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(root, "project-template", "Claude", "hooks"))
import kit_doctor, uefn_session as us
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
d = tempfile.mkdtemp()
ini = os.path.join(d, "EditorSettings.ini")
ok(kit_doctor.load_on_startup_check(ini) is None, "no settings file: the check is skipped")
open(ini, "w", encoding="utf-8").write("[%s]\n%s=HomeScreen\n" % (us.SECTION, us.LOAD_KEY))
r = kit_doctor.load_on_startup_check(ini)
ok(r and r[0] == "NOTE" and "Most Recent Project" in r[1], "home screen: a note says how to change it")
open(ini, "w", encoding="utf-8").write("[%s]\n%s=LastProject\n" % (us.SECTION, us.LOAD_KEY))
ok(kit_doctor.load_on_startup_check(ini)[0] == "OK", "last project: OK")
