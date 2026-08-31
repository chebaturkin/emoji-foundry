import math

import numpy as np

from frame_core.brush import draw_pressure_stroke, pressure_profile
from frame_core.composite import phase, smooth
from frame_core.depth import DepthLayer, compose_depth
from frame_core.models import FrameMotionSpec
from frame_motions.common import BLUE, PAPER, canvas


def explosion_ring_state(frame):
    close = smooth(phase(frame, 5, 22))
    expansion = smooth(phase(frame, 20, 36))
    retract = smooth(phase(frame, 39, 47))
    return {
        "clockwise_arc": close * (1.0 - retract),
        "counterclockwise_arc": smooth(phase(frame, 8, 22)) * (1.0 - retract),
        "radius": 10.0 + 22.0 * expansion,
        "irregularity": math.sin(math.pi * phase(frame, 16, 39)) * (1.0 - retract),
        "retract": retract,
    }


def _arc_path(size, radius, irregularity, start, sweep, progress):
    count = max(2, round(72 * progress))
    angles = np.linspace(start, start + sweep * progress, count)
    wobble = irregularity * (
        1.15 * np.sin(angles * 5) + .55 * np.sin(angles * 3 + .8)
    )
    rr = (radius + wobble) * size / 100.0
    center = size * .5
    return np.column_stack((
        center + np.cos(angles) * rr,
        center + np.sin(angles) * rr,
    ))


def _arc(size, state, direction):
    progress = state["clockwise_arc" if direction > 0 else "counterclockwise_arc"]
    layer = canvas(size)
    if progress <= 0:
        return layer
    path = _arc_path(
        size, state["radius"], state["irregularity"],
        -math.pi / 2, direction * math.pi, progress,
    )
    draw_pressure_stroke(
        layer, path, BLUE, size * .043,
        pressure_profile(len(path), .3, 1.0, .35), 1.0,
    )
    return layer


def explosion_ring_layers(frame, size):
    state = explosion_ring_state(frame)
    inner_strength = smooth(phase(frame, 1, 14)) * (
        1.0 - smooth(phase(frame, 31, 43))
    )
    inner = canvas(size)
    if inner_strength > 0:
        path = _arc_path(size, 7 + state["radius"] * .22, 0, 0, math.tau, 1.0)
        draw_pressure_stroke(
            inner, path, PAPER, size * .032,
            pressure_profile(len(path), .8, 1.0, .8), inner_strength,
        )
    echo = canvas(size)
    echo_strength = math.sin(math.pi * phase(frame, 27, 42))
    if echo_strength > 0:
        path = _arc_path(
            size, state["radius"] + 6, state["irregularity"] * .5,
            0, math.tau, 1.0,
        )
        draw_pressure_stroke(
            echo, path, BLUE, size * .014,
            pressure_profile(len(path), .45, 1.0, .45), echo_strength * .65,
        )
    return [
        DepthLayer("clockwise_arc", _arc(size, state, 1), 10),
        DepthLayer("counterclockwise_arc", _arc(size, state, -1), 10),
        DepthLayer("paper_impact", inner, 20),
        DepthLayer("material_echo", echo, 30),
    ]


def draw_frame(frame, size):
    if frame <= 0 or frame >= 47:
        return canvas(size)
    return compose_depth(explosion_ring_layers(frame, size))


SPEC = FrameMotionSpec("26-explosion-ring", draw_frame, duration_frames=48, tags=("impact", "tactile"))
