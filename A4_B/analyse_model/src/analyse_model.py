from common._recording import recorded
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.unit
from get_storey_for_element.src.get_storey_for_element import get_storey_for_element
from detect_elevation_scale.src.detect_elevation_scale import detect_elevation_scale
from get_storey_elevations.src.get_storey_elevations import get_storey_elevations
from determine_storey_by_elevation.src.determine_storey_by_elevation import determine_storey_by_elevation
from get_element_bbox.src.get_element_bbox import get_element_bbox
from find_windows_by_geometry.src.find_windows_by_geometry import find_windows_by_geometry
from get_space_area.src.get_space_area import get_space_area
from get_window_area.src.get_window_area import get_window_area
from common.constants import RELEVANT_TYPES


@recorded
def analyse_model(ifc_file, progress_callback=None):
    """Screen an already-open model without modifying it or writing files."""
    # grab the real unit scales from the model instead of assuming m/m2.
    # NB - area unit is NOT just the length unit squared, IFC lets them be
    # declared independently, learned that one the hard way before
    area_unit_scale = ifcopenshell.util.unit.calculate_unit_scale(ifc_file, unit_type="AREAUNIT")
    length_unit_scale = ifcopenshell.util.unit.calculate_unit_scale(ifc_file)

    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)

    spaces = ifc_file.by_type("IfcSpace")
    windows = ifc_file.by_type("IfcWindow")

    if progress_callback:
        progress_callback(f"Found {len(spaces)} spaces and {len(windows)} windows...")
        progress_callback("Checking for unit mismatches...")

    temp_space_z_min = float('inf')
    temp_space_z_max = float('-inf')
    sample_count = 0

    for space in spaces[:50]:  # don't need to check every single space for this
        bbox = get_element_bbox(space, settings)
        if bbox is not None:
            temp_space_z_min = min(temp_space_z_min, bbox['min'][2])
            temp_space_z_max = max(temp_space_z_max, bbox['max'][2])
            sample_count += 1

    space_z_range = (temp_space_z_min, temp_space_z_max) if sample_count > 0 else None

    raw_storey_elevations = get_storey_elevations(ifc_file, scale_factor=1.0)
    elevation_scale = detect_elevation_scale(raw_storey_elevations, space_z_range)
    storey_elevations = get_storey_elevations(ifc_file, scale_factor=elevation_scale)

    if progress_callback:
        progress_callback("Computing space bounding boxes...")

    space_bboxes = {}
    for space in spaces:
        bbox = get_element_bbox(space, settings)
        if bbox is not None:
            space_z = bbox['min'][2]
            space_storey = determine_storey_by_elevation(space_z, storey_elevations)
            space_bboxes[space.id()] = {
                'space': space,
                'bbox': bbox,
                'storey': space_storey
            }

    if progress_callback:
        progress_callback("Matching windows to rooms...")

    window_assignments = find_windows_by_geometry(windows, space_bboxes, settings, ifc_file, storey_elevations)

    if progress_callback:
        progress_callback("Building room data...")

    rooms_data = []
    for space in spaces:
        space_name = space.Name or f"Unnamed_Space_{space.id()}"
        space_long_name = getattr(space, 'LongName', "") or ""

        raw_area = get_space_area(space)
        floor_area = raw_area * area_unit_scale if raw_area else None

        if space.id() in space_bboxes:
            storey = space_bboxes[space.id()]['storey']
            storey_name = storey.Name if storey else "Unassigned"
        else:
            storey = get_storey_for_element(ifc_file, space)
            storey_name = storey.Name if storey else "Unassigned"

        full_name = (space_long_name if space_long_name else space_name).lower()
        is_relevant = any(room_type in full_name for room_type in RELEVANT_TYPES)

        rooms_data.append({
            'name': space_name,
            'long_name': space_long_name,
            'floor_area': floor_area,
            'storey': storey_name,
            'global_id': space.GlobalId,
            'space_id': space.id(),
            'is_relevant': is_relevant,
            'windows': [],
            'total_window_area': 0
        })

    for window in windows:
        wid = window.id()
        raw_window_area, source = get_window_area(window)

        if raw_window_area is None:
            window_area = None
        elif source == 'area_unit':
            window_area = raw_window_area * area_unit_scale
        else:  # width * height, so the length scale needs squaring
            window_area = raw_window_area * (length_unit_scale ** 2)

        if wid in window_assignments:
            assigned_space = window_assignments[wid]
            for room in rooms_data:
                if room['space_id'] == assigned_space.id():
                    room['windows'].append({
                        'id': wid,
                        'global_id': window.GlobalId,
                        'name': window.Name or f"Window_{wid}",
                        'area': window_area
                    })
                    if window_area:
                        room['total_window_area'] += window_area
                    break

    total_floor_area = sum(r['floor_area'] for r in rooms_data if r['floor_area'])
    total_window_area = sum(r['total_window_area'] for r in rooms_data)
    rooms_with_windows = len([r for r in rooms_data if len(r['windows']) > 0])
    overall_ratio = (total_window_area / total_floor_area) * 100 if total_floor_area > 0 and total_window_area > 0 else 0

    if progress_callback:
        progress_callback("Done!")

    return {
        'rooms': rooms_data,
        'total_floor_area': total_floor_area,
        'total_window_area': total_window_area,
        'rooms_with_windows': rooms_with_windows,
        'total_rooms': len(rooms_data),
        'total_windows': len(windows),
        'windows_assigned': len(window_assignments),
        'overall_ratio': overall_ratio
    }
