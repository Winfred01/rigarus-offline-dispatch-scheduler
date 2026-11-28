#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod draft_journal;
mod draft_restore;
mod restore_faults;
mod sidecar;

use serde::{Deserialize, Serialize};
use serde_json::Value;
use sidecar::Sidecar;
use std::{path::PathBuf, sync::Mutex};
use tauri::{Manager, State};

#[derive(Deserialize, Serialize)]
struct DemoProject {
    job_number: String,
    site_name: String,
    note: String,
}

#[tauri::command]
async fn bulk_projects(
    app: tauri::AppHandle,
    action: String,
    input: Value,
) -> Result<Value, String> {
    if input
        .get("content")
        .and_then(Value::as_str)
        .is_some_and(|content| content.len() > 7_000_000)
    {
        return Err("Choose input of at most 5 MiB.".into());
    }
    with_sidecar(app, move |service| service.bulk_projects(&action, &input)).await
}

#[tauri::command]
async fn preview_import(app: tauri::AppHandle, content: String) -> Result<Value, String> {
    if content.len() > 7_000_000 {
        return Err("Choose an .xlsx workbook of at most 5 MiB.".into());
    }
    with_sidecar(app, move |service| service.preview_import(&content)).await
}

#[tauri::command]
async fn read_demo(app: tauri::AppHandle) -> Result<DemoProject, String> {
    with_sidecar(app, Sidecar::read_demo).await
}

#[tauri::command]
async fn save_demo_note(app: tauri::AppHandle, note: String) -> Result<DemoProject, String> {
    with_sidecar(app, move |service| service.save_note(&note)).await
}

#[tauri::command]
async fn search_projects(app: tauri::AppHandle, term: String) -> Result<Value, String> {
    with_sidecar(app, move |service| service.search_projects(&term)).await
}

#[tauri::command]
async fn day_recommendations(
    app: tauri::AppHandle,
    action: String,
    input: Value,
) -> Result<Value, String> {
    with_sidecar(app, move |service| {
        service.day_recommendations(&action, &input)
    })
    .await
}

#[tauri::command]
async fn schedule_workbench(
    app: tauri::AppHandle,
    action: String,
    input: Value,
) -> Result<Value, String> {
    with_sidecar(app, move |service| {
        service.schedule_workbench(&action, &input)
    })
    .await
}

#[tauri::command]
async fn day_editor(app: tauri::AppHandle, action: String, input: Value) -> Result<Value, String> {
    with_sidecar(app, move |service| service.day_editor(&action, &input)).await
}

#[tauri::command]
async fn draft_transactions(
    app: tauri::AppHandle,
    action: String,
    input: Value,
) -> Result<Value, String> {
    with_sidecar(app, move |service| {
        service.draft_transactions(&action, &input)
    })
    .await
}

#[tauri::command]
async fn draft_restores(
    app: tauri::AppHandle,
    action: String,
    input: Value,
) -> Result<Value, String> {
    with_sidecar(app, move |service| service.draft_restores(&action, &input)).await
}

#[tauri::command]
async fn read_availability(
    app: tauri::AppHandle,
    employee_id: i64,
    start_date: String,
    end_date: String,
) -> Result<Value, String> {
    with_sidecar(app, move |service| {
        service.read_availability(employee_id, &start_date, &end_date)
    })
    .await
}

#[tauri::command]
async fn read_working_calendar(
    app: tauri::AppHandle,
    scope: String,
    entity_id: i64,
    start_date: String,
    end_date: String,
) -> Result<Value, String> {
    with_sidecar(app, move |service| {
        service.read_working_calendar(&scope, entity_id, &start_date, &end_date)
    })
    .await
}

#[tauri::command]
async fn save_working_calendar(
    app: tauri::AppHandle,
    scope: String,
    entity_id: i64,
    calendar: Value,
) -> Result<Value, String> {
    with_sidecar(app, move |service| {
        service.save_working_calendar(&scope, entity_id, &calendar)
    })
    .await
}

