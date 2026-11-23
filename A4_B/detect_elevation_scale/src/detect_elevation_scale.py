from common._recording import recorded


@recorded
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
