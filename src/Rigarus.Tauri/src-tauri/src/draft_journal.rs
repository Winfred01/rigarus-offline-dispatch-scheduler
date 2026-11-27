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
        self.read_pending("pending.json")
    }
    pub fn restore_pending(&self) -> Result<Option<Value>, String> {
        let value = self.read_pending("restore-pending.json")?;
        if value.as_ref().is_some_and(|v| {
            v["operation"] != "DraftRestore" || v["format"] != "rigarus-restore-journal-v1"
        }) {
            return Err(ERROR.into());
        }
        Ok(value)
    }
    fn read_pending(&self, name: &str) -> Result<Option<Value>, String> {
        let path = self.folder.join(name);
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
        if self.restore_pending()?.is_some() {
            return Err("Resolve the original Restore request before another Draft Apply.".into());
        }
        if let Some(old) = self.pending()? {
            return if old == *value {
                self.sync_existing("pending.json", File::sync_all)
            } else {
                Err("Resolve the original Draft request before another save.".into())
            };
        }
        self.write_new(&self.folder.join("pending.json"), value)
    }
    pub fn remember_restore(&self, value: &Value) -> Result<(), String> {
        if self.pending()?.is_some() {
            return Err("Resolve the original Draft Apply before Restore.".into());
        }
        if value["operation"] != "DraftRestore" || value["format"] != "rigarus-restore-journal-v1" {
            return Err(ERROR.into());
        }
        if let Some(old) = self.restore_pending()? {
            return if old == *value {
                self.sync_existing("restore-pending.json", File::sync_all)
            } else {
                Err(ERROR.into())
            };
        }
        self.write_new(&self.folder.join("restore-pending.json"), value)
    }
    fn write_new(&self, path: &Path, value: &Value) -> Result<(), String> {
        self.write_new_synced(path, value, File::sync_all)
    }
    fn sync_existing(
        &self,
        name: &str,
        sync: fn(&File) -> std::io::Result<()>,
    ) -> Result<(), String> {
        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .open(self.folder.join(name))
            .map_err(|_| ERROR)?;
        sync(&file).map_err(|_| ERROR.into())
    }
    fn write_new_synced(
        &self,
        path: &Path,
        value: &Value,
        sync: fn(&File) -> std::io::Result<()>,
    ) -> Result<(), String> {
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
            .and_then(|_| sync(&f))
            .map_err(|_| ERROR.into())
    }
    pub fn acknowledge(&self, expected: &Value, receipt: &Value) -> Result<(), String> {
        self.archive_pending("pending.json", "receipt", expected, receipt)
    }
    pub fn acknowledge_restore(&self, expected: &Value, receipt: &Value) -> Result<(), String> {
        self.archive_pending("restore-pending.json", "restore-receipt", expected, receipt)
    }
    fn archive_pending(
        &self,
        name: &str,
        prefix: &str,
        expected: &Value,
        receipt: &Value,
    ) -> Result<(), String> {
        self.archive_pending_synced(name, prefix, expected, receipt, File::sync_all)
    }
    fn archive_pending_synced(
        &self,
        name: &str,
        prefix: &str,
        expected: &Value,
        receipt: &Value,
        sync: fn(&File) -> std::io::Result<()>,
    ) -> Result<(), String> {
        if self.read_pending(name)?.as_ref() != Some(expected) {
            return Err(ERROR.into());
        }
        let id = expected["request"]["request_id"].as_str().ok_or(ERROR)?;
        if id.len() != 36 || !id.bytes().all(|b| b.is_ascii_hexdigit() || b == b'-') {
            return Err(ERROR.into());
        }
        let archive = self.folder.join(format!("{prefix}-{id}.json"));
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
            self.sync_existing(&format!("{prefix}-{id}.json"), sync)?;
        } else {
            self.write_new_synced(&archive, receipt, sync)?;
        }
        fs::remove_file(self.folder.join(name)).map_err(|_| ERROR.into())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn restore_envelope() -> Value {
        let mut v = envelope();
        v["operation"] = serde_json::json!("DraftRestore");
        v["format"] = serde_json::json!("rigarus-restore-journal-v1");
        v
    }
    #[test]
    fn restore_and_apply_same_key_have_separate_archives_and_shared_interlock() {
        let root = folder();
        let db = root.join("rigarus.db");
        let apply = envelope();
        let restore = restore_envelope();
        {
            let j = Journal::open(&db, PROFILE).unwrap();
            j.remember(&apply).unwrap();
            assert!(j.remember_restore(&restore).is_err());
            assert_eq!(j.pending().unwrap(), Some(apply.clone()));
            j.acknowledge(&apply, &serde_json::json!({"operation":"Apply"}))
                .unwrap();
            j.remember_restore(&restore).unwrap();
            assert!(j.remember(&apply).is_err());
            assert!(Journal::open(&db, PROFILE).is_err());
        }
        {
            let j = Journal::open(&db, PROFILE).unwrap();
            assert_eq!(j.restore_pending().unwrap(), Some(restore.clone()));
            j.remember_restore(&restore).unwrap();
            assert!(
                j.acknowledge_restore(&apply, &serde_json::json!({}))
                    .is_err()
            );
            j.acknowledge_restore(&restore, &serde_json::json!({"operation":"Restore"}))
                .unwrap();
            assert!(j.restore_pending().unwrap().is_none());
            assert!(j.pending().unwrap().is_none());
            assert!(
                j.folder
                    .join("receipt-22222222-2222-4222-8222-222222222222.json")
                    .is_file()
            );
            assert!(
                j.folder
                    .join("restore-receipt-22222222-2222-4222-8222-222222222222.json")
                    .is_file()
            );
        }
        fs::remove_dir_all(root).unwrap();
    }
    #[test]
    fn restore_archive_sync_failure_keeps_pending_and_retry_reflushes_existing_archive() {
        fn failure(_: &File) -> std::io::Result<()> {
            Err(std::io::Error::other("synthetic flush failure"))
        }
        let root = folder();
        let db = root.join("rigarus.db");
        let original = restore_envelope();
        let result = serde_json::json!({"saved":"synthetic"});
        {
            let j = Journal::open(&db, PROFILE).unwrap();
            j.remember_restore(&original).unwrap();
            assert!(
                j.archive_pending_synced(
                    "restore-pending.json",
                    "restore-receipt",
                    &original,
                    &result,
                    failure
                )
                .is_err()
            );
            assert_eq!(j.restore_pending().unwrap(), Some(original.clone()));
            assert!(
                j.archive_pending_synced(
                    "restore-pending.json",
                    "restore-receipt",
                    &original,
                    &result,
                    failure
                )
                .is_err()
            );
            assert_eq!(j.restore_pending().unwrap(), Some(original.clone()));
            assert!(
                j.acknowledge_restore(&original, &serde_json::json!({"mismatch":true}))
                    .is_err()
            );
        }
        let j = Journal::open(&db, PROFILE).unwrap();
        j.acknowledge_restore(&original, &result).unwrap();
        assert!(j.restore_pending().unwrap().is_none());
        drop(j);
        fs::remove_dir_all(root).unwrap();
    }
    #[test]
    fn unreadable_malformed_or_oversized_restore_never_allows_apply_replacement() {
        let root = folder();
        let j = Journal::open(&root.join("rigarus.db"), PROFILE).unwrap();
        for bytes in [
            b"{".to_vec(),
            vec![b' '; LIMIT + 1],
            serde_json::to_vec(&envelope()).unwrap(),
        ] {
            fs::write(j.folder.join("restore-pending.json"), bytes).unwrap();
            assert!(j.restore_pending().is_err());
            assert!(j.remember(&envelope()).is_err());
            assert!(j.remember_restore(&restore_envelope()).is_err());
        }
        drop(j);
        fs::remove_dir_all(root).unwrap();
    }
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
        static SEQUENCE: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
        let p = std::env::temp_dir().join(format!(
            "rigarus-journal-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            SEQUENCE.fetch_add(1, std::sync::atomic::Ordering::Relaxed)
        ));
        fs::create_dir(&p).unwrap();
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
