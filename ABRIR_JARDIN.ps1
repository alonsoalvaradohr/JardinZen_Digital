$ErrorActionPreference = 'Stop'
$port = 8765
$url = "http://127.0.0.1:$port"
$script = Join-Path $PSScriptRoot 'visor.py'
$python = $null
$prefix = @()

$response = $null
try { $response = Invoke-WebRequest -Uri "$url/api/overview" -TimeoutSec 1 -UseBasicParsing } catch { }
if ($response -and $response.StatusCode -eq 200 -and ($response.Content | ConvertFrom-Json).app -eq 'JardineroVisor') {
    $health = $null
    try { $health = Invoke-RestMethod -Uri "$url/api/health" -TimeoutSec 2 } catch { }

    # HTML se sirve desde disco, pero Python conserva sus imports en memoria.
    # Reiniciar solo este visor; nunca terminar un proceso ajeno del puerto.
    $connections = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
    foreach ($connection in $connections) {
        $process = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $connection.OwningProcess) -ErrorAction SilentlyContinue
        $runtimeProcess = if ($process) { Get-Process -Id $process.ProcessId -ErrorAction SilentlyContinue } else { $null }
        $sourceNewer = $false
        foreach ($sourcePath in @($script, (Join-Path $PSScriptRoot 'propuestas.py'), (Join-Path $PSScriptRoot 'visor.html'))) {
            if ($runtimeProcess -and (Test-Path -LiteralPath $sourcePath) -and (Get-Item -LiteralPath $sourcePath).LastWriteTime -gt $runtimeProcess.StartTime) { $sourceNewer = $true }
        }
        if ($process -and $runtimeProcess -and $process.Name -match '^python(w)?\.exe$' -and $process.CommandLine -match [regex]::Escape($script) -and -not $sourceNewer -and $health -and $health.proposal_api -and $health.proposal_build -eq 'jz018-paginated-v3') {
            Start-Process $url
            exit 0
        } elseif ($process -and $runtimeProcess -and $process.Name -match '^python(w)?\.exe$' -and $process.CommandLine -match [regex]::Escape($script)) {
            Stop-Process -Id $process.ProcessId -Force -ErrorAction Stop
        } else {
            throw "El puerto $port lo ocupa otro proceso; no se detuvo."
        }
    }
}

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

$logDir = Join-Path $env:LOCALAPPDATA 'JardinZen\logs'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$stdoutLog = Join-Path $logDir 'visor.stdout.log'
$stderrLog = Join-Path $logDir 'visor.stderr.log'
$pythonArgs = @($prefix) + @('-B', '-u', $script)
Start-Process -FilePath $python -ArgumentList $pythonArgs -WorkingDirectory $PSScriptRoot -WindowStyle Hidden `
    -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog | Out-Null
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 400
    try {
        $health = Invoke-RestMethod -Uri "$url/api/health" -TimeoutSec 1
        if ($health.proposal_api -and $health.proposal_build -eq 'jz018-paginated-v3') { $ready = $true; break }
    } catch { }
}
if (-not $ready) {
    $diagnostic = ''
    if (Test-Path -LiteralPath $stderrLog) { $diagnostic = (Get-Content -LiteralPath $stderrLog -Tail 8 -ErrorAction SilentlyContinue) -join ' ' }
    throw "El visor no respondió con el build esperado en $url. $diagnostic"
}
Start-Process $url
