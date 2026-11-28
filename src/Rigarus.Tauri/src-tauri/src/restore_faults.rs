//! Separate synthetic-only archive fault; no permissions or production storage changes.
use serde_json::Value;
use std::{
    fs::File,
    io::Read,
    path::{Path, PathBuf},
};

const ERROR: &str = "Synthetic Restore fault state is invalid; retain the original request.";

pub fn archive_fault(database: &Path, original: &Value) -> Result<Option<String>, String> {
    if std::env::var("RIGARUS_DRAFT_RESTORE_FAULT_TEST").as_deref() != Ok("1") {
        return Ok(None);
    }
    if std::env::var("RIGARUS_DRAFT_RESTORE_TEST").as_deref() != Ok("1") {
        return Err(ERROR.into());
    }
    let root = std::env::var_os("RIGARUS_SMOKE_DATA_ROOT").ok_or(ERROR)?;
    let data = PathBuf::from(root).join("data");
    if database != data.join("rigarus.db") {
        return Err(ERROR.into());
    }
    claim(&data, original)
}

fn read(path: &Path) -> Result<Value, String> {
    let mut bytes = Vec::new();
    File::open(path)
        .map_err(|_| ERROR)?
        .take(4097)
        .read_to_end(&mut bytes)
        .map_err(|_| ERROR)?;
    if bytes.len() > 4096 {
        return Err(ERROR.into());
    }
    serde_json::from_slice(&bytes).map_err(|_| ERROR.into())
}

fn claim(data: &Path, original: &Value) -> Result<Option<String>, String> {
    use std::{fs::OpenOptions, io::Write};
    let plan = read(&data.join("restore-fault.json"))?;
    let request = &original["request"];
    if plan.as_object().is_none_or(|v| v.len() != 6)
        || plan["format"] != "rigarus-restore-fault-v1"
        || plan["synthetic_only"] != true
        || plan["profile_id"] != request["profile_id"]
        || plan["source_version_id"] != request["source_version_id"]
        || !matches!(
            plan["transport"].as_str(),
            Some(
                "none"
                    | "after_commit_timeout"
                    | "before_commit_timeout"
                    | "refresh_once"
                    | "wrong_profile_once"
            )
        )
    {
        return Err(ERROR.into());
    }
    let mode = match plan["archive"].as_str() {
        Some("none") => return Ok(None),
        Some(v @ ("write_once" | "flush_once")) => v,
        _ => return Err(ERROR.into()),
    };
    let folder = data.join("restore-fault-state");
    std::fs::create_dir_all(&folder).map_err(|_| ERROR)?;
    let path = folder.join("archive.json");
    let identity = serde_json::json!({"mode":mode,"request":request});
    // The complete original request is bounded by the existing native proof.
    let bytes = serde_json::to_vec(&identity).map_err(|_| ERROR)?;
    if bytes.len() > 4096 {
        return Err(ERROR.into());
    }
    match OpenOptions::new().write(true).create_new(true).open(&path) {
        Ok(mut file) => {
            file.write_all(&bytes)
                .and_then(|_| file.sync_all())
                .map_err(|_| ERROR)?;
            Ok(Some(mode.into()))
        }
        Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => {
            if read(&path)? != identity {
                return Err(ERROR.into());
            }
            Ok(None)
        }
        Err(_) => Err(ERROR.into()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn strict_identity_and_durable_single_archive_fault() {
        let root = std::env::temp_dir().join(format!(
            "rigarus-fault-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        std::fs::create_dir(&root).unwrap();
        let original = serde_json::json!({"request":{"profile_id":"synthetic","source_version_id":1,"request_id":"original"}});
        let mut plan = serde_json::json!({"format":"rigarus-restore-fault-v1","synthetic_only":true,"profile_id":"synthetic","source_version_id":1,"transport":"none","archive":"flush_once"});
        let path = root.join("restore-fault.json");
        std::fs::write(&path, plan.to_string()).unwrap();
        assert_eq!(claim(&root, &original).unwrap(), Some("flush_once".into()));
        assert_eq!(claim(&root, &original).unwrap(), None);
        let mut other = original.clone();
        other["request"]["request_id"] = serde_json::json!("replacement");
        assert!(claim(&root, &other).is_err());
        plan["profile_id"] = serde_json::json!("wrong");
        std::fs::write(&path, plan.to_string()).unwrap();
        assert!(claim(&root, &original).is_err());
        std::fs::remove_dir_all(root).unwrap();
    }
}
