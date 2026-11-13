# Inspects the Git index. Stage the intended commit before running locally.
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$files = @(git -c core.quotepath=false ls-files)
if ($LASTEXITCODE -ne 0 -or $files.Count -eq 0) {
    throw 'Could not read staged repository paths.'
}

$allowedRoot = '^(?:\.editorconfig|\.gitattributes|\.gitignore|README\.md|AGENTS\.md|Directory\.Build\.props|Rigarus\.sln|global\.json)$'
$allowedSource = '^(?:src|tests)/[A-Za-z0-9_.-]+/(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.(?:cs|xaml|csproj|json)$'
$allowedBackend = '^src/Rigarus\.Backend/(?:pyproject\.toml|uv\.lock|tests/fixtures/legacy_ef_schema\.sql|(?:rigarus_backend|tests)/(?:[A-Za-z0-9_]+/)*[A-Za-z0-9_]+\.py)$'
$allowedTauri = '^src/Rigarus\.Tauri/(?:index\.html|(?:package(?:-lock)?|tsconfig)\.json|src/[A-Za-z0-9_-]+\.(?:tsx|css)|src-tauri/(?:Cargo\.(?:toml|lock)|build\.rs|tauri\.conf\.json|icons/icon\.ico|src/[A-Za-z0-9_-]+\.rs))$'
$allowedDocs = '^(?:docs/|samples/synthetic-only/)(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.md$'
$allowedAutomation = '^(?:\.github/(?:workflows/ci\.yml|pull_request_template\.md|ISSUE_TEMPLATE/(?:config\.yml|feature\.yml|bug\.yml))|\.config/dotnet-tools\.json|scripts/[A-Za-z0-9_.-]+\.ps1)$'
foreach ($file in $files) {
    if ($file -match '(?i)(RIGARUS_OFFLINE_WINDOWS_PROJECT_PLAN|RIGARUS_DEVELOPMENT_DEMO_DELIVERY_PLAYBOOK|chat[-_ ]?export|/(?:data|attachments|logs|backups|imports|exports|bin|obj)/)' -or
        ($file -cnotmatch $allowedRoot -and $file -cnotmatch $allowedSource -and
         $file -cnotmatch $allowedBackend -and $file -cnotmatch $allowedTauri -and
         $file -cnotmatch $allowedDocs -and $file -cnotmatch $allowedAutomation)) {
        throw "Unexpected staged path: $file"
    }
}

$secretPattern = '(gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|AKIA[A-Z0-9]{16})'
$matches = @(git grep --cached -I -l -E -e $secretPattern -- .)
switch ($LASTEXITCODE) {
    0 { throw "Possible secret detected in staged files: $($matches -join ', ')" }
    1 { Write-Host "Privacy scan passed for $($files.Count) staged paths." }
    default { throw 'The staged content scan could not run.' }
}

# Git grep returns 1 for no matches. Report successful validation to the caller.
exit 0
