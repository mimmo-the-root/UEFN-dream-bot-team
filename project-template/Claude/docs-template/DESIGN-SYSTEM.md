# Design — <system name>  (copy to `Claude/docs/DESIGN-<system>.md`)

> Gate: NO refactor code until the owner approves section 4. Editor changes are done by the owner from an exact list.
> Input: an up-to-date `DEPENDENCY-MAP.md`.

Status: Draft / Approved <date> · Kit: <version>

## 1. Inventory
Current flags, states and the files that own them (from the dependency map).

## 2. Design
- **Goals and principles**
- **States**: name · meaning · owner file
- **Transitions**: from → to · trigger · guard
- **Multiplayer**: who owns state; per-player vs shared; join/leave
- **Mapping from current flags** to the new states
- **Emergency mechanisms**: reset / recovery paths
- **Migration strategy** in steps (each step compiles and plays on its own)
- **Out of scope**
- **Risks**

## 3. Reduction proposal
What can be removed or merged, with a pilot and the validation protocol (see `TEST-PLAN.md`).

## 4. Owner decisions and approval checklist
- [ ] Decision 1: <question> → <answer>
- [ ] Section 2 approved · Section 3 approved · Migration may start
