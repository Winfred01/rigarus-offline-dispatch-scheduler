# Issue #35 — local supervisor finalization

November 23, 2026, America/Toronto. See [sources, authority and plan](../design/2026-11-23-issue-35-supervisor-checklist.md). Tool-only continuation after the native calendar/Draft assertions in PR #84 reached PASS twice but the outer supervisor never produced its final exit summary. Those older aggregate runs remain BLOCKED; later evidence must not erase them.

## Confirmed reproduction and cause

Frozen event/output/transcript tail reads in separate Windows PowerShell 5.1 host processes all returned in approximately 0.2 seconds. A short no-NIC guest control with stage markers also completed process polling, tail reads, serial open/write/dispose, exit-code read, transcript close and cleanup (exit 0; 29.129 seconds including cold startup). That control used shallow serialization and did not establish a fix for the deep serializer.

The exact host boundary then reproduced the failure: `Get-Content -Tail 1` produced an extended string with six filesystem note properties. Embedding that object as `lastEvent` in `ConvertTo-Json -Depth 10` did not return within a separate five-second watchdog. The last local marker was before JSON, not before the file read. Materializing `.ToString()` removed those note properties; the same record serialized to 170 characters in 40 milliseconds. An independent copied plain string also completed in 36 milliseconds.

The stalled outer callback was serializing Provider/Drive metadata attached to the string, rather than only reporting log text. This explains the missing progress/final report while the independent GUI worker continued and finished. Switching process launch/redirection did not change that boundary. This does not establish a product/WebView2 defect or attribute every earlier UIA failure to this cause.

## Fix and regression boundary

`Read-AcceptanceProgressText` returns the final line as primitive text. Missing/empty/non-file input supplies no event; real file-read errors propagate. Callers construct a primitive-only progress record. The existing support file is already included in acceptance kits. No product, native assertion, Save retry, package, schema, dependency or wait profile is changed.

The harness uses a real log path containing spaces, verifies the Windows PowerShell decorated-string fixture, exact final text and absence of note properties, then performs a depth-12 JSON round trip and checks that `lastEvent` remains a string without Provider/Drive/Credential fields. It also covers absent/empty/non-file paths and an exclusively locked file. Raw deep serialization is not run unbounded in CI.

## Live-writer failure discovered during verification

The first guest raw/fixed comparison confirmed the boundary: raw depth ten reached the independent watchdog in 40.221 seconds; fixed completed with exit0 in 30.590 seconds. A native wrapper then failed after 107.567 seconds when its advisory progress read collided with an append. That local poll now reports narrowly recognized sharing codes 32/33 as busy and defers to its next existing bounded poll; other errors still fail, and native writes/assertions are not retried.

The next normal Crew-choice native run completed with exit0 in 158.845 seconds, unchanged default DB and no remaining product processes. Its subsequent hidden full run exited1: the actual exception chain identifies `Write-AcceptanceEvent` / `Add-Content`, IOException `0x80070020`, before the first Data navigation. The unchanged product window was enabled, visible and foreground; this was a log-writer failure, not a demonstrated product/selector defect. Both failed aggregate attempts and their stage records remain local; the full flow was not certified.

A separate Windows PowerShell 5.1 host reproduction holds a real read handle open with read/write sharing. Old `Add-Content` throws the same `0x80070020`; the new explicit append stream permits the reader and writes correctly. `Write-AcceptanceEvent` now uses `FileShare.ReadWrite` with UTF-8 encoding and deterministic disposal. This supports one verifier writer plus supervisor readers; it does not claim atomic arbitrary multi-writer logging. The harness verifies Unicode, one UTF-8 preamble, preservation of both prior lines and explicit exclusive-lock write failure. All existing harness cases still pass. No product/package, native assertion, Save retry or GUI/exit wait profile changes.

| Verification | Status at commit | Boundary |
| --- | --- | --- |
| Frozen host tail-read isolation | PASS | Three separate bounded Windows PowerShell 5.1 processes |
| Exact host deep-JSON failure and plain-text comparison | PASS, diagnosis | Raw process stopped at 5 seconds; two text variants completed in 40/36 ms; raw diagnostics stay local |
| Guest shallow control / phase instrumentation | PASS | 29.129 s / exit 0, ordinary isolated no-NIC Win11 x64 build26100 guest; no product scenario run |
| Final helper / existing acceptance harness | PASS | Windows PowerShell 5.1, including locked-file failure, deep JSON round trip and all existing wait/sidecar/UIA/WAL cases |
| Guest raw-versus-fixed depth-10 comparison | PASS | Raw watchdog 40.221 s; fixed exit0 / 30.590 s, matching stage markers; later repeat also reproduced |
| Matching package native GUI / complete outer exit | Pending | Same installer/client/sidecar; separate synthetic profile, actual result and connectivity required |
| Final closed-disk identity/data audit | Pending | Only after guest process and QMP are closed |
| Parser/docs/whitespace/privacy | PASS | All PowerShell files parse; Markdown links/fences and staged whitespace pass; privacy scan of 225 indexed paths |
| Current-head Windows CI | Pending | Final evidence attached to PR; CI is not native acceptance |
| Customer Demo/UAT / production | NOT RUN / NOT GRANTED | No sign-off or Release authorization |

The pending rows are a source snapshot; final PR/Issue updates identify the actual results without claiming a new CI package was tested. Do not close #35/#42 or infer complete RC readiness from this tool fix.
