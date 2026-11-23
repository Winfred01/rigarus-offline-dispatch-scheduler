use crate::DemoProject;
use reqwest::blocking::{Client, RequestBuilder};
use serde::Deserialize;
use serde::de::DeserializeOwned;
use serde_json::Value;
use std::{
    fmt::Write as _,
    io::{BufRead, BufReader, Write},
    os::windows::process::CommandExt,
    path::PathBuf,
    process::{Child, Command, Stdio},
    sync::mpsc,
    thread,
    time::{Duration, Instant},
};

const CREATE_NO_WINDOW: u32 = 0x08000000;
const STARTUP_TIMEOUT: Duration = Duration::from_secs(60);
const SERVICE_UNAVAILABLE: &str = "The local service is unavailable. Reopen Rigarus to retry.";
const STARTUP_TIMED_OUT: &str =
    "The local service took too long to start. Try again, or reopen Rigarus.";
const OPEN_DATABASE: &str =
    "Unable to open the local database. Check folder permissions and close other Rigarus windows.";
const INCOMPATIBLE_DATABASE: &str =
    "This database needs a compatible version of Rigarus. Verify the selected database.";

#[derive(Deserialize)]
struct Ready {
    event: String,
    port: u16,
}

pub struct Sidecar {
    child: Child,
    client: Client,
    token: String,
    port: u16,
}

impl Sidecar {
    pub fn start(executable: PathBuf, database: PathBuf) -> Result<Self, String> {
        let client = Client::builder()
            .no_proxy()
            .redirect(reqwest::redirect::Policy::none())
            .timeout(Duration::from_secs(8))
            .build()
            .map_err(|_| SERVICE_UNAVAILABLE)?;
        let mut random = [0_u8; 32];
        getrandom::fill(&mut random).map_err(|_| SERVICE_UNAVAILABLE)?;
        let mut token = String::with_capacity(64);
        for byte in random {
            write!(&mut token, "{byte:02x}").expect("Writing to a string cannot fail.");
        }

        let child = Command::new(executable)
            .arg("--database")
            .arg(database)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .creation_flags(CREATE_NO_WINDOW)
            .spawn()
            .map_err(|_| "Unable to launch the local service. Reinstall Rigarus.")?;
        let mut service = Self {
            child,
            client,
            token,
            port: 0,
        };

        let mut stdout = BufReader::new(service.child.stdout.take().unwrap());
        let mut stderr = BufReader::new(service.child.stderr.take().unwrap());
        let (tx, rx) = mpsc::channel();
        let (error_tx, error_rx) = mpsc::channel();
        thread::spawn(move || {
            let mut line = String::new();
            if stdout.read_line(&mut line).is_ok() {
                let _ = tx.send(serde_json::from_str::<Ready>(&line));
            }
            let _ = std::io::copy(&mut stdout, &mut std::io::sink());
        });
        thread::spawn(move || {
            let mut line = String::new();
            if stderr.read_line(&mut line).is_ok() {
                let _ = error_tx.send(line);
            }
            let _ = std::io::copy(&mut stderr, &mut std::io::sink());
        });

        writeln!(service.child.stdin.as_mut().unwrap(), "{}", service.token)
            .map_err(|_| SERVICE_UNAVAILABLE)?;
        service.port = wait_for_readiness(rx, error_rx, STARTUP_TIMEOUT)?;
        Ok(service)
    }

    pub fn is_running(&mut self) -> bool {
        matches!(self.child.try_wait(), Ok(None))
    }

    pub fn read_demo(&self) -> Result<DemoProject, String> {
        self.send(self.client.get(self.url("/demo")))
    }

    pub fn preview_import(&self, content: &str) -> Result<Value, String> {
        self.send(
            self.client
                .post(self.url("/import-preview"))
                .timeout(Duration::from_secs(60))
                .json(&serde_json::json!({ "content": content })),
        )
    }

