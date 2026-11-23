from common._recording import recorded
import numpy as np


@recorded
def distance_2d(p1, p2):
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)
