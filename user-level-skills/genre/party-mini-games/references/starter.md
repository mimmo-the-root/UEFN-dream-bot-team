# Starter - party-mini-games (generated from the owner's approved patterns; do not edit by hand)

Use when the owner starts a NEW project of this genre. Each section lists what the owner's maps taught (proven = rule, confirmed = default, hypothesis = suggestion, contested = ask) and the open questions. Nothing here comes from general knowledge: an empty section means nothing was learned yet, so ask the owner and write a DESIGN-<system>.md for it. No code before the owner approves the design.

## Map anatomy: what a map of this genre is made of

Learned from 1 analysed map(s) of the owner. Numbers are what was OBSERVED in each map (labels, not names): a value seen in several maps is a safe default, one seen in a single map is an example to adapt. To build a map of this genre, start here.

### Concept
- Map 1 (type: pillars): Free-for-all last-player-standing on floating stone pillars: 12 players spawn on 12 peripheral pillars around a central one, a storm shrinks toward the centre and item granters feed weapons until one survivor remains; rounds loop forever.

### Layout (what is placed in the level)
- **Peripheral pillars with a tile on top** (1 of 1 map(s)): Map 1: 12 ring radius ~4096uu (centres at 30 degree steps, e.g. (4096,0), (3584,2048)); each carries a 512x512uu PillarTile floor at z 14968..14984 and one arena spawner
- **Central platform** (1 of 1 map(s)): Map 1: 1 pillar + 9 PillarTile 3x3 grid of 512uu tiles around the origin (x,y -768..768, same z), final showdown
- **Support stands (DemoDisplay)** (1 of 1 map(s)): Map 1: 2 outside play area at x~18700-19200, hold granters/timer/accolades/elimination manager

### Game loop of one match
- Map 1: PreLobby: 12 pre-lobby spawners (island start, priority 1); wait for MinPlayersToStart (1) players, polling every 0.5s -> Countdown 15s: HUD 'round starts in N s', inventories cleared, cancelled if players drop below the minimum -> InProgress: participants (max = 12 arena spawners) teleported with TeleportTo to disabled arena spawners, storm generated, item granter system started (cycle 5s, pool-first), survival timer 60s, HUD 'next item in N s - players left M' every -> EndGame: storm destroyed, granters stopped, outcome message 10s (Victory/Defeat/Draw), survivors inventory cleared and teleported to pre-lobby, pause until 12s total -> Back to PreLobby; 1s guard loop returns any active non-participant found in the arena (X < 15000) to the pre-lobby