#[tauri::command]
async fn read_working_calendar_history(
    app: tauri::AppHandle,
    scope: String,
    entity_id: i64,
) -> Result<Value, String> {
    with_sidecar(app, move |service| {
        service.read_working_calendar_history(&scope, entity_id)
    })
    .await
}

#[tauri::command]
async fn read_calendar_assessment(
    app: tauri::AppHandle,
    work_item_id: i64,
    crew_id: i64,
    local_date: String,
    slot: String,
) -> Result<Value, String> {
    with_sidecar(app, move |service| {
        service.read_calendar_assessment(work_item_id, crew_id, &local_date, &slot)
    })
    .await
}

#[tauri::command]
async fn save_availability(
    app: tauri::AppHandle,
    employee_id: i64,
    availability: Value,
) -> Result<Value, String> {
    with_sidecar(app, move |service| {
        service.save_availability(employee_id, &availability)
    })
    .await
}

#[tauri::command]
async fn read_availability_history(
    app: tauri::AppHandle,
    employee_id: i64,
) -> Result<Value, String> {
    with_sidecar(app, move |service| {
        service.read_availability_history(employee_id)
    })
    .await
}

#[tauri::command]
async fn read_availability_on_slot(
    app: tauri::AppHandle,
    local_date: String,
    slot: String,
) -> Result<Value, String> {
    with_sidecar(app, move |service| {
        service.read_availability_on_slot(&local_date, &slot)
    })
    .await
}

#[tauri::command]
async fn list_assignments(app: tauri::AppHandle, query: Value) -> Result<Value, String> {
    with_sidecar(app, move |service| service.list_assignments(&query)).await
}

#[tauri::command]
async fn save_staffing(app: tauri::AppHandle, id: i64, staffing: Value) -> Result<Value, String> {
    with_sidecar(app, move |service| service.save_staffing(id, &staffing)).await
}

#[tauri::command]
async fn read_staffing_history(app: tauri::AppHandle, id: i64) -> Result<Value, String> {
    with_sidecar(app, move |service| service.read_staffing_history(id)).await
}

#[tauri::command]
async fn read_assignment(app: tauri::AppHandle, id: i64) -> Result<Value, String> {
    with_sidecar(app, move |service| service.read_assignment(id)).await
}

#[tauri::command]
async fn save_assignment(
    app: tauri::AppHandle,
    id: Option<i64>,
    assignment: Value,
) -> Result<Value, String> {
    with_sidecar(app, move |service| service.save_assignment(id, &assignment)).await
}

#[tauri::command]
async fn cancel_assignment(
    app: tauri::AppHandle,
    id: i64,
    expected_revision: i64,
) -> Result<Value, String> {
    with_sidecar(app, move |service| {
        service.cancel_assignment(id, expected_revision)
    })
    .await
}

#[tauri::command]
async fn read_project(app: tauri::AppHandle, id: i32) -> Result<Value, String> {
    with_sidecar(app, move |service| service.read_project(id)).await
}

#[tauri::command]
async fn save_project(
    app: tauri::AppHandle,
    id: Option<i32>,
    project: Value,
) -> Result<Value, String> {
    with_sidecar(app, move |service| service.save_project(id, &project)).await
}

#[tauri::command]
async fn search_crews(app: tauri::AppHandle, term: String) -> Result<Value, String> {
    with_sidecar(app, move |service| service.search_crews(&term)).await
}

#[tauri::command]
async fn save_crew(app: tauri::AppHandle, id: Option<i64>, crew: Value) -> Result<Value, String> {
    with_sidecar(app, move |service| service.save_crew(id, &crew)).await
}

#[tauri::command]
async fn read_foreman(app: tauri::AppHandle, crew_id: i64) -> Result<Value, String> {
    with_sidecar(app, move |service| service.read_foreman(crew_id)).await
}

