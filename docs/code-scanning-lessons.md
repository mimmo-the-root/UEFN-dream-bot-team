# Code-scanning lessons (CodeQL)

What we learned taking `skills_lib.py` from 18 open CodeQL alerts to zero (PR #12, October 2026).
Read this before accepting a Copilot Autofix PR or changing how files are opened.

## 1. Fix the alert where the data enters, not where it is used

All the "Uncontrolled data used in path expression" alerts started in one place: the POST body
(`genre`, `proposal`) in `agent-console-server.py`, flowing into `skills_lib.check()` / `act()` and
from there into every file helper. The scanner keeps the value "untrusted" the whole way, so each
file operation was reported, however many checks sat in front of it.

What worked: `resolve_genre()` accepts a requested genre only if it exists, and **returns the name
taken from the directory listing, not the caller's string**. `_proposal_path()` does the same with
the inbox listing. After that the data reaching the paths is no longer request data.

## 2. What the scanner did NOT recognise

- `os.path.commonpath([root, full]) == root` inside a helper (`_inside`): no effect.
- `realpath` + `startswith(root + os.sep)` inside a helper that returns the path: no effect.

Those checks are still correct and worth keeping as a second layer (and the tests prove they stop
`..`, symlinks and sibling-prefix directories), but do not expect them to close an alert.

## 3. Do not put "inside the skills root" in a helper that also serves user-chosen paths

`export_pack` and `merge` legitimately work **outside** the skills root. Several Autofix PRs added a
root check to `_write_json` and silently broke the export. Owner-chosen paths get their own narrow
checks (`_user_file`: existing `.json`, size cap; `_user_dir`: folder, not a file or a filesystem
root) and the export writes inside the folder the user picked (`base=out_dir`).

## 4. A blocked path must be a visible error

Returning the default value when a path is rejected makes an attack look like "file not found" and a
configuration mistake look like an empty file. `_inside()` raises `ValueError`; only a genuinely
missing or corrupt file returns the default.

## 5. Validation regexes: `fullmatch`, not `match` with `$`

`$` also matches before a trailing newline, so `survival\n` and `pr-0123456789\n` passed. Use
`re.fullmatch` (or `\Z`) for slugs, variants and ids.

## 6. Logging alerts: read the path before changing the code

Alert #19 ("clear-text logging") was a false positive: the "sensitive" source was the list
`_SECRET_RULES`, and what reached the log was only the rule **names** (`github_token`, ...), returned
as labels in privacy-check findings. The scanner reacts to the word "secret" in the variable name.
Open "Show paths", check what is really printed, and dismiss with a comment if it is a label.

Never "fix" such an alert by printing only `{"ok": ...}`: the CLI output is parsed by agents and hooks
(`patterns` and `proposals` print lists, `summary` prints the full payload). The tests in
`tests/test_skills_safety.py` cover those shapes.

## 7. Checklist for an Autofix pull request

1. Fetch the branch and read the diff (`git fetch origin`, `git diff main...origin/<branch>`).
2. Run both test files on the branch code. Do not trust a green GitHub check: the original tests did
   not exercise the CLI or the export.
3. Does it cover **all** the sinks of that alert, or only one line?
4. Does it break a legitimate use (export, merge, CLI output)?
5. Does a blocked input give a visible error?
6. Merge only after the PR's CodeQL check says "No new alerts".

Copilot can also push **more commits to the same branch after the PR is merged**: run `git fetch`
and look at the branch before deleting it.

## 8. How we verify a security change

Open a pull request and do **not** merge it. CodeQL runs on the PR; read the "Code scanning results"
check. After the merge the scan runs on `main` and old alerts close by themselves (Security -> Code
scanning shows `0 Open`).