    pub fn bulk_projects(&self, action: &str, input: &Value) -> Result<Value, String> {
        let request = match action {
            "template" => self.client.get(self.url("/bulk-projects/template")),
            "preview" => self
                .client
                .post(self.url("/bulk-projects/preview"))
                .json(input),
            "confirm" => self
                .client
                .post(self.url("/bulk-projects/confirm"))
                .json(input),
            _ => return Err("Choose a supported Bulk Add action.".into()),
        };
        self.send(request.timeout(Duration::from_secs(60)))
    }

    pub fn save_note(&self, note: &str) -> Result<DemoProject, String> {
        if note.encode_utf16().count() > 200 {
            return Err("The demo note must be 200 characters or fewer.".into());
        }
        self.send(
            self.client
                .put(self.url("/demo/note"))
                .json(&serde_json::json!({ "note": note })),
        )
    }

    pub fn search_projects(&self, term: &str) -> Result<Value, String> {
        self.search("/projects", term)
    }

    pub fn search_crews(&self, term: &str) -> Result<Value, String> {
        self.search("/crews", term)
    }

    pub fn search_employees(&self, term: &str) -> Result<Value, String> {
        self.search("/employees", term)
    }

    pub fn search_rigs(&self, term: &str) -> Result<Value, String> {
        self.search("/rigs", term)
    }

    fn search(&self, path: &str, term: &str) -> Result<Value, String> {
        let mut url =
            reqwest::Url::parse(&self.url(path)).map_err(|_| SERVICE_UNAVAILABLE.to_string())?;
        url.query_pairs_mut().append_pair("term", term);
        self.send(self.client.get(url))
    }

    pub fn read_project(&self, id: i32) -> Result<Value, String> {
        self.send(self.client.get(self.url(&format!("/projects/{id}"))))
    }

    pub fn save_project(&self, id: Option<i32>, project: &Value) -> Result<Value, String> {
        let request = match id {
            Some(id) => self.client.put(self.url(&format!("/projects/{id}"))),
            None => self.client.post(self.url("/projects")),
        };
        self.send(request.json(project))
    }

    pub fn save_crew(&self, id: Option<i64>, crew: &Value) -> Result<Value, String> {
        self.save_roster_record("/crews", id, crew)
    }

    pub fn save_employee(&self, id: Option<i64>, employee: &Value) -> Result<Value, String> {
        self.save_roster_record("/employees", id, employee)
    }

    pub fn read_foreman(&self, crew_id: i64) -> Result<Value, String> {
        self.send(
            self.client
                .get(self.url(&format!("/crews/{crew_id}/foreman"))),
        )
    }

    pub fn list_assignments(&self, query: &Value) -> Result<Value, String> {
        let url = assignment_query_url(&self.url("/draft-assignments"), query)?;
        self.send(self.client.get(url))
    }

    pub fn read_working_calendar(
        &self,
        scope: &str,
        id: i64,
        start: &str,
        end: &str,
    ) -> Result<Value, String> {
        let path = working_calendar_path(scope, id)?;
        let url = local_query_url(
            &self.url(&path),
            &[("start_date", start), ("end_date", end)],
        )?;
        self.send(self.client.get(url))
    }

    pub fn save_working_calendar(
        &self,
        scope: &str,
        id: i64,
        value: &Value,
    ) -> Result<Value, String> {
        self.send(
            self.client
                .put(self.url(&working_calendar_path(scope, id)?))
                .json(value),
        )
    }

    pub fn read_working_calendar_history(&self, scope: &str, id: i64) -> Result<Value, String> {
        self.send(
            self.client
                .get(self.url(&format!("{}/history", working_calendar_path(scope, id)?))),
        )
    }

    pub fn read_calendar_assessment(
        &self,
        work_item_id: i64,
        crew_id: i64,
        day: &str,
        slot: &str,
    ) -> Result<Value, String> {
        let work = work_item_id.to_string();
        let crew = crew_id.to_string();
        let url = local_query_url(
            &self.url("/working-calendars/assessment"),
            &[
                ("work_item_id", &work),
                ("crew_id", &crew),
                ("local_date", day),
                ("slot", slot),
            ],
        )?;
        self.send(self.client.get(url))
    }

