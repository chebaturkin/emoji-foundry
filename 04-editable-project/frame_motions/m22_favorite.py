import math

import numpy as np
from PIL import ImageDraw

from frame_core.brush import draw_pressure_stroke, pressure_profile
from frame_core.composite import phase, smooth
from frame_core.depth import DepthLayer, compose_depth
from frame_core.models import FrameMotionSpec
from frame_motions.common import BLUE, PAPER, canvas


def favorite_state(frame):
    leave = smooth(phase(frame, 40, 47))
    return {
        "bookmark": smooth(phase(frame, 1, 17)) * (1.0 - leave),
        "notch": smooth(phase(frame, 13, 28)) * (1.0 - leave),
        "settle": math.sin(math.pi * phase(frame, 25, 38)) * (1.0 - leave),
    }


def _bookmark_points(state, size):
    unit = size / 100.0
    top = 20.0
    bottom = top + 54.0 * state["bookmark"]
    notch_depth = 3.0 + 14.0 * state["notch"]
    settle = 1.2 * state["settle"]
    return np.array((
        (30, top),
        (70, top),
        (70 + settle * .3, bottom),
        (50, bottom - notch_depth - settle),
        (30 - settle * .3, bottom),
    ), dtype=float) * unit


def favorite_layers(frame, size):
    state = favorite_state(frame)
    depth = canvas(size)
    bookmark = canvas(size)
    inset = canvas(size)
    if state["bookmark"] > 0:
        points = _bookmark_points(state, size)
        shifted = points + np.array((size * .018, size * .024))
        ImageDraw.Draw(depth, "RGBA").polygon(
            [tuple(point) for point in shifted], fill=(*BLUE[:3], 100)
        )
        ImageDraw.Draw(bookmark, "RGBA").polygon(
            [tuple(point) for point in points], fill=BLUE
        )
        unit = size / 100.0
        inset_path = np.array((
            (34, 24), (66, 24), (66, 69),
            (50, 58 + 2 * (1 - state["notch"])), (34, 69),
        ), dtype=float) * unit
        draw_pressure_stroke(
            inset, inset_path, PAPER, size * .035,
            pressure_profile(len(inset_path), .45, .9, .4), state["bookmark"],
        )
    return [
        DepthLayer("blue_depth", depth, 0),
        DepthLayer("blue_bookmark", bookmark, 10),
        DepthLayer("paper_inset", inset, 20),
    ]


def draw_frame(frame, size):
    if frame <= 0 or frame >= 47:
        return canvas(size)
    return compose_depth(favorite_layers(frame, size))


SPEC = FrameMotionSpec("22-favorite", draw_frame, duration_frames=48, tags=("soft", "tactile"))
