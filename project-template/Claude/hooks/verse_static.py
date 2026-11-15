#!/usr/bin/env python3
"""Static check of Verse files, without the editor and without building (v1.111).

Catches the mistakes that are certain from the text alone, so a build is not wasted on them:

  error    unbalanced { } ( ) [ ]               mixed tabs and spaces in the indentation of one file
  error    @editable on a `var` declaration     the same top-level class or struct name defined in two files
  error    OnBegin / OnEnd declared without <override> in a creative_device class
  warning  Print( used outside a device class but /UnrealEngine.com/Temporary/Diagnostics is not imported
  warning  creative_device used but /Fortnite.com/Devices is not imported
  warning  Sleep( or spawn used but /Verse.org/Simulation is not imported
  warning  function without <transacts>/<computes>/<decides> called inside `if (...)` or `[]`
  warning  field initializer calls a function (X : t = Call(...)) — set in OnBegin
  warning  integer `/` outside a failure context — use Floor[] on floats
  warning  name used from module without `using` import (10 common APIs)
  warning  `array:` literal syntax — use `array{}`
  warning  `ToString(` called on a logic value
  warning  local/field shadows module function (Distance, Lerp, Clamp) when module imported

It does NOT prove the code compiles: a clean result here only means none of these mistakes is present. The real answer is
verse_check.py (needs the open editor). Read-only, no AI tokens.

  python Claude/hooks/verse_static.py [project folder | file.verse] [--json]     exit 1 when there is an error
"""
import json
import os
import re
import sys

SKIP_DIRS = {"Claude", ".claude", "__ExternalActors__", "__ExternalObjects__", "Saved", "Intermediate", ".git", "VerseUIKit"}

# Common Verse modules and their commonly used exports
COMMON_MODULES = {
    "/UnrealEngine.com/Temporary/SpatialMath": {"Distance", "Lerp", "Clamp", "Abs", "Min", "Max", "Sign", "Sqrt", "Pow", "Exp", "Sin", "Cos", "Tan", "Floor", "Ceil", "Round", "Frac", "Mod", "Step", "SmoothStep", "Normalize", "Dot", "Cross", "Length", "LengthSquared", "RadiansToDegrees", "DegreesToRadians"},
    "/Fortnite.com/Characters": {"GetAgent", "GetFortCharacter", "GetController", "GetPawn", "GetTeam", "GetHealth", "GetMaxHealth", "GetShield", "GetMaxShield", "Damage", "Heal", "SetHealth", "SetShield", "IsDead", "IsInVehicle", "GetVehicle", "ExitVehicle"},
    "/Fortnite.com/UI": {"ShowWidget", "HideWidget", "GetWidget", "SetWidgetVisibility", "GetWidgetVisibility", "AddWidget", "RemoveWidget", "SetText", "GetText", "SetColor", "GetColor", "AnimateWidget", "PlayAnimation", "StopAnimation"},
    "/Verse.org/Random": {"NextInt", "NextFloat", "NextBool", "Shuffle", "Choose", "NextIntInRange", "NextFloatInRange", "RandomStream", "Seed"},
}


def strip(text):
    """The code with comments and string contents blanked (same length, same line breaks)."""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if text.startswith("<#", i):
            j = text.find("#>", i + 2)
            j = n if j < 0 else j + 2
            out.append("".join(ch if ch == "\n" else " " for ch in text[i:j]))
            i = j
        elif c == "#":
            j = text.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
        elif c == '"':
            j = i + 1
            while j < n and text[j] != '"' and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            out.append('"' + " " * max(0, j - i - 1) + ('"' if j < n and text[j] == '"' else ""))
            i = min(n, j + 1)
        else:
            out.append(c)
            i += 1
    return "".join(out)


def find_imported_modules(text):
    """Return set of module paths that are imported with `using { ... }`."""
    modules = set()
    for m in re.finditer(r"using\s*\{\s*([^}]+)\s*\}", text):
        module_path = m.group(1).strip()
        modules.add(module_path)
    return modules


