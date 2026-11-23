from common._recording import recorded


@recorded
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
