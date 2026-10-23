---
description: Score a game idea for feasibility (1-5 on six criteria, weighted to 100) and write the concept card
---

Ask the owner for the one-sentence pitch if it was not given. Score the six criteria from 1 to 5 yourself, from what UEFN and Verse can really do (check the matching skills and the second brain first) and from the days left; say in one short line why for each. For `scope`, 5 means small and easy to finish. Then run `python Claude/hooks/concept_card.py --title "..." --pitch "..." --scores feasibility=N,scope=N,hook=N,retention=N,originality=N,showability=N --days-left N` (on Windows use `py -3` if `python` is not found). Show the result. Write it with `--write` only after the owner says yes.
