//! Exact synthetic Restore proof/receipt validation, independent of Apply.
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;

pub const ERROR: &str = "Restore proof/result is incomplete or uncertain. Retain and resolve the original request; never replace its key.";
pub const FORMAT: &str = "rigarus-restore-journal-v1";
pub const LIMIT: usize = 8_000_000;
type Result<T> = std::result::Result<T, String>;
pub fn check(ok: bool) -> Result<()> {
    if ok { Ok(()) } else { Err(ERROR.into()) }
}
pub fn id(v: &Value) -> Result<u64> {
    v.as_u64()
        .filter(|n| *n > 0 && *n < 9_007_199_254_740_991)
        .ok_or(ERROR.into())
}
pub fn uuid(v: &Value) -> Result<&str> {
    let s = v.as_str().ok_or(ERROR)?;
    check(
        s.len() == 36
            && s.bytes().enumerate().all(|(i, b)| {
                if [8, 13, 18, 23].contains(&i) {
                    b == b'-'
                } else {
                    b.is_ascii_digit() || (b'a'..=b'f').contains(&b)
                }
            }),
    )?;
    Ok(s)
}
fn sha(v: &Value) -> bool {
    v.as_str().is_some_and(|s| {
        s.len() == 64
            && s.bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    })
}
pub fn flags(v: &Value) -> bool {
    v["validation_status"] == "Pending" && v["applyable"] == false && v["publishable"] == false
}
pub fn digest(v: &Value) -> String {
    fn canonical(v: &Value) -> String {
        match v {
            Value::Object(map) => {
                let mut keys: Vec<_> = map.keys().collect();
                keys.sort();
                format!(
                    "{{{}}}",
                    keys.into_iter()
                        .map(|k| format!(
                            "{}:{}",
                            serde_json::to_string(k).unwrap(),
                            canonical(&map[k])
                        ))
                        .collect::<Vec<_>>()
                        .join(",")
                )
            }
            Value::Array(a) => format!(
                "[{}]",
                a.iter().map(canonical).collect::<Vec<_>>().join(",")
            ),
            _ => v.to_string(),
        }
    }
    format!("{:x}", Sha256::digest(canonical(v).as_bytes()))
}
fn date(v: &Value) -> bool {
    let Some(s) = v.as_str() else {
        return false;
    };
    if s.len() != 10
        || !s.bytes().enumerate().all(|(i, b)| {
            if i == 4 || i == 7 {
                b == b'-'
            } else {
                b.is_ascii_digit()
            }
        })
    {
        return false;
    }
    let (y, m, d) = (
        s[..4].parse::<u32>().unwrap(),
        s[5..7].parse::<u32>().unwrap(),
        s[8..].parse::<u32>().unwrap(),
    );
    let max = match m {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        2 => {
            if y % 4 == 0 && (y % 100 != 0 || y % 400 == 0) {
                29
            } else {
                28
            }
        }
        _ => 0,
    };
    y > 0 && d > 0 && d <= max
}
fn ids(v: &Value) -> Result<Vec<u64>> {
    let a = v.as_array().ok_or(ERROR)?;
    check(a.len() <= 100)?;
    let values: Vec<_> = a.iter().map(id).collect::<Result<_>>()?;
    check(values.iter().collect::<BTreeSet<_>>().len() == values.len())?;
    Ok(values)
}
fn rows(v: &Value) -> Result<&Vec<Value>> {
    let a = v.as_array().ok_or(ERROR)?;
    check(a.len() <= 366)?;
    let mut seen = BTreeSet::new();
    for r in a {
        check(
            r.as_object().is_some_and(|m| m.len() == 10)
                && r["record_kind"] == "FullDayDraft"
                && seen.insert(id(&r["id"])?)
                && date(&r["local_date"])
                && matches!(r["status"].as_str(), Some("Draft" | "Cancelled")),
        )?;
        for k in ["revision", "work_item_id", "project_id", "crew_id"] {
            id(&r[k])?;
        }
        check(
            r["notes"]
                .as_str()
                .is_some_and(|s| s.chars().count() <= 2000 && !s.contains('\0')),
        )?;
        if !r["employee_ids"].is_null() {
            ids(&r["employee_ids"])?;
        }
    }
    Ok(a)
}
pub fn original(v: &Value, profile: &str, source: u64) -> Result<()> {
    check(
        flags(v)
            && v["outcome"] == "Committed"
            && v["database_identity"] == profile
            && v["version_id"] == source
            && v["plan"]["format"] == "rigarus-unconfirmed-draft-v1"
            && v.to_string().len() <= 4_000_000,
    )?;
    let after = rows(&v["after"])?;
    check(
        !after.is_empty()
            && rows(&v["plan"]["before"])?
                .iter()
                .all(|r| after.iter().any(|a| a["id"] == r["id"])),
    )
}
pub fn bundle(source: &Value, plan: &Value, profile: &str, source_id: u64) -> Result<()> {
    original(source, profile, source_id)?;
    check(
        flags(plan)
            && plan["production_writes_enabled"] == false
            && plan["format"] == "rigarus-draft-restore-v1"
            && plan["database_identity"] == profile
            && plan["source_record_kind"] == "DraftVersion"
            && plan["source_version_id"] == source_id
            && plan["source_fingerprint"] == digest(source)
            && sha(&plan["plan_fingerprint"])
            && plan.to_string().len() <= 4_000_000,
    )?;
    let mut unsigned = plan.clone();
    unsigned
        .as_object_mut()
        .ok_or(ERROR)?
        .remove("plan_fingerprint");
    check(
        plan["plan_fingerprint"] == digest(&unsigned) && plan["before_restore"] == source["after"],
    )?;
    let current = rows(&plan["before_restore"])?;
    let desired = rows(&plan["proposed_restore"])?;
    check(current.len() == desired.len())?;
    for (old, new) in current.iter().zip(desired) {
        let mut target = source["plan"]["before"]
            .as_array()
            .ok_or(ERROR)?
            .iter()
            .find(|r| r["id"] == old["id"])
            .cloned()
            .unwrap_or_else(|| {
                let mut r = old.clone();
                r["status"] = json!("Cancelled");
                r
            });
        target["revision"] = json!(id(&old["revision"])? + 1);
        check(target == *new)?;
    }
    let blockers = plan["blockers"].as_array().ok_or(ERROR)?;
    check(
        (plan["status"] == "Current" && blockers.is_empty())
            || (plan["status"] == "Blocked" && !blockers.is_empty()),
    )?;
    let warnings = plan["warnings"].as_array().ok_or(ERROR)?;
    check(warnings.len() <= 20000 && !warnings.is_empty())?;
    let mut seen = BTreeSet::new();
    for w in warnings {
        let mut item = w.clone();
        item.as_object_mut().ok_or(ERROR)?.remove("warning_id");
        check(
            w["state"] == "Pending"
                && sha(&w["warning_id"])
                && w["warning_id"] == digest(&item)
                && seen.insert(w["warning_id"].as_str().ok_or(ERROR)?)
                && w["check"].as_str().is_some_and(|s| !s.is_empty())
                && w["reason"].as_str().is_some_and(|s| !s.is_empty()),
        )?;
    }
    if plan["status"] == "Current" {
        observations(&plan["observations"], desired)?;
    }
    Ok(())
}
fn observations(v: &Value, desired: &[Value]) -> Result<()> {
    let active: Vec<_> = desired.iter().filter(|r| r["status"] == "Draft").collect();
    let observations = v.as_array().ok_or(ERROR)?;
    check(observations.len() == active.len())?;
    let mut seen = BTreeSet::new();
    for o in observations {
        let r = active.iter().find(|r| r["id"] == o["id"]).ok_or(ERROR)?;
        check(
            flags(o)
                && o["record_kind"] == "FullDayDraft"
                && seen.insert(id(&o["id"])?)
                && o["staffing_configured"] == !r["employee_ids"].is_null(),
        )?;
        for k in [
            "revision",
            "work_item_id",
            "project_id",
            "crew_id",
            "local_date",
            "notes",
        ] {
            check(o[k] == r[k])?;
        }
        let workers = o["workers"].as_array().ok_or(ERROR)?;
        let mut actual: Vec<_> = workers
            .iter()
            .map(|w| id(&w["id"]))
            .collect::<Result<_>>()?;
        let mut expected = if r["employee_ids"].is_null() {
            vec![]
        } else {
            ids(&r["employee_ids"])?
        };
        actual.sort();
        expected.sort();
        check(actual == expected)?;
        let checks = o["checks"].as_array().ok_or(ERROR)?;
        for name in [
            "DailyCalendars",
            "PersonnelConflicts",
            "ApprovedDriver",
            "CrewType",
            "MinimumStaffing",
            "SkillsLevel1",
            "SkillsLevel2",
            "SkillsLevel3",
            "Qualifications",
            "Foreman",
            "ActualRig",
            "VehicleCategory",
            "WeekendConsent",
        ] {
            check(checks.iter().filter(|c| c["check"] == name).count() == 1)?;
        }
        check(checks.iter().all(|c| {
            c["reasons"].as_array().is_some()
                && (matches!(c["state"].as_str(), Some("Pending" | "Satisfied"))
                    || (c["check"] == "DailyCalendars" && c["state"] == "Matched"))
        }))?;
    }
    Ok(())
}
pub fn envelope(v: &Value, profile: &str) -> Result<()> {
    check(
        v.to_string().len() <= LIMIT
            && v.as_object().is_some_and(|m| m.len() == 5)
            && v["format"] == FORMAT
            && v["operation"] == "DraftRestore",
    )?;
    let r = &v["request"];
    uuid(&r["profile_id"])?;
    uuid(&r["request_id"])?;
    check(
        r.as_object().is_some_and(|m| m.len() == 7)
            && r["profile_id"] == profile
            && r["source_record_kind"] == "DraftVersion"
            && r["confirmed"] == true
            && r.to_string().len() <= 2_000_000,
    )?;
    bundle(
        &v["source"],
        &v["reviewed"],
        profile,
        id(&r["source_version_id"])?,
    )?;
    check(
        v["reviewed"]["status"] == "Current"
            && r["plan_fingerprint"] == v["reviewed"]["plan_fingerprint"],
    )?;
    let mut expected: Vec<_> = v["reviewed"]["warnings"]
        .as_array()
        .ok_or(ERROR)?
        .iter()
        .map(|w| w["warning_id"].clone())
        .collect();
    let mut got = r["acknowledged_warning_ids"]
        .as_array()
        .ok_or(ERROR)?
        .clone();
    expected.sort_by_key(Value::to_string);
    got.sort_by_key(Value::to_string);
    check(expected == got)
}
pub fn receipt(pending: &Value, result: &Value, profile: &str) -> Result<()> {
    envelope(pending, profile)?;
    let request = &pending["request"];
    check(
        result.to_string().len() <= LIMIT
            && flags(result)
            && result["database_identity"] == profile
            && result["request_id"] == request["request_id"]
            && result["source_record_kind"] == "DraftVersion"
            && result["source_version_id"] == request["source_version_id"]
            && result["confirmation"] == *request
            && result["recorded_at"].as_str().is_some_and(|s| {
                s.len() >= 20 && s.len() <= 64 && (s.ends_with("+00:00") || s.ends_with('Z'))
            }),
    )?;
    if result["outcome"] == "Rejected" {
        return check(matches!(
            result["code"].as_str(),
            Some(
                "SOURCE_NOT_FOUND"
                    | "Stale"
                    | "Blocked"
                    | "STALE_RESTORE_PLAN"
                    | "EACH_PENDING_ITEM_REQUIRES_CONFIRMATION"
                    | "FINAL_RESOURCE_REVALIDATION_FAILED"
            )
        ));
    }
    id(&result["version_id"])?;
    check(
        result["outcome"] == "Committed"
            && result["record_kind"] == "DraftRestoreVersion"
            && result["plan"] == pending["reviewed"]
            && result["after"] == pending["reviewed"]["proposed_restore"]
            && result["observations"] == pending["reviewed"]["observations"],
    )?;
    observations(&result["observations"], rows(&result["after"])?)
}

