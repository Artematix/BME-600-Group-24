# start_ollama_server.ps1 : start the Ollama server for parallel runs (Phase 1 text step).
#
# What it does
# 1. Stops the Ollama tray app and any server or stray llama-server.exe (they hold GPU memory).
# 2. Starts `ollama serve` detached with OLLAMA_NUM_PARALLEL (default 8) and flash attention on.
# 3. Waits until the server answers, then prints `ollama ps`.
# Logs: fda-maude/clean/logs/ollama_serve_<timestamp>.log (gitignored folder).
#
# Usage (PowerShell, from the repo root):
#   powershell -ExecutionPolicy Bypass -File fda-maude/scripts/start_ollama_server.ps1 [-Parallel 8]
# When finished with long runs: Stop-Process -Name ollama -Force ; then start Ollama from the Start menu again.

param(
    [int]$Parallel = 8,
    [string]$LogDir = "fda-maude/clean/logs"
)

$ErrorActionPreference = "Continue"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"

# 1. stop everything that could hold the GPU
foreach ($name in @("ollama app", "ollama", "llama-server")) {
    $procs = Get-Process -Name $name -ErrorAction SilentlyContinue
    if ($procs) {
        Write-Output ("stopping {0} x{1}" -f $name, $procs.Count)
        $procs | Stop-Process -Force -ErrorAction SilentlyContinue
    }
}
Start-Sleep -Seconds 3
$left = Get-Process -Name "llama-server" -ErrorAction SilentlyContinue
if ($left) { Write-Output "WARNING: llama-server.exe still running" } else { Write-Output "no llama-server.exe left" }

# 2. start the server detached
$env:OLLAMA_NUM_PARALLEL = "$Parallel"
$env:OLLAMA_FLASH_ATTENTION = "1"
$env:OLLAMA_KEEP_ALIVE = "30m"
$out = Join-Path $LogDir ("ollama_serve_{0}.out.log" -f $stamp)
$err = Join-Path $LogDir ("ollama_serve_{0}.log" -f $stamp)
$p = Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden -PassThru -RedirectStandardOutput $out -RedirectStandardError $err
Write-Output ("started ollama serve pid {0}, OLLAMA_NUM_PARALLEL={1}, flash attention on; log {2}" -f $p.Id, $Parallel, $err)

# 3. wait for it
$ok = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    try {
        $v = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/version" -TimeoutSec 2
        Write-Output ("server up: ollama {0}" -f $v.version)
        $ok = $true
        break
    } catch { }
}
if (-not $ok) { Write-Output "ERROR: server did not answer in 30 s"; exit 1 }
ollama ps
