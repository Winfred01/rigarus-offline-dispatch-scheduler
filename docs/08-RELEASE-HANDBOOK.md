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
