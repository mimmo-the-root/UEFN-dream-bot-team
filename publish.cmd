@echo off
rem Publishes the kit (tests, commit, push, tag, GitHub Release) without changing the execution policy.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0publish.ps1" %*
pause
