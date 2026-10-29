---
tags: [kit, manual]
created: kit-1.115.0
updated: kit-1.115.0
sources: [docs/manual/epic-ai-megajam.md]
type: kit
status: current
---
# 2026 Epic AI MegaJam

How the kit helps in [the 2026 Epic AI MegaJam](https://itch.io/jam/2026-epic-ai-megajam), what we added for it in version 1.108, and what Epic's official rules ask of you. Epic's announcement is on [unrealengine.com](https://www.unrealengine.com/news/2026-epic-ai-megajam). This chapter summarises the Official Rules published on 22 October 2026; the rules themselves always win, so read them before you start.

## The dates, in your local time

The contest runs from 12:00 AM Eastern Time on 12 November 2026 to 8:59 PM Eastern Time on 15 November 2026. In Rome that is 12 November at 6:00 to 16 November at 2:59. The theme is announced at the start, on Epic's livestream and on X. The **What's new** page of the console has a live countdown in your own local time: first to the start, then to the deadline. The dates are one line (`JAM`) at the top of that page's script.

## What the rules say about AI, and where the kit fits

AI is allowed, both to build the game and inside it. The important line is about timing:

- **Allowed before the jam:** AI tools, agent configurations, MCP settings, prompt libraries and scripts. This is exactly what the kit is: install it, learn it and try it on a test map before 12 November.
- **Must be made during the jam:** all game content, meaning gameplay, levels and art (sourced assets, which you declare, are the exception). Epic may ask for your prepared AI materials or your version history to check this.
- **A person submits.** The entry must be sent by an entrant, not by an AI agent.
- **AI use does not change the score.** How much AI you used is read for context only.

So: start the game when the jam starts. Do not bring an existing map or its gameplay.

## What the kit helps with

- **A team of agents** that plan first, write Verse, and pass two reviews before a change counts as done. See *Your team*.
- **The UEFN MCP, mapped and proven**, with a guard against calls that save or delete too much. See *The UEFN MCP engine*.
- **`/verse-check`** compiles the project and reports clean, errors, or not analysed.
- **Memory between sessions** in `Claude/docs/`, and `/handoff` for a fresh session.
- **Skills** for Verse, devices, UI, Niagara, materials and retention. See *Skill catalog*.

## What we added for the jam (version 1.108)

| What | What it does for you |
|---|---|
| New project question | A new project asks: map or Fab product? A map gets the kit in a few clicks. See *A UEFN map project* and *A Fab product project*. |
| Verse headers without history | Each header keeps an up-to-date English summary, the real date and the version. Changes go to a log. |
| `verse-changes.jsonl` | One line per change: file, summary, reason, outcome. It feeds the dev log and is a record of how the game grew during the jam. |
| `/concept-card` | Scores an idea with Epic's seven judging criteria plus feasibility and scope. See below. |
| `/devlog` | Builds the dev log from the logs. It is what the Glass Box prize asks for. |
| `/jam-check` | Checks Verse headers, asset names, path length, dev log and concept card, then lists what only you can confirm, taken from the rules. |
| Jam countdown | On the What's new page, in your local time, with a link to the jam page. |

## How the judges score, and how `/concept-card` follows it

Qualified entries are scored on seven criteria, up to 5 points each: Ambition and Innovation, Use of Contest Theme, Fun Factor, Gameplay, Visuals, Level Design and Audio. Ambition and Innovation is judged on the entry itself, and the amount of AI you disclosed does not raise or lower it. In a tie, the tied entries are scored again with Fun Factor counting double.

`/concept-card` uses the same seven, each scored 1 to 5, as **70 of its 100 points**. Score what the idea can realistically reach, not a dream. The theme is announced on 12 November, so before that you leave it out: the card scales the other six and says the theme is not scored yet. A theme score of 1 means the idea ignores the theme, which the rules do not allow, so the verdict is "pick another idea".

The other **30 points are our own two checks**, 15 each: **feasibility** (can UEFN and Verse really do it) and **scope** (5 means small, easy to finish in the days left). The judges do not score these, but an idea that cannot be finished scores nothing. A 1 in either never gives a plain "build it". Verdict: 75 or more, build it; 55 to 74, build it only with a smaller scope; below 55, pick another idea.

## Prizes you can aim at

Per category, one main prize and one modifier prize per entry. UEFN main prizes are $7,500, $5,000 and $2,500 for the first three places. Modifier prizes of $2,500 each (Best Team $5,000) include **Solo Driver** (best game by one developer), **Best Team** (two or more), **Render Royalty** (best visuals), **Pocket Powerhouse** (best mobile game), **Glass Box** (best dev log, submitted with the entry) and **Walkie-Talkie** (best narrative UEFN game with LLM-powered characters made with the UEFN conversations feature). Development continuation grants of up to $50,000 may be offered afterwards at Epic's discretion and are not contest prizes. Winners are notified around 29 January 2027.

## What to hand in, from the rules

- A **private version code** of your island, created during the contest period: the final build you want judged. Live island codes and playtest codes are not accepted, and later updates are not judged.
- A **video** of 30 to 60 seconds of recorded gameplay, 1920x1080 or higher.
- Everything in **English**: in-game text, audio, the video and the entry information.
- A game that **uses the theme**, suitable for players aged 13 and over (Teen), with no trademarks or logos except the Developed in Fortnite logo.
- A **team of 1 to 5**, with names and emails and one team owner, and one entry per team. Entrants must be 18 or older, with an Epic account, living in an eligible country.
- **Sourced (non-original) assets** noted in the submission, with licences you cleared yourself. They are not scored, and AI-generated content does not count as sourced.

## Your first hours on theme day

The steps are the ones in *A working day*, section "Starting a new game: from the idea", with the jam's own rules on top.

1. **Before 12 November**: install the kit and try it on a throwaway test map. If you create the empty project you will use for the jam, keep it empty: no gameplay, level or art, because all game content must be made during the contest. If you are unsure, read the rules.
2. **When the theme is announced**, open the empty project from its `Content` folder, answer **map** and let the setup finish.
3. **Get ideas** and give Claude the theme with them: either your own ("a rhythm game inside a living museum") or "give me 5 ideas that use the theme '...', small enough for a team of two in three days". Ask for variations until two or three feel right.
4. **Score them** with `/concept-card`. Now the theme counts. Pick one that scores 75 or more, or shrink the best one until it does.
5. **Make the plan**: ask for **project-bootstrap**, answer its questions in a few lines, then read `ROADMAP.md` and keep only what the first playable version needs. Put the extras under "out of scope".
6. **Build**, with `/verse-check` often. Spend one hour at most on steps 3 to 5: the days you have are for the game.

## A suggested path through the jam

1. **Before the theme** (now to 11 November). Install the kit, run `/kit-doctor`, try it on a throwaway test map so you know how the agents and the console behave. Do not start the game.
2. **Theme day.** Run `/concept-card` on two or three ideas, now with the theme scored, and pick one that scores 75 or more.
3. **Building days.** Plan in `ROADMAP`, build, run `/verse-check` often. Every change lands in the log without extra work.
4. **Before you submit.** Run `/devlog`, then `/jam-check`, and go through the list it prints yourself.

## What only you can confirm

The kit checks what it can see in your files. It cannot know the private version code, the video, the licences or whether your idea honours the theme, so `/jam-check` lists them from the rules for you to tick. The "How AI was used" part of the dev log is your own account of what you decided: the kit proposes a draft and you correct it.

## Sources
- The kit manual, chapter "2026 Epic AI MegaJam" (docs/manual/epic-ai-megajam.md), kit v1.115.0. Rebuilt on every kit release: do not edit this page, edit the manual.
