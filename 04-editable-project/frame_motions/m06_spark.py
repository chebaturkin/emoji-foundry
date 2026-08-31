import math

import numpy as np
from PIL import Image, ImageChops

from frame_core.brush import draw_pressure_stroke, pressure_profile
from frame_core.composite import phase, smooth
from frame_core.deform import deform_points
from frame_core.depth import DepthLayer, compose_depth, glint_window
from frame_core.models import FrameMotionSpec
from frame_core.path import cubic_points, reveal_points
from frame_core.retime import retime_draw
from frame_motions.common import BLUE, PAPER, TAUPE, canvas


TIMELINE = {
    "vertical": (1, 14),
    "horizontal": (8, 20),
    "ray_0": (17, 27),
    "ray_1": (19, 29),
    "ray_2": (21, 31),
    "ray_3": (23, 33),
}

RAY_EXITS = {
    3: (48, 53),
    2: (49, 54),
    1: (50, 55),
    0: (51, 56),
}

RAY_COORDS = {
    0: ((31, 30), (17, 15)),
    1: ((69, 30), (85, 19)),
    2: ((70, 68), (88, 84)),
    3: ((30, 68), (17, 81)),
}

RAY_PRESSURE = {
    0: (0.30, 1.12, 0.18),
    1: (0.22, 0.92, 0.13),
    2: (0.38, 1.18, 0.20),
    3: (0.26, 1.02, 0.11),
}

SHADOW_BLUE = (46, 58, 77, 158)


def spark_timeline():
    return dict(TIMELINE)


def _axis_paths(frame, size):
    unit = size / 100.0
    settle = math.sin(math.pi * smooth(phase(frame, 24, 38)))
    vertical = cubic_points(
        (50 * unit, 19 * unit),
        ((49.2 - 1.1 * settle) * unit, 36 * unit),
        ((51.0 + 0.8 * settle) * unit, 62 * unit),
        (50 * unit, 79 * unit),
        34,
    )
    horizontal = cubic_points(
        (20 * unit, 49 * unit),
        (36 * unit, (50.2 + 0.9 * settle) * unit),
        (65 * unit, (47.8 - 0.7 * settle) * unit),
        (81 * unit, 49 * unit),
        34,
    )
    vertical = deform_points(
        vertical,
        controls=((17, (1.1 * unit * settle, -0.5 * unit * settle), 6),),
        anchors=(0, len(vertical) - 1),
    )
    horizontal = deform_points(
        horizontal,
        controls=((17, (-0.7 * unit * settle, 0.8 * unit * settle), 6),),
        anchors=(0, len(horizontal) - 1),
    )
    return {"vertical": vertical, "horizontal": horizontal}


def _ray_path(frame, index, size):
    unit = size / 100.0
    start, end = RAY_COORDS[index]
    path = np.linspace(np.asarray(start, dtype=float), np.asarray(end, dtype=float), 11)
    pulse = math.sin(math.pi * smooth(phase(frame, 29, 40)))
    direction = path[-1] - path[0]
    normal = np.array((-direction[1], direction[0]), dtype=float)
    normal /= max(np.linalg.norm(normal), 1e-9)
    path = deform_points(
        path,
        controls=((5, normal * pulse * (0.32 + index * 0.09), 2.6),),
        anchors=(0, len(path) - 1),
    )
    return path * unit


def _axis_progress(frame, name):
    enter = smooth(phase(frame, *TIMELINE[name]))
    exit_timing = (53, 59) if name == "vertical" else (52, 58)
    return enter, 1.0 - smooth(phase(frame, *exit_timing))


def _ray_progress(frame, index):
    enter = smooth(phase(frame, *TIMELINE[f"ray_{index}"]))
    remain = 1.0 - smooth(phase(frame, *RAY_EXITS[index]))
    return enter * remain


def _stroke(points, progress, size, color, width, pressure, opacity=1.0):
    layer = canvas(size)
    visible = reveal_points(points, progress)
    if len(visible) >= 2:
        draw_pressure_stroke(
            layer,
            visible,
            color,
            width,
            pressure_profile(len(visible), *pressure),
            opacity,
        )
    return layer


