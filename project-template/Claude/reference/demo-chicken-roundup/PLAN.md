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

## Build order
- Pass 1 (structure): S1 first: the farm, the pen and the flow of the loop; the loop is playable at the end of this pass, then S2.
- Pass 2 (details): sounds for the delivery, a nicer pen, effects.
- Try one sample first: one chicken and one pen checked alone before the flock.

## S1 - Round up the chickens
### Devices
| Device or system | Status | Note |
|---|---|---|
| Creature spawner for the chickens | explore | try it in a test project first |
| Pen volume that counts deliveries | skill | uefn-level-devices |
| Score manager and round timer | recipe | proven recipe |

### Verse files
- chicken_roundup.verse: round start, delivery count, score, end of round.

### Assets inventory
| Asset | Status | Source |
|---|---|---|
| Fence and barn props | present | Fortnite |
| Grass and trees allowed in a playable island | import | Fortnite |
| Delivery sound | create | project |

### Manual steps (only the owner can do them)
- Assign the spawner array and the pen references in the Details panel, then tell Claude.

## S2 - Two chickens at once
### Devices
| Device or system | Status | Note |
|---|---|---|
| Same pen volume | skill | each chicken counts once |

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
