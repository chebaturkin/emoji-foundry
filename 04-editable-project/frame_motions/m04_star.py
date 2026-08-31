import math

import numpy as np
from PIL import Image, ImageChops, ImageDraw

from frame_core.brush import draw_pressure_stroke, pressure_profile
from frame_core.composite import phase, smooth
from frame_core.depth import DepthLayer, compose_depth, glint_window
from frame_core.models import FrameMotionSpec
from frame_core.retime import retime_draw
from frame_motions.common import BLUE, PAPER, canvas


TIP_TIMELINE = {
    0: (3, 14),
    1: (6, 17),
    2: (9, 20),
    3: (12, 23),
    4: (15, 26),
}

FOLD_TIMELINE = {
    4: (48, 55),
    3: (49, 56),
    2: (50, 57),
    1: (51, 58),
    0: (52, 59),
}

SHADOW_BLUE = (46, 58, 77, 148)


def tip_timeline():
    return dict(TIP_TIMELINE)


def _polar(center, radius, angle):
    return center + np.array((math.cos(angle), math.sin(angle))) * radius


def _tip_scale(frame, index):
    start, end = TIP_TIMELINE[index]
    fold_start, fold_end = FOLD_TIMELINE[index]
    return smooth(phase(frame, start, end)) * (
        1.0 - smooth(phase(frame, fold_start, fold_end))
    )


def _material_envelope(frame):
    return smooth(phase(frame, 2, 12)) * (
        1.0 - smooth(phase(frame, 53, 59))
    )


def _tip_geometry(frame, index, size):
    """Unfold one paper triangle around its fixed inner base."""
    scale = _tip_scale(frame, index)
    if scale <= 0:
        return None

    center = np.array((size * 0.5, size * 0.5))
    angle = -math.pi / 2 + index * math.tau / 5
    inner_radius = size * 0.225
    outer_radius = size * 0.385
    base_left = _polar(center, inner_radius, angle - math.pi / 5)
    base_right = _polar(center, inner_radius, angle + math.pi / 5)
    base_mid = (base_left + base_right) / 2
    outer = _polar(center, outer_radius, angle)

    # The crease stays pinned while the point opens away from the centre.
    tip = base_mid + (outer - base_mid) * scale
    half_base = 0.72 + 0.28 * scale
    left = base_mid + (base_left - base_mid) * half_base
    right = base_mid + (base_right - base_mid) * half_base
    path = np.vstack((left, tip, right))
    envelope = _material_envelope(frame)
    return center + (path - center) * envelope


def _core_geometry(frame, size):
    scale = _material_envelope(frame)
    if scale <= 0:
        return None
    center = np.array((size * 0.5, size * 0.5))
    points = [
        _polar(center, size * 0.228, -math.pi / 2 + math.pi / 5 + i * math.tau / 5)
        for i in range(5)
    ]
    points = np.asarray(points)
    return center + (points - center) * scale


def _filled_polygon(path, color, size):
    layer = canvas(size)
    if path is not None and len(path) >= 3 and not np.allclose(path, path[0]):
        ImageDraw.Draw(layer, "RGBA").polygon(
            [tuple(point) for point in path], fill=color
        )
    return layer


def _tip_layer(path, size):
    layer = _filled_polygon(path, PAPER, size)
    if path is None:
        return layer
    outer_segments = np.asarray((path[0], path[1], path[2]))
    draw_pressure_stroke(
        layer,
        outer_segments,
        BLUE,
        size * 0.055,
        pressure_profile(len(outer_segments), 0.40, 1.14, 0.31),
    )
    return layer


def _core_layer(path, size):
    # The five crease edges stay below their paper tips. Only the exposed V-shaped
    # sides receive ink, so the settled star has no internal pentagon seams.
    return _filled_polygon(path, PAPER, size)


def _star_material_mask(frame, size):
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    core = _core_geometry(frame, size)
    if core is not None:
        draw.polygon([tuple(point) for point in core], fill=255)
    for index in range(5):
        tip = _tip_geometry(frame, index, size)
        if tip is not None:
            draw.polygon([tuple(point) for point in tip], fill=255)
    return mask


def _star_perimeter(size):
    center = np.array((size * 0.5, size * 0.5))
    points = []
    for index in range(5):
        tip_angle = -math.pi / 2 + index * math.tau / 5
        points.append(_polar(center, size * 0.385, tip_angle))
        points.append(_polar(center, size * 0.225, tip_angle + math.pi / 5))
    return np.asarray(points)


def _glint_layer(frame, size):
    glint = canvas(size)
    strength = glint_window(frame, 29, 43)
    if strength <= 0:
        return glint

    travel = smooth(phase(frame, 29, 43))
    center = np.array((size * 0.5, size * 0.5))
    perimeter = _star_perimeter(size)
    progress = travel * len(perimeter)
    segment = min(len(perimeter) - 1, int(progress))
    local = progress - segment
    start = perimeter[segment]
    end = perimeter[(segment + 1) % len(perimeter)]
    position = start + (end - start) * local
    position = center + (position - center) * 0.88
    direction = end - start
    direction /= max(np.linalg.norm(direction), 1e-9)
    tangent = direction * size * 0.026
    streak = np.vstack((position - tangent, position, position + tangent))
    draw_pressure_stroke(
        glint,
        streak,
        PAPER,
        size * 0.020,
        pressure_profile(len(streak), 0.16, 1.0, 0.12),
        strength,
    )
    clipped_alpha = ImageChops.multiply(
        glint.getchannel("A"), _star_material_mask(frame, size)
    )
    glint.putalpha(clipped_alpha)
    return glint


def star_layers(frame, size):
    layers = []
    shadow_frame = max(0, frame - 2)
    shadow_remain = 1.0 - smooth(phase(shadow_frame, 53, 59))
    shadow_offset = np.array((2.3, 3.0)) * size / 100.0 * shadow_remain
    lagged_core = _core_geometry(shadow_frame, size)
    if lagged_core is not None:
        layers.append(
            DepthLayer(
                "core_shadow",
                _filled_polygon(lagged_core + shadow_offset, SHADOW_BLUE, size),
                0,
            )
        )

    for index in range(5):
        lagged_tip = _tip_geometry(shadow_frame, index, size)
        if lagged_tip is not None:
            layers.append(
                DepthLayer(
                    f"tip_{index}_shadow",
                    _filled_polygon(lagged_tip + shadow_offset, SHADOW_BLUE, size),
                    index + 1,
                )
            )

    core = _core_geometry(frame, size)
    for index in range(5):
        tip = _tip_geometry(frame, index, size)
        layers.append(DepthLayer(f"tip_{index}", _tip_layer(tip, size), 20 + index))

    # The core lies over folded creases and masks non-exterior stroke segments.
    layers.append(DepthLayer("paper_core", _core_layer(core, size), 30))
    layers.append(DepthLayer("travelling_glint", _glint_layer(frame, size), 40))
    return layers


def draw_frame(frame, size):
    if frame <= 0 or frame >= 59:
        return canvas(size)
    return compose_depth(star_layers(frame, size))


SPEC = FrameMotionSpec(
    "04-star",
    retime_draw(draw_frame, 48),
    duration_frames=48,
    tags=("batch1", "impact", "tactile"),
)
