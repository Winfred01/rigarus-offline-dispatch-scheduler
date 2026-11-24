# Issue #25 — explicit capability requirements engineering evidence

Baseline main `860e02d01c515fa8883c17759e9e1dc6fa81c205` includes human-merged
PR96. Isolated codex/issue-25-capability-validation; Design-First commit eee3081
preceded product code. See [source inventory/plan](../design/2026-11-24-issue-25-capability-checklist.md).
PUBLIC repository; synthetic source/data and sanitized engineering evidence.
Issue25 remains Open/partial; no company policy or customer acceptance is invented.

## Implemented

Pure validate_capabilities consumes explicit dated actual workers, Crew/WorkItem
context, WorkItem requirements and separate qualification evidence. Requirements
have no defaults: positive minimum members, three nonnegative Level minima,
explicit Exact/AtLeast mode and explicit exact-code/count list. Counts are
independent and may overlap, not disjoint role allocation. An explicitly empty
qualification list is recorded policy, not the missing-policy fallback.
Level never implies certification and qualification never changes recorded Level.

The report identifies real Project/WorkItem/Crew/Assignment, policy change ID,
required values, confirmed/possible Employee IDs, states and reasons. Active,
Available, nonconflicting actual workers supply definite capacity. Unknown
metadata/availability/qualification stays possible only; inactive, Unavailable
or double-booked workers cannot count. A known possible upper bound below the
explicit minimum blocks; enough definite workers satisfies that subcheck.
Missing policy or empty/unconfigured workers stays Pending. Civil/Tower mismatch
and inactive Crew block; Small/Other mapping is Pending.

Foreman appointment/eligibility is not dated attendance. Effective-date, promotion,
merger and presence rules remain unresolved, so Foreman and all otherwise clear
overall reports remain Pending. This per-Crew visit scope does not certify
simultaneous multi-Crew work or project completion. No actual worker/visit/master
record is changed by validation. Every result keeps Apply=false / Publish=false.

Internal CapabilityEvidenceStore records explicit company-confirmed assertions
with references, expected revision, dated range/cells, immutable owner/history,
same-value/reference no-op and transactional rollback. Schema12's three new tables
are necessary because no persisted requirement/separate qualification source
existed. No existing employee Level/DriverStatus/Home Crew, staffing, assignment,
calendar, driver evidence or Foreman history is rewritten. Confirmation is a
recorded assertion, not authenticated authority or legal certification.
No capability UI/API or company defaults are seeded.

Snapshot v4 adds related WorkItem parent/type/policy owner/revision/cells, every
horizon Crew's type/active state and related employees' qualification owners/
native revisions/cells on the same pinned read-only connection and fingerprint.
Malformed payload/context fails without a fingerprint; duplicate JSON keys reject.
Other-Crew/Project policy, qualification and master changes can make old inputs
Stale. Rebuild v3 objects. Read-only calculation never upgrades an old database.

Pure evaluation indexes evidence and deterministically sorts, without pairwise
worker comparisons. Aggregate evidence and assessment work are each bounded to
100,000 units, at most32 qualification requirements; exceeding a bound rejects
without a partial report. Qualification owner reads are also bounded.

## Reproduce / actual stored example

From src/Rigarus.Backend in locked Python3.13 / uv0.10.12:

```powershell
uv sync --locked --group bundle
uv run --locked ruff check
uv run --locked ruff format --check
uv run --locked python -m unittest discover -s tests -p "test_capability*.py" -v
uv run --locked python -m unittest discover -s tests -q
```

Executed Store-backed synthetic fixture: WorkItem1/Project1/Crew1, actual Employee1
borrowed from its different Home Crew, Level2, recorded Available at November23 AM.
Explicit requirements: members1, Exact Level minima(0,1,0), SYN-Q count1.
Separate SYN-Q Verified evidence was recorded and re-read from SQLite.

