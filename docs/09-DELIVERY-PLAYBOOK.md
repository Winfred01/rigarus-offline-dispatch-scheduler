# Delivery playbook for repository use

Repository-safe summary of the delivery playbook. The complete planning copy remains in local development storage.

## Gates

1. **Engineering** requires reproducible Windows build and tests, offline operation, restart persistence and evidence for migration or conflict handling.
2. **Demo** requires the operator to try the agreed scope and a designated reviewer to record Accepted, Accepted with conditions, or Rejected. For conditional acceptance, record the owner, follow-up test and agreed due date.
3. **Production** requires target-PC offline installation, upgrade, backup/restore, real data migration under local controls, UAT, closed P0/P1 defects and handover.

## For each Demo

Choose one agreed Issue per PR and use synthetic data. Review the tests and screenshots and get human review before merging. Freeze the engineering version and record the commit, Windows package SHA-256, walkthrough, verification results, known limitations and sample output where applicable. With authorization, publish a private release and arrange customer review. Record feedback as Bug, Change Request, Question or Training. Document scope changes before scheduling them. Keep source-code ownership, maintenance terms and delivery rights in the commercial agreement.

M0 is technical preparation. Demo A starts with a separate project master-data slice after the M0 engineering gate and owner review. The Demo A acceptance draft is in [the walkthrough](05-DEMO-ACCEPTANCE.md).