    pub fn read_availability(
        &self,
        employee_id: i64,
        start: &str,
        end: &str,
    ) -> Result<Value, String> {
        let url = local_query_url(
            &self.url(&format!("/employees/{employee_id}/availability")),
            &[("start_date", start), ("end_date", end)],
        )?;
        self.send(self.client.get(url))
    }

    pub fn save_availability(&self, employee_id: i64, value: &Value) -> Result<Value, String> {
        self.send(
            self.client
                .put(self.url(&format!("/employees/{employee_id}/availability")))
                .json(value),
        )
    }

    pub fn read_availability_history(&self, employee_id: i64) -> Result<Value, String> {
        self.send(
            self.client
                .get(self.url(&format!("/employees/{employee_id}/availability/history"))),
        )
    }

    pub fn read_availability_on_slot(&self, day: &str, slot: &str) -> Result<Value, String> {
        let url = local_query_url(
            &self.url("/employee-availability"),
            &[("local_date", day), ("slot", slot)],
        )?;
        self.send(self.client.get(url))
    }

    pub fn read_assignment(&self, id: i64) -> Result<Value, String> {
        self.send(
            self.client
                .get(self.url(&format!("/draft-assignments/{id}"))),
        )
    }

    pub fn save_staffing(&self, id: i64, staffing: &Value) -> Result<Value, String> {
        self.send(
            self.client
                .put(self.url(&format!("/draft-assignments/{id}/staffing")))
                .json(staffing),
        )
    }

    pub fn read_staffing_history(&self, id: i64) -> Result<Value, String> {
        self.send(
            self.client
                .get(self.url(&format!("/draft-assignments/{id}/staffing-history"))),
        )
    }

    pub fn save_assignment(&self, id: Option<i64>, assignment: &Value) -> Result<Value, String> {
        self.save_roster_record("/draft-assignments", id, assignment)
    }

    pub fn cancel_assignment(&self, id: i64, expected_revision: i64) -> Result<Value, String> {
        self.send(
            self.client
                .post(self.url(&format!("/draft-assignments/{id}/cancel")))
                .json(&serde_json::json!({"expected_revision":expected_revision})),
        )
    }

    pub fn save_foreman(&self, crew_id: i64, change: &Value) -> Result<Value, String> {
        self.send(
            self.client
                .put(self.url(&format!("/crews/{crew_id}/foreman")))
                .json(change),
        )
    }

    pub fn save_rig(&self, id: Option<i64>, rig: &Value) -> Result<Value, String> {
        self.save_roster_record("/rigs", id, rig)
    }

    fn save_roster_record(
        &self,
        path: &str,
        id: Option<i64>,
        record: &Value,
    ) -> Result<Value, String> {
        let request = match id {
            Some(id) => self.client.put(self.url(&format!("{path}/{id}"))),
            None => self.client.post(self.url(path)),
        };
        self.send(request.json(record))
    }

    fn url(&self, path: &str) -> String {
        format!("http://127.0.0.1:{}{path}", self.port)
    }

    fn send<T: DeserializeOwned>(&self, request: RequestBuilder) -> Result<T, String> {
        let response = request
            .bearer_auth(&self.token)
            .send()
            .map_err(|_| SERVICE_UNAVAILABLE.to_string())?;
        if response.status().is_success() {
            return response.json().map_err(|_| SERVICE_UNAVAILABLE.into());
        }
        #[derive(Deserialize)]
        struct ApiError {
            detail: String,
        }
        Err(response
            .json::<ApiError>()
            .map(|error| error.detail)
            .unwrap_or_else(|_| SERVICE_UNAVAILABLE.into()))
    }
}

