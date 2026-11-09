@echo off
if not exist "%LOCALAPPDATA%\JardinZen" mkdir "%LOCALAPPDATA%\JardinZen"
type nul > "%LOCALAPPDATA%\JardinZen\STOP"
echo STOP creado. Se detendran nuevos lotes.