#[cfg(test)]
mod tests {
    use super::*;
    const PROFILE: &str = "11111111-1111-4111-8111-111111111111";
    fn fixture() -> (Value, Value) {
        let row = json!({"record_kind":"FullDayDraft","id":1,"revision":2,"work_item_id":1,"project_id":1,"crew_id":1,"local_date":"2026-11-27","notes":"Synthetic café note","status":"Cancelled","employee_ids":[8]});
        let source = json!({"outcome":"Committed","validation_status":"Pending","applyable":false,"publishable":false,"database_identity":PROFILE,"version_id":1,"plan":{"format":"rigarus-unconfirmed-draft-v1","before":[row.clone()]},"after":[row.clone()]});
        let mut target = row.clone();
        target["revision"] = json!(3);
        let w = json!({"record_kind":"DraftRestore","check":"UNCONFIRMED_DRAFT_ONLY_NO_DISPATCH","state":"Pending","reason":"UNCONFIRMED_DRAFT_ONLY_NO_DISPATCH"});
        let mut warning = w.clone();
        warning["warning_id"] = json!(digest(&w));
        let mut plan = json!({"format":"rigarus-draft-restore-v1","validation_status":"Pending","applyable":false,"publishable":false,"production_writes_enabled":false,"database_identity":PROFILE,"source_record_kind":"DraftVersion","source_version_id":1,"source_fingerprint":digest(&source),"before_restore":[row],"proposed_restore":[target.clone()],"observations":[],"warnings":[warning.clone()],"blockers":[],"status":"Current"});
        plan["plan_fingerprint"] = json!(digest(&plan));
        let request = json!({"profile_id":PROFILE,"request_id":"22222222-2222-4222-8222-222222222222","source_record_kind":"DraftVersion","source_version_id":1,"plan_fingerprint":plan["plan_fingerprint"],"confirmed":true,"acknowledged_warning_ids":[warning["warning_id"].clone()]});
        let envelope = json!({"operation":"DraftRestore","format":FORMAT,"source":source,"reviewed":plan.clone(),"request":request.clone()});
        let result = json!({"outcome":"Committed","validation_status":"Pending","applyable":false,"publishable":false,"database_identity":PROFILE,"request_id":request["request_id"],"source_record_kind":"DraftVersion","source_version_id":1,"confirmation":request,"record_kind":"DraftRestoreVersion","version_id":1,"recorded_at":"2026-11-27T12:00:00+00:00","plan":plan,"after":[target],"observations":[]});
        (envelope, result)
    }
    #[test]
    fn exact_inverse_hashes_receipt_and_stable_typed_id() {
        let (p, r) = fixture();
        envelope(&p, PROFILE).unwrap();
        receipt(&p, &r, PROFILE).unwrap();
        assert_eq!(r["after"][0]["id"], p["source"]["after"][0]["id"]);
        assert_eq!(r["after"][0]["revision"], 3);
        assert_eq!(r["validation_status"], "Pending");
    }
    #[test]
    fn source_plan_and_each_warning_are_hash_bound() {
        let (p, _) = fixture();
        for path in [
            "/source/after/0/notes",
            "/reviewed/proposed_restore/0/notes",
            "/reviewed/warnings/0/reason",
            "/reviewed/source_fingerprint",
            "/request/plan_fingerprint",
        ] {
            let mut bad = p.clone();
            *bad.pointer_mut(path).unwrap() = json!("changed");
            assert!(envelope(&bad, PROFILE).is_err(), "{path}");
        }
        for value in [
            json!([]),
            json!([
                p["reviewed"]["warnings"][0]["warning_id"].clone(),
                p["reviewed"]["warnings"][0]["warning_id"].clone()
            ]),
        ] {
            let mut bad = p.clone();
            bad["request"]["acknowledged_warning_ids"] = value;
            assert!(envelope(&bad, PROFILE).is_err());
        }
    }
    #[test]
    fn receipt_identity_kind_revision_members_notes_and_flags_cannot_be_substituted() {
        let (p, r) = fixture();
        for (path, value) in [
            ("/request_id", json!(PROFILE)),
            ("/database_identity", json!("other")),
            ("/record_kind", json!("DraftVersion")),
            ("/source_record_kind", json!("LegacyHalfDay")),
            ("/source_version_id", json!(2)),
            ("/version_id", json!(0)),
            ("/after/0/revision", json!(2)),
            ("/after/0/employee_ids", json!([])),
            ("/after/0/notes", json!("changed")),
            ("/publishable", json!(true)),
            ("/applyable", json!(true)),
            ("/validation_status", json!("Passed")),
            ("/confirmation/confirmed", json!(false)),
            ("/plan/warnings", json!([])),
        ] {
            let mut bad = r.clone();
            *bad.pointer_mut(path).unwrap() = value;
            assert!(receipt(&p, &bad, PROFILE).is_err(), "{path}");
        }
    }
    #[test]
    fn only_sealed_known_rejection_can_be_archived_not_absence_or_unknown() {
        let (p, r) = fixture();
        let mut rejected = r;
        rejected["outcome"] = json!("Rejected");
        rejected["code"] = json!("Stale");
        receipt(&p, &rejected, PROFILE).unwrap();
        for value in [json!({"outcome":"NotFound"}), json!({"detail":"Stale"})] {
            assert!(receipt(&p, &value, PROFILE).is_err());
        }
        rejected["code"] = json!("UNKNOWN_STORAGE");
        assert!(receipt(&p, &rejected, PROFILE).is_err());
    }
    #[test]
    fn operation_source_kind_date_and_profile_are_strict() {
        let (p, _) = fixture();
        for (path, value) in [
            ("/operation", json!("DraftApply")),
            ("/format", json!("legacy")),
            ("/request/source_record_kind", json!("DraftRestoreVersion")),
            ("/request/profile_id", json!("other")),
            ("/source/after/0/local_date", json!("2026-02-31")),
            ("/source/after/0/id", json!(true)),
        ] {
            let mut bad = p.clone();
            *bad.pointer_mut(path).unwrap() = value;
            assert!(envelope(&bad, PROFILE).is_err());
        }
        assert!(uuid(&json!("------------------------------------")).is_err());
        assert!(id(&json!(0)).is_err());
    }
    #[test]
    fn real_python_synthetic_contract_has_native_exact_validation() {
        use std::{
            io::Read,
            process::{Command, Stdio},
            time::{Duration, Instant},
        };
        let backend = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .unwrap()
            .parent()
            .unwrap()
            .join("Rigarus.Backend");
        let mut child = Command::new(backend.join(".venv/Scripts/python.exe"))
            .arg("tests/desktop_restore_fixture.py")
            .current_dir(&backend)
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .expect("Run locked backend restore before cargo tests");
        let stdout = child.stdout.take().unwrap();
        let stderr = child.stderr.take().unwrap();
        let out = std::thread::spawn(move || {
            let mut bytes = Vec::new();
            stdout
                .take((LIMIT + 1) as u64)
                .read_to_end(&mut bytes)
                .unwrap();
            bytes
        });
        let err = std::thread::spawn(move || {
            let mut bytes = Vec::new();
            stderr.take(128_000).read_to_end(&mut bytes).unwrap();
            bytes
        });
        let start = Instant::now();
        let status = loop {
            if let Some(status) = child.try_wait().unwrap() {
                break status;
            }
            if start.elapsed() > Duration::from_secs(45) {
                let _ = child.kill();
                let _ = child.wait();
                panic!("Synthetic Python contract exceeded45s");
            }
            std::thread::sleep(Duration::from_millis(20));
        };
        let bytes = out.join().unwrap();
        let errors = err.join().unwrap();
        assert!(status.success(), "{}", String::from_utf8_lossy(&errors));
        assert!(bytes.len() <= LIMIT);
        let value: Value = serde_json::from_slice(&bytes).unwrap();
        let profile = value["pending"]["request"]["profile_id"].as_str().unwrap();
        envelope(&value["pending"], profile).unwrap();
        receipt(&value["pending"], &value["result"], profile).unwrap();
    }
}
