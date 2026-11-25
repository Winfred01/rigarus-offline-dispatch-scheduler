import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .domain import DemoProject
from .day_draft_api import day_draft_router
from .day_recommendation_api import day_recommendation_router
from .schedule_workbench import workbench_router
from .daily_calendar_api import daily_calendar_router
from .assignment_api import assignment_router
from .availability_api import availability_router
from .working_calendar_api import working_calendar_router
from .foreman_api import foreman_router
from .bulk_project_api import bulk_project_router
from .import_preview_api import import_preview_router
from .project_api import project_router
from .rig_api import rig_router
from .roster_api import crew_router, employee_router
from .storage import DemoStore, UnsupportedDatabaseError, initialize_database


class DemoNote(BaseModel):
    note: str


def create_app(
    database_path: Path,
    *,
    database_initialized: bool = False,
    enable_day_draft_writes: bool = False,
    enable_daily_calendar_writes: bool = False,
) -> FastAPI:
    store = DemoStore(database_path)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        if not database_initialized:
            initialize_database(database_path)
        yield

    app = FastAPI(lifespan=lifespan, openapi_url=None)
    app.include_router(project_router(database_path))
    app.include_router(assignment_router(database_path))
    app.include_router(day_recommendation_router(database_path))
    app.include_router(workbench_router(database_path))
    app.include_router(
        day_draft_router(database_path, enable_writes=enable_day_draft_writes)
    )
    app.include_router(availability_router(database_path))
    app.include_router(
        daily_calendar_router(database_path, enable_writes=enable_daily_calendar_writes)
    )
    app.include_router(working_calendar_router(database_path))
    app.include_router(crew_router(database_path))
    app.include_router(employee_router(database_path))
    app.include_router(foreman_router(database_path))
    app.include_router(rig_router(database_path))
    app.include_router(import_preview_router(database_path))
    app.include_router(bulk_project_router(database_path))

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ready"}

    @app.get("/demo")
    def read_demo() -> DemoProject:
        try:
            return store.read()
        except (sqlite3.Error, UnsupportedDatabaseError) as error:
            raise HTTPException(
                503, "Unable to read the local demo project."
            ) from error

    @app.put("/demo/note")
    def save_note(request: DemoNote) -> DemoProject:
        try:
            return store.save_note(request.note)
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        except (sqlite3.Error, UnsupportedDatabaseError) as error:
            raise HTTPException(503, "Unable to save the local demo note.") from error

    return app
