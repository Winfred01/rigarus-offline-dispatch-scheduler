$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
$root = Split-Path -Parent $PSScriptRoot
$output = Join-Path $root 'artifacts/sidecar'
Push-Location (Join-Path $root 'src/Rigarus.Backend')
try {
    uv run --locked --group bundle pyinstaller --noconfirm --onedir --console `
        --name Rigarus.Sidecar `
        --hidden-import uvicorn.lifespan.on `
        --distpath $output `
        --workpath (Join-Path $output 'build') `
        --specpath (Join-Path $output 'build') `
        rigarus_backend/sidecar.py
}
finally {
    Pop-Location
}
