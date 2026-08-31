import numpy as np
from PIL import Image

from frame_core.brush import draw_brush_stroke, jitter_points


def test_jitter_is_deterministic_for_one_path():
    points = np.array([(10, 10), (50, 50), (90, 10)], dtype=float)
    assert np.array_equal(jitter_points(points, seed=19, amount=0.8), jitter_points(points, seed=19, amount=0.8))


def test_jitter_locks_path_endpoints():
    points = np.array([(10, 10), (50, 50), (90, 10)], dtype=float)
    result = jitter_points(points, seed=19, amount=0.8)
    assert np.array_equal(result[0], points[0])
    assert np.array_equal(result[-1], points[-1])


def test_brush_stroke_draws_rgba_pixels():
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    draw_brush_stroke(image, np.array([(10, 50), (90, 50)]), (46, 58, 77, 255), width=8)
    assert image.getchannel("A").getbbox() is not None
