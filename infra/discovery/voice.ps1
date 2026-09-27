param(
    [ValidateSet('Install', 'Start', 'Stop', 'Status', 'Smoke', 'Ask', 'Transcribe', 'Speak')]
    [string]$Action = 'Status',
    [string]$Text,
    [string]$InputFile
)
$ErrorActionPreference = 'Stop'
$compose = @('compose', '--project-directory', $PSScriptRoot, '-f', (Join-Path $PSScriptRoot 'compose.yaml'))
$install = $compose + @('-f', (Join-Path $PSScriptRoot 'compose.install.yaml'))
$runtime = Join-Path $PSScriptRoot 'runtime'
New-Item -ItemType Directory -Force -Path $runtime | Out-Null

function Invoke-VoiceDocker([string[]]$DockerArgs) {
    & docker @DockerArgs
    if ($LASTEXITCODE -ne 0) { throw "Local voice Docker command failed (exit $LASTEXITCODE)." }
}

switch ($Action) {
    Install {
        Invoke-VoiceDocker ($install + @('build', 'speech'))
        # Recreate only this Compose project's network to enable the explicit download step.
        Invoke-VoiceDocker ($compose + @('down'))
        try {
            Invoke-VoiceDocker ($install + @('up', '-d', '--wait', 'interviewer'))
            Invoke-VoiceDocker ($install + @('run', '--rm', 'speech', 'bootstrap'))
        } finally {
            # Never leave the download-enabled network running after success or failure.
            Invoke-VoiceDocker ($install + @('down'))
        }
        Invoke-VoiceDocker ($compose + @('up', '-d', '--wait', 'interviewer'))
        Invoke-VoiceDocker ($compose + @('run', '--rm', 'speech', 'verify'))
    }
    Start { Invoke-VoiceDocker ($compose + @('up', '-d', '--wait', 'interviewer')) }
    Stop { Invoke-VoiceDocker ($compose + @('stop')) }
    Status { Invoke-VoiceDocker ($compose + @('ps', '-a')) }
    Smoke {
        Invoke-VoiceDocker ($compose + @('up', '-d', '--wait', 'interviewer'))
        Invoke-VoiceDocker ($compose + @('run', '--rm', 'speech', 'smoke'))
        Write-Host "Synthetic audio and results: $runtime\smoke"
    }
    Ask {
        if (-not $Text) { throw 'Supply -Text with one response to clarify.' }
        Invoke-VoiceDocker ($compose + @('run', '--rm', 'speech', 'ask', $Text))
    }
    Transcribe {
        if (-not $InputFile) { throw 'Supply -InputFile with an audio recording.' }
        $source = Get-Item -LiteralPath $InputFile
        if ($source.PSIsContainer -or $source.Length -gt 50MB) { throw 'Choose an audio file no larger than 50 MiB.' }
        $name = 'input-' + [guid]::NewGuid().ToString('N') + $source.Extension
        Copy-Item -LiteralPath $source.FullName -Destination (Join-Path $runtime $name)
        Invoke-VoiceDocker ($compose + @('run', '--rm', 'speech', 'transcribe', ('/work/' + $name)))
        Write-Host "Local input copy retained in $runtime\$name"
    }
    Speak {
        if (-not $Text) { throw 'Supply -Text for the spoken prompt.' }
        Invoke-VoiceDocker ($compose + @('run', '--rm', 'speech', 'speak', $Text, '/work/prompt.wav'))
        Write-Host "Audio: $runtime\prompt.wav"
    }
}
