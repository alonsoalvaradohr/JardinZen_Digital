@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$port=8765; $script=[regex]::Escape((Join-Path '%~dp0' 'visor.py')); $connections=Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue; foreach($connection in $connections){$process=Get-CimInstance Win32_Process -Filter ('ProcessId='+$connection.OwningProcess) -ErrorAction SilentlyContinue; if($process -and $process.Name -match '^python(w)?\.exe$' -and $process.CommandLine -match $script){Stop-Process -Id $process.ProcessId -Force; Write-Host 'Visor Jardin detenido.'; exit 0}}; Write-Host 'No se encontro un visor Jardin activo en el puerto 8765.'"
pause
