# Snippets (written for this kit)

Status: a snippet is "verified" only after it builds `clean` with `/verse-check` in a project that has the kit; the line below records the date and UEFN version. Names such as `UW_MyScreen` are your own widget.

Verified: Toast (2026-10-15, UEFN 42.40, `/verse-check` clean). Not yet compiled: the screen, the shared handler and the freeze/release snippets (they need your own widget).

## Toast (needs only the kit)
```verse
using { /Verse.org/Simulation }
using { VerseUIKit.Verse.Feedback }

SavedHeading<localizes> : message = "Saved"
SavedBody<localizes> : message = "Your changes are stored."

ShowSaved(Player : player) : void =
    ui_feedback_toast{}.ShowSuccessToast(Player, SavedHeading, SavedBody)
```

## A screen that opens, takes focus and closes on Back
Needs a widget `UW_MyScreen` of yours with an `OnCloseClicked` event bound to the kit close button.
```verse
using { /UnrealEngine.com/Temporary/UI }
using { /Verse.org/Input/UI }
using { /Verse.org/Simulation }
using { VerseUIKit.Verse }

my_screen := class:
    var Widget<private> : UW_MyScreen = UW_MyScreen{}
    var MaybePlayer<private> : ?player = false
    Helper<private> : ui_helper_function_library = ui_helper_function_library{}

    Show<public>(Player : player) : void =
        set MaybePlayer = option{Player}
        set Widget = UW_MyScreen{}
        Helper.ShowFullScreen(Player, Widget)
        Helper.AddInputMappingToPlayer(Player, UI.MenuNavigationMapping)
        Helper.SubscribeToEvent(Player, Widget.OnCloseClicked, OnCloseClicked)
        Helper.FocusWidgetForPlayer(Player, Widget)

    Hide<public>(Player : player) : void =
        Helper.ClearAllForPlayer(Player)

    OnCloseClicked<private>(Event : tuple()) : void =
        if (Player := MaybePlayer?):
            Hide(Player)
```

## Several buttons, one handler
Each child button sends its own number (set in the editor, counting from 1) to one shared event.
```verse
OnOptionClicked<private>(Option : tuple(int)) : void =
    case (Option(0)):
        1 => set Widget.IsOption1Selected = true
        2 => set Widget.IsOption2Selected = true
        _ => {}
```

## Freezing the player: release on every exit
```verse
Show<public>(Player : player) : void =
    Helper.HoldPlayerStill(Player)
    # ... show the screen ...

Hide<public>(Player : player) : void =
    Helper.ReleasePlayer(Player)   # every way out must reach this line
    Helper.ClearAllForPlayer(Player)
```
