@echo off
setlocal
if "%~1"=="" (
 echo Uso: PREGUNTAR.cmd "pregunta"
 exit /b 2
)
set "SCRIPT=%~dp0jardinero.py"
set "RUNTIME=%LOCALAPPDATA%\JardinZen\runtime.json"
set "CONFIG=%~dp0config.json"
py -3 "%SCRIPT%" ask --runtime "%RUNTIME%" --config "%CONFIG%" --query "%~1"
exit /b %ERRORLEVEL%
