"""Run the IFC daylight screening and export its room table."""

import argparse
from pathlib import Path

if __package__:
    from .Analysis.daylight_analysis import run_ifc_analysis
    from .Analysis.analysis_formatted import export_csv, export_xlsx, make_tables
else:
    from Analysis.daylight_analysis import run_ifc_analysis
    from Analysis.analysis_formatted import export_csv, export_xlsx, make_tables


def main():
    folder = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "model", nargs="?", type=Path,
        default=folder.parent / "model" / "B308X.ifc",
        help="IFC model (default: model/B308X.ifc in this repository)",
    )
    parser.add_argument(
        "--output", type=Path, default=Path.home() / "Downloads" / "results.csv",
        help="CSV destination (default: ~/Downloads/results.csv); XLSX saved alongside it",
    )
    args = parser.parse_args()
    if not args.model.is_file():
        parser.error(f"IFC model not found: {args.model}")

    results = run_ifc_analysis(str(args.model), progress_callback=print)
    rows, summary = make_tables(results)
    if not rows:
        parser.exit(1, "No rooms found in the model; no CSV was written.\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    export_csv(rows, args.output)
    xlsx_path = args.output.with_suffix(".xlsx")
    export_xlsx(rows, xlsx_path)

    print(f"CSV saved to: {args.output.resolve()}")
    print(f"XLSX saved to: {xlsx_path.resolve()}")


if __name__ == "__main__":
    main()

