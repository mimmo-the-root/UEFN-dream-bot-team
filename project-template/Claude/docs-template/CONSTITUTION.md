# Constitution: <GAME NAME>

<!-- Written by /piano the first time, from the genre and the lessons already learned; the owner approves it.
     Rules that do not change from task to task. Change one only with a written reason. Checked by plan_check.py (/coerenza):
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
