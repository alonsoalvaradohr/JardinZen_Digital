@echo off
setlocal
if "%~1"=="" (
 echo Uso: BUSCAR.cmd "consulta"
 exit /b 2
)
set "SCRIPT=%~dp0jardinero.py"
set "RUNTIME=%LOCALAPPDATA%\JardinZen\runtime.json"
set "CONFIG=%~dp0config.json"
py -3 "%SCRIPT%" search --runtime "%RUNTIME%" --config "%CONFIG%" --query "%~1"
exit /b %ERRORLEVEL%
