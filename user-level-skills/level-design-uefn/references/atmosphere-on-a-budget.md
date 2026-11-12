# Atmosphere on a budget

How to give each area of a map its own mood with lights, grading and a few cheap tricks, without new Verse code. Learned from reading Epic's "Shadows of the Abbey" example island (a night horror map). Take the methods, not the look.

## What the example does (restated)
- Color grading per zone with post-process volumes, so each area has its own tone.
- Many local lights (about 190 in the whole map), including fake fill lights and volumetric spots.
- Candle flicker through a light-flicker material, no script.
- Fog cards for depth, rain that follows the player, wet decals.
- Zone devices that recognize an inside area and switch an effect off there.
- Few unique meshes reused many times; variety comes from material instances; a small base color texture plus detail packed in shared channel textures.
- A lighting quality manager so the look scales down on weaker platforms.
Epic says the example holds no NPCs, dialogue, quests or progression. It is a look and optimization reference only.

## How to reuse it for areas or stages
1. One post-process volume per area, with a clear grade: warm and dirty, cold and even, rich and colorful.
2. A few local lights per area, placed for the focus of attention first.
3. Flicker on neon, screens or candles with the light-flicker material.
4. Fog or dust only where the mood needs it.
5. Zone devices to tell areas apart, only after a test shows they work for the case.
6. Material instances for variation, not new textures.
7. A lighting quality manager, so the frame rate stays above 30 on weaker platforms.
8. Play it in the editor and in a session before adding more lights.

## Limits
- Anything taken from the example island is not original work: if it ships, note it as an origin asset.
- The example is photorealistic and heavy on memory; a stylized map should use fewer lights and simpler materials.
- Day sequence settings became readable from Verse in 43.10; using them needs new code, so keep them for later.
