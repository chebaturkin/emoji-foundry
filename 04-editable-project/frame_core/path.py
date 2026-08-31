import numpy as np


def cubic_points(p0, p1, p2, p3, count=32):
    t = np.linspace(0.0, 1.0, count)[:, None]
    a, b, c, d = map(lambda point: np.asarray(point, dtype=float), (p0, p1, p2, p3))
    return (1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t ** 2 * c + t ** 3 * d


def resample_points(points, count):
    points = np.asarray(points, dtype=float)
    distance = np.linalg.norm(np.diff(points, axis=0), axis=1)
    cumulative = np.concatenate(([0.0], np.cumsum(distance)))
    if cumulative[-1] == 0:
        return np.repeat(points[:1], count, axis=0)
    targets = np.linspace(0.0, cumulative[-1], count)
    x = np.interp(targets, cumulative, points[:, 0])
    y = np.interp(targets, cumulative, points[:, 1])
    sampled = np.column_stack((x, y))
    if np.allclose(points[0], points[-1]):
        sampled[-1] = sampled[0]
    return sampled


def reveal_points(points, progress):
    points = np.asarray(points, dtype=float)
    progress = float(np.clip(progress, 0.0, 1.0))
    if len(points) < 2 or progress <= 0:
        return points[:1]
    if progress >= 1:
        return points.copy()
    distance = np.linalg.norm(np.diff(points, axis=0), axis=1)
    cumulative = np.concatenate(([0.0], np.cumsum(distance)))
    target = cumulative[-1] * progress
    index = min(len(points) - 2, max(0, int(np.searchsorted(cumulative, target, side="right") - 1)))
    segment = max(distance[index], 1e-9)
    local = (target - cumulative[index]) / segment
    endpoint = points[index] + (points[index + 1] - points[index]) * local
    return np.vstack((points[:index + 1], endpoint))


def morph_points(start, end, progress, count=96):
    a = resample_points(start, count)
    b = resample_points(end, count)
    t = float(np.clip(progress, 0.0, 1.0))
    return a + (b - a) * t
