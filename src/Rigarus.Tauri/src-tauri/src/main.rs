#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod sidecar;

use serde::{Deserialize, Serialize};
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
async fn read_demo(app: tauri::AppHandle) -> Result<DemoProject, String> {
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
        slot.as_ref().unwrap().read_demo()
    })
    .await
    .map_err(|_| "Unable to start the local service. Reopen Rigarus to retry.")?
}

#[tauri::command]
async fn save_demo_note(app: tauri::AppHandle, note: String) -> Result<DemoProject, String> {
    tauri::async_runtime::spawn_blocking(move || {
        let state = app.state::<Mutex<Option<Sidecar>>>();
        let slot = state.lock().map_err(|_| "Reopen Rigarus to retry.")?;
        slot.as_ref()
            .ok_or("The local service is unavailable. Reopen Rigarus to retry.")?
            .save_note(&note)
    })
    .await
    .map_err(|_| "Unable to save the local demo note. Reopen Rigarus to retry.")?
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
        .invoke_handler(tauri::generate_handler![read_demo, save_demo_note])
        .build(tauri::generate_context!())
        .expect("Unable to start the Rigarus desktop.")
        .run(|app, event| {
            if matches!(event, tauri::RunEvent::Exit) {
                stop_sidecar(app.state());
            }
        });
}
