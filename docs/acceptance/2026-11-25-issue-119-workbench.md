# Issue119 — Full Day weekly workbench engineering evidence

## Scope and sources

First read-only slice of #99/#16, based on main
`6d93916c5891b1b988996ff683c659712c3b7c43` after human merge of PR118.
Pre-code plan commit `6c26d8f`; branch `codex/issue-119-day-workbench`.
Repository visibility was PUBLIC. Existing root edits were preserved in place;
all development used an independent worktree. No original design, database,
binary, customer file or raw diagnostic is included in this record.

The [Design Compliance Checklist](../design/2026-11-25-issue-119-workbench-checklist.md)
records the actual source revisions and inspected original figures. AGENTS
d3b9bea; plan/playbook/model/acceptance 7604d2a; architecture79e14eb;
client decisions f966ad7. Latest accessible local original UI design November24
was freshly read, with L01/image53, L03/image55 and L14/image66 actually viewed.
Prototype half-day/Validated/active Apply examples do not override confirmed
Full Day and Pending gates. Complete DOCX remains local.

## Implemented behavior and compatibility

- Default Job Schedule / Crew Board show a coherent saved week containing
  FullDayDraft and raw LegacyHalfDay records. Slots, notes, IDs, revisions,
  actual workers and recorded actual Rig remain separate; Home Crew is reference
  roster, not attendance. No legacy conversion, estimate deduction or auto Rig.
- Existing independent calendar/personnel/driver/capability/Rig/weekend checks
  supply explanations. Matched calendars do not certify the whole assignment.
  Every card and response stays Pending, applyable=false, publishable=false.
- Locate uses record kind plus ID, re-reads the current target and its entire
  week in one snapshot, closes source detail/review, preserves compatible filters
  and focuses the exact namespaced card. Missing/cancelled/unknown kinds fail;
  no integer-only fallback. Workbench also exposes the merged read-only
  recommendation dialog; preview does not add saved/reserved grid records.
- Schema18 is unchanged. GET-only endpoints and one fixed authenticated Tauri
  command; day writers remain disabled by default. One query-only pinned SQLite
  transaction, shared100k read-unit/64MiB budget,30second SQL/final deadline,
  at most7 local dates and100 Crews. Limits fail explicitly, never truncate to
  apparently safe data. The view fingerprint identifies the loaded projection,
  not complete source freshness or Apply authorization.
- Legacy half-day CRUD remains behind an explicit compatibility entry. The
  historical verifier now optionally enters it when Job Schedule exposes that
  entry, retaining all original assertions. Full historical native suite was
  NOT RUN; mock harness success does not certify native timing of this hook.

## Commands and automated results

Executed on Windows11 x64, Python3.13.7, Node22.20, Rust1.95.0/MSVC and.NET10.
Local wrappers preserve exact commands, exit codes, limits and elapsed times in
the ignored `day-workbench-evidence` directory. No dependency lock changed.

| Command / check | Result |
| --- | --- |
| `uv sync --locked --group bundle`; `npm ci`; `dotnet restore Rigarus.sln --locked-mode`; Cargo locked build | PASS |
| `uv run --locked ruff check`; `uv run --locked ruff format --check` | PASS;124 files formatted |
| `uv run --locked python -m unittest discover -s tests -v` | PASS;566 tests,205.555s, no skips; wrapper206.661s/900s limit |
| Focused `test_schedule_workbench.py` | PASS;11 tests; final wrapper7.126s/180s limit |
| Packaged sidecar `test_sidecar.py` with isolated EXE | PASS;15 tests,23.263s; wrapper23.946s/900s limit; subset repeated, not extra distinct tests |
| `npm run format`; `npm test`; `npm run build` | PASS;56 tests, TypeScript and Vite production build |
| `cargo +1.95.0 fmt --check`; locked release build and release tests with `tauri/custom-protocol` | PASS;8 Rust tests |
| `dotnet format whitespace ... --verify-no-changes --no-restore`; Release build/test | PASS;35 tests, no skips; historical compatibility only |
| Direct Windows PowerShell5.1 `Test-TauriAcceptanceHarness.ps1` after verifier navigation hook | PASS; synthetic harness, not native GUI |

Total665 distinct backend/frontend/Rust/.NET tests passed. New coverage includes
same integer across record kinds, notes/slots, actual cross-kind personnel
conflict, blocked calendar, missing/cancelled/moved targets, year1/year9999,
budget/source errors, query-only transaction, concurrent atomic metadata edits,
logical data preservation, closed writer gate, authenticated packaged requests
and sidecar restart. Frontend covers mixed cell projection, filter revelation,
date boundaries, typed cue lifetime and late-response epochs. Existing tests
also run; pure helper tests are not full React/native scenario coverage.

Initial failures were corrected before passing: strict JSON-integer type used
for an HTTP path, synthetic fixture argument mismatch, Node extensionless TS
test imports and unavailable reqwest query feature. Rust reused the existing
encoded URL helper; no new dependency was needed. One restricted local focused
run stalled and was interrupted, then passed under a bounded180second wrapper.
Final source review corrected same-week Today/Go request invalidation so it
always triggers a new bounded read; related builds/tests were rerun.

