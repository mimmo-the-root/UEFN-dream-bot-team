# Agent Console: design

One source of truth: `user-level-skills/console-ui/references/tokens.css` (tokens) and `components.md` (pieces). A page is built from those, never from scratch. A page that cannot be built from them means a piece is missing: add the piece first.

## Colour is meaning
| Colour | Token | Meaning |
|---|---|---|
| Green | `--ok` | done, proven |
| Amber | `--warn` | needs the owner |
| Red | `--bad` | blocked or broken |
| Cyan | `--live` | running now |
| Grey | `--todo` | not started |
Never colour alone: always a dot shape or a word as well (daltonic readers).

## Surfaces and contrast (measured)
Default palette (the owner's choice, 2026-10-29): deep indigo with a violet accent. Background `--bg` #0c0820, panels `--panel` #16123a and `--panel2` #110d2c, lines `--line` #2b2468, text `--text` #e8e2ff, muted text `--dim` #9a90d4, `--blue` #8b7cf6. On the panel: text 14.2:1, muted text 6.2:1, amber 10.1:1, red 5.5:1. Rule: muted text is never below 4.5:1. Cyan stays as the "live" status colour and as one of the six Aura themes; the default Aura is Violet.

## Type
`--sans` for every word and number. `--mono` only for code, file names and ids. Counters and clocks use tabular numbers so columns line up. Text lines are at most 65 characters wide.

## Motion
- Only `transform` and `opacity` animate. A glow is a static shadow on a `::after` layer whose opacity breathes; a moving stripe is a wider layer that slides.
- Live: ring about 1.3 s. Waiting: slow breath about 3.4 s. Idle or done: no motion.
- Every animation has a `prefers-reduced-motion` rule that turns it off.

## Browser surfaces
Visible keyboard focus on every control (cyan outline), themed text selection, scrollbars and form controls follow the dark theme.

## Neon is the identity (owner's decision, 2026-10-29)
The dark surface with neon colours and glows is the look of the kit and stays. Three tones, the same on every page: `--neon-hi` (bright cyan) for the one card the page is about, `--neon-mid` for ordinary panels, `--neon-lo` (blue) for nested or secondary pieces. Glows are static shadows; only the opacity of a glow layer may breathe. Neon never replaces meaning: the colour table above still decides what a colour says.

## Aura, Drift and Motion
Six accent themes (Cyan, Blue, Violet, Magenta, Teal, Ice), picked with small cubes under the title that pulse one after the other, each at its own speed. The accent is a set of variables (`--acc`, `--acc2`, `--acc-h`); glows and the pixel wave read them. Drift fades the accent by itself between two themes with irregular fades and rests. Motion shows the movement even when the system asks to reduce it. Status colours are never themed.

## Life on the page
Panels breathe at their own rhythm; a light crosses the top; live dots pulse; a changing number ticks; a pixel wave passes over a panel whose data changes (fast or slow, random direction, one per panel every 8 s). Bars ease to their new width (from zero the first time) with a sheen, rings fill with a soft curve, percentages count up. Everything moves only transform and opacity (width and dash offset ease only when a value changes). Under reduced motion only brightness changes remain, unless Motion is on.

## Words on the page
Labels, table heads and section titles are in sentence case. The header is the plain title (no `>` prompt, no blinking `_`, no `#` before the subtitle). The Console page opens with one summary line (where we are, what is your turn). The Docs next action is always Found, Advice, Then, and last the Question for you.

## Never
A coloured side stripe wider than 1px (use a dot, a tint, or an underline for the selected tab). Gradient text, except the page title. A small label above every heading. Cards inside cards. The big-number-plus-tiny-label template as the page structure.

## Declared exceptions (the owner's brief wins)
Generic design checklists refuse some things by default. These are chosen on purpose here, each with its limit: static glow (a shadow whose opacity may breathe, never a moving blur), gradient only on the page title, progress rings and bars only for real progress, big numbers only for real totals with a label that says what they count, no animated blur or backdrop filter.

## Responsive
Structural, not fluid type. Every page has `<meta name="viewport">`. Under 900px the header wraps and the tab bar scrolls inside itself; under 640px tables scroll inside their own box and side margins shrink; on touch screens tabs and buttons are at least 40px high and the Aura cubes 24px. The page itself never scrolls sideways at 390px. Checked at 390, 820 and 1280px.

## Modes per page
Console, Stats, Docs, Flow, Skills, News, Score, Fab are Operate pages: the person is in a task, so familiarity and scanning come before expression and brand lives in details. The manual is Read: comprehension first. The README, manifesto and release art are Persuade: they may use more imagery and ambition.

## Selected tab and counters
The active tab is a filled pill with a gradient mixed from the accent (white text, readable in every Aura theme), not a left stripe. Tabs may carry a small amber counter with a real number (Skills: waiting for your yes; Docs: tasks that wait for you), hidden at zero.

## Glass panels
Panels are glass without blur: the panel colour, a faint accent tint, a soft top highlight, 16px corners, and a fixed indigo glow behind the page. Nothing is animated and no `backdrop-filter` is used, so the console can stay open all day.

## Charts
A daily chart is one thick bar per day with a gradient from the accent and the best day lighter; a missing day is a dot. Change chips (`+26.3%`) show the move since the previous day with an arrow as well as a colour.

## Pictures
README, manifesto and release art come from the `dream-illustration` skill: one hand-drawn style, one script, a title line and one closing sentence, no brand art, no private dream. Real result images appear only after the demo is validated.

## Enforcement
`python Claude/hooks/ui_lint.py` checks token drift, animated properties, reduced-motion rules, side stripes and contrast. The `console-ui` skill says to run it before saying a page is done. Current state after 2026-10-29: all pages pass.
