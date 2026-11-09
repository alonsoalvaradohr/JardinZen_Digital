$ErrorActionPreference = 'Stop'
$port = 8765
$url = "http://127.0.0.1:$port"
$script = Join-Path $PSScriptRoot 'visor.py'
$python = $null
$prefix = @()

try {
    $response = Invoke-WebRequest -Uri "$url/api/overview" -TimeoutSec 1 -UseBasicParsing
    if ($response.StatusCode -eq 200 -and ($response.Content | ConvertFrom-Json).app -eq 'JardineroVisor') {
        try {
            $proposalHealth = Invoke-WebRequest -Uri "$url/api/proposals/status" -TimeoutSec 2 -UseBasicParsing
            if ($proposalHealth.StatusCode -eq 200) { Start-Process $url; exit 0 }
        } catch { }
        # La página HTML se sirve desde disco, pero Python conserva las rutas
        # importadas en memoria. Si la API nueva falta, reiniciar solo nuestro
        # visor de este directorio; nunca terminar un proceso ajeno del puerto.
        $connections = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
        foreach ($connection in $connections) {
            $process = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $connection.OwningProcess) -ErrorAction SilentlyContinue
            if ($process -and $process.Name -match '^python(w)?\.exe$' -and $process.CommandLine -match [regex]::Escape($script)) {
                Stop-Process -Id $process.ProcessId -Force -ErrorAction Stop
            } else {
                throw "El puerto $port lo ocupa otro proceso; no se detuvo."
            }
        }
    }
} catch { }

$candidates = @(
    (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python314\python.exe')
)
foreach ($candidate in $candidates) {
    if (Test-Path -LiteralPath $candidate) { $python = $candidate; break }
}
if (-not $python) {
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        & $launcher.Source -3 -c 'import sys; raise SystemExit(sys.version_info < (3,10))' 2>$null
        if ($LASTEXITCODE -eq 0) { $python = $launcher.Source; $prefix = @('-3') }
    }
}
if (-not $python) {
    $command = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($command) {
        & $command.Source -c 'import sys; raise SystemExit(sys.version_info < (3,10))' 2>$null
        if ($LASTEXITCODE -eq 0) { $python = $command.Source }
    }
}
if (-not $python) { throw 'No se encontró Python 3.10 o superior. Instala Python o ejecuta INICIAR.cmd primero.' }

$pythonArgs = @($prefix) + @('"' + $script + '"')
Start-Process -FilePath $python -ArgumentList $pythonArgs -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 400
    try {
        $response = Invoke-WebRequest -Uri "$url/api/overview" -TimeoutSec 1 -UseBasicParsing
        if ($response.StatusCode -eq 200) { $ready = $true; break }
    } catch { }
}
if (-not $ready) { throw "El visor no respondió en $url. Revisa si el puerto $port está ocupado." }
Start-Process $url
