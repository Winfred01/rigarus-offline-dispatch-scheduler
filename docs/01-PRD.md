# Product requirements draft

## M0 acceptance

| Requirement | Acceptance evidence |
| --- | --- |
| Windows .NET 10 and WPF | An English desktop window opens with a Dashboard, sidebar placeholders and Demo Mode. |
| Local SQLite | First launch applies the initial migration and shows one fictional project. |
| Local write and restart | Save a demo note in the window and reopen the app to see the saved value. |
| Engineering baseline | Private visibility and the initial commit are verified on GitHub. Locked restore, formatting, build, tests and privacy checks pass. |
| Development isolation | The repository, logs and CI use synthetic examples and exclude runtime data and original customer material. |

## Later product behavior

- Create and find projects and work items. Maintain crews, employees, foremen, approved drivers and rigs.
- Preview downstream scheduling impact before changing confirmed assignments. Locks may cover a start date, a crew or the full assignment. Pausing work releases the reserved crew time. Resuming requires operator confirmation.
- Show a small set of viable recommendations. Default to earliest finish and offer an earliest start view. Keep scheduling, approval and publishing separate.
- Detect overlaps and eligibility failures based on actual people and vehicles. Explicit approval applies to weekend work. Drafts may contain hard conflicts. Publishing blocks them.
- Keep revisions and audit history for published changes. Export company weekly schedules, crew schedules and project lists. Preview local imports before committing.
- Validate performance and backup/restore on a target Windows computer. See the [decisions register](10-CLIENT-DECISIONS.md) for items requiring confirmation.
