import math

import numpy as np
from PIL import ImageDraw

from frame_core.brush import draw_pressure_stroke, pressure_profile
from frame_core.composite import phase, smooth
from frame_core.depth import DepthLayer, compose_depth
from frame_core.models import FrameMotionSpec
from frame_core.path import cubic_points
from frame_motions.common import BLUE, PAPER, canvas


DELAYS = (8, 11, 14, 9, 16, 12, 18, 10)
LENGTHS = (40, 36, 43, 38, 42, 35, 44, 39)
PRESSURES = (.020, .027, .017, .032, .023, .029, .019, .025)


def explosion_ray_state(frame):
    ray_progress = tuple(
        smooth(phase(frame, delay, delay + 11))
        * (1.0 - smooth(phase(frame, 23 + index, 35 + index)))
        for index, delay in enumerate(DELAYS)
    )
    core_impulses = tuple(
        progress * (0.35 + PRESSURES[index] * 18.0)
        for index, progress in enumerate(ray_progress)
    )
    return {
        "ray_progress": ray_progress,
        "core_impulses": core_impulses,
        "pressures": PRESSURES,
    }


def _core_points(state, size):
    unit = size / 100.0
    points = []
    for index in range(16):
        angle = -math.pi / 2 + index * math.pi / 8
        nearest_ray = index // 2
        impulse = state["core_impulses"][nearest_ray]
        radius = 16.5 + (2.2 if index % 2 == 0 else -1.1) + impulse * 4.0
        points.append((
            50 * unit + math.cos(angle) * radius * unit,
            50 * unit + math.sin(angle) * radius * unit,
        ))
    return np.asarray(points)


def _ray_layer(state, size, index, color, offset=(0.0, 0.0)):
    progress = state["ray_progress"][index]
    layer = canvas(size)
    if progress <= 0:
        return layer
    unit = size / 100.0
    angle = math.radians(-90 + index * 45 + (index % 2) * 4)
    direction = np.array((math.cos(angle), math.sin(angle)))
    normal = np.array((-direction[1], direction[0]))
    displacement = np.asarray(offset) * unit
    start = np.array((50, 50)) * unit + direction * 18 * unit + displacement
    end = np.array((50, 50)) * unit + direction * LENGTHS[index] * unit + displacement
    control = (start + end) / 2 + normal * ((index % 3) - 1) * 1.6 * unit
    path = cubic_points(start, control, control, end, 16)
    draw_pressure_stroke(
        layer, path, color, size * PRESSURES[index] * 1.18,
        pressure_profile(len(path), .25, 1.0, .15), progress,
    )
    return layer


def explosion_ray_layers(frame, size):
    state = explosion_ray_state(frame)
    core = _core_points(state, size)
    material = canvas(size)
    ImageDraw.Draw(material, "RGBA").polygon([tuple(p) for p in core], fill=PAPER)
    outline = canvas(size)
    closed = np.vstack((core, core[:1]))
    draw_pressure_stroke(
        outline, closed, BLUE, size * .045,
        pressure_profile(len(closed), .8, 1.0, .8), 1.0,
    )
    shadow = canvas(size)
    shifted = core + np.array((size * .018, size * .022))
    ImageDraw.Draw(shadow, "RGBA").polygon(
        [tuple(p) for p in shifted], fill=(*BLUE[:3], 105)
    )
    layers = []
    for index in range(8):
        layers.append(DepthLayer(
            f"ray_depth_{index}",
            _ray_layer(state, size, index, BLUE, (1.4, 1.8)),
            index,
        ))
        layers.append(DepthLayer(
            f"ray_{index}",
            _ray_layer(state, size, index, PAPER),
            8 + index,
        ))
    layers.extend((
        DepthLayer("core_depth", shadow, 10),
        DepthLayer("paper_core", material, 20),
        DepthLayer("core_outline", outline, 30),
    ))
    return layers


def draw_frame(frame, size):
    if frame <= 0 or frame >= 47:
        return canvas(size)
    visibility = smooth(phase(frame, 1, 8)) * (1.0 - smooth(phase(frame, 40, 47)))
    if visibility <= 0:
        return canvas(size)
    image = compose_depth(explosion_ray_layers(frame, size))
    if visibility < 1:
        alpha = image.getchannel("A").point(lambda value: round(value * visibility))
        image.putalpha(alpha)
    return image


SPEC = FrameMotionSpec("24-explosion-ray", draw_frame, duration_frames=48, tags=("impact", "tactile"))
