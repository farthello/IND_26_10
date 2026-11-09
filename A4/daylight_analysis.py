from pathlib import Path
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.unit
import numpy as np

EXCLUDED_TYPES = ['toilet', 'corridor', 'utility', 'elevator', 'atrium', 'auditorium', 'multipurpose', 'terrace', 'storage', 'stair', 'shaft', 'technical', 'cleaning', 'wardrobe', 'lobby', 'entrance', 'hall', 'passage', 'wc', 'bathroom']
RELEVANT_TYPES = ['office', 'room', 'meeting room', 'student work area']

def get_storey_for_element(ifc_file, element):
    # climbs the IFC spatial hierarchy to find which storey something is on
    for rel in ifc_file.by_type("IfcRelContainedInSpatialStructure"):
        if element in rel.RelatedElements:
            structure = rel.RelatingStructure
            if structure.is_a("IfcBuildingStorey"):
                return structure
            if structure.is_a("IfcSpace"):
                return get_storey_for_element(ifc_file, structure)

    for rel in ifc_file.by_type("IfcRelAggregates"):
        if element in rel.RelatedObjects:
            if rel.RelatingObject.is_a("IfcBuildingStorey"):
                return rel.RelatingObject

    return None


def detect_elevation_scale(storey_elevations, space_z_range):
    # some exports mix units between storeys and geometry (mm vs m), this
    # tries to spot that by comparing how "tall" the building looks either way
    if not storey_elevations or space_z_range is None:
        return 1.0

    min_storey_elev = min(s['elevation'] for s in storey_elevations)
    max_storey_elev = max(s['elevation'] for s in storey_elevations)
    storey_range = max_storey_elev - min_storey_elev
    space_range = space_z_range[1] - space_z_range[0]

    if storey_range > 0 and space_range > 0:
        ratio = storey_range / space_range
        if ratio > 500:
            return 0.001
        elif ratio > 50:
            return 0.01
        elif ratio < 0.002:
            return 1000.0
        elif ratio < 0.02:
            return 100.0

    if abs(min_storey_elev) > 100 or abs(max_storey_elev) > 100:
        if abs(space_z_range[0]) < 50 and abs(space_z_range[1]) < 50:
            return 0.001

    return 1.0


def get_storey_elevations(ifc_file, scale_factor=1.0):
    storeys = ifc_file.by_type("IfcBuildingStorey")
    storey_data = []

    for storey in storeys:
        elevation = storey.Elevation if storey.Elevation else 0
        storey_data.append({
            'storey': storey,
            'name': storey.Name,
            'elevation': elevation * scale_factor,
            'raw_elevation': elevation
        })

    storey_data.sort(key=lambda x: x['elevation'])
    return storey_data


def determine_storey_by_elevation(z_position, storey_elevations):
    # each storey "owns" everything from its own elevation up to the next one
    if not storey_elevations:
        return None

    best_storey = storey_elevations[0]['storey']

    for i, storey_data in enumerate(storey_elevations):
        current_elevation = storey_data['elevation']
        if i < len(storey_elevations) - 1:
            next_elevation = storey_elevations[i + 1]['elevation']
            if current_elevation <= z_position < next_elevation:
                return storey_data['storey']
        else:
            if z_position >= current_elevation:
                return storey_data['storey']

    return best_storey


def get_element_bbox(element, settings):
    try:
        shape = ifcopenshell.geom.create_shape(settings, element)
        verts = np.array(shape.geometry.verts).reshape(-1, 3)
        if len(verts) == 0:
            return None
        return {
            'min': verts.min(axis=0),
            'max': verts.max(axis=0),
            'center': verts.mean(axis=0)
        }
    except Exception:
        return None  # some elements just don't have usable geometry


def bbox_intersects_2d(bbox1, bbox2, tolerance=0.5):
    if bbox1 is None or bbox2 is None:
        return False
    return (bbox1['min'][0] - tolerance <= bbox2['max'][0] and
            bbox1['max'][0] + tolerance >= bbox2['min'][0] and
            bbox1['min'][1] - tolerance <= bbox2['max'][1] and
            bbox1['max'][1] + tolerance >= bbox2['min'][1])


def bbox_contains_point_2d(bbox, point, tolerance=0.5):
    if bbox is None or point is None:
        return False
    return (bbox['min'][0] - tolerance <= point[0] <= bbox['max'][0] + tolerance and
            bbox['min'][1] - tolerance <= point[1] <= bbox['max'][1] + tolerance)


