import math

import numpy as np
from PIL import ImageChops, ImageDraw

from frame_core.brush import draw_pressure_stroke, pressure_profile
from frame_core.composite import phase, smooth
from frame_core.depth import DepthLayer, compose_depth
from frame_core.models import FrameMotionSpec
from frame_motions.common import BLUE, PAPER, canvas


def star_four_state(frame):
    leave = smooth(phase(frame, 39, 47))
    top = smooth(phase(frame, 2, 15)) * (1.0 - leave)
    right = smooth(phase(frame, 7, 20)) * (1.0 - leave)
    left = smooth(phase(frame, 10, 23)) * (1.0 - leave)
    bottom = smooth(phase(frame, 14, 27)) * (1.0 - leave)
    accent = math.sin(math.pi * phase(frame, 22, 37))
    values = (top, right, bottom, left)
    leading = min(3, max(0, int(phase(frame, 22, 36) * 4)))
    return {
        "top": top,
        "right": right,
        "bottom": bottom,
        "left": left,
        "rays": values,
        "settle": math.sin(math.pi * phase(frame, 24, 38)) * (1.0 - leave),
        "glints": tuple(accent if index == leading else 0.0 for index in range(4)),
    }


def _star_points(state, size):
    unit = size / 100.0
    center = np.array((50.0, 50.0)) * unit
    tips = (state["top"], state["right"], state["bottom"], state["left"])
    radii = tuple(13.0 + value * 23.0 for value in tips)
    settle = state["settle"] * 1.5
    points = []
    for index in range(16):
        angle = -math.pi / 2 + index * math.pi / 8
        if index % 4 == 0:
            tip = index // 4
            radius = radii[tip] + settle * (1 if tip % 2 == 0 else -.55)
        elif index % 2 == 0:
            radius = 9.0
        else:
            radius = 7.5
        points.append(
            center + np.array((math.cos(angle), math.sin(angle))) * radius * unit
        )
    return np.asarray(points)


def _glint(state, star_mask, size):
    index = max(range(4), key=lambda item: state["glints"][item])
    strength = state["glints"][index]
    layer = canvas(size)
    if strength <= 0:
        return layer
    unit = size / 100.0
    ends = ((50, 17), (83, 50), (50, 83), (17, 50))
    end = np.asarray(ends[index], dtype=float) * unit
    center = np.asarray((50, 50), dtype=float) * unit
    start = center + (end - center) * .55
    path = np.linspace(start, end, 18)
    draw_pressure_stroke(
        layer, path, PAPER, size * .018,
        pressure_profile(len(path), .2, 1.0, .15), strength,
    )
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), star_mask))
    return layer


def star_four_layers(frame, size):
    state = star_four_state(frame)
    points = _star_points(state, size)
    material = canvas(size)
    ImageDraw.Draw(material, "RGBA").polygon([tuple(p) for p in points], fill=BLUE)
    outline = canvas(size)
    closed = np.vstack((points, points[:1]))
    draw_pressure_stroke(
        outline, closed, BLUE, size * .03,
        pressure_profile(len(closed), .8, 1.0, .8), 1.0,
    )
    depth = canvas(size)
    shifted = points + np.array((size * .018, size * .022))
    ImageDraw.Draw(depth, "RGBA").polygon(
        [tuple(p) for p in shifted], fill=(*BLUE[:3], 90)
    )
    return [
        DepthLayer("blue_depth", depth, 0),
        DepthLayer("single_star", material, 10),
        DepthLayer("blue_outline", outline, 20),
        DepthLayer("paper_glint", _glint(state, material.getchannel("A"), size), 30),
    ]


def draw_frame(frame, size):
    if frame <= 0 or frame >= 47:
        return canvas(size)
    return compose_depth(star_four_layers(frame, size))


SPEC = FrameMotionSpec("05-star-four", draw_frame, duration_frames=48, tags=("impact", "tactile"))
