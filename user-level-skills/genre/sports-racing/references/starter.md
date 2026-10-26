# Starter - sports-racing (generated from the owner's approved patterns; do not edit by hand)

Use when the owner starts a NEW project of this genre. Each section lists what the owner's maps taught (proven = rule, confirmed = default, hypothesis = suggestion, contested = ask) and the open questions. Nothing here comes from general knowledge: an empty section means nothing was learned yet, so ask the owner and write a DESIGN-<system>.md for it. No code before the owner approves the design.

## Map anatomy: what a map of this genre is made of

Learned from 1 analysed map(s) of the owner. Numbers are what was OBSERVED in each map (labels, not names): a value seen in several maps is a safe default, one seen in a single map is an example to adapt. To build a map of this genre, start here.

### Concept
- Map 1 (type: checkpoint-race): Up to 4 players, one truck each, race a single lap through 20 numbered checkpoints; best of 3 rounds (MostRoundWins), 300 s per round. Native devices run the whole race; Verse only adds meta layers (playtime XP, coin XP, HUD widgets).

### Layout (what is placed in the level)
- **Racing Checkpoints** (1 of 1 map(s)): Map 1: 20, numbered 1..20 contiguous phase Gameplay Only, all vehicles allowed; cp1 at (-43.9k,-49.2k,-0.5k), cp15 highest z 16.2k, cp20 at (-6.9k,-22.5k,2.1k)
- **Pre-lobby Player Spawners** (1 of 1 map(s)): Map 1: 4 priorityGroup 2, useAsIslandStart true, hidden, unwired, near (-23k,-28k)
- **Race-start Player Spawners** (1 of 1 map(s)): Map 1: 4 priorityGroup 1, TeamIndex 1..4, near (-37k,-43k), each assigns driver to one truck
- **Basic Truck Spawners** (1 of 1 map(s)): Map 1: 4 respawn on, max health 800, off-road tires, fuel off
- **Gold Coins (Collectible Object V2)** (1 of 1 map(s)): Map 1: 66 score 0; XP via Verse tag collector
- **Explosive barrels / pinball flippers / trick tiles** (1 of 1 map(s)): Map 1: 41 / 5 / 5 track hazards triggered by zone plates and perception triggers
- **Support cluster** (1 of 1 map(s)): Map 1: 1 Playtime manager + 7 Accolades around (10.3k..10.7k,-20.5k..-20.1k,z 12.5k), far off the track and ~10k above it
- **Accolades inside play area** (1 of 1 map(s)): Map 1: 4 3 near race-start spawners (-35.7k,-42.5k..-42.9k) and 1 near cp20 finish (-9k,-24.3k)

### Game loop of one match
- Map 1: Pre-lobby wait: autoStart 20 s (force start 5 s after max players 4) -> gameStartCountdown 10 s -> Timed Objective 1 'Race is starting in' 10 s: on complete disables 4 start-gate barriers, starts Race Manager and bonus Timer -> Race: 1 lap, 20 checkpoints; each checkpoint -> Score Manager +1 and tracker progress -> Timed Objective 3 'You're the winner' 10 s on race completed -> 3 rounds, 300 s limit each, winner by most round wins

### Devices to place and what each one does
- **Race Manager V2** (1 of 1 map(s)): Map 1: x1; laps, circuit, HUD nav arrow, best lap; settings: laps 1, start on game start false; wiring: enabled by Timed Objective 1
- **Racing Checkpoint V2** (1 of 1 map(s)): Map 1: x20; route; settings: Gameplay Only; wiring: OnCheckpointCompleted -> Score Manager.Activate + Tracker increment
- **Experience Settings** (1 of 1 map(s)): Map 1: x1; island config; settings: maxPlayers 4, timeLimit 300, totalRounds 3, autoStart 20, countdown 10, MostRoundWins; wiring: n/a
- **Tracker** (1 of 1 map(s)): Map 1: x4; bonus objectives (checkpoints 20, playtime, kills); settings: targets 20/10/10/30; wiring: fed by checkpoints, objectives, creature manager
- **Accolades V2** (1 of 1 map(s)): Map 1: x11; XP awards: 4 near race start/finish, 7 grouped with Playtime manager off-track; settings: xPAward is a relative size, not a number: Small x2, Medium x4, Large x4, VeryLarge x1; limitAwardCount false, awardCount 1; wiring: awarded by Verse (playtime tiers, coin collector) or native events
- **Matchmaking Portal V2** (1 of 1 map(s)): Map 1: x7; post-race / lobby portals; settings: unread; wiring: unread

