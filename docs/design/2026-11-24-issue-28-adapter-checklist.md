# Issue #28 phase three — consistent read-only SQLite adapter

## Baseline

2026-11-24, PUBLIC repository verified. Latest fetched main/current commit
`244b5ee1089f233b2d727318bd7f4d86cd1f87c8` includes human-merged PR92
(head ef8ecf0), PR91 comparator already merged. No Open PR; PR91/92 have no
submitted review entries. Issue28 remains Open, M5 / Demo E. Preserve root README,
Chinese README and local design-folder modifications; isolated branch/worktree
`codex/issue-28-sqlite-adapter`. The owner's pasted phase-three task is the
current scope authority. G1–G3 and Pending/false safety flags are unchanged.

## Design Compliance Checklist

| Source | Exists/readable | Declared version | Last-changing revision | Checkout mtime UTC (not authority) | Read-at UTC |
| --- | --- | --- | --- | --- | --- |
| `AGENTS.md` | Yes | November 2026 repository baseline | `d3b9bea778529c47bb502e59914cbdd0100697a0` | 2026-11-24T15:43:32.267815+00:00 | 2026-11-24T15:47:09.683579+00:00 |
| `docs/DEV-DESIGN-CHECKLIST.md` | Yes | November 2026 repository baseline | `d3b9bea778529c47bb502e59914cbdd0100697a0` | 2026-11-24T15:43:32.274328+00:00 | 2026-11-24T15:47:09.683579+00:00 |
| `docs/00-PROJECT-PLAN.md` | Yes | November 2026 repository baseline | `2a074876b0d8283578af7464a97ea12837c244d9` | 2026-11-24T15:43:32.269815+00:00 | 2026-11-24T15:47:09.683579+00:00 |
| `docs/09-DELIVERY-PLAYBOOK.md` | Yes | November 2026 repository baseline | `2a074876b0d8283578af7464a97ea12837c244d9` | 2026-11-24T15:43:32.273325+00:00 | 2026-11-24T15:47:09.683579+00:00 |
| `docs/02-ARCHITECTURE.md` | Yes | November 2026 repository baseline | `2a074876b0d8283578af7464a97ea12837c244d9` | 2026-11-24T15:43:32.270815+00:00 | 2026-11-24T15:47:09.683579+00:00 |
| `docs/03-DATA-MODEL.md` | Yes | November 2026 repository baseline | `d43fa6db88660fb623572aad9450774e9cc1f880` | 2026-11-24T15:43:32.270815+00:00 | 2026-11-24T15:47:09.683579+00:00 |
| `docs/05-DEMO-ACCEPTANCE.md` | Yes | November 2026 repository baseline | `2a074876b0d8283578af7464a97ea12837c244d9` | 2026-11-24T15:43:32.272321+00:00 | 2026-11-24T15:47:09.683579+00:00 |
| `docs/10-CLIENT-DECISIONS.md` | Yes | November 2026 repository baseline | `c24d88f1b57cf6046dd9db9ae245c8d499ed7fc7` | 2026-11-24T15:43:32.273325+00:00 | 2026-11-24T15:47:09.683579+00:00 |
| `docs/design/2026-11-23-issue-28-comparison-checklist.md` | Yes | November 2026 repository baseline | `cbd7b06994e27eb265d7a0f75f2461e15d2aae61` | 2026-11-24T15:43:32.292384+00:00 | 2026-11-24T15:47:09.683579+00:00 |
| `docs/acceptance/2026-11-23-issue-28-comparison.md` | Yes | November 2026 repository baseline | `cbd7b06994e27eb265d7a0f75f2461e15d2aae61` | 2026-11-24T15:43:32.282325+00:00 | 2026-11-24T15:47:09.683579+00:00 |
| `docs/design/2026-11-24-issue-28-generator-checklist.md` | Yes | November 2026 repository baseline | `ef8ecf0a8107041bbf018f35b75b5e074b153068` | 2026-11-24T15:43:32.295637+00:00 | 2026-11-24T15:47:09.683579+00:00 |
| `docs/acceptance/2026-11-24-issue-28-generator.md` | Yes | November 2026 repository baseline | `ef8ecf0a8107041bbf018f35b75b5e074b153068` | 2026-11-24T15:43:32.284384+00:00 | 2026-11-24T15:47:09.683579+00:00 |
| `docs/adr/ADR-002-sqlite-backup-restore.md` | Yes | November 2026 repository baseline | `b4c33a15bfe1e62b70ac77a99e3a9ef16b25c7bb` | 2026-11-24T15:43:32.285384+00:00 | 2026-11-24T15:47:09.683579+00:00 |

