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
Background `--bg` #060810, panels `--panel` #0d121c. On the background: text 13.7:1, muted text `--dim` #7189a3 5.5:1 (on a panel 5.2:1), amber 11.3:1, red 6.2:1. Rule: muted text is never below 4.5:1.

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
A coloured side stripe wider than 1px (use a dot, a tint, or an underline for the selected tab). Gradient text. A small label above every heading. Cards inside cards. The big-number-plus-tiny-label template as the page structure.

## Selected tab
An underline of 2px in `--blue` under the active item, not a left stripe.

## Pictures
README, manifesto and release art come from the `dream-illustration` skill: one hand-drawn style, one script, a title line and one closing sentence, no brand art, no private dream. Real result images appear only after the demo is validated.

## Enforcement
`python Claude/hooks/ui_lint.py` checks token drift, animated properties, reduced-motion rules, side stripes and contrast. The `console-ui` skill says to run it before saying a page is done. Current state after 2026-10-29: all pages pass.