def check_text(text, name="file"):
    """[(severity, line, message)] for one file."""
    res = []
    code = strip(text.replace("\r\n", "\n"))
    lines = code.split("\n")
    stack = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for ln, l in enumerate(lines, 1):
        for ch in l:
            if ch in "([{":
                stack.append((ch, ln))
            elif ch in pairs:
                if not stack or stack[-1][0] != pairs[ch]:
                    res.append(("error", ln, "'%s' closes nothing that is open" % ch))
                    stack = []
                    break
                stack.pop()
    for ch, ln in stack[:1]:
        res.append(("error", ln, "'%s' is never closed" % ch))
    tabs = sum(1 for l in lines if re.match(r"^\t", l))
    spaces = sum(1 for l in lines if re.match(r"^ +\S", l))
    if tabs and spaces:
        res.append(("error", next(i for i, l in enumerate(lines, 1) if l.startswith("\t")), "tabs and spaces both used for indentation in this file"))
    for ln, l in enumerate(lines, 1):
        if re.match(r"^\s*@editable\b", l) and re.search(r"\bvar\b\s+\w+\s*:", l):
            res.append(("error", ln, "@editable cannot be put on a var"))
        if re.match(r"^\s*@editable\s*$", l) and ln < len(lines) and re.match(r"^\s*var\s+\w+\s*:", lines[ln]):
            res.append(("error", ln, "@editable cannot be put on a var"))
    cls = None
    for ln, l in enumerate(lines, 1):
        m = re.match(r"^(\w+)(?:<[^>]*>)*\s*:=\s*class\s*(?:<[^>]*>)?\s*\(([^)]*)\)", l)
        if m:
            cls = "creative_device" if "creative_device" in m.group(2) else None
        elif l and not l[0].isspace():
            cls = None
        if cls and re.match(r"^\s+(OnBegin|OnEnd)\s*(<[^>]*>)*\s*\(", l) and "<override>" not in l:
            res.append(("error", ln, "%s in a creative_device class needs <override>" % re.match(r"^\s+(\w+)", l).group(1)))
    if re.search(r"\bPrint\s*\(", code) and "/UnrealEngine.com/Temporary/Diagnostics" not in text and not re.search(r"\bcreative_device\b", code):  # inside a device class Print is inherited
        res.append(("warning", 1, "Print( is used but /UnrealEngine.com/Temporary/Diagnostics is not imported here"))
    if re.search(r"\bcreative_device\b", code) and "/Fortnite.com/Devices" not in text:
        res.append(("warning", 1, "creative_device is used but /Fortnite.com/Devices is not imported here"))
    if re.search(r"\b(Sleep\s*\(|spawn\s*[:{])", code) and "/Verse.org/Simulation" not in text:
        res.append(("warning", 1, "Sleep/spawn is used but /Verse.org/Simulation is not imported here"))

    # --- NEW CHECKS ---
    imported_modules = find_imported_modules(text)

    # 1. Function without <transacts>/<computes>/<decides> called inside if(...) or []
    res.extend(check_function_call_in_failure_context(code, lines))

    # 2. Field initializer that calls a function
    res.extend(check_field_initializer_calls_function(code, lines))

    # 3. Integer / outside failure context
    res.extend(check_integer_division_outside_failure_context(code, lines))

    # 4. Use of name from module without using import
    res.extend(check_missing_using_import(code, lines, imported_modules))

    # 5. array: instead of array{}; ToString on logic
    res.extend(check_array_literal_and_tostring(code, lines))

    # 6. Local/field shadows module function
    res.extend(check_shadowed_module_function(code, lines, imported_modules))

    return res


