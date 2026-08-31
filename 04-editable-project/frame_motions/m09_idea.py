import math

import numpy as np
from PIL import Image, ImageChops, ImageDraw

from frame_core.brush import draw_pressure_stroke, jitter_points, pressure_profile
from frame_core.composite import phase, smooth
from frame_core.deform import deform_points
from frame_core.depth import DepthLayer, compose_depth, glint_window
from frame_core.models import FrameMotionSpec
from frame_core.path import cubic_points, reveal_points
from frame_core.retime import retime_draw
from frame_motions.common import BLUE, PAPER, TAUPE, canvas


SHADOW_BLUE = (46, 58, 77, 154)


def idea_state(frame, size):
    return {
        "filament": smooth(phase(frame, 1, 14)),
        "glass": smooth(phase(frame, 6, 24)),
        "base": smooth(phase(frame, 12, 28)),
        "rays": smooth(phase(frame, 27, 38)),
    }


def _join(parts):
    return np.vstack(
        [part if index == 0 else part[1:] for index, part in enumerate(parts)]
    )


def filament_path(size):
    unit = size / 100.0
    path = cubic_points(
        (38 * unit, 57 * unit),
        (40 * unit, 43 * unit),
        (59 * unit, 42 * unit),
        (62 * unit, 57 * unit),
        32,
    )
    return jitter_points(path, seed=503, amount=size / 1200)


def _base_glass_arcs(size):
    unit = size / 100.0
    near = _join(
        (
            cubic_points(
                (39 * unit, 69 * unit),
                (37 * unit, 60 * unit),
                (22 * unit, 54 * unit),
                (24 * unit, 36 * unit),
                24,
            ),
            cubic_points(
                (24 * unit, 36 * unit),
                (25 * unit, 20 * unit),
                (37 * unit, 12 * unit),
                (50 * unit, 13 * unit),
                24,
            ),
        )
    )
    far = _join(
        (
            cubic_points(
                (50 * unit, 13 * unit),
                (67 * unit, 11 * unit),
                (79 * unit, 24 * unit),
                (76 * unit, 42 * unit),
                24,
            ),
            cubic_points(
                (76 * unit, 42 * unit),
                (74 * unit, 56 * unit),
                (63 * unit, 59 * unit),
                (61 * unit, 69 * unit),
                24,
            ),
        )
    )
    near = jitter_points(near, seed=505, amount=size / 1050)
    far = jitter_points(far, seed=507, amount=size / 1050)[::-1].copy()
    return near, far


def glass_geometry(frame, size):
    near, far = _base_glass_arcs(size)
    unit = size / 100.0
    breathe = math.sin(math.pi * smooth(phase(frame, 29, 43)))
    near = deform_points(
        near,
        controls=(
            (21, (-1.8 * unit * breathe, 0.8 * unit * breathe), 8),
            (36, (-0.7 * unit * breathe, -1.2 * unit * breathe), 7),
        ),
        anchors=(0,),
    )
    far = deform_points(
        far,
        controls=(
            (13, (1.4 * unit * breathe, -0.8 * unit * breathe), 7),
            (31, (1.9 * unit * breathe, 0.6 * unit * breathe), 8),
        ),
        anchors=(0,),
    )
    apex = np.array((50 * unit, (13 - 1.2 * breathe) * unit))
    near[-1] = apex
    far[-1] = apex
    glass_remain = 1.0 - phase(frame, 49, 57)
    hinge = np.array((50 * unit, 69 * unit))
    near = hinge + (near - hinge) * glass_remain
    far = hinge + (far - hinge) * glass_remain
    return {"near": near, "far": far}


def _filament_geometry(frame, size):
    path = filament_path(size)
    unit = size / 100.0
    warmth = math.sin(math.pi * smooth(phase(frame, 26, 41)))
    return deform_points(
        path,
        controls=((16, (0.7 * unit * warmth, -2.1 * unit * warmth), 6),),
        anchors=(0, len(path) - 1),
    )


def _glass_progress(frame, size, far=False):
    local_frame = frame - 3 if far else frame
    return idea_state(local_frame, size)["glass"]


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


def _glass_strokes(frame, size):
    geometry = glass_geometry(frame, size)
    near = _stroke(
        geometry["near"],
        _glass_progress(frame, size),
        size,
        BLUE,
        size * 0.057,
        (0.38, 1.10, 0.27),
    )
    far = _stroke(
        geometry["far"],
        _glass_progress(frame, size, far=True),
        size,
        BLUE,
        size * 0.047,
        (0.24, 0.88, 0.18),
    )
    return near, far


def _glass_fill(frame, size):
    layer = canvas(size)
    progress = min(
        _glass_progress(frame, size), _glass_progress(frame, size, far=True)
    )
    if progress <= 0:
        return layer
    geometry = glass_geometry(frame, size)
    polygon = np.vstack((geometry["near"], geometry["far"][-2::-1]))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).polygon([tuple(point) for point in polygon], fill=255)
    yy, xx = np.mgrid[0:size, 0:size]
    center = np.array((50 * size / 100.0, 49 * size / 100.0))
    distance = np.sqrt((xx - center[0]) ** 2 + (yy - center[1]) ** 2)
    radius = size * (0.04 + 0.42 * progress)
    alpha = np.asarray(mask).copy()
    alpha[distance > radius] = 0
    fill = Image.new("RGBA", (size, size), PAPER)
    fill.putalpha(Image.fromarray(alpha, "L"))
    layer.alpha_composite(fill)
    return layer


