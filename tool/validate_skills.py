#!/usr/bin/env python3
"""validate_skills.py - structural checks for every skill under user-level-skills/.

Errors (exit 1):
  - SKILL.md without frontmatter, or without name/description (genre skills: genre_slug)
  - name does not match the folder name; description empty, too long (>1024) or containing < >
  - SKILL.md larger than HARD_SKILL chars; any reference file larger than HARD_REF chars
  - a relative link or `references/...` path that points to a file that does not exist
  - a `~/.claude/skills/<name>` mention of a skill that does not exist in the kit
Warnings (exit 0, exit 1 with --strict):
  - SKILL.md larger than SOFT_SKILL chars (keep the entry point short, move detail to references/)
  - missing `last_reviewed` (YYYY-MM-DD) or `sources` (list of URLs, or [original]) in the frontmatter

Usage: python tool/validate_skills.py [--strict] [skills_dir]
"""
import os, re, sys

SOFT_SKILL, HARD_SKILL, HARD_REF = 3000, 12000, 50000
args = [a for a in sys.argv[1:] if not a.startswith("--")]
STRICT = "--strict" in sys.argv
BASE = os.path.abspath(args[0]) if args else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "user-level-skills"))


def frontmatter(text):
    m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        k = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if k:
            fm[k.group(1)] = k.group(2).strip()
    return fm


def skill_dirs():
    for d, dirs, files in os.walk(BASE):
        dirs[:] = [x for x in dirs if x not in ("local", "pack", "official", "references", "examples", "__pycache__")]
        if "SKILL.md" in files:
            yield d


def main():
    errors, warns = [], []
    names = {os.path.basename(d) for d in skill_dirs()}
    for d in sorted(skill_dirs()):
        rel = os.path.relpath(d, BASE).replace("\\", "/")
        p = os.path.join(d, "SKILL.md")
        text = open(p, encoding="utf-8").read()
        fm = frontmatter(text)
        if fm is None:
            errors.append("%s: SKILL.md has no frontmatter" % rel)
            continue
        is_genre = rel.startswith("genre/")
        if is_genre:
            if fm.get("genre_slug") != os.path.basename(d):
                errors.append("%s: genre_slug must equal the folder name" % rel)
        else:
            if fm.get("name") != os.path.basename(d):
                errors.append("%s: name must equal the folder name (%r)" % (rel, fm.get("name")))
            desc = fm.get("description", "")
            if len(desc) < 20:
                errors.append("%s: description missing or too short" % rel)
            if len(desc) > 1024:
                errors.append("%s: description over 1024 chars" % rel)
            if "<" in desc or ">" in desc:
                errors.append("%s: description must not contain angle brackets" % rel)
            if "last_reviewed" not in fm:
                warns.append("%s: no last_reviewed (YYYY-MM-DD)" % rel)
            elif not re.fullmatch(r"\d{4}-\d{2}-\d{2}", fm["last_reviewed"].strip("'\"")):
                errors.append("%s: last_reviewed must be YYYY-MM-DD" % rel)
            if "sources" not in fm:
                warns.append("%s: no sources (URLs, or [original])" % rel)
        n = len(text)
        if n > HARD_SKILL:
            errors.append("%s: SKILL.md is %d chars (hard cap %d); move detail to references/" % (rel, n, HARD_SKILL))
        elif n > SOFT_SKILL:
            warns.append("%s: SKILL.md is %d chars (soft cap %d)" % (rel, n, SOFT_SKILL))
        # references: size + link targets
        for dd, _, files in os.walk(d):
            for f in files:
                fp = os.path.join(dd, f)
                if f.endswith(".md") and f != "SKILL.md" and os.sep + "local" + os.sep not in fp:
                    if os.path.getsize(fp) > HARD_REF:
                        errors.append("%s: %s over %d chars" % (rel, os.path.relpath(fp, d).replace("\\", "/"), HARD_REF))
        body = text
        for m in re.finditer(r"\]\((?!https?:|#|mailto:)([^)\s#]+)\)", body):
            tgt = m.group(1)
            if not os.path.exists(os.path.normpath(os.path.join(d, tgt))):
                errors.append("%s: broken link -> %s" % (rel, tgt))
        for line in body.splitlines():
            if re.search(r"(?i)\bcreate\b", line):  # "create <file> if missing" is a legitimate instruction
                continue
            for m in re.finditer(r"(?<![\w/.-])(references/[A-Za-z0-9_./-]+\.md)", line):
                if not os.path.exists(os.path.join(d, m.group(1))):
                    errors.append("%s: missing file %s" % (rel, m.group(1)))
        for m in re.finditer(r"~/\.claude/skills/([a-z0-9][a-z0-9-]*)", body):
            if m.group(1) not in names and m.group(1) not in ("genre",):
                errors.append("%s: refers to unknown skill %s" % (rel, m.group(1)))
    for w in warns:
        print("WARN  " + w)
    for e in errors:
        print("ERROR " + e)
    print("validate_skills: %d skills, %d error(s), %d warning(s)" % (len(names), len(errors), len(warns)))
    return 1 if errors or (STRICT and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
