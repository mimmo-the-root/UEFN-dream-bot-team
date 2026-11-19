@echo off
rem Start Cod (Claude Code) in this folder in the mode chosen on the Models page of the console (v1.124.2):
rem   auto = your Claude plan, and free models in the SAME session when the plan is at its limit (default)
rem   plan = your Claude plan only, without the router (as before 1.124)
rem   free = free models only: your plan is never used
rem   safe = work on free models through the router, the plan login is kept (no placeholder token; T-084)
rem Force a mode with:  cod.cmd --auto | --plan | --free | --safe   (other arguments go to claude).
set MODE=
if /i "%~1"=="--auto" (set MODE=auto& shift)
if /i "%~1"=="--plan" (set MODE=plan& shift)
if /i "%~1"=="--free" (set MODE=free& shift)
if /i "%~1"=="--safe" (set MODE=safe& shift)
if not defined MODE for /f %%M in ('py -3 "%~dp0dream_router.py" mode 2^>nul') do set MODE=%%M
if not defined MODE set MODE=auto
rem v1.124.21: the mode goes in a per-session settings file (claude --settings), which outranks the env the router wrote
rem in settings.json: so --plan / --free really win for this session, and the Models page is not changed.
set SETF=
for /f "delims=" %%S in ('py -3 "%~dp0dream_router.py" session-settings %MODE% 2^>nul') do set "SETF=%%S"
if /i "%MODE%"=="plan" (
  echo Cod starts on your Claude plan only.
  goto :run
)
py -3 "%~dp0dream_router.py" status >nul 2>&1 || call "%~dp0dream-router.cmd"
timeout /t 2 /nobreak >nul
if /i "%MODE%"=="free" (
  echo Cod starts on FREE models only. Your Claude plan is not used.
) else if /i "%MODE%"=="safe" (
  echo Cod starts SAFE: work on free models through the router, your plan login is kept for the safety check.
) else (
  echo Cod starts on your Claude plan; at the limit it goes on with free models in this same session.
)
:run
rem v1.124.39: the router's values in the user settings.json outrank --settings (owner's debug log, test 062), so Plan only
rem skips the user settings for this one session (--setting-sources project,local): the project's hooks and permissions stay.
if /i "%MODE%"=="plan" if defined SETF (
  claude --setting-sources project,local --settings "%SETF%" %1 %2 %3 %4 %5 %6 %7 %8 %9
  goto :eof
)
if defined SETF (
  claude --settings "%SETF%" %1 %2 %3 %4 %5 %6 %7 %8 %9
) else (
  claude %1 %2 %3 %4 %5 %6 %7 %8 %9
)
