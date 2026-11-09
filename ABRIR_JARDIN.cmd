@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ABRIR_JARDIN.ps1"
if errorlevel 1 (
  echo.
  echo No se pudo abrir el Jardin local. Revisa el mensaje anterior.
  pause
)
