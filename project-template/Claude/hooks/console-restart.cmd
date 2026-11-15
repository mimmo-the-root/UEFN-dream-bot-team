@echo off
rem Restart the Agent Console server of THIS project (double-click it). Useful after a kit update in the middle of a session:
rem the server keeps the old code until it restarts (new routes such as /music, v1.124.40). Pages stay where they are: press F5.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=@(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'agent-console-server' -and $_.ProcessId -ne $PID }); foreach($p in $s){ Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }; Start-Sleep -Milliseconds 700; Start-Process powershell -ArgumentList ('-ExecutionPolicy Bypass -File \"' + (Join-Path '%~dp0' 'agent-console-server.ps1') + '\"') -WindowStyle Hidden; Start-Sleep -Seconds 2; try { (Invoke-WebRequest -Uri 'http://127.0.0.1:8765/whoami' -TimeoutSec 3 -UseBasicParsing).Content } catch { 'not answering yet' }"
echo.
echo Console restarted. Press F5 on the console page.
timeout /t 5 >nul