### Devices to place and what each one does
- **Item Remover** (2 of 1 map(s)): Map 1: x1; clears player inventory at countdown, before arena teleport and on return to pre-lobby; settings: Affected Items All Items, Apply To Player (from code comment); wiring: Remove(Player) from the manager; Map 1: x1; clears the full inventory of a player on demand; settings: Affected Items = All Items, Apply To = Player; wiring: @editable on the manager, Remove(Player) called from Verse at countdown start, before the arena teleport and on survivors returning to pre-lobby
- **Player Spawner** (1 of 1 map(s)): Map 1: x24; 12 pre-lobby spawn/respawn points + 12 arena teleport positions; settings: 24 spawners: 12 pre-lobby x~22300-23000 z~19460 priority 1, island start true, always enabled; 12 arena on pillar tops ring r~6000uu z 14954..15278 priority 2, island start false, Disable() from Verse (position only); wiring: enabled/disabled by the Verse manager, SpawnedEvent subscribed
- **Basic Storm Controller** (1 of 1 map(s)): Map 1: x3; phases A/B/C, radii 750000/450000/200000uu; settings: not read; wiring: Verse manager GenerateStorm/DestroyStorm
- **Advanced Storm Beacon** (1 of 1 map(s)): Map 1: x1; storm centre at origin, z~15000; settings: not read; wiring: none in editor
- **Item Granter V2** (1 of 1 map(s)): Map 1: x6; Firearms/Chaos/Consumables/Mobility/Materials pools + legacy cycle, filled by rarity (weapons Mythic+Exotic only); settings: item lists 162/24/113/24/3; legacy cycle granter disabled; driven by the Verse item_granter_system; wiring: item_granter_system Enable/Disable/GrantItemIndex
- **Elimination Manager V3** (1 of 1 map(s)): Map 1: x1; reports the eliminator for kill XP; settings: default; wiring: EliminationEvent subscribed by the manager
- **Accolades V2** (1 of 1 map(s)): Map 1: x2; Accolade_KillXP and Accolade_SurvivalXP; settings: not read; wiring: Award called from Verse
- **Timer V2** (1 of 1 map(s)): Map 1: x1; 60s survival XP tick; settings: duration 60, count down, start at game start false; wiring: SuccessEvent subscribed by the manager
- **Island Settings (Experience Settings V2)** (1 of 1 map(s)): Map 1: x1; free-for-all match frame; settings: numTeams 0, totalRounds 1, MostRoundWins, round win by Eliminations, roundTimeLimit 120s, timeLimit 300s, autoStart 10s, gameStartCountdown 5s, respawnTime 1s, health 100, shields 100, 5 item slots, infinite ammo off, fly off, persistence N; wiring: none
- **HUD Message** (1 of 1 map(s)): Map 1: x1; countdown, status and outcome messages; settings: not read; wiring: Show(Player, message) from the manager
- **Damage Volume** (1 of 1 map(s)): Map 1: x1; cleans player-built structures in the pillar area between rounds; settings: box ~10920uu wide in x/y, z 16337..18804 over the pillar area (other settings not read); wiring: @editable on the manager; Enable after survivors return, Disable 5s before the countdown ends
- **Barrier (hollow box)** (1 of 1 map(s)): Map 1: x12; one per peripheral pillar with an arena spawner, contains the player on the pillar top right after the teleport so they do not fall; settings: hollow box about 570uu footprint, 300-430uu high on 512uu tiles; Enable/Disable from Verse only; wiring: PillarBarriers array on the game manager: ON at T-3s of Countdown, OFF 2s after the arena teleport (all together), OFF on cancelled countdown, WaitForPlayers, EndGame and init

