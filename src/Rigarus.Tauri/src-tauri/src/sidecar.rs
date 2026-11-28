use crate::DemoProject;
use reqwest::blocking::{Client, RequestBuilder};
use serde::Deserialize;
use serde::de::DeserializeOwned;
use serde_json::Value;
use std::{
    fmt::Write as _,
    io::{BufRead, BufReader, Read, Write},
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
    database: PathBuf,
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

        let mut command = Command::new(executable);
        command.arg("--database").arg(&database);
        if std::env::var("RIGARUS_DAY_EDITOR_TEST").as_deref() == Ok("1") {
            let root = std::env::var_os("RIGARUS_SMOKE_DATA_ROOT")
                .filter(|root| !root.is_empty())
                .ok_or("Synthetic editor requires a separate test data root.")?;
            if database != PathBuf::from(root).join("data/rigarus.db") {
                return Err("Synthetic editor database does not match its test root.".into());
            }
            command.arg("--synthetic-day-editor");
        }
        if std::env::var("RIGARUS_DRAFT_TRANSACTIONS_TEST").as_deref() == Ok("1") {
            let root = std::env::var_os("RIGARUS_SMOKE_DATA_ROOT")
                .filter(|r| !r.is_empty())
                .ok_or("Synthetic Draft transactions require a separate root.")?;
            if database != PathBuf::from(root).join("data/rigarus.db") {
                return Err("Synthetic Draft database does not match its root.".into());
            }
            command.arg("--synthetic-draft-transactions");
        }
        if std::env::var("RIGARUS_DRAFT_RESTORE_TEST").as_deref() == Ok("1") {
            let root = std::env::var_os("RIGARUS_SMOKE_DATA_ROOT")
                .filter(|r| !r.is_empty())
                .ok_or("Synthetic Restore requires a separate root.")?;
            if database != PathBuf::from(root).join("data/rigarus.db") {
                return Err("Synthetic Restore database does not match its root.".into());
            }
            command.arg("--synthetic-draft-restores");
        }
        if std::env::var("RIGARUS_DRAFT_RESTORE_FAULT_TEST").as_deref() == Ok("1") {
            if std::env::var("RIGARUS_DRAFT_RESTORE_TEST").as_deref() != Ok("1") {
                return Err("Synthetic faults require the independent Restore test gate.".into());
            }
            command.arg("--synthetic-restore-faults");
        }
        let child = command
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .creation_flags(CREATE_NO_WINDOW)
            .spawn()
            .map_err(|_| "Unable to launch the local service. Reinstall Rigarus.")?;
        let mut service = Self {
            database,
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

    pub fn day_recommendations(&self, action: &str, input: &Value) -> Result<Value, String> {
        let path = recommendation_path(action, input)?;
        self.send(
            self.client
                .post(self.url(path))
                .json(input)
                .timeout(Duration::from_secs(60)),
        )
    }

    pub fn schedule_workbench(&self, action: &str, input: &Value) -> Result<Value, String> {
        if input.to_string().len() > 512 {
            return Err("Weekly input is too large.".into());
        }
        let request = match action {
            "week" => {
                let start = input["start_date"].as_str().ok_or("Choose a start date.")?;
                let end = input["end_date"].as_str().ok_or("Choose an end date.")?;
                self.client.get(local_query_url(
                    &self.url("/schedule-workbench/week"),
                    &[("start_date", start), ("end_date", end)],
                )?)
            }
            "locate" => {
                let kind = input["kind"].as_str().ok_or("Choose a record kind.")?;
                if !matches!(kind, "FullDayDraft" | "LegacyHalfDay") {
                    return Err("Choose a saved record kind.".into());
                }
                let id = input["id"]
                    .as_i64()
                    .filter(|n| *n > 0 && *n <= 9_007_199_254_740_991)
                    .ok_or("Choose a saved record ID.")?;
                self.client
                    .get(self.url(&format!("/schedule-workbench/locate/{kind}/{id}")))
            }
            _ => return Err("Choose week or typed Locate.".into()),
        };
        self.send(request.timeout(Duration::from_secs(60)))
    }

    pub fn day_editor(&self, action: &str, input: &Value) -> Result<Value, String> {
        if input.to_string().len() > 64000 {
            return Err("Day editor request is too large.".into());
        }
        let safe_id = || {
            input["id"]
                .as_i64()
                .filter(|n| *n > 0 && *n <= 9_007_199_254_740_991)
                .ok_or("Choose a saved Full Day ID.")
        };
        let request = match action {
            "status" => self.client.get(self.url("/day-editor/status")),
            "read" => self
                .client
                .get(self.url(&format!("/day-editor/record/{}", safe_id()?))),
            "history" => self
                .client
                .get(self.url(&format!("/day-editor/history/{}", safe_id()?))),
            "receipt" => {
                let profile = editor_uuid(&input["profile_id"])?;
                let request = editor_uuid(&input["request_id"])?;
                self.client
                    .get(self.url(&format!("/day-editor/receipt/{profile}/{request}")))
            }
            "submit" => self.client.post(self.url("/day-editor/submit")).json(input),
            _ => return Err("Choose a supported day editor action.".into()),
        };
        self.send(request.timeout(Duration::from_secs(60)))
    }

    fn draft_wire(&self, action: &str, input: &Value) -> Result<Value, String> {
        let path = draft_path(action, input)?;
        let request = if matches!(action, "prepare" | "submit") {
            self.client.post(self.url(&path)).json(input)
        } else {
            self.client.get(self.url(&path))
        };
        let response = request
            .timeout(Duration::from_secs(60))
            .bearer_auth(&self.token)
            .send()
            .map_err(|_| SERVICE_UNAVAILABLE)?;
        let status = response.status();
        let value: Value = response.json().map_err(|_| SERVICE_UNAVAILABLE)?;
        if status.is_success() {
            return Ok(value);
        }
        let code = value["detail"].as_str().unwrap_or("");
        if action == "submit"
            && status.as_u16() == 409
            && matches!(
                code,
                "STALE_OR_CHANGED_EXACT_PLAN"
                    | "BLOCKED_OR_INCOMPLETE_PLAN"
                    | "FINAL_SAVED_RESOURCE_BLOCKED"
                    | "EXPLICIT_PLAN_AND_PENDING_CONFIRMATION_REQUIRED"
                    | "ACTUAL_RIG_WRITE_UNSUPPORTED"
            )
        {
            return Ok(
                serde_json::json!({"outcome":"Rejected","code":code,"request_id":input["request_id"],"database_identity":input["profile_id"],"confirmation":input,"validation_status":"Pending","applyable":false,"publishable":false}),
            );
        }
        Err(if action=="submit"{"Draft result is unknown or cannot be retired. Resolve the original key."}else{"Draft preparation/version is unavailable or stale. Reload exact inputs; no safety approval."}.into())
    }

    pub fn draft_transactions(&self, action: &str, input: &Value) -> Result<Value, String> {
        if input.to_string().len() > crate::draft_journal::LIMIT {
            return Err("Draft recovery payload exceeds its bound.".into());
        }
        let mut status = self.draft_wire("status", &serde_json::json!({}))?;
        let profile = editor_uuid(&status["database_identity"])?;
        let journal = crate::draft_journal::Journal::open(&self.database, &profile)?;
        if action == "status" {
            status["pending"] = journal.pending()?.unwrap_or(Value::Null);
            status["other_operation_pending"] = Value::Bool(journal.restore_pending()?.is_some());
            return Ok(status);
        }
        if action == "prepare" && journal.restore_pending()?.is_some() {
            return Err("Resolve the original Restore before preparing Draft Apply.".into());
        }
        if matches!(action, "prepare" | "receipt" | "version" | "recovery") {
            if action != "prepare" && input["profile_id"] != profile {
                return Err("Draft recovery belongs to another database.".into());
            }
            return self.draft_wire(action, input);
        }
        if action == "submit" {
            if status["test_writes_enabled"] != true || status["production_writes_enabled"] != false
            {
                return Err("Production Draft writes are closed.".into());
            }
            let request = &input["request"];
            editor_uuid(&request["request_id"])?;
            if request["profile_id"] != profile
                || request["plan_fingerprint"] != input["reviewed"]["plan_fingerprint"]
                || request.to_string().len() > 65_536
            {
                return Err("Exact reviewed Draft context is invalid.".into());
            }
            journal.remember(input)?;
            return self.draft_wire("submit", request);
        }
        if action == "acknowledge" {
            let pending = journal
                .pending()?
                .ok_or("No original Draft request to acknowledge.")?;
            let request = &pending["request"];
            if input["request_id"] != request["request_id"] || request["profile_id"] != profile {
                return Err("Wrong Draft acknowledgement identity.".into());
            }
            let receipt = self.draft_wire(
                "receipt",
                &serde_json::json!({"profile_id":profile,"request_id":request["request_id"]}),
            )?;
            let verified = if receipt["outcome"] == "Committed" {
                receipt
            } else {
                if input["receipt"]["outcome"] != "Rejected"
                    || status["test_writes_enabled"] != true
                {
                    return Err("No definite matching receipt. Retain the original request.".into());
                }
                // Explicit retirement replays the same immutable key, never a new write key.
                self.draft_wire("submit", request)?
            };
            if verified != input["receipt"]
                || verified["confirmation"] != *request
                || (verified["outcome"] == "Committed" && verified["plan"] != pending["reviewed"])
            {
                return Err(
                    "Receipt changed or is incomplete. Resolve the original request again.".into(),
                );
            }
            journal.acknowledge(&pending, &verified)?;
            return Ok(serde_json::json!({"acknowledged":true}));
        }
        Err("Unsupported Draft transaction action.".into())
    }

    fn restore_wire(&self, action: &str, input: &Value) -> Result<Value, String> {
        let path = restore_path(action, input)?;
        let request = if matches!(action, "prepare" | "submit") {
            self.client.post(self.url(&path)).json(input)
        } else {
            self.client.get(self.url(&path))
        };
        let response = request
            .timeout(Duration::from_secs(60))
            .bearer_auth(&self.token)
            .send()
            .map_err(|_| crate::draft_restore::ERROR)?;
        let status = response.status();
        let mut bytes = Vec::new();
        response
            .take((crate::draft_restore::LIMIT + 1) as u64)
            .read_to_end(&mut bytes)
            .map_err(|_| crate::draft_restore::ERROR)?;
        crate::draft_restore::check(bytes.len() <= crate::draft_restore::LIMIT)?;
        let value: Value =
            serde_json::from_slice(&bytes).map_err(|_| crate::draft_restore::ERROR)?;
        if !status.is_success() {
            return Err(match value["detail"].as_str() {
                Some("Stale" | "STALE_RESTORE_PLAN") => {
                    "Stale: records or evidence changed. Prepare again and review every warning."
                }
                Some("RESTORE_PRODUCTION_WRITES_CLOSED") => "Production Restore writes are closed.",
                _ => crate::draft_restore::ERROR,
            }
            .into());
        }
        Ok(value)
    }

    pub fn draft_restores(&self, action: &str, input: &Value) -> Result<Value, String> {
        use crate::draft_restore as proof;
        proof::check(input.to_string().len() <= proof::LIMIT)?;
        let mut status = self.restore_wire("status", &serde_json::json!({}))?;
        proof::check(
            proof::flags(&status)
                && status["production_writes_enabled"] == false
                && status["test_writes_enabled"].is_boolean(),
        )?;
        let profile = proof::uuid(&status["database_identity"])?.to_owned();
        let journal = crate::draft_journal::Journal::open(&self.database, &profile)?;
        let pending = journal.restore_pending()?;
        if let Some(ref p) = pending {
            proof::envelope(p, &profile)?;
        }
        let other = journal.pending()?.is_some();
        if action == "status" {
            status["pending"] = pending.unwrap_or(Value::Null);
            status["other_operation_pending"] = Value::Bool(other);
            return Ok(status);
        }
        if action == "original" {
            proof::check(input["profile_id"] == profile)?;
            let source = self.restore_wire("original", input)?;
            proof::original(&source, &profile, proof::id(&input["source_version_id"])?)?;
            return Ok(source);
        }
        if action == "prepare" {
            proof::check(
                status["test_writes_enabled"] == true
                    && !other
                    && pending.is_none()
                    && input["profile_id"] == profile,
            )?;
            let source = self.restore_wire("original", input)?;
            let plan = self.restore_wire("prepare", input)?;
            proof::bundle(
                &source,
                &plan,
                &profile,
                proof::id(&input["source_version_id"])?,
            )?;
            return Ok(serde_json::json!({"source":source,"reviewed":plan}));
        }
        if action == "submit" {
            proof::check(status["test_writes_enabled"] == true && !other)?;
            proof::envelope(input, &profile)?;
            journal.remember_restore(input)?;
            let result = self.restore_wire("submit", &input["request"])?;
            proof::receipt(input, &result, &profile)?;
            return Ok(result);
        }
        if matches!(action, "resolve" | "acknowledge") {
            let original = pending.ok_or("No original Restore request retained.")?;
            let request = &original["request"];
            let result = self.restore_wire("receipt", request)?;
            if action == "resolve" && result["outcome"] == "NotFound" {
                proof::check(proof::flags(&result))?;
                return Ok(result);
            }
            proof::receipt(&original, &result, &profile)?;
            if action == "resolve" {
                return Ok(result);
            }
            proof::check(
                input["profile_id"] == profile
                    && input["request_id"] == request["request_id"]
                    && input["outcome"] == result["outcome"]
                    && input["version_id"] == result["version_id"],
            )?;
            match crate::restore_faults::archive_fault(&self.database, &original)?.as_deref() {
                Some("write_once") => {
                    return Err(
                        "Synthetic archive write failure; original request retained.".into(),
                    );
                }
                Some("flush_once") => journal.archive_pending_synced(
                    "restore-pending.json",
                    "restore-receipt",
                    &original,
                    &result,
                    |_| Err(std::io::Error::other("synthetic archive flush failure")),
                )?,
                _ => journal.acknowledge_restore(&original, &result)?,
            }
            return Ok(serde_json::json!({"acknowledged":true,"request_id":request["request_id"]}));
        }
        Err("Unsupported Restore action.".into())
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

fn restore_path(action: &str, input: &Value) -> Result<String, String> {
    use crate::draft_restore as proof;
    proof::check(input.to_string().len() <= 2_000_000)?;
    match action {
        "status" | "prepare" | "submit" => Ok(format!("/draft-restores/{action}")),
        "original" => Ok(format!(
            "/draft-transactions/version/{}/{}",
            proof::uuid(&input["profile_id"])?,
            proof::id(&input["source_version_id"])?
        )),
        "receipt" => Ok(format!(
            "/draft-restores/receipt/{}/{}",
            proof::uuid(&input["profile_id"])?,
            proof::uuid(&input["request_id"])?
        )),
        _ => Err("Unsupported Restore path.".into()),
    }
}

fn draft_path(action: &str, input: &Value) -> Result<String, String> {
    if input.to_string().len() > 65_536 {
        return Err("Draft request exceeds 64KiB.".into());
    }
    let base = "/draft-transactions";
    match action {
        "status" | "prepare" | "submit" => Ok(format!("{base}/{action}")),
        "receipt" => Ok(format!(
            "{base}/receipt/{}/{}",
            editor_uuid(&input["profile_id"])?,
            editor_uuid(&input["request_id"])?
        )),
        "version" | "recovery" => {
            let id = input["version_id"]
                .as_u64()
                .filter(|n| *n > 0 && *n <= 9_007_199_254_740_991)
                .ok_or("Choose an exact saved version ID.")?;
            Ok(format!(
                "{base}/{}/{}/{id}",
                if action == "version" {
                    "version"
                } else {
                    "recovery-preview"
                },
                editor_uuid(&input["profile_id"])?
            ))
        }
        _ => Err("Unsupported Draft path.".into()),
    }
}

#[cfg(test)]
mod draft_transport_tests {
    use super::*;
    #[test]
    fn restore_routes_are_fixed_and_separate_from_apply() {
        let p = "11111111-1111-4111-8111-111111111111";
        assert_eq!(
            restore_path(
                "receipt",
                &serde_json::json!({"profile_id":p,"request_id":p})
            )
            .unwrap(),
            format!("/draft-restores/receipt/{p}/{p}")
        );
        assert_eq!(
            restore_path(
                "original",
                &serde_json::json!({"profile_id":p,"source_version_id":1})
            )
            .unwrap(),
            format!("/draft-transactions/version/{p}/1")
        );
        for value in [
            serde_json::json!({"profile_id":"../x","source_version_id":1}),
            serde_json::json!({"profile_id":p,"source_version_id":0}),
        ] {
            assert!(restore_path("original", &value).is_err());
        }
        assert!(restore_path("publish", &serde_json::json!({})).is_err());
        assert!(
            restore_path(
                "submit",
                &serde_json::json!({"notes":"x".repeat(2_000_000)})
            )
            .is_err()
        );
    }
    #[test]
    fn fixed_draft_paths_bound_uuid_id_and_payload() {
        let p = "11111111-1111-4111-8111-111111111111";
        assert_eq!(
            draft_path(
                "version",
                &serde_json::json!({"profile_id":p,"version_id":7})
            )
            .unwrap(),
            format!("/draft-transactions/version/{p}/7")
        );
        assert!(
            draft_path(
                "version",
                &serde_json::json!({"profile_id":p,"version_id":0})
            )
            .is_err()
        );
        assert!(
            draft_path(
                "receipt",
                &serde_json::json!({"profile_id":"../x","request_id":p})
            )
            .is_err()
        );
        assert!(draft_path("restore", &serde_json::json!({})).is_err());
        assert!(draft_path("submit", &serde_json::json!({"notes":"x".repeat(65_536)})).is_err());
    }
}

fn recommendation_path(action: &str, input: &Value) -> Result<&'static str, String> {
    let (path, limit) = match action {
        "preview" => ("/day-recommendations/preview", 16_384),
        "freshness" => ("/day-recommendations/freshness", 16_384),
        "impact_preview" => ("/day-impact/preview", 65_536),
        "impact_freshness" => ("/day-impact/freshness", 65_536),
        _ => return Err("Choose a supported read-only preview or freshness recheck.".into()),
    };
    if input.to_string().len() > limit {
        return Err("The recommendation input exceeds the supported size.".into());
    }
    Ok(path)
}

fn editor_uuid(value: &Value) -> Result<&str, String> {
    let value = value.as_str().ok_or("Choose an editor request identity.")?;
    if value.len() != 36
        || value.bytes().enumerate().any(|(i, b)| {
            if matches!(i, 8 | 13 | 18 | 23) {
                b != b'-'
            } else {
                !b.is_ascii_hexdigit()
            }
        })
    {
        return Err("Choose a valid editor UUID.".into());
    }
    Ok(value)
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
    fn impact_transport_accepts_annual_scope_only_on_fixed_read_only_paths() {
        let rows: Vec<Value> = (1..=366).map(|id|
            serde_json::json!({"record_kind":"FullDayDraft","record_id":id,"expected_revision":1})
        ).collect();
        let input = serde_json::json!({"replacements":rows});
        assert!(input.to_string().len() > 16_384);
        assert_eq!(
            recommendation_path("impact_preview", &input).unwrap(),
            "/day-impact/preview"
        );
        assert_eq!(
            recommendation_path("impact_freshness", &input).unwrap(),
            "/day-impact/freshness"
        );
        assert!(recommendation_path("preview", &input).is_err());
        for action in ["apply", "publish", "impact_preview/../submit", ""] {
            assert!(recommendation_path(action, &input).is_err());
        }
    }

    #[test]
    fn impact_transport_rejects_oversized_input_before_network() {
        let oversized = serde_json::json!({"unexpected": "x".repeat(65_536)});
        assert!(recommendation_path("impact_preview", &oversized).is_err());
        assert!(recommendation_path("impact_freshness", &oversized).is_err());
        assert_eq!(
            recommendation_path("preview", &serde_json::json!({})).unwrap(),
            "/day-recommendations/preview"
        );
    }
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

    #[test]
    fn editor_receipt_path_rejects_injected_or_partial_identities() {
        assert!(editor_uuid(&serde_json::json!("11111111-1111-4111-8111-111111111111")).is_ok());
        for value in [
            serde_json::json!("../receipt"),
            serde_json::json!("11111111-1111-4111-8111-11111111111/"),
            serde_json::json!(1),
            serde_json::Value::Null,
        ] {
            assert!(editor_uuid(&value).is_err());
        }
    }
}
