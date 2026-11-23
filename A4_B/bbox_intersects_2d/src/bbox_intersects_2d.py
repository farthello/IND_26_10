from common._recording import recorded


@recorded
def bbox_intersects_2d(bbox1, bbox2, tolerance=0.5):
    if bbox1 is None or bbox2 is None:
        return False
    return (bbox1['min'][0] - tolerance <= bbox2['max'][0] and
            bbox1['max'][0] + tolerance >= bbox2['min'][0] and
            bbox1['min'][1] - tolerance <= bbox2['max'][1] and
            bbox1['max'][1] + tolerance >= bbox2['min'][1])
