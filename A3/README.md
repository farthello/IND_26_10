# A3 - IFC daylight screening tool

## Problem and source
Our A2 use case concerns assessing the relationship between window area and floor area in occupied spaces. The work builds on Group 10's automated daylight calculations and our investigation of Building 308. A manual room-by-room check is time-consuming, and the information may be spread across different IFC entities and quantity sets.

## What the tool does
The script reads an IFC model, matches windows to spaces using geometry, extracts floor and window areas, and calculates window-to-floor-area ratios. It produces a room-level CSV table and a terminal summary with the number of rooms screened, flagged and requiring review. The accompanying notebook displays these as tables and summaries. There is no GUI.

This is a **screening tool**, not a complete BR18 daylight verification. The default threshold is 10%, but compliance requires verifying the applicable calculation method and assumptions. Window area is not necessarily equivalent to the relevant glass area; geometry-based assignments and room-use classifications also require review.

## Requirements
Python, `ifcopenshell`, `numpy`; `pandas` and `jupyter` for the demonstration notebook.

```bash
pip install ifcopenshell numpy pandas jupyter
python main.py "path/to/B308X.ifc" --output results.csv
jupyter notebook tutorial.ipynb
```

Place the IFC file on your computer. Do not commit it to the A3 repository. Change `model_path` in the notebook to match its location.

## Outputs
`results.csv` includes storey, room name and use, floor area, window area, number of windows, ratio, and screening status (`OK`, `FAIL`, `REVIEW USE`, `MISSING AREA`, or `N/A`). The notebook shows the same room table and a summary by screening status.

## Use in Advanced Building Design
The tool is most relevant during design assessment and development, when room layouts and window dimensions can still be adjusted. Architecture and building physics / indoor-climate teams could use it. A precise stage designation (A–D) should be aligned with the A2 workflow before submission.

## IFC information required
- `IfcSpace` objects with identifiable room names/use and floor-area quantities.
- `IfcWindow` objects with area quantities or width and height.
- Valid spatial geometry and storey information to associate windows with rooms.
- Consistent IFC units and usable geometry representations.

An IDS should validate the **presence** of required entities and properties. It cannot by itself guarantee correct geometric assignments or the accuracy of the resulting daylight screening. Add the validated IDS file to this folder before submission.

## Limitations and further checks
Room-use classification is keyword-based. The matching algorithm uses bounding geometry, which can misassign windows in complex models. Areas extracted from IFC are not independently verified. Review missing quantities, unassigned windows and borderline results manually. The script does not simulate daylight, solar shading or interior illuminance.
