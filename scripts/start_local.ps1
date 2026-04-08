param(
  [switch]$InstallDeps
)

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptDir '..'))
Set-Location $repoRoot

function Load-DotEnv([string]$path, [switch]$OverrideExisting) {
  if (-not (Test-Path $path)) {
    return
  }

  foreach ($rawLine in Get-Content $path) {
    $line = $rawLine.Trim()
    if (-not $line -or $line.StartsWith('#')) {
      continue
    }

    if ($line.StartsWith('export ')) {
      $line = $line.Substring(7).Trim()
    }

    $parts = $line -split '=', 2
    if ($parts.Count -ne 2) {
      continue
    }

    $key = $parts[0].Trim()
    $value = $parts[1].Trim()
    if (-not $key) {
      continue
    }

    if (
      $value.Length -ge 2 -and
      (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'")))
    ) {
      $value = $value.Substring(1, $value.Length - 2)
    }

    if (-not $OverrideExisting -and [System.Environment]::GetEnvironmentVariable($key, 'Process')) {
      continue
    }

    [System.Environment]::SetEnvironmentVariable($key, $value, 'Process')
  }
}

function Get-PythonExecutable() {
  foreach ($candidate in @('py', 'python')) {
    $command = Get-Command $candidate -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($command) {
      return $command.Source
    }
  }

  throw 'Python launcher not found (`py` or `python`).'
}

function Get-EnvInt([string]$name, [int]$defaultValue) {
  $raw = [System.Environment]::GetEnvironmentVariable($name, 'Process')
  if ($null -eq $raw) {
    $raw = ''
  }
  $parsed = 0
  if ([int]::TryParse($raw.Trim(), [ref]$parsed)) {
    return $parsed
  }
  return $defaultValue
}

function Get-EnvString([string]$name, [string]$defaultValue = '') {
  $raw = [System.Environment]::GetEnvironmentVariable($name, 'Process')
  if ($null -eq $raw) {
    return $defaultValue
  }

  $value = $raw.Trim()
  if (-not $value) {
    return $defaultValue
  }

  return $value
}

function Get-EnvFlag([string]$name, [bool]$defaultValue) {
  $raw = (Get-EnvString $name '').ToLowerInvariant()
  if (-not $raw) {
    return $defaultValue
  }
  return $raw -in @('1', 'true', 'yes', 'on')
}

function Get-ListenerProcessIds([int]$port) {
  @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique)
}

function Stop-Listener([int]$port) {
  foreach ($procId in Get-ListenerProcessIds $port) {
    if ($procId -and $procId -ne $PID) {
      Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    }
  }
}

function Assert-PortAvailable([int]$port, [string]$label) {
  $pids = Get-ListenerProcessIds $port
  if (-not $pids.Count) {
    return
  }

  $details = foreach ($procId in $pids) {
    $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
    if ($proc) {
      "$($proc.ProcessName)($procId)"
    } else {
      "PID $procId"
    }
  }

  throw "$label port $port is already in use by $($details -join ', '). Set SEPA_KILL_EXISTING_PORTS=1 to recycle it automatically."
}

function Get-MissingPythonModules([string]$pythonExecutable, [string[]]$modules) {
  $payload = $modules | ConvertTo-Json -Compress
  $output = & $pythonExecutable -c "import importlib.util, json; mods=json.loads(r'''$payload'''); missing=[m for m in mods if importlib.util.find_spec(m) is None]; print('\n'.join(missing))"
  if (-not $output) {
    return @()
  }
  return @($output -split "`r?`n" | Where-Object { $_.Trim() })
}

function Convert-ToSingleQuotedLiteral([string]$value) {
  return $value.Replace("'", "''")
}

$pythonExecutable = Get-PythonExecutable
$requirementsPath = Join-Path $repoRoot 'requirements.txt'

Load-DotEnv (Join-Path $repoRoot '.env.example')
Load-DotEnv (Join-Path $repoRoot '.env') -OverrideExisting

