# Kit for the jam

Three commands that help you hand in a game-jam entry, plus what the kit does when you open a brand-new project. Everything here is local: nothing is sent anywhere.

## A new project: map or Fab product?

Open a session from the `Content` folder of a UEFN project that has no kit yet. The kit notices and asks one question: **is this a map or a Fab product?**

- **Map.** The kit tells you how many files it would copy (a dry run), asks for a yes, then copies the contents of `project-template/` into `Content/` and runs the setup steps for you. It never overwrites a file that already exists. The hooks start working from the next session.
- **Fab product.** The kit installs **nothing**. A Fab product is a small UEFN project whose components are added to the customer's project later, so the kit's own files must never be inside it. The answer is remembered on your computer, outside the project, so you are asked once.

The same installer can be run by hand: `kit_install.py <Content folder> --dry-run` lists what would be copied, `--apply` copies it. It lives in your user profile, put there by `update-my-profile.cmd`.

## /concept-card: is the idea worth building?

Claude scores the idea from 1 to 5 on six criteria (feasibility in UEFN and Verse, scope for the days you have left, hook in the first 30 seconds, how well it shows in a video, retention, originality), weighted to 100. At 75 or more: build it. From 55 to 74: build it only with a smaller scope. Below 55: pick another idea. The card is saved as `Claude/docs/concept-card.md` only after you say yes.

## /devlog: what was built, and how AI was used

The kit already notes every Verse change in `Claude/logs/verse-changes.jsonl` and every failed build in `verse-errors.jsonl`. `/devlog` turns them into `Claude/docs/devlog.md`, day by day, with a few numbers on top. Above the automatic part there is a short "How AI was used" section: Claude proposes the answers from the logs, you correct them, and it is written only after your yes. Running it again updates the automatic part and keeps your text.

## /jam-check: before you hand in

Checks every Verse header (summary, real date and version, no change history), asset file names (letters, digits, underscore) and path length (140 characters at most, project folder name included), and whether the dev log and the concept card exist. Then it prints the list only you can confirm: the private version code, a 30 to 60 second video of the game being played, licences and credits for third-party assets, and the Fortnite rules.
