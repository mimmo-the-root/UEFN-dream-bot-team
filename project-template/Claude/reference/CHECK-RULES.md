# Rules for every check the kit makes

A check that cannot say it did not run is not a check. When a step could not run, its output looks exactly like a step that ran and found nothing, and the reader believes the comfortable one. These five rules apply to every gate, score, audit, doctor and review in the kit, and to any you write.

1. **Every verdict has a "could not assess" value.** Use `NOT ASSESSED` next to pass and fail, and say which reason applied (no input, no access, nothing measures it). It ranks above a pass (a scope that was not looked at is not good) and below a failure (a known problem is more useful than an unknown). It is not a softer failure: "found nothing" and "could not look" need different fixes.
2. **A missing value is never read as the comfortable one.** Before defaulting, ask who writes that value. If nothing in the kit writes it, the default branch is the normal case, not the exception.
3. **A skipped step says so in the output.** If a phase did not run (wrong project type, missing file, no editor), the report names it. A silent skip and a pass are the same text to the reader.
4. **Never assert what you cannot source.** If a device name, a function or a number is not in the digest, the map or the files, write the gap ("not sourceable: the member Enable of this device") and do not fill it from memory. Tie the gap to the verdict: a claim built on a gap cannot be a pass.
5. **A pass needs evidence newer than the work.** A screenshot, a log line or a playtest that is older than the file it vouches for counts as not assessed. `evidence_stamp.py` writes and checks that stamp.

Where it already applies: the delivery gate (`release_gate.py`, exit code 2 when a part could not be looked at), the Score page (criteria nothing measures are listed as NOT ASSESSED), `kit_doctor.py`, and the "built, not played" status of the demo.
