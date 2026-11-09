@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0INICIAR.ps1" %*
exit /b %ERRORLEVEL%
