# Inspecting IFC Models with IfcOpenShell

DTU 41934 Advanced BIM · A3 Teach

## Summary

Use Python and IfcOpenShell to open an IFC model, count building elements, and inspect their properties and spatial containers. The adjacent Jupyter notebook file shows how and what lines of code is need to export a basic table of selected elements to CSV for further analysis.

## Who this is for

This tutorial is for students who know basic Python and want to extract information from an IFC model. It introduces skills for the **OpenBIM Analyst, Level 3** role by using IfcOpenShell in a standalone Python environment. [Course role description](https://timmcginley.github.io/41934/Roles/Analyst.html)

**Focus area and BIM use (example)** · (Indoor and Energy), supporting lighting analysis. Before assessing daylight, check whether the IFC model contains windows and spaces and inspect what information is available about them. [Course focus area](https://timmcginley.github.io/41934/Focus/Indoor.html)

## Learning objectives

- Open an IFC model and identify its IFC schema.
- Find and count elements by IFC class, such as `IfcWall`, `IfcWindow`, and `IfcSpace`.
- Inspect direct attributes such as `Name` and `GlobalId`, and read property and quantity sets.
- Find an element's assigned spatial container, such as a building storey, and export a table of elements to CSV.

## Run the tutorial

1. Download or clone this repository. You will need Python and an `.ifc` model. The saved notebook example used Python 3.11 and IfcOpenShell 0.8.5.
2. Open a terminal in the folder containing [`IFCopenshell_tutorial.ipynb`](IFCopenshell_tutorial.ipynb), install the packages, and launch the notebook.

   ```bash
   python -m pip install ifcopenshell pandas jupyter
   python -m notebook test.ipynb
   ```

3. In **Section 2**, set `IFC_PATH` to your model file. If your model is named `example.ifc` and is in the notebook folder, use the default below. For a model stored elsewhere, use its full path eg: `IFC_PATH = Path(r"C:\Users\Student\Documents\Advanced BIM\example.ifc")`

   ```python
   IFC_PATH = Path("example.ifc")
   ```

4. Run the cells from top to bottom. The notebook shows the model schema, a table of element counts, and the attributes and property sets of the first element in the selected class. The final cell writes `outputs/elements.csv` with `GlobalId`, `Name`, `IFC class`, and `Container` for all elements in that class.

## Try a query

Once the IFC model is open, `by_type()` retrieves elements in a given class. For example, count the windows in the model with the following code.

```python
windows = model.by_type("IfcWindow")
print(len(windows))
```

The model used in the notebook example returned **229 windows**. Your count will depend on your IFC file.

## Peer exercise

Choose a class with a nonzero count, such as `IfcWindow`. Set `ELEMENT_CLASS` in **Section 4** and rerun Sections 4–6. Check that the CSV contains the same number of data rows as the class count in Section 3. Pick one row and identify its spatial container, if one is assigned. Rerunning the export replaces the previous CSV.

## Troubleshooting

- **`ModuleNotFoundError`** · Check that the notebook kernel uses the Python environment where you installed the packages.
- **`FileNotFoundError`** · Check the model filename and the full path shown in the error message.
- **Empty `Container` value** · The element has no spatial container returned by the query, so its container field is blank in the CSV.

## Further reading

- [IfcOpenShell Python documentation](https://docs.ifcopenshell.org/ifcopenshell-python.html)
- [DTU 41934 A3 Teach assignment](https://timmcginley.github.io/41934/Assignments/A3.html)
