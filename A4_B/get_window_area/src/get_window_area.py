from common._recording import recorded


@recorded
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
