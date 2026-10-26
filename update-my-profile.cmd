@echo off
rem Updates YOUR Claude profile (~/.claude) from this kit copy. Safe to run again.
rem Never overwrites what the skills learned (local\ and pack\ folders are skipped).
set SRC=%~dp0
set DST=%USERPROFILE%\.claude
echo Kit template (project files)...
robocopy "%SRC%project-template" "%DST%\kit-template" /E /NFL /NDL /NJH /NJS
echo Agents...
robocopy "%SRC%user-level-agents" "%DST%\agents" /E /NFL /NDL /NJH /NJS
echo Skills (learned data protected)...
robocopy "%SRC%user-level-skills" "%DST%\skills" /E /XD local pack /NFL /NDL /NJH /NJS
rem This copy has publish.ps1: it is the maintainer's. The Skills page then releases from the console (no GitHub sending, release boxes).
if exist "%SRC%publish.ps1" (
  if not exist "%DST%\skills" mkdir "%DST%\skills"
  echo {"maintainer": true}> "%DST%\skills\maintainer.json"
)
echo Official packs for technique skills...
if exist "%SRC%user-level-skills\genre\llm-npc-conversations\official" robocopy "%SRC%user-level-skills\genre\llm-npc-conversations\official" "%DST%\skills\genre\llm-npc-conversations\official" /E /NFL /NDL /NJH /NJS
if exist "%SRC%user-level-skills\genre\materials\official" robocopy "%SRC%user-level-skills\genre\materials\official" "%DST%\skills\genre\materials\official" /E /NFL /NDL /NJH /NJS
echo Epic Verse UI Kit guide (private, never published)...
if exist "%SRC%_private\epic\AGENTS.md" (
  if not exist "%DST%\skills\verse-ui-kit\references\epic" mkdir "%DST%\skills\verse-ui-kit\references\epic"
  copy /Y "%SRC%_private\epic\AGENTS.md" "%DST%\skills\verse-ui-kit\references\epic\AGENTS.md" >nul
)
echo User-level rule 14 (old kits update themselves)...
py -3 "%SRC%tool\install-rule14.py" "%SRC%user-level-memory\section-14-kit-self-update.md" "%DST%\CLAUDE.md" || python "%SRC%tool\install-rule14.py" "%SRC%user-level-memory\section-14-kit-self-update.md" "%DST%\CLAUDE.md"
echo Global update hook (old kits update themselves at session start)...
if not exist "%DST%\hooks" mkdir "%DST%\hooks"
copy /Y "%SRC%user-level-hooks\kit-sync-global.py" "%DST%\hooks\kit-sync-global.py" >nul
copy /Y "%SRC%user-level-hooks\kit_install.py" "%DST%\hooks\kit_install.py" >nul
copy /Y "%SRC%user-level-hooks\fab_pack.py" "%DST%\hooks\fab_pack.py" >nul
copy /Y "%SRC%user-level-hooks\economy_sim.py" "%DST%\hooks\economy_sim.py" >nul
copy /Y "%SRC%user-level-hooks\log_signals.py" "%DST%\hooks\log_signals.py" >nul
copy /Y "%SRC%user-level-hooks\fab_lab.py" "%DST%\hooks\fab_lab.py" >nul
copy /Y "%SRC%user-level-hooks\fab_assets.py" "%DST%\hooks\fab_assets.py" >nul
copy /Y "%SRC%user-level-hooks\fab_checklist.py" "%DST%\hooks\fab_checklist.py" >nul
copy /Y "%SRC%user-level-hooks\map_trace.py" "%DST%\hooks\map_trace.py" >nul
py -3 "%SRC%tool\install-global-hook.py" "%DST%\settings.json" "%DST%\hooks\kit-sync-global.py" || python "%SRC%tool\install-global-hook.py" "%DST%\settings.json" "%DST%\hooks\kit-sync-global.py"
echo.
echo Done. Now open a project session: the kit updates the project by itself and the
echo official LLM pack appears on the Skills page for your approval.
pause