### Verse components to write
- **pillar_game_manager (PillarGameManager.verse, v6)** (1 of 1 map(s)): Map 1: server-authoritative state machine game_phase PreLobby/Countdown/InProgress/EndGame, round_outcome None/Victory/Defeat/Draw, infinite loop of RunRound; v5 adds ItemRemover inventory clearing, 10s winner message before return, exclusive Aren; api: @editable: PreLobbySpawner01..12, ArenaSpawner01..12 (single fields), StormController, GranterSystem, ItemRemover, EliminationManager, AccoladeKillXP, AccoladeSurvivalXP, SurvivalTimer, RoundDurationSeconds 600, EndGameResetDelaySeconds 12,
- **item_granter_system (ItemGranterSystem.verse, v6)** (1 of 1 map(s)): Map 1: cyclic drop: every CycleSeconds each living player gets a different item; first cycle weapons only, weighted pool draw 40/30/15/15 with per-player pool anti-streak, then unused valid index != last; Materials pool separate on each eliminatio; api: @editable: PoolFirearms/Chaos/Consumables/Mobility/Materials (item_granter_device), CycleSeconds 5, XxxItemCount overrides 0 (auto-probe by GetItemGrantCountAtIndex up to 512), XxxWeight (0.40/0.15/0.30/0.15 for Firearms/Chaos/Consumables/M
- **VerseUIKit (VerseUIKit/*, 20 files, third-party UI kit)** (1 of 1 map(s)): Map 1: reusable UMG widget kit: ui_helper_function_library tracks per-player widgets, input mappings and listeners and clears them with ClearAllForPlayer; ui_feedback_toast shows one toast per player with id-guarded timed slide-in/out; composite e; api: ui_helper_function_library: AddWidgetToPlayer, SubscribeToEvent, AddInputMappingToPlayer, FocusWidgetForPlayer, ClearAllForPlayer, WatchInputMethodForPlayer; ui_feedback_toast.ShowToast(Player, toast_settings); ui_showcase_device @editable 
- **legacy side modules (Tag_collector_device, big_number, coin_display_manager, island_map_code/MapCode, party_up_manager, Playtime_manager)** (1 of 1 map(s)): Map 1: reusable independent devices read in full 2026-10-24: tag-driven collectible respawn, K/M/B number formatter, per-player coin HUD, map code HUD bar (10 styles), party-size gold bonus via GetLocalParty, real-clock playtime checkpoints with p; api: all @editable-driven creative_devices with DebugLoggingEnabled logger; per-player state maps pruned on PlayerRemoved

### Game logic rules
- **an elimination is reported by the Elimination Manager during InProgress** (1 of 1 map(s)): Map 1: then award the kill Accolade to the eliminator [1 kill = 1 award]
- **the survival timer completes during InProgress** (1 of 1 map(s)): Map 1: then award the survival Accolade to every living player [interval 60s]
- **island starts** (1 of 1 map(s)): Map 1: then island-level round/time limits are Island Settings values, independent of the Verse RoundDurationSeconds [island roundTimeLimit 120s / timeLimit 300s vs Verse 600s: mismatch]
- **countdown reaches zero with more players than arena spawners** (1 of 1 map(s)): Map 1: then only the first 12 are teleported to arena; the rest stay in pre-lobby for the next round [max 12]
- **alive players reach 1 (started with >=2) or the only player dies (started with 1)** (1 of 1 map(s)): Map 1: then round ends; winner message for 10s then return to pre-lobby [or 600s timeout = Draw]
- **a round ends** (1 of 1 map(s)): Map 1: then winner/defeat message stays 10s with survivors still in the arena, then survivors are cleared and returned to pre-lobby, cleanup volume enabled, remaining time padded to a 12s total [WinnerMessageSeconds 10, EndGameResetDelaySeconds 12, cleanup disable 5s before start]
- **participants are assigned to arena positions** (1 of 1 map(s)): Map 1: then each slot is used once; a slot that is occupied or whose teleport fails is flagged blocked and the next free slot is tried; leftover players stay in pre-lobby [12 arena slots]
- **every 5s during InProgress** (1 of 1 map(s)): Map 1: then each living player gets one item: pool drawn by weight with anti-streak (never the same pool twice in a row), then an unused valid index different from the player's last; first cycle of a round draws only from Firearms/Chaos so everyone get [weights Firearms 40 / Consumables 30 / Chaos 15 / Mobility 15; lists probed up to 512 indices, stop after 16 consecutive empty; code Pool*1000+Index; materials on kill only (itemCount 20); effective weights compensate the anti-streak exclus]
- **Countdown reaches 3 s before the arena teleport** (1 of 1 map(s)): Map 1: then enable all pillar barriers; disable 2 s after the teleport (a run id invalidates a late disable) [3 s before, 2 s after]

### Scoring and rewards
- **kill XP via Elimination Manager + Accolade** (1 of 1 map(s)): present
- **survival XP every 60s alive via Timer + Accolade** (1 of 1 map(s)): present
- **XP values not read from the Accolade devices** (1 of 1 map(s)): present

### Build order
- Map 1:
  1. 1. build 12 pillars around a central one at equal radius
  2. 2. put a Player Spawner on each pillar
  3. 3. place storm controllers (3 phases) and a beacon at the centre
  4. 4. place item granters, timer, elimination manager and accolades on a stand outside the play area
  5. 5. write and place the Verse game manager and wire its @editable references
  6. 6. set Island Settings (free-for-all, round time, respawn)
  7. 7. place a hollow-box Barrier on each pillar top that has a spawner, assign them to the manager's barrier array in Details (the MCP cannot bind device references)

### Not known yet (not read or not decided)
- Map 1: storm controller and item granter settings
- Map 1: accolade XP values
- Map 1: Island timeLimit 300s / roundTimeLimit 120s disagree with manager RoundDurationSeconds 600s
- Map 1: max players as a separate island field (12 spawners imply 12)
- Map 1: storm controller GetDeviceProperties (3 phases) not re-read
- Map 1: arena spawner and pillar positions re-read against the new 4096uu ring not repeated for spawners (only PillarTile read this pass)
- Map 1: whether the old HudMessage_RoundMessages device is still placed (unused by v6 code)
- Map 1: TeleportTo error colliding seen in logs 2026-10-24 00:11, cause not confirmed (barriers suspected)

## 1. Core loop

Questions: What is one round/run/match; how does it start, end (win, loss, timeout) and restart? What is shared between players?

- [hypothesis] pillars: when a round loops indefinitely with distinct phases -> model the round as an explicit enum state machine (Waiting, InProgress, EndGame) driven by a single server-side loop that resets state and re-enables spawners each cycle (1 map(s))
- [hypothesis] pillars: when a round must end on last survivor or on a time limit -> race a WaitForSingleSurvivor loop against Sleep(RoundDuration) so whichever finishes first ends the round; at timeout with more than one survivor declare a draw (1 map(s))
- [hypothesis] pillars: when a round-based map with infinite rounds -> drive Waiting, InProgress and EndGame from one Verse manager that enables/disables spawners, storm and item granters per phase and resets after a delay (1 map(s))
- [hypothesis] pillars: when players wait between rounds while arena spawners are only positions -> spawn players in a pre-lobby spawner group; teleport participants to disabled arena spawners at start; a 1s guard returns stray arena players to the pre-lobby (1 map(s))
- [hypothesis] pillars: when a round needs a visible wait before the arena opens -> run a countdown phase between pre-lobby and arena, cancel it if players fall under the minimum, and show the remaining seconds on the HUD (1 map(s))
- [hypothesis] pillars: when items from one round must not leak into the next or into the arena start -> call an Item Remover (all items, apply to player) from Verse on participants at countdown start, right before the arena teleport, and on survivors returning to the pre-lobby (1 map(s))
- [hypothesis] pillars: when players build structures during a round and the area must be clean for the next one -> enable a damage volume over the build area only while nobody is in the arena (after survivors return, disable a few seconds before the next start) (1 map(s))
- [hypothesis] pillars: when the first drop of a round decides whether players can fight at all -> limit the first cycle to weapon pools, then draw pools by weight (about 40/30/15/15) with a per-player anti-streak never repeating a pool (1 map(s))

## 2. Architecture

Questions: Which Verse files/classes own game state, transitions, player state, spawning, rewards? One owner per transition.

- [hypothesis] pillars: when a manager must track players across rounds with events that fire per character -> subscribe to events once in OnBegin (spawners, elimination manager, playspace join/leave) and validate the alive list with a periodic IsActive sweep instead of subscribing per character (1 map(s))
- [hypothesis] pillars: when each player needs a personal HUD widget with per-player counters -> keep a map agent->widget created on join (and lazily in a guard loop), update fields server-side, and rebuild the maps without the agent in PlayerRemovedEvent (1 map(s))
- [hypothesis] pillars: when a UI screen needs widgets, input mappings and event listeners that must all be removed when the screen closes -> route every AddWidget, input mapping and event subscription through one helper that records them per player, and clean up with a single ClearAllForPlayer on every exit path (1 map(s))
- [hypothesis] pillars: when a UMG widget animation or state must be driven from Verse -> expose a logic field on the widget, set it true, Sleep ~0.1s so the widget notices, then set it false; build a fresh widget instance each time the screen opens (1 map(s))
- [hypothesis] pillars: when a transient on-screen message (toast) can be replaced or dismissed while its timer is still running -> give each shown message a monotonically increasing id stored per player and re-check it is still current after every Sleep before animating out or removing (1 map(s))
- [hypothesis] pillars: when a per-player menu device must handle players joining and leaving -> keep a [player]menu map created lazily on first open, subscribe PlayerAddedEvent/PlayerRemovedEvent, and on leave close the menu and rebuild the map without that player (1 map(s))

## 3. Devices in the level

Questions: Which spawners, trackers, granters, barriers and UI devices exist; which are global and which per player; who wires them? (read them via the MCP when live)

- [hypothesis] pillars: when XP/score is awarded per kill and per survival interval -> delegate scoring to Accolade devices fed by Elimination Manager and a Timer, and award survival XP from a snapshot of the alive list taken in a non-suspending handler (1 map(s))
- [hypothesis] pillars: when a Verse creative_device exists in code -> verify with find_actors that an instance is placed in the level and its @editable references are filled (1 map(s))
- [hypothesis] pillars: when a periodic drop gives each living player a different item from several granter pools -> pick the pool first by weight/(served+1) plus jitter, then an unused index different from the player's last; keep granters disabled outside the round (1 map(s))
- [hypothesis] pillars: when participants are teleported onto a fixed set of arena positions -> keep a per-slot blocked flag array: try the preferred slot then the next free ones, mark a slot blocked when occupied or when the teleport fails, and log duplicates (1 map(s))
- [hypothesis] pillars: when an Item Granter list size is unknown or may exceed a small bound, and drops must feel fair -> probe the list at startup with GetItemGrantCountAtIndex over a wide range (up to 512), keep only valid indices, stop after a run of consecutive empty slots; allow a manual size override (1 map(s))
- [hypothesis] pillars: when pillars were built from one actor and a floor tile on top must match the spawner -> place a floor tile per pillar and re-align pillars to tiles so spawn height and footprint are consistent (1 map(s))
- [hypothesis] pillars: when a granter system must prove grants actually landed -> subscribe to each granter's ItemGrantedEvent, snapshot the agents of the previous cycle and log which agents received no event, with periodic cumulative distribution percentages (1 map(s))
- [hypothesis] pillars: when players must receive random loot from several Item Granter pools without streaks -> pick a weighted pool per player excluding their last pool, and renormalize weights by fixed point to compensate the exclusion (1 map(s))
- [hypothesis] pillars: when a Verse device needs a list of many placed devices wired via MCP -> declare numbered single @editable fields (Spawner01..12) and collect them into an array in code, because array wiring is not settable through MCP (1 map(s))
- [hypothesis] pillars: when a Verse handler needs per-player context inside a Subscribe callback and local lambdas are unavailable -> create a small relay class per player holding manager, player and agent, store it in a per-agent map and subscribe its method; keep the cancelables to cancel on leave (1 map(s))
- [hypothesis] pillars: when a Verse device must show a map code or favorite prompt HUD to all players -> attach a widget bar per player with a retry loop waiting for player UI, raced against PlayerRemoved, cycling name and favorite prompt on a timer with a minimum interval (1 map(s))

## 4. Progression

Questions: What persists between rounds/runs and what resets; unlocks, currencies, difficulty or tier scaling. Numbers only from the owner or his maps' data.

_Nothing learned yet for this section._

## 5. Strategies around death, defeat and progress

Questions: Respawn/retry rules, paid retry or continue, rewards, boosts. Design strategies, learned as patterns with a variant.

_Nothing learned yet for this section._

## 6. Persistence

Questions: What is stored per player; what happens when data is not loaded yet or the player left.

_Nothing learned yet for this section._

## 7. Performance

Questions: Item/NPC pools, listeners, per-frame work.

- [hypothesis] pillars: when item pool sizes are unknown to Verse at runtime -> probe GetItemGrantCountAtIndex over indices at start, stop after 16 consecutive zeros, and offer a manual size override with a round-robin fallback (1 map(s))

## 8. Launch checklist

Questions: First 10 minutes of a new player, a full round, a death/defeat, a restart, two players at once, a player leaving mid-round.

_Nothing learned yet for this section._
