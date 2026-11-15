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
w = v.check_text("using { /Verse.org/Simulation }\nf():void=\n    Print(\"x\")\n")
ok([s for s, _, _ in w] == ["warning"] and "Diagnostics" in w[0][2], "missing Diagnostics import is a warning outside a device class")
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
# Print inside a creative_device class is inherited: no import needed (a real published map builds without it)
dev = "using { /Fortnite.com/Devices }\nusing { /Verse.org/Simulation }\nd := class(creative_device):\n    OnBegin<override>()<suspends> : void =\n        Print(\"x\")\n"
ok(v.check_text(dev) == [], "Print in a device class is not flagged")
ok(any("Print(" in m for _, _, m in v.check_text("f():void=\n    Print(\"x\")\n")), "Print outside a device class without the import is still a warning")

# --- NEW CHECKS TESTS ---

# 1. Function without <transacts>/<computes>/<decides> called inside if(...) or []
fn_no_effects = '''using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/Diagnostics }
MyFunc(): int = 42
a_device := class(creative_device):
    OnBegin<override>()<suspends> : void =
        if (MyFunc()) then Print("x")
        else Print("y")
'''
ok(any("without <transacts>/<computes>/<decides> called inside if" in m for _, _, m in v.check_text(fn_no_effects)), "function without effects in if(...) is a warning")

fn_no_effects_bracket = '''using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/Diagnostics }
MyFunc(): int = 42
a_device := class(creative_device):
    OnBegin<override>()<suspends> : void =
        x := [MyFunc()]
'''
ok(any("without <transacts>/<computes>/<decides> called inside" in m for _, _, m in v.check_text(fn_no_effects_bracket)), "function without effects in [] is a warning")

fn_with_transacts = '''using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/Diagnostics }
MyFunc()<transacts> : int = 42
a_device := class(creative_device):
    OnBegin<override>()<suspends> : void =
        if (MyFunc()) then Print("x")
'''
ok(v.check_text(fn_with_transacts) == [], "function with <transacts> in if(...) is ok")

# 2. Field initializer that calls a function
field_init_call = '''using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/Diagnostics }
a_device := class(creative_device):
    Value : int = SomeFunc()
    OnBegin<override>()<suspends> : void = Print("x")
'''
ok(any("initializes with function call" in m for _, _, m in v.check_text(field_init_call)), "field initializer calling function is a warning")

field_init_literal = '''using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/Diagnostics }
a_device := class(creative_device):
    Value : int = 42
    Arr : []int = array{1, 2, 3}
    OnBegin<override>()<suspends> : void = Print("x")
'''
ok(v.check_text(field_init_literal) == [], "field initializer with literals/array{} is ok")

# 3. Integer / outside failure context
int_div = '''using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/Diagnostics }
a_device := class(creative_device):
    OnBegin<override>()<suspends> : void =
        x := 5 / 2
'''
ok(any("integer division" in m for _, _, m in v.check_text(int_div)), "integer division outside failure context is a warning")

int_div_in_if = '''using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/Diagnostics }
a_device := class(creative_device):
    OnBegin<override>()<suspends> : void =
        if (5 / 2 > 0) then Print("x")
'''
ok(v.check_text(int_div_in_if) == [], "integer division in if(...) is ok")

int_div_in_bracket = '''using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/Diagnostics }
a_device := class(creative_device):
    OnBegin<override>()<suspends> : void =
        x := [5 / 2]
'''
ok(v.check_text(int_div_in_bracket) == [], "integer division in [] is ok")

float_div = '''using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/Diagnostics }
a_device := class(creative_device):
    OnBegin<override>()<suspends> : void =
        x := 5.0 / 2.0
'''
ok(v.check_text(float_div) == [], "float division is ok")

# 4. Use of name from module without using import
missing_using = '''using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/Diagnostics }
a_device := class(creative_device):
    OnBegin<override>()<suspends> : void =
        Distance(vector3{0,0,0}, vector3{1,1,1})
'''
ok(any("Distance" in m and "not imported" in m for _, _, m in v.check_text(missing_using)), "missing using import for SpatialMath is a warning")

with_using = '''using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/Diagnostics }
using { /UnrealEngine.com/Temporary/SpatialMath }
a_device := class(creative_device):
    OnBegin<override>()<suspends> : void =
        Distance(vector3{0,0,0}, vector3{1,1,1})
'''
ok(v.check_text(with_using) == [], "with using import is ok")

# 5. array: instead of array{}; ToString on logic
array_colon = '''using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/Diagnostics }
a_device := class(creative_device):
    OnBegin<override>()<suspends> : void =
        x := array: 1, 2, 3
'''
ok(any("array:" in m for _, _, m in v.check_text(array_colon)), "array: literal is a warning")

array_braces = '''using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/Diagnostics }
a_device := class(creative_device):
    OnBegin<override>()<suspends> : void =
        x := array{1, 2, 3}
'''
ok(v.check_text(array_braces) == [], "array{} literal is ok")

tostring_logic = '''using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/Diagnostics }
a_device := class(creative_device):
    OnBegin<override>()<suspends> : void =
        x := ToString(true)
'''
ok(any("ToString" in m and "logic" in m for _, _, m in v.check_text(tostring_logic)), "ToString on logic is a warning")

# 6. Local/field shadows module function
shadow_field = '''using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/Diagnostics }
using { /UnrealEngine.com/Temporary/SpatialMath }
a_device := class(creative_device):
    @editable
    Distance : float = 0.0
    OnBegin<override>()<suspends> : void = Print("x")
'''
ok(any("shadows a module function" in m and "Distance" in m for _, _, m in v.check_text(shadow_field)), "field shadowing Distance is a warning")

shadow_local = '''using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/Diagnostics }
using { /UnrealEngine.com/Temporary/SpatialMath }
a_device := class(creative_device):
    OnBegin<override>()<suspends> : void =
        var Distance : float = 0.0
        Print("x")
'''
ok(any("shadows a module function" in m and "Distance" in m for _, _, m in v.check_text(shadow_local)), "local variable shadowing Distance is a warning")

shadow_param = '''using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/Diagnostics }
using { /UnrealEngine.com/Temporary/SpatialMath }
a_device := class(creative_device):
    OnBegin<override>()<suspends> : void =
        MyFunc(Distance: float) : void = Print("x")
'''
ok(any("shadows a module function" in m and "Distance" in m for _, _, m in v.check_text(shadow_param)), "parameter shadowing Distance is a warning")

no_shadow_without_import = '''using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/Diagnostics }
a_device := class(creative_device):
    @editable
    Distance : float = 0.0
    OnBegin<override>()<suspends> : void = Print("x")
'''
ok(v.check_text(no_shadow_without_import) == [], "shadow check only when module is imported")
