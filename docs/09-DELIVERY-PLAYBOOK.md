# Delivery playbook for repository use

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
