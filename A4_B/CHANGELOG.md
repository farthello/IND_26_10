# Changelog

## 2026-11-23

- Copied the A4 daylight screening into `daylight/src`, preserving the existing
  calculation and matching algorithms. A4 remains unchanged.
- Added an importable `analyse(model)` returning JSON-compatible data, including
  room/window GlobalIds, screening rows, detailed room data and summary counts.
- Registered daylight alongside window counting. The runner loads the IFC once
  and saves daylight JSON in a unique run folder.
- Added integration tests and dependencies.
- Simplified output to JSON only and removed optional export dependencies.
- Recorded known geometry, area and classification limitations in each result.

## 2026-11-16

- Grouped each analysis's source and results in its own top-level folder:
  `window_count/src/main.py` and `window_count/results/run-.../result.json`.
  The shared `runall.py` and `settings.py` are now at the template root.
  Register additional analysis folder names in `ANALYSES`.
- The optional `--results-dir` override retains its separate output-root layout.
  Existing results are left untouched.
  The shared runner opens the IFC once for the registered analyses.

- Initial starter: count IFC windows using an import-safe callable function.
- Added a local runner that writes JSON to a new folder on each run.
- Added `settings.py` for the local model path, keeping setup separate from
  the analysis. A command-line path can still override it.
- No automatic publishing, run metadata or engineering assessment.

Add dated entries for your meaningful changes and explain their effect on the
receiving team. Routine executions do not need changelog entries.

## 2026-11-23 — A4_B function structure

- Split 13 daylight functions into src/<function>/<function>.py.
- Record actual calls in per-function JSON files and timestamped combined results.
- Preserve the original daylight assessment and document inaccessible copied history.


## 2026-11-23 ? Per-function packages

- Moved all 13 function packages alongside daylight, each with src and results subfolders.
- Moved shared recording, constants and registry into common.
- Updated imports, output paths, documentation and tests; combined results retain their existing location.
