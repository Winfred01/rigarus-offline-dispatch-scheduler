"""Portable synthetic contract fixture for the Rust/TypeScript boundary tests."""

import json
import sys
from pathlib import Path


def contract():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from test_draft_restore import RestoreTests

    case = RestoreTests()
    case.setUp()
    try:
        source = case.source()
        plan = case.rprepare()
        request = case.rrequest(plan)
        request["source_record_kind"] = "DraftVersion"
        pending = dict(
            format="rigarus-restore-journal-v1",
            operation="DraftRestore",
            request=request,
            reviewed=plan,
            source=source,
        )
        response = case.rpost(request)
        assert response.status_code == 200, response.text
        assert response.json()["outcome"] == "Committed", response.json()
        return dict(pending=pending, result=response.json())
    finally:
        case.tearDown()
        case.doCleanups()


if __name__ == "__main__":
    print(json.dumps(contract(), ensure_ascii=True, separators=(",", ":")))
