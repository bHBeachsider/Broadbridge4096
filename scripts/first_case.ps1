# Stock S0-cases only. -MockResponse is entirely offline; omit it only for an approved live run.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Export,
    [Parameter(Mandatory=$true)][string[]]$CaseId,
    [string]$RunRoot,
    [string]$Python = 'python',
    [string]$Foundry = (Join-Path (Split-Path $PSScriptRoot -Parent) '..\slm-foundry'),
    [string]$Key = 'C:\Users\bradu\Documents\ilyrium-autostudio\slm-foundry-key-v2.pem',
    [ValidateNotNullOrEmpty()][string]$MockResponse
)
$ErrorActionPreference = 'Stop'
$Repo = Split-Path $PSScriptRoot -Parent
$Pack = Join-Path $Repo 'packs\oil-gas'
$Batch = Join-Path $Pack 'scripts\batch_cases.py'
$Instance = 'i-0e5e1cbc7b1367566'
$Region = 'us-east-1'
$Utf8 = New-Object System.Text.UTF8Encoding($false)
$ExitCode = 0
$StartAttempted = $false
$Tunnel = $null
$OldUrl = $env:OLLAMA_URL
$OldModel = $env:OLLAMA_MODEL
if (-not $RunRoot) {
    $RunId = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8)
    $RunRoot = Join-Path $Pack "outputs\first-case\$RunId"
}
$RunRoot = [System.IO.Path]::GetFullPath($RunRoot)
try {
    $PrepareArgs = @($Batch, 'prepare', $Export, $RunRoot, '--case-id', ($CaseId -join ','))
    if ($MockResponse) { $PrepareArgs += @('--mock-response', $MockResponse) }
    & $Python @PrepareArgs
    if ($LASTEXITCODE -ne 0) { throw 'Batch preflight failed. Resolve the export/selection and choose a fresh run.' }
    $Revision = git -C $Repo rev-parse HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Cannot record Broadbridge revision' }
    [System.IO.File]::WriteAllText((Join-Path $RunRoot 'broadbridge_revision.txt'), "$Revision`n", $Utf8)
    if ($MockResponse) {
        # Do not probe AWS, SSH, Foundry, ports or any model endpoint on this path.
        & $Python $Batch run $RunRoot
        if ($LASTEXITCODE -ne 0) { throw 'One or more mock cases failed; inspect batch_results.json' }
    } else {
        if (-not (Test-Path -LiteralPath $Key -PathType Leaf)) { throw 'SSH key not found' }
        if (-not (Test-Path -LiteralPath (Join-Path $Foundry 'src\llm_client.py') -PathType Leaf)) { throw 'Foundry client not found' }
        $Revision = git -C $Foundry rev-parse HEAD
        if ($LASTEXITCODE -ne 0) { throw 'Cannot record Foundry revision' }
        [System.IO.File]::WriteAllText((Join-Path $RunRoot 'foundry_revision.txt'), "$Revision`n", $Utf8)
        $Listeners = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners()
        if ($Listeners | Where-Object { $_.Port -eq 11435 }) { throw 'Port 11435 is in use. Close the previous tunnel/session before starting a batch.' }
        $State = aws ec2 describe-instances --region $Region --instance-ids $Instance --query 'Reservations[0].Instances[0].State.Name' --output text
        if ($LASTEXITCODE -ne 0 -or "$State".Trim() -ne 'stopped') { throw 'Batch requires the existing instance to be stopped; another operator may be using it.' }
        $StartAttempted = $true
        aws ec2 start-instances --region $Region --instance-ids $Instance
        if ($LASTEXITCODE -ne 0) { throw 'EC2 start failed; attempting teardown' }
        aws ec2 wait instance-running --region $Region --instance-ids $Instance
        if ($LASTEXITCODE -ne 0) { throw 'EC2 did not reach running' }
        aws ec2 wait instance-status-ok --region $Region --instance-ids $Instance
        if ($LASTEXITCODE -ne 0) { throw 'EC2 health checks failed' }
        $PublicIp = aws ec2 describe-instances --region $Region --instance-ids $Instance --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($PublicIp) -or $PublicIp -eq 'None') { throw 'No current public IP' }
        $SshArgs = @('-i', ('"' + $Key + '"'), '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                     '-o', 'ExitOnForwardFailure=yes', '-o', 'ConnectTimeout=15', '-N', '-L',
                     '127.0.0.1:11435:localhost:11434', "ec2-user@$($PublicIp.Trim())")
        $Tunnel = Start-Process -FilePath 'ssh' -ArgumentList $SshArgs -PassThru -WindowStyle Hidden -RedirectStandardError (Join-Path $RunRoot 'ssh_stderr.log') -RedirectStandardOutput (Join-Path $RunRoot 'ssh_stdout.log')
        $env:OLLAMA_URL = 'http://localhost:11435'
        $env:OLLAMA_MODEL = 'qwen3:8b'
        $Deadline = (Get-Date).AddSeconds(60)
        $Tags = $null
        do {
            if ($Tunnel.HasExited) { throw 'SSH tunnel exited. Inspect ssh_stderr.log; verify the host key/SSH access manually.' }
            try { $Tags = Invoke-RestMethod -Uri "$env:OLLAMA_URL/api/tags" -Method Get -TimeoutSec 2 } catch { $Tags = $null }
            if ($null -ne $Tags) { break }
            Start-Sleep -Seconds 1
        } while ((Get-Date) -lt $Deadline)
        if ($null -eq $Tags) { throw 'Remote Qwen unreachable at http://localhost:11435; inspect the tunnel (see slm-foundry/docs/SLM_SERVING_BRIEF.md).' }
        if (-not ($Tags.models | Where-Object { $_.name -eq 'qwen3:8b' })) { throw 'Stock qwen3:8b is missing; no download is attempted' }
        $ModelInfo = Invoke-RestMethod -Uri "$env:OLLAMA_URL/api/show" -Method Post -ContentType 'application/json' -Body (@{model='qwen3:8b'} | ConvertTo-Json) -TimeoutSec 15
        [System.IO.File]::WriteAllText((Join-Path $RunRoot 'ollama_tags.json'), ($Tags | ConvertTo-Json -Depth 30), $Utf8)
        [System.IO.File]::WriteAllText((Join-Path $RunRoot 'ollama_model_info.json'), ($ModelInfo | ConvertTo-Json -Depth 30), $Utf8)
        & $Python $Batch run $RunRoot --foundry $Foundry
        if ($LASTEXITCODE -ne 0) { throw 'One or more cases failed; successful briefs and scorecards are preserved' }
    }
} catch {
    $ExitCode = 2
    Write-Warning $_.Exception.Message
    if (Test-Path -LiteralPath (Join-Path $RunRoot 'batch_manifest.json')) {
        try { [System.IO.File]::WriteAllText((Join-Path $RunRoot 'session_error.txt'), ($_.Exception.Message + "`n"), $Utf8) }
        catch { Write-Warning 'Could not save session_error.txt; retain the terminal error for review.' }
    }
} finally {
    try {
        if ($StartAttempted) {
            try {
                aws ec2 stop-instances --region $Region --instance-ids $Instance
                if ($LASTEXITCODE -ne 0) { throw 'Stop request failed' }
                aws ec2 wait instance-stopped --region $Region --instance-ids $Instance
                if ($LASTEXITCODE -ne 0) { throw 'Stopped state not confirmed' }
                [System.IO.File]::WriteAllText((Join-Path $RunRoot 'instance_stopped.txt'), ((Get-Date).ToUniversalTime().ToString('o') + "`n"), $Utf8)
            } catch {
                $ExitCode = 2
                Write-Warning "TEARDOWN FAILED: $($_.Exception.Message). Stop $Instance and confirm stopped in AWS before leaving."
                try { [System.IO.File]::WriteAllText((Join-Path $RunRoot 'teardown_error.txt'), ($_.Exception.Message + "`n"), $Utf8) }
                catch { Write-Warning 'Could not save teardown_error.txt; retain the terminal error for review.' }
            }
        }
    } finally {
        try {
            if ($null -ne $Tunnel) {
                try { Stop-Process -Id $Tunnel.Id -Force -ErrorAction Stop }
                catch { Write-Warning 'SSH process already exited or could not be closed; check the saved process/session.' }
            }
        } finally {
            $env:OLLAMA_URL = $OldUrl
            $env:OLLAMA_MODEL = $OldModel
        }
    }
}
if (Test-Path -LiteralPath (Join-Path $RunRoot 'batch_summary.md')) {
    Get-Content -LiteralPath (Join-Path $RunRoot 'batch_summary.md') -Encoding UTF8
    Write-Host "Run root: $RunRoot"
}
exit $ExitCode