$apiHost = Get-EnvString 'API_HOST' '127.0.0.1'
$apiPort = Get-EnvInt 'API_PORT' 8000
$frontendPort = Get-EnvInt 'FRONTEND_PORT' 8080
$runAfterClose = Get-EnvFlag 'SEPA_RUN_AFTER_CLOSE' $true
$backfillDays = Get-EnvInt 'SEPA_BACKFILL_DAYS' 84
$killExistingPorts = Get-EnvFlag 'SEPA_KILL_EXISTING_PORTS' $false
$openBrowser = Get-EnvFlag 'SEPA_OPEN_BROWSER' $true
$installMode = if ($InstallDeps) { 'always' } else { (Get-EnvString 'SEPA_INSTALL_DEPS' 'auto').ToLowerInvariant() }

$apiUrl = "http://${apiHost}:${apiPort}"
$frontendUrl = "http://127.0.0.1:${frontendPort}"

Write-Host "[0/5] Checking local ports..."
if ($killExistingPorts) {
  Stop-Listener $apiPort
  Stop-Listener $frontendPort
  Start-Sleep -Milliseconds 500
} else {
  Assert-PortAvailable $apiPort 'API'
  Assert-PortAvailable $frontendPort 'Frontend'
}

Write-Host "[1/5] Checking Python dependencies..."
$requiredModules = @('fastapi', 'uvicorn', 'yfinance')
$missingModules = Get-MissingPythonModules $pythonExecutable $requiredModules
if ($installMode -eq 'never' -and $missingModules.Count) {
  throw "Missing Python modules: $($missingModules -join ', '). Either install them or remove SEPA_INSTALL_DEPS=never."
}

$shouldInstall = $installMode -eq 'always' -or ($installMode -eq 'auto' -and $missingModules.Count -gt 0)
if ($shouldInstall) {
  if (Test-Path $requirementsPath) {
    Write-Host "Installing dependencies from requirements.txt..."
    & $pythonExecutable -m pip install -r $requirementsPath | Out-Null
  } else {
    Write-Host "Installing missing modules: $($missingModules -join ', ')"
    & $pythonExecutable -m pip install @missingModules | Out-Null
  }
} else {
  Write-Host "Dependencies already available."
}

if ($runAfterClose) {
  Write-Host "[2/5] Running after-close pipeline..."
  & $pythonExecutable -m sepa.pipeline.run_after_close
} else {
  Write-Host "[2/5] Skipping after-close pipeline (SEPA_RUN_AFTER_CLOSE=0)."
}

if ($backfillDays -gt 0) {
  Write-Host "[2.5/5] Backfilling recent leader history..."
  & $pythonExecutable -m sepa.pipeline.backfill_history --days $backfillDays
} else {
  Write-Host "[2.5/5] Skipping leader history backfill (SEPA_BACKFILL_DAYS=0)."
}

$repoRootLiteral = Convert-ToSingleQuotedLiteral $repoRoot
$pythonExecutableLiteral = Convert-ToSingleQuotedLiteral $pythonExecutable
$apiCommand = "Set-Location '$repoRootLiteral'; & '$pythonExecutableLiteral' -m uvicorn sepa.api.app:app --host $apiHost --port $apiPort"
Write-Host "[3/5] Starting API server on ${apiHost}:${apiPort}..."
Start-Process powershell -ArgumentList '-NoExit', '-Command', $apiCommand

Start-Sleep -Seconds 2

Write-Host "[4/5] API health check..."
try {
  $response = Invoke-WebRequest "$apiUrl/api/health" -UseBasicParsing
  Write-Host "API OK: $($response.StatusCode)"
} catch {
  Write-Host "API failed. Check the uvicorn window."
  throw
}

$frontendCommand = "Set-Location '$repoRootLiteral'; & '$pythonExecutableLiteral' -m http.server $frontendPort --directory sepa/frontend"
Write-Host "[5/5] Starting frontend server on 127.0.0.1:${frontendPort}..."
Start-Process powershell -ArgumentList '-NoExit', '-Command', $frontendCommand

Start-Sleep -Seconds 1
if ($openBrowser) {
  Start-Process $apiUrl
}

Write-Host "Done. Dashboard at $apiUrl (API + frontend on same origin)"