fn working_calendar_path(scope: &str, id: i64) -> Result<String, String> {
    if !matches!(scope, "Crew" | "Project") || !(1..=9_007_199_254_740_991).contains(&id) {
        return Err("Select an existing Crew or Project calendar.".to_string());
    }
    Ok(format!("/working-calendars/{scope}/{id}"))
}

fn local_query_url(base: &str, fields: &[(&str, &str)]) -> Result<reqwest::Url, String> {
    let mut url = reqwest::Url::parse(base).map_err(|_| SERVICE_UNAVAILABLE.to_string())?;
    url.query_pairs_mut().extend_pairs(fields.iter().copied());
    Ok(url)
}

fn assignment_query_url(base: &str, query: &Value) -> Result<reqwest::Url, String> {
    let mut url = reqwest::Url::parse(base).map_err(|_| SERVICE_UNAVAILABLE.to_string())?;
    let fields = query
        .as_object()
        .ok_or("Choose supported draft assignment filters.")?;
    for (key, value) in fields {
        if !matches!(
            key.as_str(),
            "start_date" | "end_date" | "crew_id" | "employee_id" | "include_cancelled"
        ) {
            return Err("Choose supported draft assignment filters.".into());
        }
        if value.is_null() {
            continue;
        }
        let text = match value {
            Value::String(value) => value.clone(),
            Value::Bool(_) | Value::Number(_) => value.to_string(),
            _ => return Err("Choose scalar draft assignment filters.".into()),
        };
        url.query_pairs_mut().append_pair(key, &text);
    }
    Ok(url)
}

fn wait_for_readiness(
    ready: mpsc::Receiver<Result<Ready, serde_json::Error>>,
    startup_error: mpsc::Receiver<String>,
    timeout: Duration,
) -> Result<u16, &'static str> {
    match ready.recv_timeout(timeout) {
        Ok(Ok(ready)) if ready.event == "ready" && ready.port > 0 => Ok(ready.port),
        Err(mpsc::RecvTimeoutError::Timeout) => Err(STARTUP_TIMED_OUT),
        _ => {
            let hint = startup_error.recv_timeout(Duration::from_millis(250));
            Err(match hint.as_deref().map(str::trim) {
                Ok(OPEN_DATABASE) => OPEN_DATABASE,
                Ok(INCOMPATIBLE_DATABASE) => INCOMPATIBLE_DATABASE,
                _ => SERVICE_UNAVAILABLE,
            })
        }
    }
}

impl Drop for Sidecar {
    fn drop(&mut self) {
        self.child.stdin.take();
        let deadline = Instant::now() + Duration::from_secs(7);
        while matches!(self.child.try_wait(), Ok(None)) && Instant::now() < deadline {
            thread::sleep(Duration::from_millis(30));
        }
        if self.is_running() {
            let _ = self.child.kill();
            let _ = self.child.wait();
        }
    }
}

#[cfg(test)]
mod tests {
    #[test]
    fn working_calendar_paths_allow_only_shared_project_or_crew_owners() {
        assert_eq!(
            super::working_calendar_path("Project", 17).unwrap(),
            "/working-calendars/Project/17"
        );
        assert!(super::working_calendar_path("Crew", 7).is_ok());
        for scope in [
            "WorkItem",
            "Employee",
            "Project/../employees",
            "Project?publish=true",
        ] {
            assert!(super::working_calendar_path(scope, 7).is_err());
        }
        assert!(super::working_calendar_path("Project", 0).is_err());
        assert!(super::working_calendar_path("Crew", 9_007_199_254_740_992).is_err());
    }
    use super::*;