def _filament_layer(frame, size):
    enter = idea_state(frame, size)["filament"]
    remain = 1.0 - smooth(phase(frame, 52, 59))
    return _stroke(
        _filament_geometry(frame, size),
        enter * remain,
        size,
        TAUPE,
        size * 0.039,
        (0.24, 1.04, 0.17),
    )


def _base_layer(frame, size):
    result = canvas(size)
    lines = (
        ((37, 73), (63, 73), 0.058),
        ((40, 80), (60, 80), 0.052),
        ((44, 87), (56, 87), 0.047),
    )
    build_progress = idea_state(frame, size)["base"]
    exit_progress = smooth(phase(frame, 52, 59))
    unit = size / 100.0
    for index, (start, end, width) in enumerate(lines):
        enter = smooth(np.clip(build_progress * 1.8 - index * 0.4, 0, 1))
        remain = max(0.0, 1.0 - np.clip(exit_progress * 1.22 - index * 0.11, 0, 1))
        center = (np.asarray(start, dtype=float) + np.asarray(end, dtype=float)) / 2
        half = (np.asarray(end, dtype=float) - np.asarray(start, dtype=float)) / 2
        path = np.vstack((center - half * remain, center + half * remain)) * unit
        if enter > 0 and remain > 0:
            visible = reveal_points(path, enter)
            if len(visible) >= 2:
                draw_pressure_stroke(
                    result,
                    visible,
                    BLUE,
                    size * width,
                    pressure_profile(len(visible), 0.34, 1.08, 0.28),
                )
    return result


RAYS = (
    ((30, 24), (20, 16)),
    ((50, 8), (50, 18)),
    ((70, 23), (81, 14)),
    ((80, 43), (91, 42)),
    ((20, 44), (9, 43)),
)


def _rays_layer(frame, size):
    result = canvas(size)
    unit = size / 100.0
    build_progress = idea_state(frame, size)["rays"]
    for index, (inner, outer) in enumerate(RAYS):
        enter = smooth(np.clip(build_progress * 1.5 - index * 0.125, 0, 1))
        exit_start = 46 + index * 0.5
        remain = 1.0 - smooth(phase(frame, exit_start, exit_start + 3))
        path = np.asarray((inner, outer), dtype=float) * unit
        visible = reveal_points(path, enter * remain)
        if len(visible) >= 2:
            draw_pressure_stroke(
                result,
                visible,
                BLUE,
                size * (0.025 + index * 0.0015),
                pressure_profile(len(visible), 0.30, 1.06, 0.14),
            )
    return result


def _glint_layer(frame, size):
    result = canvas(size)
    strength = glint_window(frame, 28, 42)
    if strength <= 0:
        return result
    unit = size / 100.0
    streak = cubic_points(
        (31 * unit, 39 * unit),
        (28 * unit, 31 * unit),
        (32 * unit, 23 * unit),
        (39 * unit, 20 * unit),
        13,
    )
    draw_pressure_stroke(
        result,
        streak,
        PAPER,
        size * 0.019,
        pressure_profile(len(streak), 0.16, 0.84, 0.10),
        strength,
    )
    return result


def idea_layers(frame, size):
    shadow_frame = max(0, frame - 2)
    shadow_near, shadow_far = _glass_strokes(shadow_frame, size)
    near, far = _glass_strokes(frame, size)
    lagged_alpha = ImageChops.lighter(
        shadow_far.getchannel("A"), shadow_near.getchannel("A")
    )
    offset = (round(size * 0.02), round(size * 0.03))
    lagged_alpha = ImageChops.offset(lagged_alpha, *offset)
    lagged_alpha = lagged_alpha.point(
        lambda value: round(value * SHADOW_BLUE[3] / 255)
    )
    shadow = Image.new("RGBA", (size, size), SHADOW_BLUE)
    shadow.putalpha(lagged_alpha)
    return [
        DepthLayer("glass_shadow", shadow, 0),
        DepthLayer("glass_light", _glass_fill(frame, size), 5),
        DepthLayer("filament", _filament_layer(frame, size), 10),
        DepthLayer("glass_far", far, 15),
        DepthLayer("base", _base_layer(frame, size), 20),
        DepthLayer("glass_near", near, 25),
        DepthLayer("rays", _rays_layer(frame, size), 30),
        DepthLayer("directional_glint", _glint_layer(frame, size), 40),
    ]


def draw_frame(frame, size):
    if frame <= 0 or frame >= 59:
        return canvas(size)
    return compose_depth(idea_layers(frame, size))


SPEC = FrameMotionSpec(
    "09-idea",
    retime_draw(draw_frame, 48),
    duration_frames=48,
    tags=("batch1", "story", "tactile"),
)
