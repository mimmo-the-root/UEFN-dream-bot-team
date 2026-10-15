# Working rules for Verse UI Kit screens

Written for this kit from the behavior of the Verse UI Kit; if the project's assets or Epic's own AGENTS.md say otherwise, they win.

## Must, for all UI (with or without the kit)
- **Every screen works on gamepad, keyboard and mouse.** The first control gets focus when the screen opens (on a destructive confirm, the safest button). Every control is reachable with D-pad and arrows, the focus highlight is visible, Back closes the screen.
- **No values on nested instances.** UEFN does not show them in Details, so nobody could find or change them. Use a named slot, a field on your screen bound to the child, or Verse.
- **Player-facing text is localizable:** `<localizes>` messages in Verse, text blocks in UMG, never text baked into a texture.
- **Order of work:** compile the widget, save it, then build Verse (the compiler reads saved assets). If the build says "Unknown member" for fields that exist and are saved, stop and tell the owner; do not move or rename assets to get around it.
- **Ask first** before deleting assets, renaming named slots, restructuring a kit widget or changing project settings. Stop if an asset has unsaved changes you did not make or is checked out by someone else. Save only your own paths: an empty path list saves everything, including other people's work.
- **Say what you could not do**: list the manual steps instead of leaving work half done.

## Only with the Verse UI Kit
- **Own screens, untouched kit.** Put kit widgets inside your own screen and style them from there. Edit a kit widget only if the owner asks, and then check every screen that uses it.
- **Style through slots** with material instances, so the look previews in the designer.

### Wiring
- A parent cannot listen to a child's Verse event. Bind the child's inner native button to one shared int event on your screen; each child sends its own number, counting from 1 (0 means nothing chosen). The inner button path depends on the widget: read it from the child's tree.
- To show a choice, one bool per child (`IsOption1Selected`) set from Verse needs no manual step. One int field through a conversion function needs a manual value per binding.
- Code folders are internal modules unless `ui_modules.verse` makes them public. Error 3593 means the folder is not public: copy the pattern in that file.
- Subscribe through the kit's helper so `ClearAllForPlayer` cleans up. Create a fresh widget each time a screen opens.

## Input (all UI)
- After the widget is on screen, give focus to its first control; set the screen's Desired Focus Widget too.
- Menu navigation is turned on with the menu input mapping and off with `ClearAllForPlayer`.
- With the kit, close: use its close button, bind both its inner buttons (click and Back) to one `OnCloseClicked` event. A close button added from Verse also needs a listener on the Back release.
- With the kit, tab rows and pagers send -1 or +1 through a navigate event. After anything that changes which controls exist (tab, page, filter), give focus again.
- Collapse empty rows instead of leaving focusable controls with nothing visible.
- HUD pieces and toasts use input mode None so they never steal input.
- If you freeze the player, release them on every way out of the screen.
- Touch: watch the input method and switch layout when it changes.

## Should
- Hover and gamepad focus look the same. Input prompts use ActionWidgets so the right glyph shows. Keep important UI about 5% inside the screen edge, touch targets about 64 px, body text about 24 px or more. Never rely on color alone for state.
- Follow the project's naming. Without one: widgets `UW_<Category>_<Name>`, role first in tree names (`Main_Button`), bools `Is<Adjective>`, events `On<Event>`.
- Remove debug `Print` calls before finishing.

## Done checklist
Widgets compile, own assets saved, Verse build `clean`; asset validation passes or the owner was asked to run it; focus lands on the first control and every control is reachable; Back closes and input is restored; nothing set on nested instances; manual steps listed.
