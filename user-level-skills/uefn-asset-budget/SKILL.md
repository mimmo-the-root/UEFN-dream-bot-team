---
name: uefn-asset-budget
description: Checks that a prop or material made by an AI tool or taken from outside fits a UEFN map before it goes in: triangle band, one material, simple collision, texture size, scale in centimeters, and a test in the editor. Use when the owner says triangles, poly count, polygons, LOD, collision, texture size, scale, heavy mesh, Rodin, Tripo, generated model, imported mesh or asset budget.
kind: discipline
last_reviewed: 2026-11-12
sources: [Epic's "Fortnite-ready assets" best practices, read 2026-11-12, restated in our own words; the thresholds applied to AI-made models are our own checks]
---

# Asset budget for props and materials

A generated model is a draft, not a finished asset. Measure it, bring it into the band, prove it in the editor, then record it. The numbers below come from Epic's guide and are indicative; the guide says nothing about AI-generated models, so using them as a gate for those is a kit rule.

## When to use
- A model comes out of Rodin, Tripo or any generator, or arrives from Fab or another project, and is about to be placed.
- The map lags, loads slowly or looks wrong in scale after new props were added.

**When not to use:** reading mesh data and physics through the MCP (use `uefn-physics-mesh`), memory and actor count of a whole map (use `performance-uefn-checklist`), shader and material graphs (use `uefn-materials`).

## The gate (all must pass)
1. Scale: 1 unit is 1 cm, Z is up, checked next to a 192 cm character. A model that is "1 m" in the tool is 100 units here.
2. Triangles at the highest level of detail (LOD0): small props about 400 to 1,200; medium props about 900 to 4,000; large props about 2,500 to 9,000 (simple to complex). Vertices: small up to about 1,000, medium up to about 3,000, large up to about 5,000. Above 20,000 vertices with no LODs: reject or rebuild with fewer polygons.
3. One material per mesh. Several materials multiply draw cost, especially on Switch and mobile.
4. Textures: PNG or TGA, sides a power of two (64 to 2048), 2K at most; 512 by 512 when mobile or Switch matter. Normal maps use the DirectX convention.
5. Collision: simple convex pieces named `UCX_<MeshName>` (`_01`, `_02` for copies), at most 10. No per-triangle collision on props.
6. Level of detail: Epic asks for five levels, each about half the triangles of the previous. For a small jam or demo map keep props low and add levels only to large or heavily repeated props (a kit choice, not Epic's rule).
7. Test: place it in the map, look at it in the light of its area, check scale and frame rate in a play session.
8. Record: source, tool, date, triangles, vertices, materials, license, and whether it is an origin asset (Fab or another project's).

## Workflow
1. Generate or import into a scratch folder, never straight into the map.
2. Read the counts (triangles, vertices, materials). Through the MCP the static mesh tools list vertex and triangle counts, LODs, collision and material slots; they were not verified on project meshes in the lab, so check the answer against the editor's mesh window.
3. Over the band: ask the generator for a lower polygon count or retopologize; do not decimate blindly (the silhouette must stay stable from every side).
4. Merge materials, resize textures, add the simple collision.
5. Move it into its asset-type folder, fix redirectors, place it, test, record.

## Rules (symptom, cause, remedy)
- Giant or tiny prop: the model was built in meters. Rescale to centimeters before import.
- Lag after adding many props: heavy meshes repeated many times. Lower the triangles or share one mesh with material instances.
- Dark or wrong-looking surface: normal map in the wrong convention. Use DirectX.
- Player snags on a prop: collision follows the mesh. Replace it with simple convex pieces.
- Three materials on a small crate: merge into one atlas.
- The generator's license is unclear: record it and treat the asset as unusable for sale until checked.

Related: `uefn-materials`, `performance-uefn-checklist`, `uefn-physics-mesh`.
