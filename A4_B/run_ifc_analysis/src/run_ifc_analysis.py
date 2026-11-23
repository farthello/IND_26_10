from common._recording import recorded
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.unit
from analyse_model.src.analyse_model import analyse_model


@recorded
def run_ifc_analysis(file_path, progress_callback=None):
    if progress_callback:
        progress_callback("Loading IFC file...")

    ifc_file = ifcopenshell.open(file_path)

    return analyse_model(ifc_file, progress_callback)