def _axis_layer(frame, name, size):
    paths = _axis_paths(frame, size)
    enter, remain = _axis_progress(frame, name)
    path = paths[name]
    if enter < 1.0:
        progress = enter
    else:
        center = np.array((50 * size / 100.0, 49 * size / 100.0))
        path = center + (path - center) * remain
        progress = 1.0 if remain > 0 else 0.0
    pressure = (0.34, 1.16, 0.24) if name == "vertical" else (0.24, 1.02, 0.34)
    width = size * (0.061 if name == "vertical" else 0.053)
    return _stroke(path, progress, size, BLUE, width, pressure)


def _ray_layer(frame, index, size):
    path = _ray_path(frame, index, size)
    return _stroke(
        path,
        _ray_progress(frame, index),
        size,
        BLUE,
        size * (0.034 + index * 0.0025),
        RAY_PRESSURE[index],
    )


def _intersection_detail_layer(frame, size):
    layer = canvas(size)
    enter = smooth(phase(frame, 20, 25))
    remain = 1.0 - smooth(phase(frame, 50, 56))
    scale = enter * remain
    if scale <= 0:
        return layer
    unit = size / 100.0
    center = np.array((51.8 * unit, 51.3 * unit))
    diamond = np.array(((0, -3.8), (4.2, 0), (0, 3.8), (-4.2, 0), (0, -3.8)))
    diamond = center + diamond * unit * scale
    draw_pressure_stroke(
        layer,
        diamond,
        TAUPE,
        size * 0.023,
        pressure_profile(len(diamond), 0.26, 0.88, 0.18),
    )
    return layer


def _lagged_shadow(material, size):
    offset = (round(size * 0.02), round(size * 0.03))
    alpha = ImageChops.offset(material.getchannel("A"), *offset)
    alpha = alpha.point(lambda value: round(value * SHADOW_BLUE[3] / 255))
    shadow = Image.new("RGBA", (size, size), SHADOW_BLUE)
    shadow.putalpha(alpha)
    return shadow


def _glint_layer(frame, size):
    layer = canvas(size)
    strength = glint_window(frame, 31, 42)
    if strength <= 0:
        return layer
    unit = size / 100.0
    streak = cubic_points(
        (46.9 * unit, 31.5 * unit),
        (46.4 * unit, 27.5 * unit),
        (47.3 * unit, 24.6 * unit),
        (48.5 * unit, 22.6 * unit),
        10,
    )
    draw_pressure_stroke(
        layer,
        streak,
        PAPER,
        size * 0.017,
        pressure_profile(len(streak), 0.16, 0.82, 0.10),
        strength,
    )
    return layer


def spark_layers(frame, size):
    shadow_frame = max(0, frame - 2)
    lagged_vertical = _axis_layer(shadow_frame, "vertical", size)
    lagged_horizontal = _axis_layer(shadow_frame, "horizontal", size)
    layers = [
        DepthLayer(
            "vertical_shadow",
            _lagged_shadow(lagged_vertical, size),
            0,
        ),
        DepthLayer(
            "horizontal_shadow",
            _lagged_shadow(lagged_horizontal, size),
            1,
        ),
    ]
    for index in range(4):
        layers.append(
            DepthLayer(
                f"ray_{index}_shadow",
                _lagged_shadow(_ray_layer(shadow_frame, index, size), size),
                2 + index,
            )
        )

    layers.extend(
        (
            DepthLayer(
                "intersection_detail", _intersection_detail_layer(frame, size), 10
            ),
            DepthLayer("vertical", _axis_layer(frame, "vertical", size), 20),
            DepthLayer("horizontal", _axis_layer(frame, "horizontal", size), 21),
        )
    )
    for index in range(4):
        layers.append(
            DepthLayer(f"ray_{index}", _ray_layer(frame, index, size), 22 + index)
        )
    layers.append(DepthLayer("directional_glint", _glint_layer(frame, size), 40))
    return layers


def draw_frame(frame, size):
    if frame <= 0 or frame >= 59:
        return canvas(size)
    return compose_depth(spark_layers(frame, size))


SPEC = FrameMotionSpec(
    "06-spark",
    retime_draw(draw_frame, 48),
    duration_frames=48,
    tags=("batch1", "impact", "tactile"),
)
