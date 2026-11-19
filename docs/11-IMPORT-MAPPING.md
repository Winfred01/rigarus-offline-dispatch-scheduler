# Project import preview mapping

Issue #11 provides a local .xlsx preview. Choose a workbook in Import preview and select Preview workbook. Preview and Cancel leave persisted project data intact. Excel and other office software are optional for reading an existing .xlsx file.

Put the following headers in worksheet row 1. Header comparisons ignore surrounding spaces and English letter case. Duplicate headers or missing required headers stop that worksheet and show its header range. All worksheets, including hidden sheets, are inspected. Blank rows are skipped and source worksheet/cell references remain visible.

| Header | Preview rule |
| --- | --- |
| Job # | Required text, trimmed. Keep leading zeroes in text cells. Compare duplicates with SQLite's current ASCII NOCASE semantics. |
| Site ID | Required text under the existing Project Master assumption, pending Demo A confirmation. Preserve leading zeroes. |
| Site Name | Required text, trimmed. |
| Description | Optional review field. Visible in row details with a warning that the current project model does not store it. |
| Customer | Optional review field with the same current model limitation. |
| Crew Type | Optional work-item group. If any work-item field is present, supply all three. Accept Small, Civil, Tower or Other. |
| Crew Count | A positive whole number up to 2147483647. |
| Estimated Half-days | A positive whole number up to 2147483647, following Project Master. |
| Other columns | Display the value and warn that its mapping requires approval. Date columns receive this treatment. |

Each data row represents one proposed project with at most one work item. Repeated Job #s anywhere in the workbook, including on different worksheets, are marked Duplicate and Skip for operator review. Combining repeated rows into one project with several work items needs an agreed layout.

The preview classifies a new valid row as Ready / Create. Missing or invalid values and formulas are Invalid / Skip. Existing Job #s are Duplicate / Skip when the compared fields are unchanged, or Review / Update when supplied fields differ. Updates identify the existing project and require review. Unsupported populated fields produce Review. Proposed outcomes describe a future import decision.

Formulas, Excel error cells such as #REF!, and external-link formulas require verified fixed values. The preview does not evaluate formulas or follow links. Numeric Job # or Site ID cells are flagged because formatting may conceal leading zeroes. Dates, ambiguous columns and unknown fields receive no automatic mapping.

## Limits and data lifecycle

Files must be .xlsx, at most 5 MiB, up to 10 worksheets, 40 columns and 2000 data rows across the workbook. Worksheet dimensions must also fit 2000 data rows and 40 columns. The archive is limited to 1000 entries and 25 MiB expanded content. Macro-bearing workbooks are rejected. Cell text over 2000 characters is flagged and its displayed value is truncated.

The browser reads the selected file into memory. The Tauri command sends its content only to the authenticated loopback sidecar. The backend parses it in memory and opens SQLite in read-only mode for a consistent snapshot of existing projects and work items. The preview HTTP request has a 60-second deadline. Cancel clears the selected file and preview from the screen. Source files, parsed rows and batch metadata are not saved by this feature.

The grid validation and row diagnostics support a later shared flow for #45. Fixed-format pasted text, import confirmation, source hashes and repeat-batch tracking require subsequent implementation. Demo F must approve the real worksheet layout, project/work-item grouping, date interpretation and unsupported field mappings using authorized local copies.

## Verification

Generate synthetic workbooks in memory for tests. Include a valid row, repeated Job #, missing Site ID, numeric identifiers, a formula, #REF!, an external-link formula, unknown dates and an existing project. Verify precise worksheet/cell references, proposed outcomes, unchanged SQLite main-file SHA-256 and logical content after repeated previews. Cancel in the native GUI and reopen Projects to verify no new project was inserted. Record packaged sidecar, Windows GUI, network conditions and customer acceptance separately.
