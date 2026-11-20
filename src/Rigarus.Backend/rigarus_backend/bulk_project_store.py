from contextlib import closing
from pathlib import Path

from .bulk_projects import preview_bulk
from .import_preview import PreviewError
from .import_snapshot import project_snapshot, read_existing_projects
from .projects import ProjectDraft
from .storage import connect


class StaleBulkPreview(ValueError):
    pass


class BulkProjectStore:
    def __init__(self, path: Path):
        self.path = path

    def preview(self, kind: str, content: str):
        return preview_bulk(kind, content, read_existing_projects(self.path))

    def confirm(self, kind: str, content: str, preview_id: str):
        with closing(connect(self.path)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            # Revalidate against a snapshot protected by the same write lock.
            checked = preview_bulk(kind, content, project_snapshot(connection))
            if checked.preview_id != preview_id:
                raise StaleBulkPreview(
                    "Input or matching projects changed. Preview again before confirming."
                )
            if not checked.ready_count or checked.preview.diagnostics:
                raise PreviewError(
                    "No confirmable preview. Resolve input diagnostics and preview again."
                )
            created = []
            for row in checked.preview.rows:
                if row.status != "Ready" or row.action != "Create":
                    continue
                draft = ProjectDraft(
                    row.values["Job #"],
                    row.values["Site ID"],
                    row.values["Site Name"],
                    [],
                )
                project_id = connection.execute(
                    "INSERT INTO Projects (JobNumber, SiteId, SiteName) VALUES (?, ?, ?)",
                    (draft.job_number, draft.site_id, draft.site_name),
                ).lastrowid
                created.append(project_id)
            return {
                "created_ids": created,
                "created_count": len(created),
                "skipped_count": checked.skipped_count,
            }