def distance_2d(p1, p2):
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def find_windows_by_geometry(windows, space_bboxes, settings, ifc_file, storey_elevations):
    # works out which room each window belongs to using geometry instead of
    # IFC relationships, since those are often missing or just wrong
    window_assignments = {}

    for window in windows:
        window_bbox = get_element_bbox(window, settings)
        if window_bbox is None:
            continue

        window_z = window_bbox['min'][2]
        window_storey = determine_storey_by_elevation(window_z, storey_elevations)

        if window_storey is None:
            ifc_storey = get_storey_for_element(ifc_file, window)
            if ifc_storey:
                window_storey = ifc_storey

        if window_storey is None:
            continue  # can't place it on a floor, so skip it

        window_center = window_bbox['center']
        matching_spaces = []

        for space_id, space_data in space_bboxes.items():
            space_bbox = space_data['bbox']
            space_storey = space_data.get('storey')

            if space_storey != window_storey:
                continue

            if bbox_intersects_2d(window_bbox, space_bbox, tolerance=0.3):
                matching_spaces.append(space_data)
            elif bbox_contains_point_2d(space_bbox, window_center, tolerance=1.0):
                matching_spaces.append(space_data)

        # if a window touches more than one room, give it to whichever one
        # it's geometrically closest to so we don't double count the area
        if len(matching_spaces) >= 1:
            closest_space = min(
                matching_spaces,
                key=lambda s: distance_2d(window_center, s['bbox']['center'])
            )
            window_assignments[window.id()] = closest_space['space']

    return window_assignments


def get_space_area(space):
    # pulls the floor area straight off the quantity set, if there is one.
    # returns the raw value + where it came from - unit conversion happens
    # later once we know the model's area unit
    for definition in space.IsDefinedBy:
        if definition.is_a('IfcRelDefinesByProperties'):
            prop_def = definition.RelatingPropertyDefinition
            if prop_def.is_a('IfcElementQuantity'):
                for quantity in prop_def.Quantities:
                    if quantity.is_a('IfcQuantityArea'):
                        if quantity.Name in ['NetFloorArea', 'GrossFloorArea', 'Area',
                                              'NetArea', 'GrossArea', 'FloorArea']:
                            return quantity.AreaValue
    return None


def get_window_area(window):
    # same idea as get_space_area, but windows don't always have a proper
    # quantity set, so there's a couple of fallbacks here
    for definition in window.IsDefinedBy:
        if definition.is_a('IfcRelDefinesByProperties'):
            prop_def = definition.RelatingPropertyDefinition
            if prop_def.is_a('IfcElementQuantity'):
                for quantity in prop_def.Quantities:
                    if quantity.is_a('IfcQuantityArea'):
                        return quantity.AreaValue, 'area_unit'

    for definition in window.IsDefinedBy:
        if definition.is_a('IfcRelDefinesByProperties'):
            prop_def = definition.RelatingPropertyDefinition
            if prop_def.is_a('IfcPropertySet'):
                for prop in prop_def.HasProperties:
                    if hasattr(prop, 'Name') and 'area' in prop.Name.lower():
                        if hasattr(prop, 'NominalValue') and prop.NominalValue:
                            return prop.NominalValue.wrappedValue, 'area_unit'

    # last resort - just multiply the frame dimensions. these are LENGTH
    # values though, not area, so they need squaring with the length scale
    # further down, not the area scale
    width = getattr(window, 'OverallWidth', None)
    height = getattr(window, 'OverallHeight', None)
    if width and height:
        return width * height, 'length_squared'

    return None, None


def check_br18(ratio, room_type_text, threshold_percent):
    # BR18 §379: glass area must be at least 10% of the relevant floor area
    # for rooms people actually occupy (offices, classrooms, living rooms
    # etc). bathrooms, storage, technical rooms, corridors and the like are
    # exempt - which conveniently is already our EXCLUDED_TYPES list
    full_name = room_type_text.lower()
    for excluded in EXCLUDED_TYPES:
        if excluded in full_name:
            return "N/A"

    if ratio is None:
        return "FAIL"  # no windows at all in an occupied room = definitely not compliant

    return "OK" if ratio >= threshold_percent else "FAIL"


def run_ifc_analysis(file_path, progress_callback=None):
    if progress_callback:
        progress_callback("Loading IFC file...")

    ifc_file = ifcopenshell.open(file_path)

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
            'space_entity': space,
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
                if room['space_entity'] == assigned_space:
                    room['windows'].append({
                        'id': wid,
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