## Observed native Windows results

Actual Tauri release executable with its own packaged sidecar, synthetic-only
isolated profile, normal visible window. Host Windows11 Pro25H2 build26200.9974,
WebView2 and developer tools already present, network CONNECTED. This is not an
installer, clean VM, ordinary dispatcher account or offline deployment test.

Fixture: one Project/WorkItem, nine Crews, one actual employee; two Full Day
Drafts and two legacy PM records. FullDayDraft#1 and LegacyHalfDay#1 deliberately
share integer1. Separate legacy#2 overlaps the actual worker on FullDayDraft#1.

Reproduce with authorized synthetic fixtures: launch isolated profile → Job
Schedule November22–28 → open FullDayDraft#1 → Locate → Enter → correct detail
→ close → open LegacyHalfDay#1 → Locate → Enter → legacy PM detail → read-only
Auto-Recommend (explicit Remaining Days1, Crew03) → close → Crew Board → focus
table and End → inspect Crew09 November27 → Legacy compatibility → close app.

| Native scenario | Result and actual evidence |
| --- | --- |
| Seven dates, mixed saved records, distinct same-ID cards/details | PASS; blue Full Day vs amber legacy PM, exact separate notes/IDs |
| Actual worker conflict, missing driver/staffing/Rig/Foreman/category and matched calendar | PASS; independent Blocked/Pending reasons, no false-safe overall badge |
| Detail Locate and keyboard focus for both kinds sharing integer1 | PASS; Enter reopened the correct FullDayDraft#1 and LegacyHalfDay#1 respectively |
| Real recommendation from workbench detail | PASS; Crew03 November25→25,1/1days; Rig unassigned, Pending, Apply/Publish disabled; cancel writes nothing |
| Crew Board reference roster vs actual borrowed worker | PASS; Crew01 Home roster separate from legacy Crew02 actual attendance |
| Last Crew and sticky date/header alignment | PASS using table focus/End; Crew09 Full Day Draft on November27; complete wheel/scrollbar journey NOT RUN |
| Legacy compatibility entry and raw retained half-days | PASS; old board and notes/workers retained, no new Full Day editing implied |
| Final rebuilt candidate reopen and same-week Today | PASS;4 mixed saved records retained, same week returned without stuck loading; no artificially delayed native race induced |
| Layout comparison against original L01/L03/L14 | PASS for this read-only hierarchy; initial toolbar consumed grid height, corrected to collapsed tools and internal flex scroll |
| Normal close, logical records/integrity/FKs and owned process exit | PASS; initial/final logical digest identical, integrity=ok,0 FK errors, no owned app/sidecar remaining |
| Native cross-week filter-clearing Locate, induced HTTP failure/races, reduced motion and exact cue duration | NOT RUN; selected helper/API cases automated only |
| Hidden supervisor, narrow viewport and screen reader | NOT RUN |
| Full Employee Week/Availability/staffing/legacy-write native regression | NOT RUN on this candidate |
| Offline install, upgrade, VM/host reboot, uninstall/reinstall and clean-device test | NOT RUN; no earlier package result borrowed |
| Customer Demo/UAT and production approval | NOT RUN / NOT APPROVED |

Final native EXE SHA256:
`105511fd2d10467c4afef37c4bff92676842b6bb7d7e3bfab5f6e1544f4ff2e9`.
First corrected-layout executable
SHA256 was `4ff9dd6afa07bfec8b191c8bee2da67f38cfb190e568cf422528d37d8257c20d`;
the subsequent navigation fix was rebuilt separately. Initial/final synthetic
logical digest, also unchanged after the final navigation/reopen check:
`215980577870da8848b1be9a9e41a912ce037e4bc5a1da717193b7f17a474f8d`.
Native screenshots were inspected, not uploaded. Full logs and database remain
local. A restricted process-query failure was not accepted as evidence; a
successful authorized read-only process check confirmed zero remaining owned
processes.

## Delivery gates and unfinished operator loop

Staged privacy PASS for367 indexed paths; `git diff --cached --check` PASS.
Documentation UTF-8/fences/local-link checks PASS for10 files and153 links.
Exact-head remote Windows CI is reported in the PR after execution; pending CI
is not a pass.
Build artifact SHA is archive identity, not installed executable/installer SHA.

Independent daily create/edit/cancel with safe save/revisions/recovery is #120,
not implemented here. Global Schedule search still lists legacy records;
Full Day typed Locate is available through the workbench. New multi-day strips,
daily Employee Week, Foreman emphasis and the wider #99/#16 UI are incomplete.
Human Apply/revalidation, locks/Before-After, recoverable published versions and
formal company/Crew/employee PDF/Excel remain later slices. No recommendation
is auto-applied, no Issue closed, no PR merged or Release published.

Engineering checks, human review, offline deployment acceptance, customer UAT
and production permission remain separate gates.
