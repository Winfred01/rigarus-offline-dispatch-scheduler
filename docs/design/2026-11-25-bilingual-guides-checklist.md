# Issue115 — README and bilingual operator guides

## Design Compliance Checklist

November25,2026 09:15–09:25 UTC, PUBLIC repository. Latest fetched main
7ee8d9bddcce1445ea291d2dcf9a4844e7fc85e0 is human-merged PR114.
No Open PR found; main CI45582406268 initially running. Isolated branch
codex/bilingual-user-guide; root README language link, untracked Chinese README
and original-design directory preserved untouched. Incorporate bilingual navigation
intent into the reviewed docs without copying obsolete M0-only claims.
Issue115 is the owner-approved documentation slice; no milestone behavior change.

| Read source | Revision / declared identity | Checkout modified UTC | Relevant sections |
| --- | --- | --- | --- |
| AGENTS.md / DEV-DESIGN-CHECKLIST |d3b9bea / mandatory workflow | November25 09:15:34 | Documentation-only checks, source/acceptance boundaries |
|00-PROJECT-PLAN.md |7604d2a / living November2026 summary |09:15:34.6660684 | Full-day rule, desktop transition, offline stack, next UI priority |
|09-DELIVERY-PLAYBOOK.md |7604d2a / living playbook |09:15:34.6700727 | Internal examples versus visible UI, engineering/Demo/production gates |
|02-ARCHITECTURE.md |7604d2a / living architecture |09:15:34.6670726 | Consent/backend v6, actual staffing, no UI/writer cutover |
|03-DATA-MODEL.md |7604d2a / SQLite model |09:15:34.6680704 | Schema18 additive compatibility, verified recovery |
|05-DEMO-ACCEPTANCE.md |7604d2a / living acceptance |09:15:34.6680704 | Full-day backend limits and independent GUI/offline acceptance |
|10-CLIENT-DECISIONS.md |f966ad7 / register |09:15:34.6700727 | Full Day supersedes half-day rules, pending approval/Apply/export |
|acceptance/2026-11-25-daily-weekend.md |7604d2a / engineering evidence |09:15:34 checkout |630 tests not customer acceptance; daily writes/UI gates |
|07-SECURITY-BACKUP /08-RELEASE-HANDBOOK | Living local data/build procedures |09:15:34 checkout | SQLite/WAL consistency, current Tauri packaging versus historical WPF |

UI source: actual React components and Tauri configuration/bridge, checked against
stored contracts. No UI implementation or new screenshots; original-design
page/image inspection not applicable. Do not present conceptual controls as
available. Existing handbook private-repository wording/old M0 instructions are
historical; repository is currently Public and current desktop is Tauri.
No original customer/design document is uploaded.

Additional source revisions: README/CN README7957153, securityb4c33a1,
release handbookad996ad. Current main CI45582406268 subsequently passed.

| Requirement | Authority / existing state | Change / acceptance |
| --- | --- | --- |
| README update | Explicit owner request; root copy M0/WPF, latest main already bilingual Tauri but recommendation details stale | Preserve current main overview/build/navigation and update daily backend status, no false release claim |
| Two manuals | Explicit owner Chinese + English request | Separate equivalent operator guides with language links/contents |
| Actual UI instructions | Existing legacy React controls | Verify labels/routes/save/cancel/reload/Locate in owning sources |
| Full-day transition honesty | Confirmed owner Full Day / existing closed daily writers | Explain visible AM/PM as compatibility, not recommended new day workflow |
| Data safety/status | Existing invariants | No silent conversion, manual SQL, approval inference or unimplemented exports |

## Implementation Plan

1. Commit this checklist/plan before writing deliverables.
2. Update README.md and add docs/README.zh-CN.md, with current desktop/backend
   capability matrix, operator manual links, locked developer build/test commands
   and legacy .NET reference separated from current launch.
3. Add docs/USER-GUIDE.en.md and docs/USER-GUIDE.zh-CN.md with matching numbered
   sections: scope, startup, navigation, master data, legacy Draft lifecycle,
   actual workers, calendars, availability, Employee Week, Locate, imports,
   recommendations/status gates, data/recovery, troubleshooting and practice.
   Keep actual English button labels in both. Synthetic examples only.
4. No UI/API/schema/dependency/runtime changes or business defaults. Document
   loading/empty/stale/uncertain-save handling; do not invent UI controls.
   Installation describes an authorized reviewed build, not a new Release/UAT.
5. Validate UTF-8, Markdown fences/local links/anchors, language section parity,
   source-backed labels/commands, staged diff/privacy and repository Windows CI.
   Product rebuild/test and native/offline GUI rerun N/A for docs-only changes;
   do not claim a new product test or customer acceptance.
6. One Draft PR for115, sync Issue, retain human review. No merge/Release/Issue
   closure or customer-profile modification. Initial checks NOT RUN.

Source correction before deliverables: latest tracked README/CN README revision
7957153 already documents Tauri and operator features. The old M0 copy is an
unrelated root-worktree change, not the baseline. Update the current summaries
and retain their existing topics; do not overwrite root changes.

## Actual documentation verification

- PASS: five affected Markdown files, UTF-8/no replacement/NUL, balanced fences,
  relative files and local anchors;16 corresponding bilingual sections and shared
  English control labels/safety statuses; README daily/schema18 status.
- PASS: manual source review against React routes/forms, Tauri local data path/
  package configuration and existing backend acceptance boundaries. Bulk Add
  confirmation versus read-only Data preview is explicitly distinguished.
- PASS staged privacy/diff:353 indexed paths, clean diff; only intended Markdown.
- Local product restore/build/test: N/A, only Markdown changed. No lockfile,
  runtime/API/UI/schema/behavior change. Main's completed CI is reference only.
- Exact-head PR Windows CI: NOT RUN before push; final Draft PR records observed
  run/head/jobs. Native/offline GUI/new installation and customer UAT NOT RUN.
- Delivered files: README.md, docs/README.zh-CN.md, USER-GUIDE.en.md,
  USER-GUIDE.zh-CN.md and this source/plan/check record. Originals and root edits
  remain untouched. No customer data, merge, Release or Issue closure.
