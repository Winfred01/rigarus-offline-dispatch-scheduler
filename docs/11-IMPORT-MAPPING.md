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

The Projects page now reuses this validation and diagnostic grid for the #45 Bulk Add flow described below. The separate Import preview screen remains read-only. Persistent source hashes/batch history and historical reconciliation remain future #31 work. Demo F must approve the real worksheet layout, project/work-item grouping, date interpretation and unsupported field mappings using authorized local copies.

## Bulk Add Projects

Open Projects → Bulk Add Projects. Choose Paste Text or Upload Excel. Download Excel Template creates a local .xlsx workbook without a server or installed Office application; the supported entry range is formatted as text. Fill one project per row, preserving identifiers as text. The three fields are Project Number, Site ID and Site Name. The Excel flow also recognizes Job # as the existing mapping alias; the CSV header and order are fixed:

```csv
Project Number,Site ID,Site Name
000045,0002,"Synthetic, yard"
SYN-046,0003,Synthetic tower site
```

The CSV reader handles quoted commas and quoted multiline names and reports physical line numbers. The Excel flow retains worksheet/cell references and the same formula/error/numeric-identifier checks as Import preview. Both inputs allow up to 5 MiB and 2000 nonblank data rows, with the existing workbook archive/sheet/column limits. CSV fields above the parser's 128-KiB field limit are rejected; cell values above 2000 characters produce validation errors. Blank input rows are skipped.

The grid and count line show Ready and skipped rows. Existing project numbers (including case variants) and every occurrence of a repeated number within the input are skipped. Existing projects and work items are never updated. Extra populated fields, including work-item data, are invalid here; use the separate read-only preview to review those fields. Missing or repeated Excel headers prevent confirmation until resolved, including when another sheet contains ready rows.

Changing text, selecting another file or switching input tabs invalidates the preview. Cancel leaves SQLite unchanged. Confirm is enabled only for a nonempty ready subset with no workbook-level diagnostics, and its label includes the eligible count. The service re-parses and revalidates the exact input against matching projects under the same `BEGIN IMMEDIATE` transaction as all inserts. Changes to input or affected duplicate classification return a stale-preview response before any insert. Any insertion failure rolls back the entire attempt. A successful batch reports created/skipped counts, refreshes Projects and selects the first new project; a prior search is cleared if it would hide that project.

A repeated confirmation cannot insert duplicate projects. After success, or after an uncertain/lost response, preview again to see the current state; a repeated original confirmation returns a stale-preview error rather than another copy. Preview fingerprints are content checks, not durable batch receipts. Original inputs, workbook files and fingerprints are not stored in new database tables. No schema migration or scheduling priority is added.

## Verification

Generate synthetic workbooks in memory for tests. Include a valid row, repeated Job #, missing Site ID, numeric identifiers, a formula, #REF!, an external-link formula, unknown dates and an existing project. Verify precise worksheet/cell references, proposed outcomes, unchanged SQLite main-file SHA-256 and logical content after repeated previews. Cancel in the native GUI and reopen Projects to verify no new project was inserted. Record packaged sidecar, Windows GUI, network conditions and customer acceptance separately.
