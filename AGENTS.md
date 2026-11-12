# Rigarus repository instructions

- Read `docs/00-PROJECT-PLAN.md`, `docs/09-DELIVERY-PLAYBOOK.md`, the current milestone and linked Issue before changing code. Check `docs/10-CLIENT-DECISIONS.md` and current acceptance evidence for any affected rule.
- Keep work to one approved vertical slice. Use one short-lived branch and one PR per Issue after the initial M0 commit. Keep `main` buildable. Require human review before merge and explicit approval before publishing a GitHub Release.
- Keep runtime Windows-only, single-operator and offline, with local SQLite. Keep scheduling rules separate from UI and persistence. Option C produces proposals for operator approval. Preserve locks and hard publishing constraints.
- Use synthetic data in source, tests, CI, screenshots and GitHub. Keep real business data, original spreadsheets and PDFs, chat exports, database files, local diagnostics and backups on authorized local systems.
- Run locked restore, format, Windows build, tests and the staged privacy scan. State the GUI and offline test conditions precisely. Record migration and regression evidence for data changes.
- Record unsettled business defaults in the decisions register or an ADR. Record client acceptance separately from engineering verification and production readiness.
