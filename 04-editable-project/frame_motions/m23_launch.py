import math

import numpy as np
from PIL import ImageDraw

from frame_core.brush import draw_pressure_stroke, pressure_profile
from frame_core.composite import phase, smooth
from frame_core.depth import DepthLayer, compose_depth
from frame_core.models import FrameMotionSpec
from frame_core.path import cubic_points
from frame_motions.common import BLUE, PAPER, TAUPE, canvas
from frame_motions.native_utils import master_image, transform_image


def launch_state(frame, size):
    entry = smooth(phase(frame, 1, 15))
    flame = smooth(phase(frame, 8, 20)) * (1.0 - smooth(phase(frame, 39, 47)))
    flight = smooth(phase(frame, 19, 38))
    return {
        "entry": entry,
        "flame": flame,
        "flight": flight,
        "rocket_y": size * (0.25 * (1.0 - entry) - 0.15 * flight),
        "trail": math.sin(math.pi * phase(frame, 17, 45)) * flame,
    }


def _trail(frame, size):
    state = launch_state(frame, size)
    layer = canvas(size)
    unit = size / 100.0
    y = state["rocket_y"]
    path = cubic_points(
        (50 * unit, 79 * unit + y),
        (47 * unit, 84 * unit + y),
        (53 * unit, 88 * unit + y),
        (50 * unit, 92 * unit + y),
        20,
    )
    draw_pressure_stroke(
        layer, path, BLUE, size * .018,
        pressure_profile(len(path), .2, 1.0, .12), state["trail"] * .7,
    )
    return layer


def _flame(frame, size):
    state = launch_state(frame, size)
    layer = canvas(size)
    if state["flame"] <= 0:
        return layer
    unit = size / 100.0
    y = state["rocket_y"]
    length = (9 + 12 * state["flame"] + 2 * math.sin(math.pi * phase(frame, 20, 38))) * unit
    points = np.array((
        (44 * unit, 72 * unit + y),
        (50 * unit, 72 * unit + y + length),
        (56 * unit, 72 * unit + y),
        (52 * unit, 75 * unit + y),
        (48 * unit, 75 * unit + y),
    ))
    ImageDraw.Draw(layer, "RGBA").polygon(
        [tuple(point) for point in points], fill=TAUPE
    )
    highlight = canvas(size)
    inner = np.array((
        (48 * unit, 74 * unit + y),
        (50 * unit, 74 * unit + y + length * .62),
        (52 * unit, 74 * unit + y),
    ))
    ImageDraw.Draw(highlight, "RGBA").polygon(
        [tuple(point) for point in inner], fill=PAPER
    )
    layer.alpha_composite(highlight)
    return layer


def launch_layers(frame, size):
    state = launch_state(frame, size)
    rocket = transform_image(
        master_image("23-launch", size),
        scale=(.72, .72),
        rotation=1.8 * math.sin(math.pi * phase(frame, 18, 36)),
        offset=(0, state["rocket_y"] * 100 / size),
    )
    return [
        DepthLayer("trail", _trail(frame, size), 0),
        DepthLayer("rocket", rocket, 10),
        DepthLayer("flame", _flame(frame, size), 20),
    ]


def draw_frame(frame, size):
    if frame <= 0 or frame >= 47:
        return canvas(size)
    return compose_depth(launch_layers(frame, size))


SPEC = FrameMotionSpec("23-launch", draw_frame, duration_frames=48, tags=("story", "tactile"))
