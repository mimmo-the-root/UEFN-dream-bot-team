# Tidy a material graph with an agent (layout pass only)

Source: Epic's note on cleaning up material graphs with an AI agent connected to the editor (Nov 2026). The idea: you build the material fast and messy, then hand the tidy-up to the agent while you do something else. The prompt below is our version of it, in our words.

## When
The owner says "tidy", "clean up", "organize" or "make readable" about a material graph (crossed wires, unlabeled nodes, odd parameter names). It is a LAYOUT and NAMING pass. It is never an optimization or a redesign.

## Before you start
1. The owner names the material. Ask once if it is not clear. Work on that asset only.
2. Keep a way back: ask the owner to save, and to duplicate the asset in the Content Browser if it matters. The MCP has no undo for node moves.
3. Read the baseline and keep it: `MaterialTools/get_expressions`, `get_statistics` (instruction counts), `get_property_input` for every output pin, `list_parameter_groups`. This is what "no change in behavior" is measured against.
4. Check which tools exist in this editor: `MaterialTools/layout_expressions`, `connect_expressions`, `disconnect_expressions`, `delete_unused_expressions`, `rename_parameter_group` are known. For comment boxes and named reroutes read `list_expression_classes` first (look for a Comment class and the NamedRerouteDeclaration / NamedRerouteUsage classes). If a class or a tool is missing, say so and do the rest; never invent a tool name. NOT verified in this kit yet: comment boxes, named reroutes and node positions through the MCP.

## The prompt (give it to the coder, with the material path)
```
Organize this material graph for readability without changing its behavior:
- Left to right: inputs on the left, material outputs on the right.
- One clear horizontal main line for the primary data flow; supporting branches above or below it.
- Use Named Reroute Declaration/Usage nodes for values shared across sections or over long distances, with meaningful names.
- Group related operations in comment boxes with clear labels.
- Fewer wire crossings, fewer backward connections, no unnecessary reroutes.
- Keep every parameter, every calculation and every output connection. This is a layout and readability pass, not an optimization or a redesign.
```
The last line matters most: it tells the agent not to "improve" the math. Say what "clean" means for this team (flow direction, when to use comments, when to use reroutes) and the agent follows it.

## After
- Recompile (`MaterialTools/recompile`), then compare with the baseline: same instruction count, same pin connections, same parameter names and default values. `diff_material` against the saved copy if one exists. Any difference in values is a failure: stop and report it, do not fix by guessing.
- Parameter renames change what material instances and Verse refer to. Rename a parameter only when the owner asked for it, and list every rename in the report.
- Report in 5 lines: what was moved, what was grouped, reroutes added, renames, and the before/after numbers.

## Once it works
Turn the version that worked for this owner's conventions into a short lesson (the lesson flow, owner approves). Do not keep a second copy of the prompt elsewhere.
