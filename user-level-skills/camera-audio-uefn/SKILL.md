---
name: camera-audio-uefn
description: Rules for cameras and sound in a UEFN map: when to change the camera and how to give it back, how to keep audio readable, music that follows the action, and sound near the source. Use when the owner says camera, view, cinematic, fixed camera, third person, music, ambience, volume, audio balance or sound is too loud.
kind: discipline
last_reviewed: 2026-10-30
sources: [original]
---

# Camera and audio in UEFN

Both are shared with the player's expectations. Change them on purpose, keep them readable, and always give control back.

## When to use
- A map needs a special camera (intro, fixed view, spectator view) or the camera feels wrong.
- Setting up music, ambience or event sounds, or the mix is unclear.

**When not to use:** feedback design for actions (use `game-feel-uefn`), HUD and menus (use `uefn-ui-widgets`).

## Workflow
1. Decide what the camera must show and for whom (all players or one agent) and when it ends.
2. Add the camera only for that moment and remove it for that player at the end, on respawn and when the player leaves.
3. Place audio devices near the source and set ranges so sounds fade with distance.
4. Set levels: music below effects, voice above both, ambience lowest. Listen with all three at once.
5. Test with a second player: the camera must not trap or confuse someone who joins late.

## Rules (symptom, cause, remedy)
- Camera that never returns: the player is stuck in a special view after an event. Always pair add with remove, and remove on respawn.
- Camera for everyone by mistake: a personal view shows to all. Send the camera to the agent, not the whole playspace.
- Music that masks cues: effects are lost in the music. Lower the music or use a shorter loop.
- One loop for a whole round: it tires players. Use two or three pieces and change at the phases.
- Sound from far away at full volume: the range is too wide. Shorten the range and test by walking away.
- Cinematics that cannot be skipped: replay is a chore. Keep them under ten seconds or skippable.

Level table and device notes: `references/levels-and-cameras.md`.
