# Game UI style guide — derived from reference examples

Source of these observations: `references/examples/**` — screenshots from published Roblox
experiences, given by the owner purely as **aesthetic reference for the "chunky cartoon game
UI" genre** (stores, shops, missions, rewards). They are NOT UEFN screenshots and contain no
UEFN-native widgets — treat every rule below as a visual/interaction pattern to **reinterpret**
with real UEFN UMG widgets (`canvas_panel`, `stack_box`, `button`, `text_block`, `image`, etc.),
never as something to literally recreate pixel-for-pixel or copy branding/assets from.

## 1. Panel anatomy (common to every example)
- A single centered modal panel, rounded corners (18–28px radius equivalent), thick outer
  stroke (3–6px) in a saturated color that contrasts with the panel's fill.
- A **title banner** across the top, usually a ribbon/ribbon-cutout shape or a solid bar with
  its own rounded top corners, containing the panel's title in a bold, often outlined font.
- A circular or rounded-square **close button** ("X"), red fill, white icon, always top-right,
  slightly overlapping the panel's own border (sits partially outside the panel edge).
- Panel background is a busy, low-contrast pattern (soft dots, diagonal stripes, subtle
  gradient) — never flat/plain, but always kept low-saturation enough that foreground cards
  stay readable on top.

## 2. Section / tab structure
- Content is split into **labeled sub-sections** (e.g. "Server Luck", "Seeds"), each its own
  colored header bar (green, purple, pink…) directly above a grid of item cards — one color per
  section, not per item, so sections stay visually distinct at a glance.
- Where there are top-level categories instead of sections (Store: "Seeds/Gears/Sheckies",
  Premium Shop: "Gamepasses/Boosts/Coins/Bundles", Quests: "All/Daily/Weekly/Limited"), they
  render as a **row of pill-shaped tab buttons**, each with its own solid color, the active tab
  usually the one visually "selected"/highlighted state (brighter, or drawn "pressed in").

## 3. Item card pattern (the most reusable unit)
Every reward/purchase/mission item, regardless of context, follows the same recipe:
1. A rounded-rect card, own background color (often a light neutral or a light tint of the
   section's header color), own border.
2. An icon/image roughly centered or top, large relative to the card (coin stack, gem, chest,
   badge, weapon icon) — always a bright, saturated, slightly-3D icon, never flat/line-art.
3. A short bold label (item name, or a countdown/multiplier like "1x → 2x", "10 mins").
4. A **price/action pill button** anchored at the bottom of the card: rounded, solid saturated
   color (green = buy/claim-available, grey/dark = claimed/disabled, orange/yellow = premium
   currency, purple/pink = gem currency), containing a small currency icon + the number.
- Grids are consistently 2-wide or up-to-4-wide, generous gutters, cards never touch edges.

## 4. Currency & value display
- Every price uses an icon-before-number pattern: `[icon] amount`, never a bare number and
  never a trailing icon.
- Distinct icon+color per currency type observed: gold coin (yellow/orange), gem (green or
  cyan diamond), premium/robux-style token (own icon) — each currency keeps ONE consistent
  icon+color across every screen it appears on, so the player learns to recognize it instantly.
- "Best value" / "Most Popular" callouts use a small ribbon or starburst badge overlaid on the
  card's top corner, in a color that doesn't otherwise appear on that card (usually red/gold),
  never text alone.

## 5. Progress & time elements
- Countdown timers render as bold monospace-feeling digits (`23:51:49`) inside their own small
  pill, always paired with a progress bar directly below/beside when the item is a mission or
  multi-day tracker (thin rounded bar, filled portion in a bright color, unfilled portion a
  muted version of the same hue — never a neutral grey unfilled track).
- Multi-day reward strips (7-day login etc.) render as a single horizontal row of day-cards,
  each showing: day label, reward icon+amount, and a state (claimed = checkmark/dim overlay,
  today = highlighted border/glow, future = normal). The current day is always the most
  visually emphasized card in the row, never just "day N" text.

## 6. Typography & color rules to reuse
- Titles: bold, condensed/rounded display font feel, usually white or cream fill with a dark
  outline/drop-shadow for contrast against any background — never thin/regular weight.
- Body/label text: still bold, smaller, high contrast against its own card background — no
  low-contrast grey-on-grey label text anywhere in these references.
- Section colors are used structurally, not decoratively: once a color is assigned to a
  category (e.g. purple = "Void Server Luck" tier), that color reappears on its price
  button/border, reinforcing the same category — don't assign arbitrary colors card-by-card.

## 7. What NOT to copy directly
- Don't reuse the specific brand icons/art (crowns, specific mascots) — these are the other
  games' IP. Reinterpret the *shape language and layout*, not the artwork itself.
- Don't assume UEFN has ribbon-banner or starburst-badge primitives out of the box — these need
  to be built from `image` widgets with authored/uploaded textures, or approximated with
  rotated rectangles + text; flag this to the owner as an asset-authoring dependency when a
  requested screen needs one and no such texture exists yet in the project.