    #[test]
    fn availability_dates_slots_and_query_values_remain_separate() {
        let url = local_query_url(
            "http://127.0.0.1:42000/employees/7/availability",
            &[
                ("start_date", "2026-12-31"),
                ("end_date", "2027-01-01&employee_id=8"),
            ],
        )
        .unwrap();
        let pairs: Vec<_> = url.query_pairs().collect();
        assert_eq!(url.path(), "/employees/7/availability");
        assert_eq!(pairs.len(), 2);
        assert_eq!(pairs[0].1, "2026-12-31");
        assert_eq!(pairs[1].1, "2027-01-01&employee_id=8");
        let slot = local_query_url(
            "http://127.0.0.1:42000/employee-availability",
            &[("local_date", "2026-12-31"), ("slot", "PM")],
        )
        .unwrap();
        assert_eq!(slot.query_pairs().last().unwrap().1, "PM");
    }

    #[test]
    fn assignment_filters_preserve_local_dates_ids_and_cancelled_visibility() {
        let url = assignment_query_url("http://127.0.0.1:42000/draft-assignments", &serde_json::json!({
            "start_date":"2026-12-31", "end_date":"2027-01-01", "crew_id":42, "include_cancelled":true
        })).unwrap();
        let values: std::collections::HashMap<_, _> = url.query_pairs().collect();
        assert_eq!(url.path(), "/draft-assignments");
        assert_eq!(values.get("start_date").unwrap(), "2026-12-31");
        assert_eq!(values.get("end_date").unwrap(), "2027-01-01");
        assert_eq!(values.get("crew_id").unwrap(), "42");
        assert_eq!(values.get("include_cancelled").unwrap(), "true");
    }

    #[test]
    fn assignment_filter_values_cannot_add_another_query_parameter() {
        let url = assignment_query_url(
            "http://127.0.0.1:42000/draft-assignments",
            &serde_json::json!({"start_date":"2026-12-31&include_cancelled=true"}),
        )
        .unwrap();
        assert_eq!(url.query_pairs().count(), 1);
        assert!(assignment_query_url(url.as_str(), &serde_json::json!({"publish":true})).is_err());
        assert!(assignment_query_url(url.as_str(), &serde_json::json!({"crew_id":[1,2]})).is_err());
    }

    #[test]
    fn accepts_a_delayed_valid_readiness_signal() {
        let (ready_tx, ready_rx) = mpsc::channel();
        let (_, error_rx) = mpsc::channel();
        let worker = thread::spawn(move || {
            thread::sleep(Duration::from_millis(30));
            ready_tx
                .send(serde_json::from_str(r#"{"event":"ready","port":42000}"#))
                .unwrap();
        });
        assert_eq!(
            wait_for_readiness(ready_rx, error_rx, Duration::from_secs(3)),
            Ok(42000),
        );
        worker.join().unwrap();
    }

    #[test]
    fn reports_a_deadline_when_the_pipe_is_open_without_readiness() {
        let (_ready_tx, ready_rx) = mpsc::channel();
        let (_, error_rx) = mpsc::channel();
        assert_eq!(
            wait_for_readiness(ready_rx, error_rx, Duration::ZERO),
            Err(STARTUP_TIMED_OUT),
        );
    }

    #[test]
    fn preserves_known_database_errors_when_the_sidecar_exits() {
        for message in [OPEN_DATABASE, INCOMPATIBLE_DATABASE] {
            let (ready_tx, ready_rx) = mpsc::channel();
            let (error_tx, error_rx) = mpsc::channel();
            error_tx.send(format!("{message}\r\n")).unwrap();
            drop(ready_tx);
            assert_eq!(
                wait_for_readiness(ready_rx, error_rx, Duration::from_secs(3)),
                Err(message),
            );
        }
    }

    #[test]
    fn rejects_invalid_readiness_without_exposing_stderr() {
        for line in ["", r#"{"event":"ready","port":0}"#] {
            let (ready_tx, ready_rx) = mpsc::channel();
            let (error_tx, error_rx) = mpsc::channel();
            ready_tx.send(serde_json::from_str(line)).unwrap();
            error_tx.send("Unexpected synthetic error.".into()).unwrap();
            assert_eq!(
                wait_for_readiness(ready_rx, error_rx, Duration::ZERO),
                Err(SERVICE_UNAVAILABLE),
            );
        }
    }
}