### Verse components to write
- **Playtime_manager** (1 of 1 map(s)): Map 1: per-player playtime tracker, automatic or legacy reward mode, WBP_Playtime HUD; api: @editable 6 accolades_device, UseAutomaticRewards, EnableWebUI; subscribes PlayerAdded/Removed; read live: useAutomaticRewards true, rewardTiers empty, 6 accolade refs read back as paths inside the device (assignment unconfirmed)
- **tag_collector_device** (1 of 1 map(s)): Map 1: tag-driven collectible handler: XP accolade + trigger + respawn; api: @editable_container CollectibleConfigs (tag, trigger, XpAccolade, timer, RespawnDelay)
- **like_follow_ui_manager** (1 of 1 map(s)): Map 1: Like/Follow world and personal widgets; api: 2 trigger_device refs
- **island_map_code** (1 of 1 map(s)): Map 1: HUD bar with map name/code, 10 styles; api: @editable name/code/style/size/offset

### Game logic rules
- **player exits truck** (1 of 1 map(s)): Map 1: then its Trigger fires and its own truck Assigns Driver again [1 trigger per truck, timesCanTrigger 1 reset by Exit event]
- **playtime reaches 5/10/15/30/45/60 min of the player's session** (1 of 1 map(s)): Map 1: then Accolade.Award(player), repeating every 60 min [tiers mod 6, cycle 3600 s]
- **coin collected** (1 of 1 map(s)): Map 1: then Accolade.Award(collecting agent), coin respawns after delay or external timer [RespawnDelay default 5 s]

### Scoring and rewards
- **+1 Score Manager per checkpoint** (1 of 1 map(s)): present
- **XP accolades per playtime tier and per coin (amounts set on Accolade devices)** (1 of 1 map(s)): present

### Build order
- Map 1:
  1. 1. Set Experience Settings (4 players, 3 rounds, 300 s, autoStart 20, countdown 10)
  2. 2. Place 4 pre-lobby + 4 race-start Player Spawners (TeamIndex 1..4) and 4 truck spawners; wire OnPlayerSpawned -> Assigns Driver
  3. 3. Place 20 checkpoints in order and a Race Manager
  4. 4. Add Timed Objectives 1-3, start-gate barriers, bonus Timer, Score Manager, Trackers, HUD messages
  5. 5. Add hazards (barrels, flippers, trick tiles) and coins
  6. 6. Place Verse devices and assign their accolade/trigger references in Details

### Not known yet (not read or not decided)
- Map 1: whether the 6 playtime accolade @editable references point to placed Accolade devices (Details read returns paths inside the Verse device itself, which may be unassigned defaults)

## 1. Core loop

Questions: What is one round/run/match; how does it start, end (win, loss, timeout) and restart? What is shared between players?

_Nothing learned yet for this section._

## 2. Architecture

Questions: Which Verse files/classes own game state, transitions, player state, spawning, rewards? One owner per transition.

- [hypothesis] *: when When a Verse device keeps per-player state (maps, widgets, trackers) and players can leave and rejoin -> Prune every per-player map on the player-removed event and give each tracker coroutine a session id that it re-checks each tick, so a quick rejoin cannot leave two trackers for the same player (1 map(s))

## 3. Devices in the level

