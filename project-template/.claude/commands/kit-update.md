---
description: Update this project to the newest kit version now; with --fetch first download the latest release from GitHub
allowed-tools: Bash(py:*), Bash(python:*), Bash(python3:*)
---

Run the kit sync for this project, from the project folder (the one that contains `Claude/`):

`py -3 Claude/hooks/kit_sync.py` (if `py` is not available use `python Claude/hooks/kit_sync.py`).

Then report in one or two short lines the `systemMessage` text of the JSON it printed (from which version to which, how many files). If it printed nothing, say the project is already up to date. Do not change anything else. Remind the owner of two things only if files changed: reload the console page in the browser, and open a new session to load the updated rules and agents. If the owner wants the newest kit first, they can run `update-my-profile.cmd` from their kit copy (it updates the profile that this command reads from).

With `--fetch` (or if the owner asks for the newest release from GitHub): first run `py -3 Claude/hooks/kit_fetch.py` (it updates the profile kit from the latest GitHub release, then syncs this project; `--check` only compares versions). Report its lines instead of the sync message.
