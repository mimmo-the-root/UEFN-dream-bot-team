<!-- Full text of base rule 12. The short version is in ~/.claude/CLAUDE.md; this file is installed to ~/.claude/kit-rules/ by update-my-profile.cmd. -->

## 12. Recognizing UEFN brand collections — optional

Epic partners with real-world franchises ("Game Collections" — TMNT, LEGO, Fall Guys, Star Wars,
KPop Demon Hunters, Squid Game, The Walking Dead Universe, Rocket Racing, and others added over
time) for exclusive assets/devices used to build themed "brand islands." `project-bootstrap`
checks for this during its A1 structure-mapping step whenever a project's folders/devices/
template name look brand-themed — see `~/.claude/skills/brand-collections-uefn/SKILL.md` for the
marker table (confirmed technical markers for some collections, name-only for others not yet
confirmed against a real project) and the procedure for capturing real markers straight from a
project when an unrecognized brand shows up, writing them both to that skill's own reference file
(works immediately, no vault needed) and, if the second brain (rule 11) is configured, to a
`type: pattern` article there via `second-brain-librarian` for cross-machine reuse. This never
blocks or fails a task — an unmatched brand-looking name is just noted in `SPEC.md`, not treated
as an error.
