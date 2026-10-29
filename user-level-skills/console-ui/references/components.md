# Console components (copy, do not reinvent)

Every block uses only the tokens in `tokens.css`. Colour carries meaning: green done, amber needs you, red blocked, cyan live, grey not started.

## Page shell
```html
<body><main class="wrap"> header (title + one-line status) | next action card | content cards | footer hint </main></body>
```
`body{margin:0;background:var(--bg);color:var(--text);font:13px/1.5 var(--sans)}` `.wrap{max-width:1180px;margin:0 auto;padding:16px}` Text blocks max 65ch.

## Card
`.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px}` title = one line, 12px uppercase dim; value = 22px; one sentence under it.

## Status dot (the heartbeat of every row)
`.jd{width:7px;height:7px;border-radius:50%}` done=`--ok`, now=`--warn` + ring pulse (`::after` scaled, opacity out), todo=1px `--todo` outline, blocked=`--bad`.

## Pulse rules (alive, almost free)
- Animate ONLY `transform` and `opacity`. A glow is a static `box-shadow` on a `::after` layer whose opacity breathes.
- Live: 1.3 s ring. Waiting: 3.4 s slow breath. Nothing pulses when idle or done.
- Always add `@media (prefers-reduced-motion:reduce){...animation:none!important}`.

## Numbers
Counters and clocks: `font-variant-numeric:tabular-nums`. Never an empty chart: show a sentence ("Nothing yet. Start with /spec").

## Step bar
Numbers on top, one short label below, no scroll bar, current step lit, done green, blocked red.

## Tick row (only the owner ticks)
`<label class="tick"><input type="checkbox"> plain-words sentence</label>`, posts to the gate; the page never ticks for Claude.

## Table
Sticky head, 12px, zebra with `--panel2`, status as dot + word, never colour alone.

## Words
Business language, no tool names, no ids in the first line. Technical detail only after "Technical:".

## Type
`--sans` for every word and number; `--mono` only for code, file names and ids (`code`, `pre`, `kbd`, class `mono`). Monospace is never a costume.

## Neon (three tones, static)
The look of the kit is dark with neon. Three tones, always the same: `--neon-hi` for the ONE card the page is about (next action, summary line, release, flow board, score tiles), `--neon-mid` for every ordinary panel, `--neon-lo` for nested or secondary pieces. A glow is a static `box-shadow` (outer glow + a soft inset); only a `::after` layer's opacity may breathe. Copy the block that starts with `console-ui: neon in three tones` from any page, unchanged. Neon never replaces meaning: green/amber/red/cyan/grey still say status.

## Plain-case labels
No shouting: labels, table heads and section titles are sentence case (`text-transform:none`, first letter capital). Copy the block `plain-case labels`.

## Header
Logo, then the plain title, the version, the menu, one sentence under it. No `>` before the title, no blinking `_`, no `#` before the sentence.

## Summary line (Console page)
One line in a hi panel: `Where we are: N of M tasks done · Claude is building N · N built, waiting for your playtest · N open bugs.` and, when only the owner can move on, the amber sentence `Your turn: ...`. Read from the project's ROADMAP and BUGS, never typed.

## Next action card (Docs page)
Fixed order, last line is the question: **Found** (where we are) | **Advice** (what Claude does) | **Then** | **Question for you** (full width, amber tint). A task that is built and only waits for the owner's playtest is never shown as "Claude is building": it is "Your turn".

## Island strip
`Island: <project> 0000-0000-0000 not published yet` + genre chip. The placeholder keeps the layout the same before and after publishing.

## Aura (theme colour)
Six accent themes, picked with small cubes under the title (`console-ui: theme` block): the accent is `--acc` / `--acc2` (r,g,b) and `--acc-h` (hue of the pixel wave). Use `rgba(var(--acc,75,216,255),.34)` for glows, never a literal cyan. Status colours (green, amber, red) are never themed. A `Motion` switch sits next to the cubes; reduced-motion rules in shared blocks are written `html:not(.motion-full) selector`.

## Bars and rings
A bar fill with a `%` width eases to its new value (first time from zero) and carries a sheen (`console-ui: motion of bars and rings`). A ring is a `circle` with `stroke-dashoffset`: it transitions by itself. A percentage figure in `#...Pct` or `.pct-n` counts up.

Aura Drift (`data-aura-auto` button): a timer fades `--acc`, `--acc2` and `--acc-h` between two themes (1.5 to 8 s), then rests (0.8 to 15 s); a click on a cube stops it. Updates only while the page is visible and only during a fade.
