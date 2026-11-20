# run_full_extract.ps1 : start OR resume the full model run as a detached background process.
#
# What it does
# 1. Checks that the Ollama server answers; if not, starts it with 8 slots (start_ollama_server.ps1).
# 2. Warns if more than one llama-server.exe is alive (a zombie from a crashed run holds GPU memory).
# 3. Starts llm_extract.py detached. The script skips reports already in the output file, so running
#    this again after a crash or reboot simply continues (resume). Checkpoint: flush every 500 reports.
# 4. Prints the process id and the commands to check progress.
#
# Usage (PowerShell, from the repo root):
#   powershell -ExecutionPolicy Bypass -File fda-maude/scripts/run_full_extract.ps1            # start or resume v3
#   powershell -ExecutionPolicy Bypass -File fda-maude/scripts/run_full_extract.ps1 -Version v3 -Parallel 8
# Progress:  Get-Content fda-maude/clean/logs/text_extract_v3.log -Tail 3
# Rows done: (Get-Content fda-maude/clean/text_extract_v3.jsonl | Measure-Object -Line).Lines
# Stop:      Stop-Process -Id <pid>   (then run this script again to resume)

param(
    [string]$Version = "v3",
    [int]$Parallel = 8,
    [int]$NumCtx = 6144,
    [string]$InputFile = "fda-maude/clean/run_set.csv.gz",
    [string]$RegexCsv = "fda-maude/clean/regex_run_set.csv",
    [string]$LogDir = "fda-maude/clean/logs"
)

$ErrorActionPreference = "Continue"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$output = "fda-maude/clean/text_extract_$Version.jsonl"
$log = Join-Path $LogDir "text_extract_$Version.log"

# 1. server
$up = $false
try { $v = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/version" -TimeoutSec 3; $up = $true; Write-Output ("ollama server up: {0}" -f $v.version) } catch { }
if (-not $up) {
    Write-Output "ollama server not answering: starting it with $Parallel slots"
    powershell -ExecutionPolicy Bypass -File fda-maude/scripts/start_ollama_server.ps1 -Parallel $Parallel
}

# 2. zombie check
$runners = @(Get-Process -Name "llama-server" -ErrorAction SilentlyContinue)
if ($runners.Count -gt 1) { Write-Output ("WARNING: {0} llama-server.exe processes alive; a zombie may hold GPU memory. Check `ollama ps` says 100% GPU." -f $runners.Count) }
else { Write-Output ("llama-server.exe processes: {0}" -f $runners.Count) }

# 3. start detached
if (-not (Test-Path $InputFile)) { Write-Output "ERROR: input $InputFile missing (run build_run_set.py)"; exit 1 }
if (-not (Test-Path $RegexCsv)) { Write-Output "ERROR: regex csv $RegexCsv missing (run extract_regex.py on the run set)"; exit 1 }
$args = @("fda-maude/scripts/llm_extract.py", $InputFile, $output,
          "--prompt-version", $Version, "--parallel", "$Parallel", "--num-ctx", "$NumCtx",
          "--checkpoint-every", "500", "--tag", "full_$Version", "--regex-csv", $RegexCsv, "--log", $log)
$out = Join-Path $LogDir ("text_extract_{0}_{1}.out.log" -f $Version, $stamp)
$err = Join-Path $LogDir ("text_extract_{0}_{1}.err.log" -f $Version, $stamp)
$p = Start-Process -FilePath "python" -ArgumentList $args -WindowStyle Hidden -PassThru -RedirectStandardOutput $out -RedirectStandardError $err
Write-Output ("started llm_extract.py pid {0}; output {1}; progress log {2}" -f $p.Id, $output, $log)
Write-Output "check progress:  Get-Content $log -Tail 3"