Questions: Which spawners, trackers, granters, barriers and UI devices exist; which are global and which per player; who wires them? (read them via the MCP when live)

- [hypothesis] *: when When a racing map has a pregame lobby or pre-race waiting area, and its Player Spawner devices are reviewed or audited -> Treat an unwired hidden island-start spawner in the higher priority group as the pre-lobby spawner, not a leftover. Flag only unwired spawners on the default priority group or not island starts (1 map(s))
- [hypothesis] *: when When reviewing a placed Verse device whose @editable device references read back as paths inside the Verse device itself -> Treat those references as unassigned defaults, not as placed devices: check the Details panel assignments before trusting that accolades, triggers or timers are wired (1 map(s))
- [hypothesis] checkpoint-race: when When a racing map gives each player a vehicle and players can leave it -> Give each vehicle its own Player Spawner with a team index and a vehicle spawner that assigns the driver on spawn, plus a per-vehicle trigger fired by the exit event that assigns the driver again (1 map(s))

## 4. Progression

Questions: What persists between rounds/runs and what resets; unlocks, currencies, difficulty or tier scaling. Numbers only from the owner or his maps' data.

- [hypothesis] *: when When a map pays timed playtime rewards per player (e.g. 5/10/15/30/45/60 min) and the schedule repeats -> Keep one forward-only award counter per player session (tier = index mod tiers, cycle = index div tiers) and pay in a catch-up loop, not per-tier timers or flags (1 map(s))
- [hypothesis] checkpoint-race: when When setting XP on Accolade devices and the real amount per award is not visible in the device -> Treat an Accolade's XP as a relative size (Small to VeryLarge), not a number; map playtime or collectible tiers to rising sizes and compare by size, never invent an XP figure (1 map(s))

## 5. Strategies around death, defeat and progress

Questions: Respawn/retry rules, paid retry or continue, rewards, boosts. Design strategies, learned as patterns with a variant.

_Nothing learned yet for this section._

## 6. Persistence

Questions: What is stored per player; what happens when data is not loaded yet or the player left.

_Nothing learned yet for this section._

## 7. Performance

Questions: Item/NPC pools, listeners, per-frame work.

_Nothing learned yet for this section._

## 8. Launch checklist

Questions: First 10 minutes of a new player, a full round, a death/defeat, a restart, two players at once, a player leaving mid-round.

- [hypothesis] *: when When a racing map has an auto-start timer plus a game-start countdown plus timed-objective countdowns before the first checkpoint -> Add the stacked waits and cut them to roughly 30 s total before the first checkpoint (for example auto start 20 s, countdown 10 s), then re-check bounce rate (1 map(s))
- [hypothesis] checkpoint-race: when When a racing map has an auto-start timer plus a game-start countdown plus timed-objective countdowns before the first checkpoint -> Add the stacked waits and cut them to roughly 30 s total before the first checkpoint (for example auto start 20 s, countdown 10 s), then re-check bounce rate (1 map(s))

## Not classified yet

Run `skills_lib.py section sports-racing <pattern id> <section id>` for each (ids: architecture, death-strategies, devices, launch-checklist, performance, persistence, progression, run-loop).

- [hypothesis] checkpoint-race: when When a racing map is built for up to 4 players who race one lap over about 20 numbered checkpoints -> Let native devices run the race (Race Manager, numbered Racing Checkpoints, Timed Objectives for start and win, Score Manager) and use Verse only for meta layers such as playtime XP and HUD (1 map(s))
- [hypothesis] checkpoint-race: when When a racing map plays several short rounds with a winner by round wins -> Use the Experience Settings rounds (about 3 rounds, about 300 s each, most round wins) with a short timed objective for the winner, instead of custom round logic (1 map(s))
- [hypothesis] checkpoint-race: when When a racing map has numbered checkpoints and bonus objectives such as total checkpoints or playtime -> Wire each checkpoint-completed event to one Score Manager activation and one Tracker increment, so score and objectives are fed by the same event (1 map(s))
