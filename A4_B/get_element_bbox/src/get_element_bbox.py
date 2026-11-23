from common._recording import recorded
import numpy as np
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.unit


@recorded
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
        return None
