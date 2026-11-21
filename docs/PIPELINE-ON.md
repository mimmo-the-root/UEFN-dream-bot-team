# Pipeline guardian (T-117)

The pipeline no longer needs a Windows scheduler. `Claude/hooks/ensure-pipeline.ps1` starts
`tools/pipeline_guardian.py supervise` once per project at session start, in a hidden window; the
guardian keeps the relay pipeline running and replaces itself after an update. It logs every step in
`Claude/logs/pipeline-guardian.log` and its heartbeat in `Claude/logs/pipeline-guardian.json`.

Every `pipeline.interval_min` minutes (default **5**, allowed **1-60**) the guardian runs these steps, in order:

1. `tools/orchestrate.py --lab LAB --integrate-cmd ""` (integration disabled; only the relay is orchestrated).
2. `tools/watchdog.py --lab LAB`.
3. `tools/pm_routine.py LAB --apply`.
4. `tools/dc_auto.py` (package 306) — skipped silently when the file is absent.
5. Second-brain hot update (package 303) — skipped silently when its module is absent.

A step that raises or exits non-zero is logged as failed and skipped; the next step and the next
cycle still run. The guardian also checks whether a newer copy of its own file is on disk: after the
current cycle it exits so the session hook starts the new version.

Settings live in `Claude/config/kit-settings.json` (defaults in `tools/kit_config.py`):

```json
"pipeline": { "enabled": true, "interval_min": 5,
  "components": ["orchestrate", "watchdog", "pm_routine", "dc_auto", "brain_hot_update"] }
```

`components` may also contain `{ "name": "...", "cmd": ["python", "script.py", "{lab}"] }` objects;
`{lab}` is replaced with the lab folder. This is how a test injects fake steps without starting the
real pipeline.

**How to stop it:** create an empty file named `STOP` in the lab folder (`Claude/STOP`). At its next
cycle the guardian removes that file, logs the stop and exits; delete it yourself to allow a fresh
start. For an off switch that survives new sessions, set `pipeline.enabled` to `false` instead: the
session hook will not start a guardian and a running one exits at the next cycle.

Commands: `python tools/pipeline_guardian.py status --lab LAB` (plain words), `once` (one cycle),
`supervise` (the loop), `stop` (create the STOP file).
