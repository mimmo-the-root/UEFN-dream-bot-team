@echo off
rem Dream Router: the local free-model router for Cod, kept alive by its guardian (dream_router.py supervise).
rem This restarts the router (the guardian starts the current version within a few seconds) and starts the guardian if needed.
if exist "%USERPROFILE%\.dream-router\STOP" del /q "%USERPROFILE%\.dream-router\STOP"
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'dream_router\.py' -and $_.CommandLine -match ' serve' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }; if (-not (Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'dream_router\.py' -and $_.CommandLine -match 'supervise' })) { Start-Process -FilePath py -ArgumentList @('-3', '\"%~dp0dream_router.py\"', 'supervise') -WindowStyle Hidden }" >nul 2>&1
echo Dream Router restarting - it answers on http://127.0.0.1:8787 within a few seconds.
