# How to use Free, Paid and Mixed mode

Plain words, for the owner. Everything here is checked against the code.
Anything marked (planned) is not shipped yet.

## The 3 modes

| Mode | Router name | What happens | Cost |
|---|---|---|---|
| Free | `free` | Only free models. Your Claude plan is never used. | 0 plan tokens. Free models are weaker. |
| Paid | `paid` | Only your Claude plan. Never a free model. | Plan tokens only. |
| Mixed (safe) | `safe` | Work goes to free models. Only the safety check uses the plan, while it has credit. | A few plan tokens. |

Two more modes exist. `auto` is the default: plan first, free models at the limit.
`plan` is plan only. Remote Control does not work in Free (see docs/REMOTE-CONTROL.md).

`python tools/mode_cost.py` prints tokens per day, paid vs free, for 7 days. Use `--days N` or `--json`.

## Switch the mode

- Console: page Models, box "How Cod works". It applies to the next Cod session.
- cod.cmd: `cod.cmd --free`, `cod.cmd --plan`, `cod.cmd --safe`. No flag means the saved mode. See docs/START-COD.md. There is no `--paid` flag: use the Models page.
- Local router address: `POST /router/mode` with `{"mode": "..."}`. `GET /router/mode` reads it.

## The budget

The budget governor (tools/budget_governor.py) answers plan or free:
- limit hit and reset not passed: free
- weekly use at 50% or more: free
- otherwise: plan

Mixed mode asks it before using the plan for the safety check. If the plan has no credit, a local check answers.
It can also flip `plan` and `free` in routing.json. It never changes `auto` or `safe`. Starting it by itself on a timer is (planned).

## A free model fails, or a provider answers 429

You do nothing. The router moves to the next provider by itself. A provider at its limit is paused, and the Models page says when it comes back.
If every free model is busy, the router retries every 3 minutes and Cod keeps waiting.
If it never recovers, switch to Paid or auto on the Models page.

## Keys

- Keys live only on your PC, in `%USERPROFILE%\.dream-router\keys.env`.
- Paste them on the Models page and press Save. Press Test keys to check them.
- Never paste a key in chat. Never put it in a file of the project.

## Providers

Order: gemini, zai, nvidia, openrouter, kilo, llm7, groq, ollama, cohere, airforce, orcarouter, cloudflare, deepseek, zenmux.
- airforce: free models only (names ending `:free`). The rest of its catalogue is pay-as-you-go and is never picked.
- orcarouter: only `orcarouter/free`, which routes to zero-price models.
- deepseek and zenmux are not free. They are last, used when the free ones fail.
- Where to get each key: docs/manual/free-models.md.

## Logs and second brain

- `%USERPROFILE%\.dream-router\router.log` and `guardian.log`.
- `%USERPROFILE%\.dream-router\usage.json`: tokens per model.
- `%USERPROFILE%\.dream-router\history\YYYY-MM.jsonl`: one line per model per day.
- Second brain: a weekly page `wiki/kit/modelli-gratuiti.md`, written by the router on Monday.
- `python user-level-hooks/model_history.py summary` prints the best and the broken models.
