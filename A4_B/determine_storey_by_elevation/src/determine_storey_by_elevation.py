from common._recording import recorded


@recorded
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
