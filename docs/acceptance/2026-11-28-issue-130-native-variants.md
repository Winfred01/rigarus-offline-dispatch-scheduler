# Issue130 — merged-main native 5→8 / 5→2 Restore acceptance

## Scope and source identity

This is actual visible Windows native interaction, not seeded Restore results,
an API substitute or offline VM acceptance. Runtime baseline
`8195f2ac273e6ef930845dbec4cbb688006920fa`; test checkout
`75c34230f7d46a2af269cd88c401a66f5eb461f5` adds only the
[pre-test checklist and plan](../design/2026-11-27-issue-130-native-variants.md).
PR134/136 were freshly verified human-merged/closed. Their final CI162/160 and
[main CI](https://github.com/Winfred01/rigarus-offline-dispatch-scheduler/actions/runs/46102413225)
passed. This new evidence branch does not append to those merged PRs.
No product code, schema, business rule, receipt validator or deadline changed.

Freshly reread AGENTS, DEV-DESIGN-CHECKLIST,00/09/02/03/05/10 affected Restore,
schema21 and authorization sections,130 design/implementation/acceptance,
official synthetic sample and130/135 implementation/Issues. At the baseline,
five00/09/02/03/05 document revisions are `1bf8341`; decisions/AGENTS are
`880c79b`; checklist is `d3b9bea`. Exact per-file hashes, full Git revisions,
UTC modification/read times remain in the local source inventory. Checkout
mtime is not business authority. Original November24 UI DOCX re-extracted and
L10/L12/L13 original images62/64/65 viewed: paragraphs54–58/64–68/69–73,
not page numbers. SHA256
`d8a7c0de16dcbbe3c0a4aafe62ab136b4ef4c58737c2fb6c6d818f7981cf743c`.
The complete original and images stay local under the owner's instruction.
No missing-source specification was invented.

## Environment, build and isolation

November28 UTC / November27 local start, Windows11Pro x64 25H2,
10.0.26200.9974. Fresh CIM/registry checks; IPv4 Internet connected.
Owned child of the actual test process reports WebView2 `158.0.4370.45`.
This is a development test host, not a disconnected or clean VM.
All artifacts retain product version0.1.0; no Release or installation performed.

| Final artifact | SHA256 |
| --- | --- |
| Actually tested standalone Release EXE | `85a31965f007117949a7c57130a8deba6893e4ba2e893f9ff509268727b5f30e` |
| Matching adjacent sidecar | `ec60aaa3d13bb9cebb18e7fa0194de5cb5a8f7d726dd3ec4601c3aca6d768de2` |
| New independent x64 NSIS, built but not installed | `3664dc5fc0913acf6c909d8883f2fe59eff0c80d6d467312a4117d3fac43210d` |

Final hashes were rechecked after all native runs. An early launch during NSIS
assembly was normally closed before any Restore; its intermediate EXE hashes
are not used as tested-artifact evidence. Bundle patch/restoration changes EXE
bytes after the direct Cargo build. Older candidate installers remain unchanged.

Two existing untouched official synthetic fixtures were verified by owned smoke
root, database UUID, source1, target revisions and coherent all-table baseline.
Database remains exactly `<smoke-root>/data/rigarus.db`; flags are process-only.
Source setup used official stores and source Apply, not pre-seeded Restore SQL,
receipts or pending. Both had zero Restore versions/receipts/pending initially.
Native test launch opted into Restore only in that isolated process; production
Apply/Restore/Publish remain closed. All subsequent reopen/Resolve/Archive runs
removed editor/Apply/Restore/fault write flags and retained only the smoke root.

| Case | Synthetic database UUID | Original request | Plan fingerprint |
| --- | --- | --- | --- |
| extension02 | a93ec70d-711e-4332-91a3-4ac787b5a1a6 | b6361acd-aacf-4eb6-9d97-4e7d3874132a | `46ccdac1b2ee92f99e44121fd4000d991ef82877b635518d34b16922b8cd226c` |
| shortening02 | 42fdfa98-af0d-481b-9c95-1b74a748f448 | a2964829-e000-4d7d-980d-38d80333d6c7 | `d92dcd56a42b0cd2acefc6b12b6584f3186ab4db656de0b60f41377de888e318` |

User's current A/B authorization covers verified isolated synthetic Confirm,
normal close/reopen, Resolve and Archive. Each exact environment was checked
before execution. No new platform refusal occurred for these completed actions;
no Replay or replacement request was used. Read-only host inventory needed normal
developer permissions after restricted CIM access failed; no OS setting changed.

## Reproducible actual native flow and SQL proof

Follow the existing [official sequence](../../samples/synthetic-only/desktop-draft-restore.md)
and [fault harness constraints](../../samples/synthetic-only/desktop-restore-faults.md).
For each independently prepared source1:

1. Launch the final matched EXE/sidecar in the verified smoke root. Open Schedule
   → Draft Restore, inspect immutable Before/After and prepare exact inverse.
   Inspect current/proposed records, stable IDs, original notes and actual staff.
2. In extension02, Escape before dispatch returned focus to the opener. Every SQL
   table equalled baseline; no pending, receipt, audit or Restore version. Reopen
   and prepare again. Shortening02 cancellation was covered on the earlier fixed
   preview candidate; it is not claimed as a fresh cancellation here.
3. Both real native reviews start0/34. Individually inspect/acknowledge all34
   Pending items, then independently check exact scope. No select-all or warning
   bypass. Missing Rig, driver, category, Foreman, staffing and unsupported rules
   remain Pending; acknowledgement is not proof or dispatch approval.
4. After observing34/34, scope checked and fully visible enabled Confirm, click
   exactly once. Real UI reports Committed and saved weekly data refreshed.
5. Independently verify SQLite in a coherent read transaction and the complete
   authoritative receipt: profile/key/operation/source, original payload,
   namespaced canonical payload SHA, plan/source/warning hashes, exact34 warning
   acknowledgements, inverse records/revisions and Pending/false flags.
6. Normal close and flag-free reopen: same original key, Retained Review explicitly
   not Current. Click native Resolve; full verified Committed, same SQL digest.
   Click native Archive only after proof: authoritative reread, flush, exact pending
   retirement. Compare all tables again; retain the independent archive.
7. Shortening02 was again closed/reopened flag-free after Archive: no pending or
   replacement key, archive persisted. Valid source1 is inspectable, Prepare stays
   disabled and production Restore/Publish remain closed. No new write occurred.

| Actual outcome | extension02,5→8 inverse | shortening02,5→2 inverse |
| --- | --- | --- |
| Restored originals | FullDay1–5 Draft rev3→4, original notes/Employee1 restored | FullDay1–5 Draft rev3→4; cancelled3–5 reactivated, original notes/Employee1 restored |
| Source additions | FullDay6–8 Draft rev1→Cancelled rev2; IDs/notes retained | None |
| Unrelated / legacy | FullDay9 and LegacyHalfDay1PM unchanged | FullDay6 and LegacyHalfDay1PM unchanged |
| Row/history counts | Day rows9 retained; history19→27 | Day rows6 retained; history16→21 |
| Source/Restore/receipt | source1 unchanged; exactly1 new Restore version and1 receipt | source1 unchanged; exactly1 new Restore version and1 receipt |
| Native Confirm/Resolve/Archive | PASS / PASS / PASS | PASS / PASS / PASS |

Before digests: extension
`ebca7fec5f06cd8dddfec54ee1deedab6c19ae6d699b0018372d106b4fa43d09`;
shortening
`1bdadd77b42c5a43f0e651f36ecc19b2ad7032f66d689dc3d25eba49ee7d9458`.
After Confirm/Resolve/Archive/final read-only inspections respectively remain:

- extension `0dc69c3838733d78a59f0a79b473a11cce0efc8ab7a66ac3e3bcacbe17824388`;
- shortening `4e62d13190d9da6bf9c4da9f1eb826303cac0a282031adda2c326a066d819fe5`.

All snapshots integrity_check=ok, foreign_key_check empty. Existing history and
members retained; only target business rows/member restoration, append history,
Restore version/receipt and sequence bookkeeping changed. No source JSON rewrite,
physical deletion, revision rewind or unrelated/legacy table mutation. Complete
result remains Validation Pending / Apply=false / Publish=false.

Archive SHA256: extension
`8b84d40d319947d501988833c7057c8e546419a07d200a849140565bc1fc6834`;
shortening `eea2fc01d241756838bf5b5cafe69d87c27256e7bbf58cfb38bf183332e6f7e4`.
Raw coherent snapshots/UI captures/journals/archives/logs remain local. Evidence
labels: extension02/shortening02, `merged-main-before`, `merged-after-confirm`,
`merged-native-verified`, `merged-after-resolve`, `merged-after-archive`,
`merged-final-ui`; original screenshots and local paths are not uploaded.

## Mixed records, saved facts and cancelled history

Fresh final-artifact native Job Schedule/Crew Board show separate projects/Crews
and Full Day versus Legacy PM. FullDay1 detail has original notes, recorded
Employee1 and recorded actual Rig1 **Context stale / Needs Review**; Rig proof is
not silently inherited. Actual native Locate exact saved card highlights FullDay1.
Separate LegacyHalfDay1 detail shows Project2/WorkItem3/Crew5, November24PM,
revision1 and original synthetic legacy note; its typed Locate highlights that
PM card, not FullDay1. Equal integer1 never aliases the other type.
Flag-free read-only FullDay editor loads cancelled6, revision2 and original long
note; immutable history shows revision2Cancelled and revision1Draft. Save disabled.
All follow-up SQL tables/digests unchanged. No new AM native view in this build,
Employee Week/search/export compatibility or new half-day editor is claimed.

## Fresh checks and commands

PASS locked `uv sync --locked --group bundle`, `npm ci`,
`dotnet restore Rigarus.sln --locked-mode`; Ruff check/format --check,
frontend format, TypeScript/Vite build, .NET whitespace --verify-no-changes,
Release build with0 warnings/errors. Full Python `unittest discover -s tests -v`:
**693 PASS,317.910s**, bounded900s wrapper319.835s; frontend `npm test`:
**103 PASS**; Rust Release locked custom-protocol:**27 PASS**,2.66s;
historical .NET:**35 PASS**. **858 distinct=693+103+27+35**.
Packaged sidecar:**18 PASS**,41.130s, repeated checks not added to858.
`cargo +1.95.0 fmt --check` and `cargo +1.95.0 fetch --locked` PASS.
`Build-RigarusSidecar.ps1`, locked Windows Release and Tauri NSIS build PASS.
This document-only branch adds no product tests or migrations. Final staged
privacy, Markdown links/UTF8/fences, whitespace and new-head Windows CI are
recorded in its Draft PR; a still-running run is never called passed.

## D01–D18 strict matrix for this final candidate

These statuses scope this exact final artifact. Earlier fault evidence in
[PR134's record](2026-11-27-issue-130-native-faults.md) and preview/blocker evidence
in [PR136's record](2026-11-27-issue-135-qualification-proof.md) remain separately
dated/hashes, not silently promoted to fresh fault reruns. Compound cases with
unexecuted native subcases stay NOT RUN even where individual parts passed.

| ID | Status | Actual evidence / gap |
| --- | --- | --- |
| D01 | PASS | Both real native5→8/5→2 exact inverse commits, stable IDs/staff/notes/new revisions, receipt and reopen proof |
| D02 | NOT RUN | Both34 independent initial unchecked warnings and scope PASS; extra/changed/missing negative GUI variants not rerun |
| D03 | NOT RUN | Prior native Stale and fixed-candidate Blocked retained; final-artifact wrong profile/source/blocker matrix not rerun |
| D04 | NOT RUN | Fresh extension Escape/focus/all-table equality PASS; all Cancel/X variants not run |
| D05 | NOT RUN | Fresh single Confirm PASS; double-click/in-flight close passed on prior fault artifact only |
| D06 | NOT RUN | Fresh normal reopen/Resolve PASS; real timeout passed on earlier fault artifact only |
| D07 | NOT RUN | Prior actual NotFound/original Replay preserved; final service-error/timeout variants not rerun |
| D08 | NOT RUN | Fresh automated exact-proof tests PASS; native full malformed/wrong-field/size matrix incomplete |
| D09 | NOT RUN | Fresh Rust real two-process guard/same-key namespaces PASS; complete native GUI contention not run |
| D10 | BLOCKED | Prior specific wire Archive Retry remains platform-refused; pending retained, no retry/bypass; full new storage matrix not run |
| D11 | NOT RUN | Fresh two complete Committed receipts/Archive PASS; sealed Rejected/flush passed on prior artifact only |
| D12 | NOT RUN | Fresh normal weekly refresh PASS; deliberate read-failure follow-through passed on earlier artifact only |
| D13 | NOT RUN | Fresh same-integer FullDay/Legacy PM, distinct projects, actual employee/Rig, two typed Locates and cancelled history PASS; fresh AM variant not run |
| D14 | NOT RUN | Long notes/visible warning scrolling/Escape focus PASS; complete keyboard/narrow/Narrator speech not run |
| D15 | NOT RUN | Fresh flag-free valid source1/disabled Prepare/no pending/SQL equality PASS; full wrong-root flag matrix automated only |
| D16 | NOT RUN |858 distinct+18 repeats/locked checks/build PASS; new evidence-head CI pending at record creation |
| D17 | PASS | Exact final-artifact native submit/reopen/Resolve/Archive, same-key proof and coherent integrity/history; host only |
| D18 | BLOCKED | No qualified licensed disconnected VM: install/upgrade/WebView2/OS reboot remain blocked |

Prior refused wire key16a2502d-ef0c-45cd-b466-657c37731b0f, profilee137227b,
was not reopened or retried. Read-only pending SHA remains
`d7885f16b0e8c5851f419835d9b307aad9ccd6c90bda8b69162efb901dd3c74f`.
Its Committed recovery basis is preserved, not reset to manufacture a pass.
No new product defect was demonstrated here. Stale cached UIA coordinates were
handled by fresh visible screenshots/scroll, not altered business logic or waits.
Next independent priorities: remaining unblocked malformed-receipt/native
concurrency/storage and accessibility subcases, then a legally usable offline VM.
Production Restore/Publish, customer Demo/UAT/deployment/delivery remain unapproved.
No merge, Issue closure, Release, real data or system-security change.
