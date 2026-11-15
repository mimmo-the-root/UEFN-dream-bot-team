---
tags: [kit, manual]
created: kit-1.124.54
updated: kit-1.124.54
sources: [docs/manual/free-models.md]
type: kit
status: current
---
# Free models and 24/7

The Dream Router is a small program on your PC that lets Cod work on free AI models: all the time, or only when your Claude plan is at its limit. It starts and stops with Cod by itself, and a guardian starts it again if it ever stops.

## The three modes

Choose one on the console page **Models**. It applies to the next Cod session, however you start Cod.

| Mode | What happens | Your Claude plan |
|---|---|---|
| **Plan, then free** (default) | Cod works on your plan; when the plan is at its limit, the same session goes on with free models, and goes back to Claude after the reset | Used first; the router passes Claude Code's own request and login to Claude untouched |
| **Plan only** | As before the router existed | Used |
| **Free only** | Only free models | Never used |

The router writes the chosen mode into the `env` of your Claude Code settings (`%USERPROFILE%\.claude\settings.json`): only the values it needs, a copy is kept as `settings.json.dream-router.bak`, and anything you set yourself is left alone.

Plan, then free sends your plan's login through a program on your PC. Claude's plan terms limit the use of its credentials outside Anthropic's apps: the choice is yours.

## What you need

1. Free accounts at a few providers. Each gives you one **API key**: a long password the router uses to call their free models. No subscription, no card.

| Provider | Where to get the key | Notes |
|---|---|---|
| Google Gemini | https://aistudio.google.com/apikey | key starts with `AIza`; a daily quota |
| Z.ai | https://z.ai/manage-apikey/apikey-list | only the free GLM Flash models are used |
| NVIDIA | https://build.nvidia.com/settings/api-keys | key starts with `nvapi-`; free use is for evaluation; slow on big requests |
| OpenRouter | https://openrouter.ai/keys | `:free` models, 50 requests a day |
| Kilo Gateway | no key needed | free models; prompts may be logged |
| LLM7.io | https://dash.llm7.io (free token, needed since 2026) | |
| DeepSeek (paid, cheap) | https://platform.deepseek.com/api_keys | not free: about 0.30 USD per million input tokens; last in the order, used only when every free provider fails |
| Groq | https://console.groq.com/keys | only small requests fit its free limit |
| Ollama Cloud | https://ollama.com/settings/keys | last in the order: its free plan answered "add credits" for every model in our test |

2. Run `update-my-profile.cmd` once (and after every kit update), so the router is in your profile.

## Start it

Nothing to start by hand: when Cod starts, the kit starts the router's **guardian**, which starts the router, starts it again if it stops, and replaces an older version after an update. When you close the last Cod session, the router stops too. `dream-router.cmd` (in `%USERPROFILE%\.claude\hooks`) restarts it by hand if you ever need it.

Open the console, page **Models**, paste each key in its box and press **Save** (keys are saved only on this PC, in `%USERPROFILE%\.dream-router\keys.env`, shown with the last 4 characters). The router tests every key when it starts, every 30 minutes and after you save one; **Test keys** tests them now. A provider is green when its key works, grey while it is being checked, red with the reason when it does not.

## The Models page

- **Free models**: switches the router on or off. **How Cod works**: the three modes above.
- **Providers and keys**: which providers are ready, paused (and when they come back) or not working, the model each one uses, and the key boxes.
- **Models used in the last 72 hours** (8 per page): each model appears as it works, with a bar of its tokens, the most used first. Your plan shows as `claude-plan`.
- **Where the tokens go**: for every Claude Code request, how much is instructions, tools and conversation, and for the last request how many UEFN tools were sent and which ones tool search loaded.
- **Last errors**: which provider and model failed, the provider's own message and how big the request was.

## How the router saves tokens and keeps Cod working