Latest accessible UI original: November22 updated DOCX, SHA256 `67cdc2ea9d006caea1a28c0faa50aee71380410dae819e6fcd32c27152161487`,
mtime UTC 2026-11-22T08:14:42.434606+00:00.
Read XML `.//w:p` locators 90 (Preview Impact, remaining, dual sort, locks,
revalidate Apply), 151 (actual workers/vehicles, driver, consent, dual sort),
277 (borrowing keeps Home Crew), and field explanatory text. These are XML
paragraph locators, not page numbers. No original figures rendered/inspected:
UI layout/interactions/loading/keyboard/accessibility are not applicable to this
backend-only service. Complete originals and exact local locations stay local.
All required repository sources exist; no inaccessible UI path is used to invent
missing design. ADR002 backup implementation remains Proposed/out of scope;
its WAL/compatible-schema principles apply, not its historical table list.

Relevant sections: Scope/Milestones/#28 owner scope; delivery Gates/engineering
preview; architecture Draft/workers/availability/calendars/generator; data model
Project/WorkItems, Draft uniqueness/cancel, staffing/availability/calendar history;
acceptance phase-two, employee/calendar checks, consistent active SQLite;
decisions #14/#22/#26/G1–G3 and pending safety/approval rules. Source inspected:
recommendation_generator/comparison, working_calendar_store, assignment_store,
staffing_store/persistence, availability_store, project_store, storage,
calendar_migration, Foreman/roster and their synthetic tests. Existing Store
public methods open separate connections; connection-level snapshot helpers
are the correct reuse point for one consistent view.

| Requirement / authority | Existing state / planned change | Acceptance case |
| --- | --- | --- |
| Confirmed owner: persisted parent FK only | Existing WorkItems.ProjectId; read and validate expected parent, retain JobNumber/type/count/estimate as reference | Wrong/missing parent, no estimate fallback |
| Confirmed G1–G3 | Generator/comparator Existing; construct compatible requests from saved data | Gaps, multi-Crew Needs Review, missing confirmation |
| Confirmed owner: Crew must not be presumed eligible | Read current Crew/type/active/Foreman; inactive or known type mismatch gets Needs Review outside ranking | Missing/inactive/Civil-Tower mismatch; Small/Other mapping pending, no invented equivalence |
| Confirmed owner: one read-only view | Missing adapter; mode=ro, query_only, foreign_keys, BEGIN pins schema read; all helpers share this connection | Concurrent atomic writer, no mixed old/new, release locks |
| Confirmed owner: real occupancy | Existing Draft/Cancelled unique Crew slots; include all WorkItems/visits, only Draft occupies | Cancel releases, other Crew separate, no exclusion/replacement semantics |
| Confirmed owner: employee observations are not approval | Reuse current staffing + availability snapshots, frozen observational rows, no assigned-worker inference for proposals | Home Crew vs borrowed actual worker; availability disagreement; missing validators Pending |
| Confirmed owner: source/revision identity | Per-calendar/availability revision, staffing/Foreman change IDs, assignment revisions; master rows lack revisions | Native source revision changes and unversioned row changes invalidate scoped fingerprint |
| Confirmed owner: repeatable scoped fingerprint | SHA256 canonical logical inputs + selection/remaining/order/limit + opaque source-path scope, never DB/WAL byte hash or global version | Repeat/permutation stability; each influencing source changes; unrelated scope documented |
| Confirmed owner: fail distinctly | Typed not-found/context/schema/read/busy/corrupt/deadline errors; no result/fingerprint on failed read | Missing DB/WorkItem/Crew, old/new schema, corrupt/locked/read fault and handle closure |
| Confirmed safety boundary | No resource certification, HTTP/Tauri/UI/write/migration/Apply/Publish | Query-only write denial, full synthetic logical dump equal, flags fixed false |

