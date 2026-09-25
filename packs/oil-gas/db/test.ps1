param([string]$Python = 'python')

# Uses only an explicitly exported URL. With none, start our own cached PG17 image.
$ErrorActionPreference = 'Stop'
$ownedContainer = $null
$ownedToken = [guid]::NewGuid().ToString('N')
$ownedName = "broadbridge-db-test-$ownedToken"
$priorUrl = $env:BROADBRIDGE_DATABASE_URL
$priorPipelineUrl = $env:BROADBRIDGE_PIPELINE_TEST_URL
$priorBytecode = $env:PYTHONDONTWRITEBYTECODE
$resultCode = 2
try {
    $env:PYTHONDONTWRITEBYTECODE = '1'
    if (-not $priorUrl) {
        & docker image inspect pgvector/pgvector:pg17 *> $null
        if ($LASTEXITCODE -ne 0) { throw 'Docker access and a cached pgvector/pgvector:pg17 image are required; this runner does not pull images.' }
        $ownedContainer = (& docker run --pull never --rm -d --name $ownedName --label "broadbridge.db-test=$ownedToken" -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_USER=broadbridge_test -e POSTGRES_DB=broadbridge_test -p '127.0.0.1::5432' pgvector/pgvector:pg17).Trim()
        if ($LASTEXITCODE -ne 0 -or $ownedContainer -notmatch '^[0-9a-f]{64}$') { throw 'Unable to start the owned test database container.' }
        $ready = $false
        for ($attempt = 0; $attempt -lt 60; $attempt++) {
            & docker exec $ownedContainer pg_isready -U broadbridge_test -d broadbridge_test *> $null
            if ($LASTEXITCODE -eq 0) { $ready = $true; break }
            Start-Sleep -Milliseconds 500
        }
        if (-not $ready) { throw 'Owned test database did not become ready.' }
        $binding = (& docker port $ownedContainer 5432/tcp).Trim()
        if ($LASTEXITCODE -ne 0 -or $binding -notmatch '^127\.0\.0\.1:(\d+)$') { throw 'Cannot verify loopback-only test database binding.' }
        $env:BROADBRIDGE_DATABASE_URL = "postgresql://broadbridge_test@127.0.0.1:$($Matches[1])/broadbridge_test"
        $env:BROADBRIDGE_PIPELINE_TEST_URL = "postgresql://broadbridge_test@127.0.0.1:$($Matches[1])/broadbridge_test_pipeline"
        & docker exec $ownedContainer createdb -U broadbridge_test broadbridge_test_pipeline
        if ($LASTEXITCODE -ne 0) { throw 'Cannot create the owned pipeline test database.' }
    }
    $testTemp = Join-Path ([System.IO.Path]::GetTempPath()) "broadbridge-db-pytest-$ownedToken"
    $testTargets = @((Join-Path $PSScriptRoot 'tests/test_db.py'), (Join-Path $PSScriptRoot '../tests'))
    if ($env:BROADBRIDGE_PIPELINE_TEST_URL) {
        $testTargets += (Join-Path $PSScriptRoot 'tests/test_pipeline.py')
    }
    & $Python -m pytest @testTargets -q -p no:cacheprovider --basetemp $testTemp --tb=short
    $resultCode = $LASTEXITCODE
} catch {
    Write-Error -ErrorAction Continue "Database test runner failed: $($_.Exception.Message)"
} finally {
    $env:BROADBRIDGE_DATABASE_URL = $priorUrl
    $env:BROADBRIDGE_PIPELINE_TEST_URL = $priorPipelineUrl
    $env:PYTHONDONTWRITEBYTECODE = $priorBytecode
    if ($ownedContainer -match '^[0-9a-f]{64}$') {
        $owner = (& docker inspect --format '{{ index .Config.Labels "broadbridge.db-test" }}' $ownedContainer 2>$null)
        if ($LASTEXITCODE -eq 0 -and $owner -eq $ownedToken) {
            & docker rm --force $ownedContainer *> $null
            if ($LASTEXITCODE -ne 0) { Write-Warning 'Owned test database cleanup failed.'; $resultCode = 2 }
        } else {
            Write-Warning 'Container ownership could not be reverified; cleanup refused.'
            $resultCode = 2
        }
    }
}
exit $resultCode
