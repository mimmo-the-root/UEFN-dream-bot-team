"""Static Verse check: certain mistakes only, no false alarms on clean code."""
import os, shutil, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project-template", "Claude", "hooks"))
import verse_static as v
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
CLEAN = '''using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/Diagnostics }
# a comment with ( unbalanced { and "quote
a_device := class(creative_device):
    @editable
    Delay : float = 1.0
    var Count : int = 0
    OnBegin<override>()<suspends> : void =
        Print("hello {Count} (not a paren")
        Sleep(Delay)
'''
ok(v.check_text(CLEAN) == [], "clean code: no findings (comments and strings are ignored)")
ok(any("never closed" in m for _, _, m in v.check_text(CLEAN + "    Foo(\n")), "unclosed paren is an error")
ok(any("closes nothing" in m for _, _, m in v.check_text("x := 1\n)\n")), "stray closer is an error")
ok(any("tabs and spaces" in m for _, _, m in v.check_text("a:\n\tb\n    c\n")), "mixed indentation is an error")
ok(any("@editable cannot" in m for _, _, m in v.check_text("a := class():\n    @editable var X : int = 0\n")), "@editable var (one line) is an error")
ok(any("@editable cannot" in m for _, _, m in v.check_text("a := class():\n    @editable\n    var X : int = 0\n")), "@editable var (two lines) is an error")
ok(any("needs <override>" in m for _, _, m in v.check_text(CLEAN.replace("OnBegin<override>", "OnBegin"))), "OnBegin without <override> is an error")
ok(v.check_text("b := class():\n    OnBegin()<suspends> : void =\n        Sleep(1.0)\n") and not any("override" in m for _, _, m in v.check_text("b := class():\n    OnBegin()<suspends> : void =\n        Sleep(1.0)\n")), "OnBegin in a plain class is not flagged")
w = v.check_text(CLEAN.replace("using { /UnrealEngine.com/Temporary/Diagnostics }\n", ""))
ok([s for s, _, _ in w] == ["warning"] and "Diagnostics" in w[0][2], "missing Diagnostics import is a warning")
d = tempfile.mkdtemp()
try:
    os.makedirs(os.path.join(d, "Content", "A")); os.makedirs(os.path.join(d, "Content", "VerseUIKit"))
    open(os.path.join(d, "Content", "A", "one.verse"), "w").write(CLEAN)
    open(os.path.join(d, "Content", "A", "two.verse"), "w").write(CLEAN)
    open(os.path.join(d, "Content", "VerseUIKit", "x.verse"), "w").write("a := class(\n")
    p = v.run(d)
    ok(len(p) == 1 and "also defined" in p[0]["message"], "duplicate class across files is an error; VerseUIKit is skipped")
    ok(v.main([d]) == 1, "exit code 1 on errors")
finally:
    shutil.rmtree(d, ignore_errors=True)