Open / out of scope: actual resource validators, Small/Other Crew mappings,
progress deduction, weekend approver identities, replacement semantics,
#18/#29 locks/revalidation/transaction Apply and customer Demo E. No missing
business answer blocks the authorized conservative read-only adapter. Never
use Home Crew/Foreman/Available/default Rig as dispatch approval.

## Implementation Plan (before product code)

1. Add optional read_only support to storage.connect; reject create+read_only;
   reuse URI escaping/foreign-key/5s busy strategy, enforce query_only and close
   on configuration failure. Existing write callers retain their behavior.
   No initialize_database, journal-mode change, checkpoint, migration or SQL write.
2. Add recommendation_adapter.py: strict immutable selection/query; source
   WorkItem/Project, Crew/Foreman/calendar, dated Assignment/current staffing,
   related employee/availability observations; frozen snapshot + content fingerprint.
   Current schema only, exact recognized migration sequence/table set; compatible
   old/new versions reject rather than auto-upgrade. Integrity/FK failures stop.
3. Open one read-only connection/BEGIN. Read schema first to pin the view. Read
   real parent, calendar helpers on that connection, all selected Crew assignments
   in the horizon including cancellations, current staffing and relevant employees
   (selected Home Crews, observed actual workers and current Foremen). Reuse
   availability_store.snapshot. Do not call Store.read methods that open more
   connections. Retain native source revisions/change IDs; master fields are
   compared by content because no native master/global revision exists.
4. Canonical SHA256 fingerprints cover actual observed values and query inputs,
   including confirmation, remaining, bounds, order/limit; source ID is an opaque
   hash of resolved DB location (scope, not a DB UUID or authorization). Exclude
   clock, SQLite page/WAL/SHM bytes and unrelated records. Re-read the same scope
   to classify Current/Stale; read failures remain errors. A new check can become
   stale immediately after completion: future Apply must revalidate transactionally.
5. Convert eligible Crew sources to existing GenerationRequest (Crew ID as stable
   option ID) and full-range CrewOccupancySnapshot. Reuse generate_and_compare
   and its generate_candidate/ExplicitOption path. Inactive/mismatched/unmapped
   Crew types remain Needs Review, not ranked; multi-Crew/missing Remaining are
   handled by existing generator. No supplied personnel/driver/Rig/weekend safety
   passes; no proposal workers are inferred. All results Pending/false.
6. Bound reads (existing 100 Crew / 366-date policies, technical observed-row
   limits and finite read/busy deadline). Add synthetic store-backed integration
   tests, concurrent WAL writer consistency, source-change/immutability/cleanup,
   bounded error handling and two generated sorting examples. Existing tests stay.
7. Update architecture/data-model/acceptance and this checklist. No DB schema,
   dependencies, FastAPI/Rust/UI changes. Reverting source needs no data downgrade.
8. Run locked Python/Ruff/full tests, sidecar build/packaged regressions,
   frontend/Rust/legacy .NET applicable checks, privacy/docs and Windows CI.
   Native GUI/physical offline install/upgrade/reboot NOT RUN: internal service
   only, no new connected user workflow; no historical result borrowed.
9. One Draft PR refs28/91/92 and Issue28 progress; human review, no merge,
   Issue closure, Release or real-customer DB access. Only synthetic/sanitized
   source/evidence enters PUBLIC GitHub; originals, DBs and logs stay local.

## Actual results

NOT RUN at this design commit. Engineering evidence will record exact commands,
counts, CI head and limitations. Customer Demo E/UAT NOT RUN; production NOT
APPROVED. Design/engineering progress does not close those separate gates.
