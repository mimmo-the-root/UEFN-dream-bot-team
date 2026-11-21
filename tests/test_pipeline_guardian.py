#!/usr/bin/env python3
"""Acceptance tests for tools/pipeline_guardian.py on a temp lab and fake step commands."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)
import kit_config as kc  # noqa: E402
import pipeline_guardian as pg  # noqa: E402

STEP = '''import sys
name, log = sys.argv[1], sys.argv[2]
with open(log, "a", encoding="utf-8", newline="\\n") as f:
    f.write(name + "\\n")
if name == "bad":
    sys.exit(1)
'''


class Guardian(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pipeline-guardian-test-")
        self.project = os.path.join(self.tmp, "project")
        self.lab = os.path.join(self.project, "Claude")
        os.makedirs(self.lab)
        self.global_env = os.environ.get("KIT_GLOBAL_SETTINGS")
        os.environ["KIT_GLOBAL_SETTINGS"] = os.path.join(self.tmp, "global-settings.json")
        self.step_log = os.path.join(self.tmp, "steps.log")
        self.step_script = os.path.join(self.tmp, "step.py")
        with open(self.step_script, "w", encoding="utf-8", newline="\n") as f:
            f.write(STEP)
        self.filename = pg.__file__

    def tearDown(self):
        pg.__file__ = self.filename
        if self.global_env is None:
            os.environ.pop("KIT_GLOBAL_SETTINGS", None)
        else:
            os.environ["KIT_GLOBAL_SETTINGS"] = self.global_env
        shutil.rmtree(self.tmp, ignore_errors=True)

    def configure(self, names, fail=False, boom=False, enabled=True):
        components = [{"name": n, "cmd": [sys.executable, self.step_script, n, self.step_log]} for n in names]
        if fail:
            components.insert(1, {"name": "bad", "cmd": [sys.executable, self.step_script, "bad", self.step_log]})
        if boom:
            components.insert(2, {"name": "boom", "cmd": [os.path.join(self.tmp, "no-such-command")]})
        settings = os.path.join(self.lab, "config", "kit-settings.json")
        os.makedirs(os.path.dirname(settings), exist_ok=True)
        with open(settings, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"pipeline": {"enabled": enabled, "interval_min": 5, "components": components}}, f, indent=2)

    def steps(self):
        try:
            with open(self.step_log, encoding="utf-8") as f:
                return [ln.strip() for ln in f if ln.strip()]
        except OSError:
            return []

    def guardian_log(self):
        try:
            with open(pg.log_path(self.lab), encoding="utf-8") as f:
                return f.read()
        except OSError:
            return ""

    def test_components_run_in_order(self):
        self.configure(["one", "two", "three"])
        self.assertEqual(pg.once(self.lab), 0)
        self.assertEqual(self.steps(), ["one", "two", "three"])
        hb = pg.read_heartbeat(self.lab)
        self.assertEqual([s["name"] for s in hb["steps"]], ["one", "two", "three"])
        self.assertTrue(all(s["result"] == "ok" for s in hb["steps"]))
        self.assertIn("cycle 1 | two | ok", self.guardian_log())

    def test_failing_step_does_not_stop_loop(self):
        self.configure(["one", "three"], fail=True, boom=True)
        outcome = pg.supervise(self.lab, sleep=lambda seconds: None, max_cycles=3)
        self.assertEqual(outcome, "rounds")
        self.assertEqual(self.steps(), ["one", "bad", "three"] * 3)
        self.assertIn("cycle 2 | bad | failed (rc=1)", self.guardian_log())
        self.assertIn("cycle 3 | boom | failed (FileNotFoundError)", self.guardian_log())
        hb = pg.read_heartbeat(self.lab)
        self.assertEqual(hb["cycle"], 3)
        self.assertEqual([s["result"] for s in hb["steps"]], ["ok", "failed (rc=1)", "failed (FileNotFoundError)", "ok"])

    def test_stop_file_stops_the_loop(self):
        self.configure(["one"])
        self.assertEqual(pg.stop(self.lab), 0)
        self.assertTrue(os.path.isfile(pg.stop_path(self.lab)))
        outcome = pg.supervise(self.lab, sleep=lambda seconds: None, max_cycles=3)
        self.assertEqual(outcome, "stopped")
        self.assertEqual(self.steps(), [])
        self.assertFalse(os.path.isfile(pg.stop_path(self.lab)))
        self.assertIn("STOP file found", self.guardian_log())
        self.assertEqual(pg.read_heartbeat(self.lab)["status"], "stopped")

    def test_hot_update_exits_after_one_cycle(self):
        self.configure(["one"])
        updated = os.path.join(self.tmp, "pipeline_guardian_new.py")
        with open(os.path.abspath(pg.__file__), encoding="utf-8") as f:
            source = f.read()
        source = source.replace('VERSION = "' + pg.VERSION + '"', 'VERSION = "9.9.9"', 1)
        with open(updated, "w", encoding="utf-8", newline="\n") as f:
            f.write(source)
        pg.__file__ = updated
        outcome = pg.supervise(self.lab, sleep=lambda seconds: None, max_cycles=3)
        self.assertEqual(outcome, "hot-update")
        self.assertEqual(self.steps(), ["one"])
        self.assertIn("hot update: file has 9.9.9", self.guardian_log())
        self.assertEqual(pg.read_heartbeat(self.lab)["status"], "hot-update")

    def test_status_uses_plain_words(self):
        self.configure(["one"])
        r = subprocess.run([sys.executable, os.path.join(TOOLS, "pipeline_guardian.py"), "status", "--lab", self.lab],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Pipeline is enabled.", r.stdout)
        self.assertIn("Pipeline guardian is not running", r.stdout)
        pg.write_heartbeat(self.lab, {"pid": os.getpid(), "cycle": 1, "status": "idle", "steps": []})
        self.assertIn("Pipeline guardian is running", pg.status_text(self.lab))
        self.configure(["one"], enabled=False)
        disabled = pg.status_text(self.lab)
        self.assertIn("Pipeline is disabled (pipeline.enabled is false)", disabled)
        self.assertNotIn("guardian is running", disabled)

    def test_optional_components_skip_when_absent(self):
        self.assertEqual(pg.resolve_component("orchestrate", self.lab)[1][-1], "")
        self.assertIn("watchdog.py", pg.resolve_component("watchdog", self.lab)[1][1])
        self.assertIn("--apply", pg.resolve_component("pm_routine", self.lab)[1])
        if not os.path.isfile(os.path.join(TOOLS, "dc_auto.py")):
            self.assertIsNone(pg.resolve_component("dc_auto", self.lab)[1])
        if pg.brain_hot_script(self.lab) is None:
            self.assertIsNone(pg.resolve_component("brain_hot_update", self.lab)[1])

    def test_hook_passes_claude_lab_and_checks_claude_stop(self):
        hook_path = os.path.join(ROOT, "project-template", "Claude", "hooks", "ensure-pipeline.ps1")
        with open(hook_path, encoding="utf-8") as f:
            hook = f.read()
        self.assertTrue(os.path.isdir(self.lab))
        self.assertIn('$lab = Join-Path $ProjectDir "Claude"', hook)
        self.assertIn('--lab", "`"$lab`"")', hook)
        self.assertNotIn('--lab", "`"$ProjectDir`"")', hook)
        self.assertIn('(Join-Path $lab "STOP")', hook)
        self.assertNotIn('(Join-Path $ProjectDir "STOP")', hook)
        self.assertIn('$log = Join-Path $lab "logs\\console-start.log"', hook)
        self.assertEqual(pg.project_dir(self.lab), self.project)
        self.assertEqual(pg.project_dir(os.path.join(self.tmp, "other")), os.path.join(self.tmp, "other"))

    def test_config_reads_real_lab_layout(self):
        self.configure(["one"], enabled=False)
        self.assertFalse(pg.config(self.lab)[0])
        self.assertEqual(pg.log_path(self.lab), os.path.join(self.lab, "logs", "pipeline-guardian.log"))
        self.assertEqual(pg.stop_path(self.lab), os.path.join(self.lab, "STOP"))

    def test_brain_hot_script_uses_lab_hooks(self):
        hooks = os.path.join(self.lab, "hooks")
        os.makedirs(hooks, exist_ok=True)
        script = os.path.join(hooks, "brain_hot_update.py")
        with open(script, "w", encoding="utf-8", newline="\n") as f:
            f.write("")
        self.assertEqual(pg.brain_hot_script(self.lab), script)

    def test_kit_config_pipeline_keys(self):
        defaults = kc.defaults()["pipeline"]
        self.assertEqual(defaults["enabled"], True)
        self.assertEqual(defaults["interval_min"], 5)
        self.assertEqual(defaults["components"], list(pg.DEFAULT_COMPONENTS))
        self.assertTrue(kc.validate(kc.defaults()) == [])
        self.assertTrue(kc.validate({"pipeline": {"interval_min": 0}}))
        self.assertTrue(kc.validate({"pipeline": {"interval_min": 61}}))
        self.assertTrue(kc.validate({"pipeline": {"enabled": "yes"}}))
        self.assertTrue(kc.validate({"pipeline": {"components": "watchdog"}}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