- When a provider is at its limit, slow or refuses a request, the router moves to the next one by itself. A model that is not free for your account is set aside for 6 hours, even across restarts.
- Tool outputs going to a free model are shrunk the same way every time: colours and repeated lines out, very long outputs kept as their beginning and end with a note. Requests on your plan are passed through untouched, so Claude's prompt cache keeps working.
- **Clear old tool results** (on by default): in a long conversation the router replaces tool results older than the last 5 with a one-line note (the tool name and how much was cut), and keeps only the last copy of a long text that appears twice. What you wrote is never touched, and the recent work stays whole. The Models page shows how much was saved.
- The UEFN tools reach the free models: the router loads them the way Claude does, only when tool search asks for them, and shortens tool names longer than free providers accept (64 characters), then gives the real name back.
- **Spread the load** (on by default): the providers that answered in the last 30 minutes take turns, so no single free quota runs out first. With it off, the provider that answered last is tried first. A provider that hangs or has used its daily quota is left alone for 10 minutes (remembered across restarts); a model that hangs twice in a row is set aside for 30 minutes.
- Auto permission mode works on free models: its safety check is sent as an ordinary request through the router. That check re-sends the whole session for every action (about 45k tokens): with **Safety check on free models: Short** (the default) the router sends only your messages and the recent part of the session, a fraction of the tokens. Full sends everything, as Claude would.
- **Accept edits on free models** (off by default): with Free only, Cod starts in accept-edits permission mode, so that safety check never runs at all, but Cod asks before every command that is not already allowed. Off, Cod stays in auto mode and the safety check is sent short. Your own permission mode comes back when you leave Free only.

## Big tasks: small pieces

A long session re-reads its whole conversation on every request, and that is most of the tokens (and minutes on free models). For a big task use `/pieces <task>` (agent `piece-orchestrator`): the task is cut into 2-6 small pieces, each run in a fresh short session that gets only its brief and the notes of the pieces before it. When a piece fails it was too big: it is cut again into smaller pieces (up to 3 levels). A piece that still fails is tried on at least 10 other free models, one after the other, and only then skipped; the next pieces are told and work around it. The run never stops on a failure and completes as many pieces as it can (`python Claude/hooks/pieces.py status <task>` shows the tree). UEFN tools that only read the level run without asking for permission, so an unattended session does not stop there; tools that change the map still ask.

## What to expect

Free models are weaker than Claude at Verse and at the editor tools: expect more correction rounds. The kit's reviewers and the rule "the same failure twice: stop and ask" stay on. Free providers may use what you send to train their models. Free quotas end during the day: with only a few keys, Cod can find every provider paused for a while.

## Model history

The router keeps a daily history of every free model it uses, and a weekly summary page in the second brain.

### Daily JSONL files

- **Location**: `%USERPROFILE%\.dream-router\history\YYYY-MM.jsonl` (one file per month)
- **Written**: at the first request after midnight, and at router quit (`/router/quit`)
- **One line per model per day** — never duplicates. Each line has:
  - `date` (YYYY-MM-DD)
  - `provider` (gemini, openrouter, nvidia, etc.)
  - `model` (e.g. `gemini-flash-latest`, `qwen/qwen3-coder:free`)
  - `requests` (total requests that day)
  - `failures` (failed requests that day)
  - `tokens_in`, `tokens_out` (totals that day)
  - `median_ms` (median answer time from `perf.json`)
- Files older than 12 months are left alone (no auto-delete).

### Weekly summary page in the second brain

- **When**: Monday, at the first router start of the week.
- **Where**: `<vault>/wiki/kit/modelli-gratuiti.md` (vault path from rule 11 of `~/.claude/CLAUDE.md`; skipped when it is the placeholder `C:\SecondBrainOssidian`).
- **What it contains**: Markdown with the vault's frontmatter, stating it is written by the router (not by second-brain-librarian). Replaces itself each week.
- **Index**: adds one row in `wiki/indice.md` if missing.
- **Log**: one line in `wiki/log.md`.

### CLI summary

```bash
python user-level-hooks/model_history.py summary [--weeks 4]
```
Prints Markdown with:
- Best models (answered / failed / average time)
- Providers that worked
- Models that stopped working (had requests but 0 in the last week)

### Models page history link

A small link **"history"** next to the **learned** chip on the Models page opens `GET /router/history` (same summary as HTML-safe text).

## When something goes wrong

| What you see | What to do |
|---|---|
| `cod.cmd --plan` still uses free models | Fixed in 1.124.21: update your profile (`update-my-profile.cmd`) |
| Cod: "Connection refused" | The router is not running: run `dream-router.cmd`; the guardian keeps it running from then on. Look at `%USERPROFILE%\.dream-router\guardian.log` and `router.log` |
| A provider is red | Read the reason next to it: a wrong key, a firewall, a model that is not free. Paste a new key or leave it |
| LLM7 shows "no key" | LLM7 now needs a free token from dash.llm7.io: paste it, or leave LLM7 out |
| Every provider paused | Free quotas are used up; they come back by themselves (the page says when) |
| In Plan, then free, a red line says your plan login does not reach the router | Your plan cannot pass through the router on this PC: choose Plan only or Free only |

## Sources
- The kit manual, chapter "Free models and 24/7" (docs/manual/free-models.md), kit v1.124.54. Rebuilt on every kit release: do not edit this page, edit the manual.
