from common._recording import recorded


@recorded
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
