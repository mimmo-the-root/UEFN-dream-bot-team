# Plan: Chicken Roundup

- Status: Approved
- Approved: yes

## Island settings
| Setting | Value | Why |
|---|---|---|
| Max players | 4 | the spec asks for 4 players |
| Min players to start | 1 | a player can start alone and others join |
| Teams | none (Free for all, one shared score) | co-op, no teams |
| Round | 1 round of 3 minutes | the loop |
| Respawn | on | nobody is out of the game |
| Join in progress | on | friends can join a running round |

## Environment
(Status words: planned, built, placeholder. "built" only with real assets from SCENERY.md; a cube is a placeholder.)
| Element | Where | Status |
|---|---|---|
| Farm ground and grass | the whole play area | built |
| Sky and warm afternoon light | the whole map | built |
| Barn, fences and haystacks | around the pen | built |
| Farm ambience and a short music loop | the whole map | built |
| Play area boundary and the spawn area | the edge of the farm | built |

## Build order
- Pass 1 (structure): S1 first: the farm, the pen and the flow of the loop; the loop is playable at the end of this pass, then S2.
- Pass 2 (details): sounds for the delivery, a nicer pen, effects.
- Try one sample first: one chicken and the egg checked alone before the flock.
- First step of the build: list the actors of the map and delete the default player pads, then place the new ones.

## S1 - Round up the chickens
### Devices
| Device or system | Status | Note |
|---|---|---|
| Wildlife Spawner V2 for the chickens (7 in the field, none inside the pen zone) | recipe | SCENERY.md; read and set the animal, the default was a wolf |
| Egg prop with a Damage Volume V2 (creatures only): each chicken that enters is removed and its spawner's elimination event scores the point | recipe | SCENERY.md, section The egg |
| Score manager and round timer | recipe | proven recipe |

### Verse files
- chicken_roundup.verse: round start, one point for each chicken eliminated by the egg, score, end of round.

### Assets inventory
| Asset | Status | Source |
|---|---|---|
| Fence and barn props | present | Fortnite |
| Grass and trees allowed in a playable island | import | Fortnite |
| Delivery sound | create | project |

### Manual steps (only the owner can do them)
- Assign the spawner array and the other device references in the Details panel, then press Done in the console (Your turn).

## S2 - Two chickens at once
### Devices
| Device or system | Status | Note |
|---|---|---|
| Same egg | recipe | each chicken counts once (one spawner, one chicken) |

### Verse files
- none: the count in chicken_roundup.verse already handles it.

### Assets inventory
| Asset | Status | Source |
|---|---|---|
| none new | present | project |

## Sources consulted
- recipes mechanics: the score and timer recipe; uefn-level-devices for the pen volume.
- uefn-device-gotchas: references assigned by hand.

## Risks to tasks
| Risk of the spec | First task that reduces it |
|---|---|
| R1 | T-001 |
| R2 | T-002 |
| R3 | T-003 |
