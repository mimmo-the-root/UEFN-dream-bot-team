# Constitution: <GAME NAME>

<!-- Written by /game-plan the first time, from the genre and the lessons already learned; the owner approves it.
     Rules that do not change from task to task. Change one only with a written reason. Checked by plan_check.py (/consistency):
     anything the plan or the tasks do against a rule here is CRITICAL. -->

- Status: Draft
- Approved: no

## Principles
- <rule>. Why: <reason>. Source: <skill, lesson or owner>
- Devices before Verse: use a device that exists before writing a new Verse one. Why: less code to break. Source: kit rule
- Every Verse file has the header (Summary, date, version, no change history). Why: it is the only description of the file. Source: kit rule

## Forbidden
- <a word or short phrase the plan and the tasks must never contain, one per line>
- Personal data: where a personal name would be written (texts, reports, file names the user owns), write `***anonymized***` in English (GDPR, Regulation (EU) 2016/679, data minimisation). Never applied to assets made by Epic, only to the user's own files.

## Names and budget
- Folders and assets: letters, digits and underscore, paths of 140 characters at most.
- Devices: every device is placed in an Outliner folder named for its role (for example `Devices/Spawners`, `Devices/Pen`, `Devices/Round`, `Devices/Hud`) and never left at the root of the Outliner; and every device gets a custom label `Role_Index` (letters, digits, underscore: `ChickenSpawner_1`, `PenCaptureArea`, `RoundTimer`, `HudScore`), never the default name, so the owner can tell them apart in the configuration pickers. Folder and label are set when the device is placed, then read back; texts and messages of a device are set to the exact text of the plan.
- Device names speak the same language as the Verse code: the label of a placed device is the name of the Verse field that points to it (field `RoundTimer` -> device `RoundTimer`; an array field `ChickenSpawners` -> devices `ChickenSpawner_1..n`), so the owner links references by choosing the identical name in the picker. The coder agent chooses the Verse field names first and the placement uses them; a mismatch is a finding that the audit fixes by itself.
- Island Settings: read and set through the MCP when the properties exist (read back every value), and list the rest as owner steps. For a game where the map must stay intact: Pickaxe Destruction None, Environment Damage Off, Building Can Destroy Environment No, building not allowed.
- Performance: <budget, e.g. no per-frame loops, number of active devices>

## Scope limits
- <what this project will not grow into, e.g. one pen, one round length>

## Self-healing (minor bugs the kit may fix by itself)
- Mode: auto
- Minor: a Verse compile error with a clear cause (type, name, comma); an old or missing Verse header; an asset name or path outside the rules; a reference to a device already placed; a value out of range (volume, time).
- Medium (propose, wait for the owner): logic that breaks an acceptance criterion; a missing device; behaviour different from the expected one.
- Major (stop and report): an error in the requirement; a change of mechanic; data loss; any conflict with this file; any change to GAME-SPEC.md, this file or a task's criteria.
- Limits: 3 attempts per bug, 10 automatic fixes per session; a restore point before each fix; undo when the rebuild shows new errors.

Version: 1
