#!/usr/bin/env python3
"""Clean the assets of a Fab product even when UEFN holds the files: close the editor, clean, reopen the project, check again.

  python fab_clean_cycle.py <project folder>            dry run: says what would happen (editor open? how many assets to clean?)
  python fab_clean_cycle.py <project folder> --apply    the owner agreed: close UEFN politely (like the X button), clean (backup outside the
                                                        project), reopen the project (Load on Startup = LastProject, so it opens the last map), wait until it is open, run `fab_pack.py check`
  add --force                                           only when the owner also agreed to lose unsaved work: stops the editor if it does not close by itself

If the editor does not close within 90 s (it is asking to save) the script stops and says so: nothing is forced, nothing is cleaned."""
import os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _root(p):
    p = os.path.abspath(p)
    for c in (p, os.path.dirname(p)):
        try:
            if any(n.endswith(".uefnproject") for n in os.listdir(c)):
                return c
        except OSError:
            pass
    return p


def _editor():
    import uefn_session as S
    return S, S.processes(S.EDITOR)


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    apply, force = "--apply" in argv, "--force" in argv
    if not args:
        print(__doc__); return 2
    root = _root(args[0])
    proj = next((os.path.join(root, n) for n in os.listdir(root) if n.endswith(".uefnproject")), None)
    import fab_assets, fab_pack, fab_lab
    sys.path.insert(0, fab_lab.template_hooks())
    S, procs = _editor()
    todo = fab_assets.clean(root, False)[0]
    print("project: %s | editor open: %s | assets to clean: %d" % (root, "yes" if procs else "no", len(todo)))
    if not apply:
        print("dry run. With --apply: %s clean, %s check." % ("close UEFN, " if procs else "", "reopen the project, " if procs else ""))
        return 0
    if procs:
        for p in procs:
            subprocess.run(["taskkill", "/PID", str(p["pid"])], capture_output=True)   # no /F: the editor closes itself, like the X button
        t0 = time.time()
        while time.time() - t0 < 90 and S.processes(S.EDITOR):
            time.sleep(2)
        if S.processes(S.EDITOR):
            if not force:
                print("UEFN did not close (it is probably asking to save). Save or close it yourself, then run again. Nothing was cleaned."); return 3
            for p in S.processes(S.EDITOR):
                S.terminate(p["pid"])
            time.sleep(3)
        print("UEFN closed.")
    notes, probs = fab_pack.auto_clean(root)
    print("\n".join(notes) or "nothing to clean")
    for x in probs:
        print("PROBLEM:", x)
    if procs:
        try:
            try:   # UEFN opens the last project by itself: Load on Startup = LastProject (the editor is closed now, so the file can be edited; backup next to it)
                r0 = S.set_load_on_startup("LastProject")
                print("Load on Startup: %s -> LastProject%s" % (r0["old"] or "unset", "" if r0["changed"] else " (already)"))
            except Exception as e:
                print("could not set Load on Startup (%s): the project path is passed anyway" % e)
            S.launch(proj)
            r = S.wait_open(proj, timeout=170)
            print("UEFN reopened: %s after %ss" % (r["state"], r["seconds"]))
        except Exception as e:
            print("could not reopen UEFN: %s (open the project by hand)" % e)
    print("--- check ---")
    return subprocess.call([sys.executable, os.path.join(HERE, "fab_pack.py"), "check", root])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
