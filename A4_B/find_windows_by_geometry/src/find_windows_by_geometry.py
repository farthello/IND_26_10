from common._recording import recorded
from get_storey_for_element.src.get_storey_for_element import get_storey_for_element
from determine_storey_by_elevation.src.determine_storey_by_elevation import determine_storey_by_elevation
from get_element_bbox.src.get_element_bbox import get_element_bbox
from bbox_intersects_2d.src.bbox_intersects_2d import bbox_intersects_2d
from bbox_contains_point_2d.src.bbox_contains_point_2d import bbox_contains_point_2d
from distance_2d.src.distance_2d import distance_2d


@recorded
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
