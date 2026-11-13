# Local M0 engineering package

The internal build version is `0.0.1`. After Windows CI and the local checks, create the self-contained x64 package in the ignored `releases` directory. Publish into an empty output directory to avoid stale files.

```powershell
dotnet restore src/Rigarus.Desktop --locked-mode -p:SelfContained=true
dotnet publish src/Rigarus.Desktop -c Release -r win-x64 --self-contained true --no-restore -o releases/m0-win-x64
Compress-Archive -Path releases/m0-win-x64/* -DestinationPath releases/rigarus-m0-0.0.1-win-x64.zip
Get-FileHash releases/rigarus-m0-0.0.1-win-x64.zip -Algorithm SHA256
```

Extract the ZIP and launch `Rigarus.Desktop.exe`. Test the extracted build using the [M0 walkthrough](05-DEMO-ACCEPTANCE.md). Record the hash and Git commit with the verification evidence. A SHA-256 hash identifies a package. Code signing, an installer, and upgrade and restore tests are future work.

GitHub Releases and customer handoff require explicit authorization. Keep local data, raw diagnostics and original material out of all distribution artifacts.

## Local Python sidecar engineering package

Use x64 Windows, Python 3.13 and uv 0.10.12. Run from the repository root in PowerShell 7.

```powershell
./scripts/Build-RigarusSidecar.ps1
$env:RIGARUS_SIDECAR_TEST_EXE = (Resolve-Path 'artifacts/sidecar/Rigarus.Sidecar/Rigarus.Sidecar.exe').Path
Push-Location src/Rigarus.Backend
try {
    uv run --locked python -m unittest discover -s tests -p test_sidecar.py -v
}
finally {
    Pop-Location
    Remove-Item Env:RIGARUS_SIDECAR_TEST_EXE
}
```

The `Rigarus.Sidecar` output directory contains the executable and its bundled Python runtime. Keep the directory together. The tests start the packaged process with a temporary synthetic SQLite database and exercise its local access boundary, startup failure hint, note persistence and exit after the parent closes stdin. Record these as sidecar process tests.

## Tauri desktop preview

On a Windows x64 development machine, use Node.js 22.12 or newer in the 22.x line, Rust 1.95.0 with the MSVC x64 target, the C++ build tools with a Windows SDK, Python 3.13, uv 0.10.12, and WebView2. Run from the repository root.

```powershell
./scripts/Build-RigarusSidecar.ps1
Set-Location src/Rigarus.Tauri
npm ci
npm run format
cargo fmt --manifest-path src-tauri/Cargo.toml --check
npm run tauri -- build -- --locked
Get-FileHash 'src-tauri/target/release/bundle/nsis/Rigarus Dispatch_0.1.0_x64-setup.exe' -Algorithm SHA256
```

The NSIS installer embeds the WebView2 offline installer and includes the Python sidecar resources. Building requires access to dependency registries and bundle tools. The operator's desktop preview uses the included Python runtime. Run the [Tauri verification walkthrough](05-DEMO-ACCEPTANCE.md#tauri-demo-note-engineering-check) on a clean Windows 11 x64 machine before marking the offline installer criterion complete.
