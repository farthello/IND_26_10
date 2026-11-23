from common._recording import recorded


@recorded
def bbox_contains_point_2d(bbox, point, tolerance=0.5):
    if bbox is None or point is None:
        return False
    return (bbox['min'][0] - tolerance <= point[0] <= bbox['max'][0] + tolerance and
            bbox['min'][1] - tolerance <= point[1] <= bbox['max'][1] + tolerance)
