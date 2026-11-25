# Delivery playbook for repository use

Daily2C2 preview: run `python -m rigarus_backend.day_driver_example` in the locked
backend environment. Synthetic no-removal borrowing is Blocked by collision;
explicit sole-driver removal leaves source Blocked; an explicit eligible source
replacement satisfies only personnel/company-driver subchecks. Editing approval
then makes the proof Stale. Full validation stays Pending, flags false and
production writes closed. See [actual checks](acceptance/2026-11-24-daily-drivers.md).

Daily2C1 personnel preview uses the same synthetic day_recommendation_example:
unstaffed Pending; explicit worker still in another Crew's old PM assignment
Blocked/excluded, with source resource rechecks Pending; a separate explicit
worker clears only the collision check while full Validation/Apply/Publish stay
Pending/false/false. See [checks](acceptance/2026-11-24-daily-personnel.md).
No production write-gate opening, transfer Apply or customer dispatch approval.

Daily2B engineering preview: run `python -m rigarus_backend.day_recommendation_example`
in the locked backend environment. It seeds only a temporary synthetic schema14
profile, demonstrates both sorts, confirmed4-day accumulation across a closed day
and Stale after editing calendar input. The recommendation steps read only.
See [scope/checks](acceptance/2026-11-24-day-recommendations.md). No UI/Apply/Publish
or opening production writes; following #15/#23/#25 and actual #24/#27 are required.

Slice2 is split into reviewable dependency steps. #101 delivers daily input
backend/compatibility only, with closed production writes; then confirmed-day
generation/full snapshot/Stale, daily #15/#23/#25, actual Rig #24/consent #27,
and finally visible day UI/native offline acceptance. See
[slice2A checks](acceptance/2026-11-24-daily-calendars.md). Green backend/CI does
not accept customer Demo or authorize Apply/Publish.

## Day-based upgrade engineering gates (#99)

November24 owner's Full Day decision supersedes the half-day previews below for
new business contracts; retain them as legacy regression examples. Deliver three
reviewable slices: compatibility/schema/Day Draft Crew occupancy first; daily
calendars/availability/recommendations/snapshots/resources second; day UI and native
offline upgrade third. First-slice daily writes stay behind a default-closed HTTP
gate until the operator can see and safely manage them in the desktop. No automatic
conversion, Apply, publication or distribution is authorized. A green first-slice
PR does not complete the upgrade or accept Demo B/E. See [audit](design/2026-11-24-day-based-checklist.md)
and [actual checks](acceptance/2026-11-24-day-based.md).

Repository-safe summary of the delivery playbook. The complete planning copy remains in local development storage.

## Gates

1. **Engineering** requires reproducible Windows build and tests, offline operation, restart persistence and evidence for migration or conflict handling.
2. **Demo** requires the operator to try the agreed scope and a designated reviewer to record Accepted, Accepted with conditions, or Rejected. For conditional acceptance, record the owner, follow-up test and agreed due date.
3. **Production** requires target-PC offline installation, upgrade, backup/restore, real data migration under local controls, UAT, closed P0/P1 defects and handover.

## For each Demo

Choose one agreed Issue per PR and use synthetic data. Review the tests and screenshots and get human review before merging. Freeze the engineering version and record the commit, Windows package SHA-256, walkthrough, verification results, known limitations and sample output where applicable. With authorization, publish a private release and arrange customer review. Record feedback as Bug, Change Request, Question or Training. Document scope changes before scheduling them. Keep source-code ownership, maintenance terms and delivery rights in the commercial agreement.

M0 is technical preparation. Demo A starts with a separate project master-data slice after the M0 engineering gate and owner review. The Demo A acceptance draft is in [the walkthrough](05-DEMO-ACCEPTANCE.md).

## Demo E engineering preview (#28 phase two)

Run `python -m rigarus_backend.recommendation_example` from the backend folder
in the locked environment. Synthetic Remaining=4 generates C1 Mon AM/Wed PM/
Thu AM/Fri PM and C2 Tue AM/PM + Wed AM/PM. Compare earliest finish (C2,C1)
with earliest start (C1,C2), accumulated/skipped slots and missing safety checks.
This is an internal console example, not a desktop recommendation screen.

Results must show Validation pending / Apply=false / Publish=false. Absent
remaining confirmation, multi-Crew, insufficient horizon, Unknown/closed
calendars, occupied Crew slots and unapproved weekends need explicit explanations.
Engineering tests do not accept customer Demo E. See the
[acceptance record](acceptance/2026-11-24-issue-28-generator.md).