#[tauri::command]
async fn save_foreman(app: tauri::AppHandle, crew_id: i64, change: Value) -> Result<Value, String> {
    with_sidecar(app, move |service| service.save_foreman(crew_id, &change)).await
}

#[tauri::command]
async fn search_rigs(app: tauri::AppHandle, term: String) -> Result<Value, String> {
    with_sidecar(app, move |service| service.search_rigs(&term)).await
}

#[tauri::command]
async fn save_rig(app: tauri::AppHandle, id: Option<i64>, rig: Value) -> Result<Value, String> {
    with_sidecar(app, move |service| service.save_rig(id, &rig)).await
}

#[tauri::command]
async fn search_employees(app: tauri::AppHandle, term: String) -> Result<Value, String> {
    with_sidecar(app, move |service| service.search_employees(&term)).await
}

#[tauri::command]
async fn save_employee(
    app: tauri::AppHandle,
    id: Option<i64>,
    employee: Value,
) -> Result<Value, String> {
    with_sidecar(app, move |service| service.save_employee(id, &employee)).await
}

async fn with_sidecar<T: Send + 'static>(
    app: tauri::AppHandle,
    operation: impl FnOnce(&Sidecar) -> Result<T, String> + Send + 'static,
) -> Result<T, String> {
    tauri::async_runtime::spawn_blocking(move || {
        let state = app.state::<Mutex<Option<Sidecar>>>();
        let mut slot = state.lock().map_err(|_| "Reopen Rigarus to retry.")?;
        if slot.as_mut().is_some_and(|service| !service.is_running()) {
            *slot = None;
        }
        if slot.is_none() {
            let executable = app
                .path()
                .resolve(
                    "sidecar/Rigarus.Sidecar.exe",
                    tauri::path::BaseDirectory::Resource,
                )
                .map_err(|_| "Unable to locate the local service. Reinstall Rigarus.")?;
            *slot = Some(Sidecar::start(executable, database_path(&app)?)?);
        }
        operation(slot.as_ref().expect("The sidecar started successfully."))
    })
    .await
    .map_err(|_| "Unable to start the local service. Reopen Rigarus to retry.")?
}

fn database_path(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    let root = match std::env::var_os("RIGARUS_SMOKE_DATA_ROOT").filter(|root| !root.is_empty()) {
        Some(root) => PathBuf::from(root),
        None => app
            .path()
            .local_data_dir()
            .map_err(|_| "Unable to find the local data folder.")?
            .join("RigarusDispatch"),
    };
    Ok(root.join("data").join("rigarus.db"))
}

fn stop_sidecar(state: State<'_, Mutex<Option<Sidecar>>>) {
    if let Ok(mut slot) = state.lock() {
        slot.take();
    }
}

fn main() {
    tauri::Builder::default()
        .manage(Mutex::<Option<Sidecar>>::new(None))
        .invoke_handler(tauri::generate_handler![
            preview_import,
            bulk_projects,
            read_demo,
            save_demo_note,
            search_projects,
            day_recommendations,
            schedule_workbench,
            day_editor,
            draft_transactions,
            draft_restores,
            list_assignments,
            read_availability,
            read_working_calendar,
            save_working_calendar,
            read_working_calendar_history,
            read_calendar_assessment,
            save_availability,
            read_availability_history,
            read_availability_on_slot,
            save_staffing,
            read_staffing_history,
            read_assignment,
            save_assignment,
            cancel_assignment,
            read_project,
            save_project,
            search_crews,
            save_crew,
            read_foreman,
            save_foreman,
            search_employees,
            save_employee,
            search_rigs,
            save_rig
        ])
        .build(tauri::generate_context!())
        .expect("Unable to start the Rigarus desktop.")
        .run(|app, event| {
            if matches!(event, tauri::RunEvent::Exit) {
                stop_sidecar(app.state());
            }
        });
}
