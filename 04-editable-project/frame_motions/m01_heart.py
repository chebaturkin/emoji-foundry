import math

import numpy as np
from PIL import ImageDraw

from frame_core.brush import draw_pressure_stroke, jitter_points, pressure_profile
from frame_core.composite import phase, smooth
from frame_core.deform import deform_points
from frame_core.depth import DepthLayer, compose_depth, glint_window
from frame_core.models import FrameMotionSpec
from frame_core.path import cubic_points
from frame_core.retime import retime_draw
from frame_motions.common import BLUE, INK, PAPER, canvas


TIMING = {
    "drops": (2, 20),
    "body": (12, 25),
    "impact": (28, 40),
    "glint": (33, 42),
    "retract": (50, 59),
}

SHADOW_BLUE = (46, 58, 77, 148)


def heart_state(frame, size):
    return {
        "drop_distance": (1.0 - smooth(phase(frame, 4, 20))) * size * 0.34,
        "body_scale": smooth(phase(frame, 12, 25))
        * (1.0 - smooth(phase(frame, 50, 59))),
        "impact": math.sin(math.pi * smooth(phase(frame, 28, 40))),
    }


def _join(parts):
    return np.vstack(
        [part if index == 0 else part[1:] for index, part in enumerate(parts)]
    )


def _base_heart(size):
    unit = size / 100.0
    path = _join(
        [
            cubic_points(
                (50 * unit, 86 * unit),
                (37 * unit, 77 * unit),
                (16 * unit, 61 * unit),
                (17 * unit, 44 * unit),
                24,
            ),
            cubic_points(
                (17 * unit, 44 * unit),
                (17 * unit, 27 * unit),
                (28 * unit, 17 * unit),
                (38 * unit, 20 * unit),
                24,
            ),
            cubic_points(
                (38 * unit, 20 * unit),
                (44 * unit, 21 * unit),
                (47 * unit, 29 * unit),
                (50 * unit, 35 * unit),
                18,
            ),
            cubic_points(
                (50 * unit, 35 * unit),
                (54 * unit, 28 * unit),
                (55 * unit, 22 * unit),
                (62 * unit, 20 * unit),
                18,
            ),
            cubic_points(
                (62 * unit, 20 * unit),
                (76 * unit, 16 * unit),
                (86 * unit, 29 * unit),
                (84 * unit, 45 * unit),
                24,
            ),
            cubic_points(
                (84 * unit, 45 * unit),
                (82 * unit, 61 * unit),
                (64 * unit, 78 * unit),
                (50 * unit, 86 * unit),
                24,
            ),
        ]
    )
    return jitter_points(path, seed=101, amount=size / 850)


def _heart_geometry(frame, size):
    """Build at the drop join, deform locally, then retract to the bottom point."""
    state = heart_state(frame, size)
    unit = size / 100.0
    impact = state["impact"]
    path = _base_heart(size)
    path = deform_points(
        path,
        controls=(
            (34, (-2.7 * unit * impact, 3.9 * unit * impact), 14),
            (88, (1.5 * unit * impact, -2.8 * unit * impact), 15),
            (112, (-0.8 * unit * impact, 1.2 * unit * impact), 10),
        ),
        anchors=(0, len(path) - 1),
    )

    enter = smooth(phase(frame, *TIMING["body"]))
    join_point = np.array((50 * unit, 36 * unit))
    path = join_point + (path - join_point) * enter

    remain = 1.0 - smooth(phase(frame, *TIMING["retract"]))
    bottom_point = np.array((50 * unit, 86 * unit))
    return bottom_point + (path - bottom_point) * remain


def _polygon_layer(path, color, size):
    layer = canvas(size)
    if len(path) >= 3 and not np.allclose(path, path[0]):
        ImageDraw.Draw(layer, "RGBA").polygon(
            [tuple(point) for point in path], fill=color
        )
    return layer


def _outline_layer(path, size, color=BLUE, width=None):
    layer = canvas(size)
    if len(path) >= 2 and not np.allclose(path, path[0]):
        closed = np.vstack((path, path[0]))
        draw_pressure_stroke(
            layer,
            closed,
            color,
            width or size * 0.057,
            pressure_profile(len(closed), 0.42, 1.12, 0.34),
        )
    return layer


def _drop_path(center, side, scale, size):
    """A compact teardrop whose point faces back toward its incoming diagonal."""
    unit = size / 100.0
    cx, cy = center
    local = np.array(
        [
            (0.0, -8.0),
            (4.2, -3.2),
            (4.8, 1.5),
            (2.4, 5.8),
            (0.0, 7.0),
            (-2.8, 5.5),
            (-4.9, 1.0),
            (-4.0, -3.4),
        ],
        dtype=float,
    )
    local[:, 0] += side * local[:, 1] * 0.16
    return np.array((cx, cy)) + local * unit * scale


def _drop_layers(frame, size):
    enter = smooth(phase(frame, 2, 7))
    merge = 1.0 - smooth(phase(frame, 18, 25))
    scale = enter * merge
    if scale <= 0:
        return canvas(size)

    distance = heart_state(frame, size)["drop_distance"]
    unit = size / 100.0
    targets = ((40 * unit, 32 * unit), (60 * unit, 33 * unit))
    directions = ((-0.58, -0.50), (0.64, -0.45))
    result = canvas(size)
    for side, (target, direction) in enumerate(zip(targets, directions)):
        center = np.asarray(target) + np.asarray(direction) * distance
        path = _drop_path(center, -1 if side == 0 else 1, scale, size)
        ImageDraw.Draw(result, "RGBA").polygon(
            [tuple(point) for point in path], fill=INK
        )
    return result


def _glint_layer(frame, size):
    glint = canvas(size)
    strength = glint_window(frame, *TIMING["glint"])
    if strength <= 0:
        return glint
    unit = size / 100.0
    impact = heart_state(frame, size)["impact"]
    streak = cubic_points(
        (27 * unit, (38 + 1.8 * impact) * unit),
        (24 * unit, 31 * unit),
        (29 * unit, 24 * unit),
        (36 * unit, 23 * unit),
        14,
    )
    draw_pressure_stroke(
        glint,
        streak,
        PAPER,
        size * 0.021,
        pressure_profile(len(streak), 0.18, 0.95, 0.12),
        strength,
    )
    return glint


def heart_layers(frame, size):
    path = _heart_geometry(frame, size)
    shadow_frame = max(0, frame - 2)
    lagged_path = _heart_geometry(shadow_frame, size)

    shadow_remain = 1.0 - smooth(phase(shadow_frame, *TIMING["retract"]))
    shadow_offset = np.array((2.3, 3.0)) * size / 100.0 * shadow_remain
    shadow = _polygon_layer(lagged_path + shadow_offset, SHADOW_BLUE, size)
    fill = _polygon_layer(path, PAPER, size)
    outline = _outline_layer(path, size)

    return [
        DepthLayer("material_shadow", shadow, 0),
        DepthLayer("ink_drops", _drop_layers(frame, size), 5),
        DepthLayer("paper_body", fill, 10),
        DepthLayer("pressure_contour", outline, 20),
        DepthLayer("glint", _glint_layer(frame, size), 30),
    ]


def draw_frame(frame, size):
    if frame <= 0 or frame >= 59:
        return canvas(size)
    return compose_depth(heart_layers(frame, size))


SPEC = FrameMotionSpec(
    "01-heart",
    retime_draw(draw_frame, 48),
    duration_frames=48,
    tags=("batch1", "soft", "tactile"),
)
