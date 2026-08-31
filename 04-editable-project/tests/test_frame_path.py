import numpy as np

from frame_core.path import cubic_points, morph_points, reveal_points, resample_points


def test_cubic_path_has_locked_endpoints():
    points = cubic_points((0, 0), (0, 10), (10, 10), (10, 0), count=21)
    assert np.allclose(points[0], (0, 0))
    assert np.allclose(points[-1], (10, 0))


def test_reveal_uses_distance_instead_of_point_count():
    points = np.array([(0, 0), (90, 0), (100, 0)], dtype=float)
    visible = reveal_points(points, 0.5)
    assert np.allclose(visible[-1], (50, 0))


def test_morph_resamples_shapes_to_compatible_topology():
    start = np.array([(0, 0), (10, 0)], dtype=float)
    end = np.array([(0, 0), (5, 10), (10, 0)], dtype=float)
    middle = morph_points(start, end, 0.5, count=32)
    assert middle.shape == (32, 2)
    assert 4.5 < middle[:, 1].max() < 5.5


def test_resample_preserves_closed_path():
    square = np.array([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)], dtype=float)
    sampled = resample_points(square, 40)
    assert np.allclose(sampled[0], sampled[-1])
