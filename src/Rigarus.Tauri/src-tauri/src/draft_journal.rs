//! Local exact-request recovery. The permanent guard file is locked by its OS handle.
use serde_json::Value;
use std::{
    fs::{self, File, OpenOptions},
    io::{Read, Write},
    os::windows::fs::OpenOptionsExt,
    path::{Path, PathBuf},
};

pub const LIMIT: usize = 8_000_000;
const ERROR: &str = "Draft recovery storage is unavailable or occupied. Keep the original request; do not delete recovery files or create a replacement.";

pub struct Journal {
    folder: PathBuf,
    _guard: File,
}
impl Journal {
    pub fn open(database: &Path, profile: &str) -> Result<Self, String> {
        if profile.len() != 36 || !profile.bytes().all(|b| b.is_ascii_hexdigit() || b == b'-') {
            return Err(ERROR.into());
        }
        let folder = database
            .parent()
            .ok_or(ERROR)?
            .join("draft-recovery")
            .join(profile);
        fs::create_dir_all(&folder).map_err(|_| ERROR)?;
        let guard = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .truncate(false)
            .share_mode(0)
            .open(folder.join("guard.lock"))
            .map_err(|_| ERROR)?;
        Ok(Self {
            folder,
            _guard: guard,
        })
    }
    pub fn pending(&self) -> Result<Option<Value>, String> {
        let path = self.folder.join("pending.json");
        let mut f = match File::open(&path) {
            Ok(f) => f,
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => return Ok(None),
            Err(_) => return Err(ERROR.into()),
        };
        let mut data = Vec::new();
        Read::by_ref(&mut f)
            .take((LIMIT + 1) as u64)
            .read_to_end(&mut data)
            .map_err(|_| ERROR)?;
        if data.len() > LIMIT {
            return Err(ERROR.into());
        }
        let value: Value = serde_json::from_slice(&data).map_err(|_| ERROR)?;
        if !value["request"].is_object() || !value["reviewed"].is_object() {
            return Err(ERROR.into());
        }
        Ok(Some(value))
    }
    pub fn remember(&self, value: &Value) -> Result<(), String> {
        if let Some(old) = self.pending()? {
            return if old == *value {
                Ok(())
            } else {
                Err("Resolve the original Draft request before another save.".into())
            };
        }
        self.write_new(&self.folder.join("pending.json"), value)
    }
    fn write_new(&self, path: &Path, value: &Value) -> Result<(), String> {
        let data = serde_json::to_vec(value).map_err(|_| ERROR)?;
        if data.len() > LIMIT {
            return Err(ERROR.into());
        }
        let mut f = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(path)
            .map_err(|_| ERROR)?;
        f.write_all(&data)
            .and_then(|_| f.sync_all())
            .map_err(|_| ERROR.into())
    }
    pub fn acknowledge(&self, expected: &Value, receipt: &Value) -> Result<(), String> {
        if self.pending()?.as_ref() != Some(expected) {
            return Err(ERROR.into());
        }
        let id = expected["request"]["request_id"].as_str().ok_or(ERROR)?;
        if id.len() != 36 || !id.bytes().all(|b| b.is_ascii_hexdigit() || b == b'-') {
            return Err(ERROR.into());
        }
        let archive = self.folder.join(format!("receipt-{id}.json"));
        if archive.exists() {
            let mut bytes = Vec::new();
            File::open(&archive)
                .map_err(|_| ERROR)?
                .take((LIMIT + 1) as u64)
                .read_to_end(&mut bytes)
                .map_err(|_| ERROR)?;
            if bytes.len() > LIMIT
                || serde_json::from_slice::<Value>(&bytes).map_err(|_| ERROR)? != *receipt
            {
                return Err(ERROR.into());
            }
        } else {
            self.write_new(&archive, receipt)?;
        }
        fs::remove_file(self.folder.join("pending.json")).map_err(|_| ERROR.into())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn archive_failure_never_releases_pending_request() {
        let root = folder();
        let j = Journal::open(&root.join("rigarus.db"), PROFILE).unwrap();
        j.remember(&envelope()).unwrap();
        fs::create_dir(
            j.folder
                .join("receipt-22222222-2222-4222-8222-222222222222.json"),
        )
        .unwrap();
        assert!(
            j.acknowledge(&envelope(), &serde_json::json!({"saved":1}))
                .is_err()
        );
        assert_eq!(j.pending().unwrap(), Some(envelope()));
        assert_eq!(root.parent().unwrap(), std::env::temp_dir().as_path());
        drop(j);
        fs::remove_dir_all(root).unwrap();
    }
    fn folder() -> PathBuf {
        let p = std::env::temp_dir().join(format!(
            "rigarus-journal-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir_all(&p).unwrap();
        p
    }
    const PROFILE: &str = "11111111-1111-4111-8111-111111111111";
    fn envelope() -> Value {
        serde_json::json!({"request":{"request_id":"22222222-2222-4222-8222-222222222222"},"reviewed":{}})
    }
    #[test]
    fn journal_reopen_replay_and_exact_ack() {
        let root = folder();
        let db = root.join("rigarus.db");
        {
            let j = Journal::open(&db, PROFILE).unwrap();
            j.remember(&envelope()).unwrap();
            assert!(Journal::open(&db, PROFILE).is_err());
            assert!(j.remember(&serde_json::json!({"other":1})).is_err());
        }
        {
            let j = Journal::open(&db, PROFILE).unwrap();
            assert_eq!(j.pending().unwrap(), Some(envelope()));
            j.remember(&envelope()).unwrap();
            assert!(
                j.acknowledge(&serde_json::json!({}), &serde_json::json!({}))
                    .is_err()
            );
            j.acknowledge(&envelope(), &serde_json::json!({"saved":1}))
                .unwrap();
            assert_eq!(j.pending().unwrap(), None);
        }
        fs::remove_dir_all(root).unwrap();
    }
    #[test]
    fn incomplete_or_large_journal_fails_closed() {
        let root = folder();
        let db = root.join("rigarus.db");
        let j = Journal::open(&db, PROFILE).unwrap();
        fs::write(j.folder.join("pending.json"), b"{").unwrap();
        assert!(j.pending().is_err());
        assert!(j.remember(&envelope()).is_err());
        fs::write(j.folder.join("pending.json"), vec![b' '; LIMIT + 1]).unwrap();
        assert!(j.pending().is_err());
        drop(j);
        fs::remove_dir_all(root).unwrap();
    }
}
