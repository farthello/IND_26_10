# A4_A — IFC daylight screening

This adapts the course's Week 11 IFC starter and Working Together example to the
existing A4 daylight tool. The original A4 files are unchanged.

## Run

From the repository root, using an environment with these requirements installed:

```powershell
.\.venv\Scripts\python.exe -m pip install -r A4_A/requirements.txt
.\.venv\Scripts\python.exe A4_A/runall.py
```

`settings.py` defaults to `../model/25-08-D-ARCH.ifc`, resolved relative to A4_A.
Override it for one run:

```powershell
.\.venv\Scripts\python.exe A4_A/runall.py "model/B308X.ifc"
```

Command-line relative paths are resolved from your working directory. The model
is opened once and shared without modification between the registered analyses.
Do not commit private models.

## Structure and reuse

- `runall.py`: model loading, analysis registration and output orchestration.
- `settings.py`: default model path.
- `daylight/src/main.py`: reusable `analyse(model)` entry point.
- `daylight/src/daylight_analysis.py`: geometry, area extraction and room matching.
- `daylight/src/analysis_formatted.py`: JSON-compatible screening rows and summary counts.

With A4_A on the Python import path:

```python
from daylight.src.main import analyse
result = analyse(model)
```

Importing does not load models or write files. `analyse` returns plain JSON data;
room/window GlobalIds support resolving entities in the source model. Internal
numeric IFC IDs are also retained, but are only meaningful within that model.
The path-based `run_ifc_analysis` helper is retained for callers that need it.

## Outputs

Each run creates:

```text
daylight/results/run-<UTC-time>-<unique-suffix>/
  result.json
```

`--results-dir <folder>` instead uses `<folder>/<analysis-name>/run-.../`.
Earlier runs are preserved. Each run produces only `result.json`, containing
the room table, GlobalIds, detailed windows, summaries, threshold and limitations.
Empty models produce JSON and an explicit no-rooms message.
Failures stop the runner; earlier files may remain, so they do not prove the
whole run succeeded.

## Screening limitations

The migration preserves A4's calculations and 10% threshold. Results are
window-to-floor-area screening, not a complete daylight compliance assessment.
Window areas may include frames; quantities are not independently verified.
Window assignment uses bounding boxes and heuristic storey elevation scaling.
Missing geometry and unassigned windows can produce misleading zero window
areas and FAIL statuses. Room-use classification relies on keywords. Review
these conditions before interpreting results; they were not corrected by the
structural migration. The unused alternative status function was removed so
`make_tables` provides the screening statuses.

Statuses: `OK`, `FAIL`, `REVIEW USE`, `MISSING AREA`, `N/A`.
Record the source model version, code commit and assumptions when sharing a
selected result; the output timestamp is not provenance. No automatic publishing
or downstream delivery occurs. Update CHANGELOG.md for meaningful changes.

## Tests

From the repository root:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s A4_A/tests
```

Tests cover the runner, preserved inputs and previous results, JSON serialization,
GlobalIds, screening statuses, and JSON-only output.

Acknowledgement: based on the course Week 11 starter and its
[Working Together example](https://github.com/timmcginley/41934/blob/main/Activities/workingTogether.md).
The starter does not execute in node-comply or replace the Speckle template.
