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
echo Official packs for technique skills...
if exist "%SRC%user-level-skills\genre\llm-npc-conversations\official" robocopy "%SRC%user-level-skills\genre\llm-npc-conversations\official" "%DST%\skills\genre\llm-npc-conversations\official" /E /NFL /NDL /NJH /NJS
if exist "%SRC%user-level-skills\genre\materials\official" robocopy "%SRC%user-level-skills\genre\materials\official" "%DST%\skills\genre\materials\official" /E /NFL /NDL /NJH /NJS
echo User-level rule 14 (old kits update themselves)...
py -3 "%SRC%tool\install-rule14.py" "%SRC%user-level-memory\section-14-kit-self-update.md" "%DST%\CLAUDE.md" || python "%SRC%tool\install-rule14.py" "%SRC%user-level-memory\section-14-kit-self-update.md" "%DST%\CLAUDE.md"
echo Global update hook (old kits update themselves at session start)...
if not exist "%DST%\hooks" mkdir "%DST%\hooks"
copy /Y "%SRC%user-level-hooks\kit-sync-global.py" "%DST%\hooks\kit-sync-global.py" >nul
py -3 "%SRC%tool\install-global-hook.py" "%DST%\settings.json" "%DST%\hooks\kit-sync-global.py" || python "%SRC%tool\install-global-hook.py" "%DST%\settings.json" "%DST%\hooks\kit-sync-global.py"
echo.
echo Done. Now open a project session: the kit updates the project by itself and the
echo official LLM pack appears on the Skills page for your approval.
pause
