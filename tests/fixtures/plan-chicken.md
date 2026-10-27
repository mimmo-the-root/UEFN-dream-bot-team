# Plan: Chicken Roundup

- Status: Approved
- Approved: yes

## Build order
- Pass 1 (structure): S1 first: the farm, the pen and the flow of the loop; the loop is playable at the end of this pass, then S2.
- Pass 2 (details): sounds for the delivery, a nicer pen, effects.
- Try one sample first: one chicken and one pen checked alone before the flock.

## S1 - Round up the chickens
### Devices
| Device or system | Status | Note |
|---|---|---|
| Creature spawner for the chickens | explore | try it in the Lab first |
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

## Risks to tasks
| Risk of the spec | First task that reduces it |
|---|---|
| R1 | T-001 |
| R2 | T-002 |
| R3 | T-003 |
