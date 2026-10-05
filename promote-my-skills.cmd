@echo off
rem Promotes your updated genre/technique skills from your profile to this repo.
rem Report first, then asks before copying. Never copies private data (local\ folders). Does not commit.
setlocal
cd /d "%~dp0"
set PY=py -3
%PY% --version >nul 2>&1 || set PY=python
echo === Differences between your profile and the repo ===
%PY% tool\promote-genre-skills.py
if errorlevel 1 goto end
echo.
set /p GO=Promote now? A = ask file by file, Y = all, N = stop (A/Y/N): 
if /i "%GO%"=="Y" %PY% tool\promote-genre-skills.py --apply --all
if /i "%GO%"=="A" %PY% tool\promote-genre-skills.py --apply
echo.
echo Next: git status, check the diff, then commit.
:end
pause
