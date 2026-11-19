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
| Proposed | Employee entry requires a Home Crew. Retain references when that crew becomes inactive. Confirm whether the roster needs unassigned employees. | Demo A |
| Proposed | Rig # uses SQLite ASCII NOCASE uniqueness and remains reserved after retirement. Rig type is required free text. A rig may have an optional default Crew link, retained when that crew becomes inactive. Confirm Rig # format, type labels and default vehicle conventions. | Demo A |
| Proposed | Check an approved driver during each actual work period | Demo D |
| Open | Qualification criteria, crew sizes and foreman replacement rules | Demo D |
| Open | Who approves weekend work and who records the decision | Demo E |
| Proposed | Early completion produces an earlier-start suggestion | Demo C |
| Open | Historical workbook mappings, exceptions and exact report fidelity | Demo F |
| Proposed | Import preview uses explicit row-1 English headers, text identifiers and one project/work-item per data row. Repeated Job #s are held for review. Real worksheet grouping, dates and unsupported field mappings require client confirmation. | Demo A/F |
| Open | Installer strategy, backup encryption, commercial source and support terms | RC or commercial agreement |
| Out of scope | Cloud, Web/mobile, multi-user accounts, payroll, fleet tracking and automated message delivery | Both plans |
