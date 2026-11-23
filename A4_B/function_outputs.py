"""Collect and save per-function results from the actual analysis execution."""

import json
from pathlib import Path
from uuid import uuid4

from common._recording import ACTIVE_RECORDS
from common.registry import FUNCTION_NAMES


def collect_results(analyse, model):
    records = {name: {"calls": []} for name in FUNCTION_NAMES}
    token = ACTIVE_RECORDS.set(records)
    try:
        result = analyse(model)
    finally:
        ACTIVE_RECORDS.reset(token)
    run_id = uuid4().hex
    for name, record in records.items():
        record.update(function=name, run_id=run_id,
                      status="success" if record["calls"] else "not_called",
                      call_count=len(record["calls"]))
    return {**result, "run_id": run_id, "function_results": records}


def write_function_results(result, root):
    for name, record in result["function_results"].items():
        folder = Path(root) / name / "results"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"result_{name}.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        temporary.replace(path)
