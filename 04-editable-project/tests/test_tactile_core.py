import numpy as np
from PIL import Image

from frame_core.brush import draw_pressure_stroke, pressure_profile
from frame_core.deform import deform_points
from frame_core.depth import DepthLayer, compose_depth, glint_window


def test_pressure_profile_locks_soft_ends_and_heavy_middle():
    values = pressure_profile(21, start=0.35, peak=1.2, end=0.25)
    assert len(values) == 21
    assert values[0] == 0.35
    assert values[-1] == 0.25
    assert values[10] == 1.2


def test_pressure_stroke_has_more_ink_at_the_peak():
    image = Image.new("RGBA", (240, 80), (0, 0, 0, 0))
    points = np.column_stack((np.linspace(20, 220, 41), np.full(41, 40)))
    pressure = pressure_profile(41, start=0.3, peak=1.25, end=0.3)
    draw_pressure_stroke(image, points, (46, 58, 77, 255), width=18, pressure=pressure)
    alpha = np.asarray(image.getchannel("A"))
    assert (alpha[:, 110:130] > 0).sum() > (alpha[:, 20:40] > 0).sum() * 1.8


def test_deformation_preserves_anchor_points():
    points = np.column_stack((np.linspace(0, 100, 21), np.zeros(21)))
    changed = deform_points(points, controls=((10, (0, 20), 5),), anchors=(0, 20))
    assert np.allclose(changed[0], points[0])
    assert np.allclose(changed[-1], points[-1])
    assert changed[10, 1] == 20


def test_deformation_falls_off_away_from_control():
    points = np.column_stack((np.linspace(0, 100, 21), np.zeros(21)))
    changed = deform_points(points, controls=((10, (0, 20), 4),), anchors=())
    assert changed[10, 1] > changed[6, 1] > changed[2, 1]


def test_depth_compositor_respects_z_order():
    back = Image.new("RGBA", (20, 20), (46, 58, 77, 255))
    front = Image.new("RGBA", (20, 20), (242, 240, 233, 255))
    result = compose_depth((DepthLayer("front", front, 2), DepthLayer("back", back, 1)))
    assert result.getpixel((10, 10)) == (242, 240, 233, 255)


def test_glint_exists_only_inside_accent_window():
    assert glint_window(20, 28, 38) == 0.0
    assert 0.9 < glint_window(33, 28, 38) <= 1.0
    assert glint_window(45, 28, 38) == 0.0
