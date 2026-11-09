param(
  [switch]$RunOnly,
  [switch]$NoSchedule
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$state = Join-Path $env:LOCALAPPDATA 'JardinZen'
$runtime = Join-Path $state 'runtime.json'
$config = Join-Path $repo 'config.json'
$pyArgs = @()

function Find-Python {
    $paths = @(
      (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'),
      (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'),
      (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python314\python.exe')
    )
    foreach ($p in $paths) {
        if (Test-Path -LiteralPath $p) { return @{ Exe=$p; Prefix=@() } }
    }
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($py) {
        & $py.Source -3 -c 'import sys; exit(sys.version_info < (3, 10))' 2>$null
        if ($LASTEXITCODE -eq 0) { return @{ Exe=$py.Source; Prefix=@('-3') } }
    }
    $cmd = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($cmd) {
        & $cmd.Source -c 'import sys; exit(sys.version_info < (3, 10))' 2>$null
        if ($LASTEXITCODE -eq 0) { return @{ Exe=$cmd.Source; Prefix=@() } }
    }
    return $null
}

function Find-Ollama {
    $exe = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
    if (Test-Path -LiteralPath $exe) { return $exe }
    $tool = Get-Command ollama.exe -ErrorAction SilentlyContinue
    if ($tool) { return $tool.Source }
    return $null
}

function Check-Api {
    try {
        $null = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -Method Get -TimeoutSec 5
        return $true
    } catch { return $false }
}

function Install-IfMissing([string]$id) {
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $winget) { throw "Falta $id y winget no esta disponible. Instalar manualmente y repetir INICIAR.cmd." }
    Write-Host "Instalando dependencia $id mediante winget..."
    & $winget.Source install --id $id --exact --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw "No se pudo instalar $id. No se movio ningun archivo." }
}

New-Item -ItemType Directory -Path $state -Force | Out-Null
$p = Find-Python
if (-not $p) {
    if ($RunOnly) { throw 'Python no encontrado; repetir INICIAR.cmd' }
    Install-IfMissing 'Python.Python.3.12'
    $p = Find-Python
    if (-not $p) { throw 'Python instalado pero no detectado; abrir nueva terminal y repetir INICIAR.cmd.' }
}
$pyArgs = @($p.Prefix)
$exe = [string]$p.Exe

if (-not $RunOnly) {
    # Windows Known Folder: Descargas y Escritorio (respeta redirecciones).
    $reg = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders'
    $guid = '{KNOWNFOLDERID_DOWNLOADS}'
    $rawDownloads = (Get-ItemProperty -LiteralPath $reg -ErrorAction Stop).$guid
    if (-not $rawDownloads) { throw 'No se pudo identificar Descargas desde Windows.' }
    $downloads = [Environment]::ExpandEnvironmentVariables($rawDownloads)
    $desktop = [Environment]::GetFolderPath('DesktopDirectory')
    foreach ($dir in @($downloads, $desktop)) {
        if (-not (Test-Path -LiteralPath $dir -PathType Container)) { throw "Ruta Windows invalida: $dir" }
    }
    $pots = @((Join-Path $downloads '00_MACETA'), (Join-Path $desktop '00_MACETA'))
    $garden = Join-Path $env:USERPROFILE 'JardinZen'
    $runtimeData = [ordered]@{ version=1; pots=$pots; garden_root=$garden; state_dir=$state }
    $temp = "$runtime.tmp"
    $runtimeData | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $temp -Encoding UTF8
    Move-Item -LiteralPath $temp -Destination $runtime -Force
    Write-Host 'F0: preparando directorios reales...'
    & $exe @pyArgs (Join-Path $repo 'jardinero.py') init --runtime $runtime --config $config
    if ($LASTEXITCODE -ne 0) { throw 'F0 fallida. No se instalan tareas programadas.' }
} elseif (-not (Test-Path -LiteralPath $runtime)) {
    throw 'F0 sin inicializar: ejecutar INICIAR.cmd'
}

if (-not $RunOnly) {
    $ollama = Find-Ollama
    if (-not $ollama) {
        Install-IfMissing 'Ollama.Ollama'
        $ollama = Find-Ollama
    }
    if (-not $ollama) { throw 'Ollama no encontrado. F0 completada, F1 bloqueada sin mover archivos.' }
    if (-not (Check-Api)) {
        Write-Host 'Iniciando Ollama local...'
        Start-Process -FilePath $ollama -ArgumentList @('serve') -WindowStyle Hidden | Out-Null
        $ok = $false
        for ($i=0; $i -lt 30; $i++) {
            Start-Sleep -Seconds 2
            if (Check-Api) { $ok = $true; break }
        }
        if (-not $ok) { throw 'Ollama no responde en localhost:11434. F1 bloqueada, sin migraciones.' }
    }
    $cfg = Get-Content -LiteralPath $config -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($model in @($cfg.classify_model, $cfg.embed_model)) {
        Write-Host "Verificando modelo local: $model"
        $models = (Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 10).models
        if ($model -notin @($models | ForEach-Object { $_.name })) {
            Write-Host "Descargando modelo $model (requiere internet y espacio de disco)..."
            & $ollama pull $model
            if ($LASTEXITCODE -ne 0) { throw "No se pudo descargar $model. F1 bloqueada, sin migraciones." }
        }
    }
}

# F1: ejecucion fisica de un lote seguro; siguientes lotes cada 15 min por tarea Windows.
Write-Host 'Jardinero: ejecutando lote...'
& $exe @pyArgs (Join-Path $repo 'jardinero.py') run --runtime $runtime --config $config
$runExit = $LASTEXITCODE

if (-not $RunOnly -and -not $NoSchedule) {
    try {
        $entry = Join-Path $repo 'EJECUTAR.cmd'
        $action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument ('/c ""{0}""' -f $entry) -WorkingDirectory $repo
        $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(60) -RepetitionInterval (New-TimeSpan -Minutes 60) -RepetitionDuration (New-TimeSpan -Days 3650)
        $settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 3) -StartWhenAvailable
        Register-ScheduledTask -TaskName 'JardinZen_Jardinero' -Action $action -Trigger $trigger -Settings $settings -Description 'Jardinero local; ingesta fisica desde dos macetas cada 15 minutos' -Force -ErrorAction Stop | Out-Null
        Write-Host 'F3: Tarea JardinZen_Jardinero instalada, periodo de 15 minutos.'
    } catch {
        Write-Warning "No se pudo instalar tarea programada: $($_.Exception.Message)"
        Write-Warning 'El primer lote ya se ejecuto; F3 sigue pendiente de programacion.'
        if ($runExit -eq 0) { $runExit = 4 }
    }
}
if ($runExit -ne 0) { Write-Warning "Estado: revisar $state\STATE.md (codigo $runExit)" }
Write-Host "Jardin: $env:USERPROFILE\JardinZen"
Write-Host "Estado: $state\STATE.md"
exit $runExit
