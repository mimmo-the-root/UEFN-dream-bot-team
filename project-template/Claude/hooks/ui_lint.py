#!/usr/bin/env python3
"""ui_lint.py - checks the Agent Console pages against the kit's shared design tokens and pulse rules.

Usage: python ui_lint.py [page.html ...]   (default: every agent-console*.html next to this file)
Prints one line per problem; exit 1 if any ERROR. Fail-open: a missing tokens file skips the token check.
Checks: shared neon/plain-case/aligned-number blocks, plain header, token drift (a page redefines a shared token with a different value), keyframes that animate
anything but transform/opacity (WARN), animations without a reduced-motion rule (ERROR).
"""
import glob, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHEAP = {"transform", "opacity", "offset-distance", "visibility"}
TOKEN_FILES = [
    os.environ.get("UEFN_CONSOLE_TOKENS", ""),
    os.path.join(os.path.expanduser("~"), ".claude", "skills", "console-ui", "references", "tokens.css"),
    os.path.join(HERE, "..", "..", "..", "user-level-skills", "console-ui", "references", "tokens.css"),
]


def parse_tokens(css):
    m = re.search(r":root\s*\{(.*?)\}", css, re.S)
    out = {}
    if m:
        for k, v in re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", m.group(1)):
            out[k] = re.sub(r"\s+", "", v)
    return out


def canonical():
    for p in TOKEN_FILES:
        if p and os.path.isfile(p):
            return parse_tokens(open(p, encoding="utf-8").read())
    return {}


def _lum(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    a, b = _lum(a), _lum(b)
    a, b = max(a, b), min(a, b)
    return (a + 0.05) / (b + 0.05)


def keyframes(css):
    for m in re.finditer(r"@keyframes\s+([\w-]+)\s*\{", css):
        i, depth = m.end(), 1
        while i < len(css) and depth:
            depth += {"{": 1, "}": -1}.get(css[i], 0)
            i += 1
        yield m.group(1), css[m.end():i - 1]


def lint(path, canon):
    s = open(path, encoding="utf-8").read()
    name = os.path.basename(path)
    problems = []
    css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", s, re.S))
    if canon:
        for root in re.findall(r":root\s*\{(.*?)\}", css, re.S):
            for k, v in re.findall(r"(--[\w-]+)\s*:\s*([^;]+)", root):
                v = re.sub(r"\s+", "", v)
                if k in canon and not canon[k].startswith("var(") and v != canon[k] and not v.startswith("var("):
                    problems.append(("ERROR", name, f"token {k} is {v}, the kit says {canon[k]}"))
    for kf, body in keyframes(css):
        props = set(re.findall(r"([a-z-]+)\s*:", body)) - {"to", "from"}
        bad = sorted(p for p in props if p not in CHEAP)
        if bad:
            problems.append(("WARN", name, f"@keyframes {kf} animates {', '.join(bad)} (only transform/opacity)"))
    # contrast: the muted text token must stay readable (WCAG 4.5:1) on the page and panel backgrounds
    toks = {}
    for root in re.findall(r":root\s*\{(.*?)\}", css, re.S):
        for k, v in re.findall(r"(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{6})\b", root):
            toks[k] = v
    for fg in ("--dim", "--text"):
        for bg in ("--bg", "--panel"):
            if fg in toks and bg in toks and contrast(toks[fg], toks[bg]) < 4.5:
                problems.append(("ERROR", name, f"{fg} on {bg} contrast {contrast(toks[fg], toks[bg]):.1f}:1 is under 4.5:1"))
    stripes = len(re.findall(r"border-(?:left|right)\s*:\s*[2-9]px|inset\s+[2-9]px\s+0\s+0", css))
    if stripes:
        problems.append(("WARN", name, f"{stripes} coloured side stripe(s) wider than 1px (use a dot or background instead)"))
    if "<button" in s or "<input" in s:
        if "focus-visible" not in css:
            problems.append(("WARN", name, "no :focus-visible style (keyboard users cannot see where they are)"))
    # v1.115: every page carries the shared blocks and the plain header (no ">" prompt, no "_" cursor, no "#" comment)
    for marker, why in (("console-ui: neon in three tones", "neon tones"), ("plain-case labels", "plain-case labels"), ("aligned numbers", "aligned numbers"), ("console-ui: micro-life", "micro-life"), ("console-ui: theme", "theme colours")):
        if marker not in css:
            problems.append(("ERROR", name, f"missing the shared '{why}' block (copy it from console-ui/references/components.md)"))
    if re.search(r"&gt;\s*<(?:b|span|strong)[^>]*>DREAM BOT|hdr-blink|class=\"blink\">_|class=\"(?:line )?comment\"[^>]*>#", s):
        problems.append(("WARN", name, "header still has the old prompt styling (> title _ and # subtitle): use the plain title"))
    if re.search(r"animation\s*:", css) and "prefers-reduced-motion" not in css:
        problems.append(("ERROR", name, "has animations but no prefers-reduced-motion rule"))
    if "prefers-reduced-motion:reduce){*," in s.replace(" ", ""):
        problems.append(("ERROR", name, "a blanket reduced-motion rule switches off every animation even when Motion is on (prefix it with html:not(.motion-full))"))
    return problems


def main(argv):
    pages = argv or sorted(glob.glob(os.path.join(HERE, "agent-console*.html")))
    canon = canonical()
    allp = []
    for p in pages:
        allp += lint(p, canon)
    for lvl, n, msg in allp:
        print(f"{lvl} {n}: {msg}")
    if not allp:
        print("ui_lint: ok")
    return 1 if any(l == "ERROR" for l, _, _ in allp) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
