# Agent Console: product

## Who it is for
A person with a game in their head, not a programmer. They want to see that the team is working, know the one thing that needs them right now, and trust what they are told. They may be away for hours and come back to a page that tells them where things stand.

## The job
The console answers four questions, in this order:
1. Is the team alive? (the live page)
2. Where are we in the work? (the Docs page: one line of steps, one card for what is next)
3. What needs me? (amber: "your turn", with exact steps and a box to tick)
4. Can I trust it? (the Score page and the delivery gate: what is built, what is proven, what is not)

## Pages
| Page | Question it answers |
|---|---|
| Console | Is the team alive and what is each member doing now? |
| Docs | Where are we from idea to delivery, and what is my turn? |
| Flow | How does the work move between the team members? |
| Skills | What has the kit learned, and what is waiting for my approval? |
| Stats | How much did it cost in time and tokens? |
| Score | How close is the game to the plan, criterion by criterion? |
| News | What changed in the kit? |
| Fab | Is the product package ready to publish? |

## Principles
- **Honest before pretty.** "Built" and "proven" are different and always shown apart. Nothing is green because it was written; it is green because it was played or checked.
- **Your turn is a first-class state.** The page never shows "all green" when a step belongs to the owner. It says "your turn", with the exact steps and what Claude will check afterwards.
- **Only the owner ticks.** The page never ticks a box for Claude and never publishes anything.
- **Plain words.** Business language first. Tool names, ids and file paths only after "Technical:".
- **Alive, almost free.** Motion shows that something is running, costs almost nothing, and stops when nothing runs. It respects reduced motion.
- **Nothing hidden.** Empty states say what to do next in one sentence, never an empty chart.

## What the owner sees first
A summary line (where we are, what is built, what waits for the playtest, open bugs, and "Your turn" when only the owner can move on), then the next action in a fixed order: Found, Advice, Then, and last the Question for you. The Score page ends in one number, Readiness, where only proven work counts.

## It is theirs
The owner picks the Aura (colour), lets it drift, and decides whether the movement always shows. Nothing about the colour touches the meaning of green, amber and red.

## What it is not
Not a game editor, not a place to change settings, not a dashboard of vanity numbers. It reads the project's own documents and logs; it never edits the game.

## How we know it works
- `python Claude/hooks/ui_lint.py` prints nothing but `ui_lint: ok`.
- `python tool/shoot_consoles.py` opens every page in a real browser with no script error and saves screenshots.
- A new owner finds their next action in under 10 seconds (checked by watching, not by asking).
