@echo off
rem Resets the clean demo Lab and installs the current kit into your profile. See reset-lab.ps1 for the switches (-Yes, -DryRun, -OpenUefn).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0reset-lab.ps1" %*