def check_function_call_in_failure_context(code, lines):
    """Check for function calls without <transacts>/<computes>/<decides> inside if(...) or []."""
    res = []
    # Find function definitions that don't have effect specifiers
    func_pattern = re.compile(r"^\s*(\w+)\s*\([^)]*\)\s*(?:<[^>]*>)*\s*:\s*\w+")
    func_without_effects = set()
    for ln, l in enumerate(lines, 1):
        m = func_pattern.match(l)
        if m:
            # Check if it has <transacts>, <computes>, or <decides>
            if not re.search(r"<(transacts|computes|decides)>", l):
                func_without_effects.add(m.group(1))

    # Check calls inside if(...) or [...] failure contexts
    for ln, l in enumerate(lines, 1):
        # if (condition)
        if_match = re.search(r"\bif\s*\(([^)]+)\)", l)
        if if_match:
            condition = if_match.group(1)
            for fname in func_without_effects:
                if re.search(r"\b" + re.escape(fname) + r"\s*\(", condition):
                    res.append(("warning", ln, "function '%s' without <transacts>/<computes>/<decides> called inside if(...); add effect specifier or use []" % fname))

        # [...] failure context
        bracket_match = re.search(r"\[([^\]]+)\]", l)
        if bracket_match:
            bracket_content = bracket_match.group(1)
            for fname in func_without_effects:
                if re.search(r"\b" + re.escape(fname) + r"\s*\(", bracket_content):
                    res.append(("warning", ln, "function '%s' without <transacts>/<computes>/<decides> called inside []; add effect specifier or use if" % fname))
    return res


def check_field_initializer_calls_function(code, lines):
    """Check for field initializers that call a function (X : t = Call(...))."""
    res = []
    # Pattern: field : type = FunctionCall(...)
    # but not: field : type = literal (number, string, false/true, {}, array{}, etc.)
    # Also skip `if (...) then ... else ...` which is an expression not a function call
    field_init_pattern = re.compile(r"^\s*(\w+)\s*:\s*\w+\s*=\s*(\w+)\s*\(")
    for ln, l in enumerate(lines, 1):
        m = field_init_pattern.match(l)
        if m:
            field_name = m.group(1)
            func_name = m.group(2)
            # Skip if it's a known literal/constructor pattern or control flow
            if func_name not in {"array", "map", "option", "tuple", "false", "true", "if"}:
                res.append(("warning", ln, "field '%s' initializes with function call '%s(...)'; set it in OnBegin instead" % (field_name, func_name)))
    return res


def check_integer_division_outside_failure_context(code, lines):
    """Check for integer / division outside a failure context (if(...) / [])."""
    res = []
    # Names that are known to be integers in this file (fields and locals declared as int).
    ints = set()
    for l in lines:
        for m in re.finditer(r"\bvar\s+(\w+)\s*:\s*int\b", l):
            ints.add(m.group(1))
        for m in re.finditer(r"^\s*(\w+)\s*:\s*int\b", l):
            ints.add(m.group(1))
    for ln, l in enumerate(lines, 1):
        if l.strip().startswith("using"):
            continue
        # A failure context is if(...) or [...] : the division result can be checked there.
        if re.search(r"\[.*?\]", l) or re.search(r"\bif\s*\(", l):
            continue
        # Two plain integer literals: 5 / 2
        if re.search(r"(?<![\w.])(\d+)\s*/\s*(\d+)(?![\w.])", l):
            res.append(("warning", ln, "integer division '/' outside a failure context; Verse truncates it — use Floor[] on floats instead"))
            continue
        # A known int name divided by an integer literal or another known int name
        for m in re.finditer(r"(?<![\w.])([A-Za-z_]\w*)\s*/\s*([A-Za-z_]\w*|\d+)(?![\w.])", l):
            left, right = m.group(1), m.group(2)
            left_int = left in ints
            right_int = right in ints or right.isdigit()
            if left_int and right_int:
                res.append(("warning", ln, "integer division '%s / %s' outside a failure context; Verse truncates it — use Floor[] on floats instead" % (left, right)))
                break
    return res


def check_missing_using_import(code, lines, imported_modules):
    """Check for use of names from common modules without the using import."""
    res = []
    for module_path, exports in COMMON_MODULES.items():
        if module_path in imported_modules:
            continue
        for export in exports:
            # Check if the export is used as a standalone function call (not a method call)
            # Pattern: start of line or whitespace or (, then name, then (
            # But not: identifier.export(
            pattern = r"(?<![\w.])" + re.escape(export) + r"\s*\("
            if re.search(pattern, code):
                res.append(("warning", 1, "function '%s' used but '%s' is not imported with `using`" % (export, module_path)))
                break  # Only warn once per module
    return res


