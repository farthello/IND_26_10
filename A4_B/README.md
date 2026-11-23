# A4_B — daylight analysis split by function

A4_B copies A4_A and splits its 13 daylight analysis functions into individual
modules. A4_A remains unchanged. Historical files that Windows would not allow
copying are listed in `copy_report.json`; the source and accessible history were
copied. Existing `daylight/results` files are historical and are not updated.

## Run

From the repository root:

```powershell
.\.venv\Scripts\python.exe A4_B/runall.py
```

The default IFC is configured in `settings.py`. Override it with:

```powershell
.\.venv\Scripts\python.exe A4_B/runall.py "model/B308X.ifc"
```

Install dependencies from `requirements.txt` if needed.

## Structure

```text
A4_B/
  runall.py
  settings.py
  daylight/
    src/
    results/
  get_space_area/
    src/
      get_space_area.py
    results/
      result_get_space_area.json
  get_window_area/
    src/
      get_window_area.py
    results/
      result_get_window_area.json
  ... (13 function folders alongside daylight)
  common/
    constants.py
    registry.py
    _recording.py
  results/
    run-<UTC-time>-<unique-suffix>/
      result.json
```

Every function from the original `daylight_analysis.py` has one folder containing
a `src` subfolder with that single function and a `results` subfolder for its JSON. Imports express dependencies
between functions. The old `daylight/src/daylight_analysis.py` now only re-exports
these functions for compatibility. Presentation and screening statuses remain in
`daylight/src/analysis_formatted.py`.

## Individual and combined results

Each function JSON contains its name, run ID, status, call count, and a `calls`
list. Every call records its inputs and output. Repeated calls (for each window,
room, or geometry comparison) are preserved rather than overwriting each other.
IFC entities become references containing numeric ID, type, GlobalId and name;
NumPy arrays become lists. Models/settings become descriptive metadata, not full
copies. Recorded data is for inspection, not automatic execution replay.

A function not needed by the current model is marked `not_called`, with an empty
call list. In particular, `run_ifc_analysis` is a path-based convenience wrapper;
the runner opens the model once and calls `analyse_model`, so that wrapper is not
called. A returned `null` is a real recorded return value, distinct from no call.

The combined `results/run-.../result.json` includes the original daylight fields
(`rooms`, `summary`, `room_details`, threshold and limitations), plus a `run_id`
and `function_results` mapping containing all 13 individual records.

Function-folder JSON files are replaced on each successful run. The combined
file preserves that run's complete records, so earlier runs remain available.
Matching run IDs let you detect files from different runs. If writing fails,
partial output may remain; only successful completion confirms all files were
written. An analysis exception stops execution before writing new results.
Detailed call recording can make the combined JSON much larger than A4_A's.

`--results-dir <folder>` places individual files under `<folder>/<function>/results/`
and the combined file under `<folder>/daylight/run-.../`. This allows isolated
runs without changing the files in the project function folders.

Importing modules and calling `analyse(model)` directly do not write files.
Recording is enabled only by `collect_results`; output is managed by the runner.

## Limitations

Calculations and the 10% screening threshold are preserved from A4_A. This is
window-to-floor-area screening, not complete daylight compliance verification.
Areas may include frames. Geometry matching, heuristic storey scaling, missing
geometry and room-use keywords require review. Splitting the functions does not
correct those existing limitations. Record the model version and code revision
when sharing a result. No automatic publishing occurs.

## Tests

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s A4_B/tests
```

Tests cover single-function modules, repeated calls, JSON output, unchanged
models, standalone imports, command-line execution and screening statuses.

Based on A4_A and the course Week 11 IFC starter / Working Together example.
