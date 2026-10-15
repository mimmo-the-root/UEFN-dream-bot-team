# Building UI without the Verse UI Kit

The kit is optional. Two ways to build a screen, pick the simpler that fits:

1. **Verse-only widgets.** Build the screen in Verse with the UI API (`/UnrealEngine.com/Temporary/UI`): a canvas or stack box holding text blocks, color or texture blocks and buttons, added to the player's UI with an input mode. Good for HUD pieces, counters, toasts and small menus. Everything is code, so it is easy to review and version.
2. **UMG widget blueprints.** Create a widget in the editor (or through the UMG toolset of the MCP, when the session offers it), lay it out, expose Verse fields and events, and drive it from Verse. Good for designed screens with art and animation.

Whichever you pick, the rules in `rules.md` under "for all UI" apply unchanged: first control focused, gamepad and keyboard reach everything, Back closes, the player is released on every way out, text is localizable, nothing hidden on nested widgets, compile and save before building, ask before destructive steps, list manual steps.

Steps for a screen without the kit:
1. Look at what the project already has (`Custom_widget`, existing screens, `Claude/docs/UI-STYLE-NOTES.md`) and match it before inventing a look.
2. Write the Verse class: create the widget, add it to the player's UI with the right input mode, keep the player in a field, and a method that removes the widget and restores input. Every exit path calls that method.
3. Make every control reachable: set the first control as the focus target after the widget is on screen and give focus again after anything that changes which controls exist.
4. Build with `/verse-check`; only `clean` counts. Report the manual test (gamepad, keyboard, mouse).

The exact API names and signatures change with UEFN updates: read the project's existing UI code or the Verse documentation for the current ones, and write a minimal version first. Snippets here stay "not compiled" until `/verse-check` builds them in a real project.

If the kit is later installed, nothing needs to be rewritten: screens built by hand keep working, and new ones can start from the kit's examples.