def check_array_literal_and_tostring(code, lines):
    """Check for array: instead of array{} and ToString on logic."""
    res = []
    for ln, l in enumerate(lines, 1):
        # array: literal syntax
        if re.search(r"\barray\s*:", l):
            res.append(("warning", ln, "`array:` literal syntax is deprecated; use `array{}`"))
        # ToString on logic
        if re.search(r"ToString\s*\(\s*(true|false)\s*\)", l):
            res.append(("warning", ln, "`ToString` called on a logic value; use `if x then \"true\" else \"false\"`"))
        # ToString on a logic variable (harder to detect, but check common patterns)
        if re.search(r"ToString\s*\(\s*\w+\s*\)", l):
            # Could be logic, but we can't know for sure without type info
            pass
    return res


def check_shadowed_module_function(code, lines, imported_modules):
    """Check for local/field names that shadow module functions when module is imported."""
    res = []
    shadow_names = {"Distance", "Lerp", "Clamp", "Abs", "Min", "Max", "Sign"}
    # Find which modules are imported that have these exports
    relevant_modules = set()
    for module_path in imported_modules:
        if module_path in COMMON_MODULES:
            relevant_modules.add(module_path)

    if not relevant_modules:
        return res

    # Check field declarations
    field_pattern = re.compile(r"^\s*(?:@editable\s+)?(?:var\s+)?(\w+)\s*:\s*\w+\s*=")
    for ln, l in enumerate(lines, 1):
        m = field_pattern.match(l)
        if m:
            field_name = m.group(1)
            if field_name in shadow_names:
                res.append(("warning", ln, "field '%s' shadows a module function from an imported module; rename the field" % field_name))

    # Check local variable declarations (var X : type = ...)
    local_pattern = re.compile(r"\bvar\s+(\w+)\s*:\s*\w+\s*=")
    for ln, l in enumerate(lines, 1):
        for m in local_pattern.finditer(l):
            var_name = m.group(1)
            if var_name in shadow_names:
                res.append(("warning", ln, "local variable '%s' shadows a module function from an imported module; rename the variable" % var_name))

    # Check function parameters
    param_pattern = re.compile(r"\(\s*(\w+)\s*:\s*\w+")
    for ln, l in enumerate(lines, 1):
        for m in param_pattern.finditer(l):
            param_name = m.group(1)
            if param_name in shadow_names:
                res.append(("warning", ln, "parameter '%s' shadows a module function from an imported module; rename the parameter" % param_name))

    return res


def top_names(text):
    code = strip(text.replace("\r\n", "\n"))
    return re.findall(r"^(\w+)(?:<[^>]*>)*\s*:=\s*(?:class|struct)\b", code, re.M)


def verse_files(target):
    if os.path.isfile(target):
        return [target]
    base = os.path.join(target, "Content") if os.path.isdir(os.path.join(target, "Content")) else target
    out = []
    for b, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        out += [os.path.join(b, f) for f in files if f.endswith(".verse")]
    return sorted(out)


def run(target):
    problems, seen = [], {}
    root = target if os.path.isdir(target) else os.path.dirname(target)
    for p in verse_files(target):
        rel = os.path.relpath(p, root).replace(os.sep, "/")
        text = open(p, encoding="utf-8", errors="replace").read()
        for sev, ln, msg in check_text(text, rel):
            problems.append({"severity": sev, "file": rel, "line": ln, "message": msg})
        for n in top_names(text):
            if n in seen and seen[n] != rel:
                problems.append({"severity": "error", "file": rel, "line": 1, "message": "'%s' is also defined in %s" % (n, seen[n])})
            seen.setdefault(n, rel)
    return problems


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    target = args[0] if args else (os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    probs = run(target)
    errs = sum(1 for p in probs if p["severity"] == "error")
    if "--json" in argv:
        print(json.dumps({"errors": errs, "warnings": len(probs) - errs, "problems": probs}, ensure_ascii=False))
    else:
        for p in probs:
            print("%s %s:%d %s" % (p["severity"].upper(), p["file"], p["line"], p["message"]))
        print("static check: %d error(s), %d warning(s) in %d file(s). Not a build: run verse_check.py for the real answer." % (errs, len(probs) - errs, len(verse_files(target))))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
