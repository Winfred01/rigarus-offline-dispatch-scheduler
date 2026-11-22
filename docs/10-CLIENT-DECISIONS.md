# Decision register

Source for this draft is the November 2026 project plan and delivery playbook. Confirmed items below reflect the recorded baseline. Proposed and open items await the designated decision-maker for the indicated gate.

| State | Decision or question | Gate or source |
| --- | --- | --- |
| Confirmed | Single operator, Windows, local storage and offline operation | Both plans |
| Confirmed | Option C proposals with operator approval and hard publishing constraints | Both plans |
| Confirmed | Default dates adjustable; an operator can lock start, crew or full assignment | Delivery playbook |
| Confirmed | Pause releases crew time; resuming requires approval. Operator enters remaining work. | Delivery playbook |
| Confirmed | Default recommendation ordering is earliest finish, with earliest start available. | Delivery playbook |
| Proposed | AM/PM granularity | Demo B |
| Open | Whether Site ID is required. Project Master currently follows the required field in the Issue #6 schema. | Demo A |
| Open | Accepted Job # format and non-ASCII case rules. Current uniqueness follows SQLite ASCII `NOCASE`. | Demo A |
| Proposed | Project and work-item table sorting compares identifiers as case-insensitive English text, preserving leading zeroes, and quantities as numbers. Equal values use ascending record ID. Sorting changes the displayed order only; search and selected project remain. Confirm whether operators prefer natural-number ordering inside identifiers. | Demo A / Issue #45 |
| Proposed | Employee entry requires a Home Crew. Retain references when that crew becomes inactive. Confirm whether the roster needs unassigned employees. | Demo A |
| Proposed | Rig # uses SQLite ASCII NOCASE uniqueness and remains reserved after retirement. Rig type is required free text. A rig may have an optional default Crew link, retained when that crew becomes inactive. Confirm Rig # format, type labels and default vehicle conventions. | Demo A |
| Proposed | Check an approved driver during each actual work period | Demo D |
| Open | Qualification criteria, crew sizes and scheduling/effective-dated foreman replacement rules; bounded master-data appointment scope is recorded separately below | Demo D |
| Confirmed (owner development scope) | A Crew may have zero or one current Foreman. New appointments select an Active employee marked Foreman eligible, including employees from another Home Crew; appointment never changes Home Crew. Record immediate appointment/replacement/clear operations in append-only history. Retain references and show warnings when the employee is later deactivated or loses eligibility. No retrospective effective dates, dispatch qualification, staffing limits or cross-Crew exclusivity is established by this master-data workflow. | Owner explicitly approved this bounded #8 proposal in the November 21, 2026 development session (November 22 UTC); customer Demo A/D still pending |
| Open | Who approves weekend work and who records the decision | Demo E |
| Proposed | Early completion produces an earlier-start suggestion | Demo C |
| Open | Historical workbook mappings, exceptions and exact report fidelity | Demo F |
| Proposed | Import preview uses explicit row-1 English headers, text identifiers and one project/work-item per data row. Repeated Job #s are held for review. Real worksheet grouping, dates and unsupported field mappings require client confirmation. | Demo A/F |
| Proposed | Bulk Add Projects uses Project Number, Site ID and Site Name only; Site ID stays required under Project Master. Existing and within-batch duplicate numbers are skipped, never updated or combined. Extra populated Excel fields are invalid for this flow. Confirmation requires the exact previewed input and unchanged matching-record classification; a stale or uncertain attempt requires a fresh preview. | Demo A / Issue #45 |
| Open | Installer strategy, backup encryption, commercial source and support terms | RC or commercial agreement |
| Out of scope | Cloud, Web/mobile, multi-user accounts, payroll, fleet tracking and automated message delivery | Both plans |
