from common._recording import recorded


@recorded
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