```text
MinimumStaffing required=1 confirmed=1 possible=1 Satisfied
SkillsLevel1 required=0 confirmed=0 possible=0 Satisfied
SkillsLevel2 required=1 confirmed=1 possible=1 Satisfied
SkillsLevel3 required=0 confirmed=0 possible=0 Satisfied
Qualification:SYN-Q required=1 confirmed=1 possible=1 Satisfied
Foreman=Pending; overall=Pending; Apply=false; Publish=false
After explicit minimum=2: Blocked, required=2 confirmed=1 possible=1
```

No industry/legal meaning is assigned to synthetic SYN-Q. Generated date options
remain unstaffed: PR91 MinimumStaffing/Skills/Qualifications/Foreman stays Pending,
even when saved-Draft subchecks pass. The wrapper exposes
`capability_validation` beside personnel/driver reports, not safety passes for
unrelated proposed dates.

## Actual gates

Connected Windows11 developer host build26200 with developer tools, temporary
synthetic DBs only. No customer database opened or migrated.

| Gate / scenario | Result |
| --- | --- |
| New focused tests | PASS, 31 (15 pure +16 Store/snapshot), final focused run 6.563s |
| Full backend | PASS, final266 tests in64.435s, includes existing generator/comparator/driver/personnel tests |
| Locked Python/Ruff | PASS, uv0.10.12 / Python3.13.7, lock unchanged; 71 files |
| Packaged sidecar | PASS, locked PyInstaller build and 11 persistence/restart/legacy-upgrade tests, 18.332s |
| Frontend | PASS, npm ci/Prettier/35 tests/TypeScript-Vite build |
| Rust | PASS, 1.95.0 fmt/locked fetch/Windows Release and 8 tests after required Sidecar resources existed |
| Historical .NET | PASS, locked restore/format/Release build, 0 warnings/errors, 35 tests (16/2/17) |
| Synthetic acceptance harness | PASS; not a native GUI run |
| Explicit/missing policy; known shortage versus unknown possible count | PASS, no numeric fallback |
| Exact/AtLeast, independent qualification codes/no equivalence | PASS |
| Borrowing both sides, collisions/cancellation, inactive/type mismatch | PASS, actual IDs retained |
| Year/leap/DST/date.max, invalid/duplicate/workload bounds | PASS |
| Determinism/frozen outputs/pure no-I/O and unchanged logical DB | PASS |
| Real evidence reload/no-op/stale/reference/history/FK/partial rollback | PASS |
| Simultaneous writers and complete WAL old/new view | PASS |
| Other-Project/unselected Crew policy/master and employee Level staleness | PASS |
| Schema11→12 preservation/failure/retry/idempotence | PASS; every original table retained, integrity/FKs checked |
| Aggregate snapshot read budget | PASS, stops before reading the next qualification owner; no fingerprint on excess |
| Scale/independent oracle | PASS, 2,000 visits/8,000 count explanations and 50 seeded comparisons; evaluation-limit failure explicit |
| Staged privacy/docs/whitespace | PASS, 274 indexed paths; staged whitespace and changed-document links/fences checked |
| Final-head Windows CI | Pending push/PR; final PR/Issues record exact SHA/run/jobs/artifact |
| Native GUI/disconnected installation/upgrade/reboot | NOT RUN |
| Customer Demo D/E/UAT | NOT RUN |
| Production | NOT APPROVED |

Initial lint found one unused test import, removed before final gates. First local
Rust invocation ran before dependent Sidecar resources completed and failed;
rerunning after Sidecar build passed without relaxing resource checks.
Raw logs/temporary DBs/full originals remain local.

## Compatibility and remaining work

Schema11 binaries reject schema12. Operational fallback needs a verified
consistent pre-upgrade backup and compatible binary; never delete live tables or
history. Test-only legacy reconstruction removes newer schema solely inside
generated synthetic fixtures. Native installer upgrade/recovery remains NOT RUN.

Actual company thresholds, hierarchy/certificate meaning/approval authority,
management UI, Foreman dated presence/promotion/merger rules, disjoint role
allocation and full multi-Crew dispatch remain separate confirmed-design work.
Complete #24 actual Rig/maintenance, #27 actual-worker weekend consent and
#18/#29 Preview/locks/transaction revalidation/human Apply/audit. No merge,
Release, Issue closure, worker reassignment or publication.
