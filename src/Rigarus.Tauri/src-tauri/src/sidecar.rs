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
const SERVICE_UNAVAILABLE: &str = "The local service is unavailable. Reopen Rigarus to retry.";
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
        let ready = rx
            .recv_timeout(Duration::from_secs(20))
            .ok()
            .and_then(Result::ok);
        match ready {
            Some(ready) if ready.event == "ready" && ready.port > 0 => {
                service.port = ready.port;
                Ok(service)
            }
            _ => {
                let hint = error_rx.recv_timeout(Duration::from_millis(250));
                Err(match hint.as_deref().map(str::trim) {
                    Ok(OPEN_DATABASE) => OPEN_DATABASE,
                    Ok(INCOMPATIBLE_DATABASE) => INCOMPATIBLE_DATABASE,
                    _ => SERVICE_UNAVAILABLE,
                }
                .into())
            }
        }
    }

    pub fn is_running(&mut self) -> bool {
        matches!(self.child.try_wait(), Ok(None))
    }

    pub fn read_demo(&self) -> Result<DemoProject, String> {
        self.send(self.client.get(self.url("/demo")))
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
        let request = match id {
            Some(id) => self.client.put(self.url(&format!("/crews/{id}"))),
            None => self.client.post(self.url("/crews")),
        };
        self.send(request.json(crew))
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
