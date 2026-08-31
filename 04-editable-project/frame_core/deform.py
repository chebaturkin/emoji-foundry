import numpy as np


def deform_points(points, controls, anchors=()):
    source = np.asarray(points, dtype=float)
    result = source.copy()
    indices = np.arange(len(source), dtype=float)
    for index, offset, radius in controls:
        weight = np.exp(-0.5 * ((indices - index) / max(radius, 1e-6)) ** 2)
        result += weight[:, None] * np.asarray(offset, dtype=float)
    for anchor in anchors:
        result[anchor] = source[anchor]
    return result
