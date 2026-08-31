import math

import numpy as np
from PIL import ImageDraw

from frame_core.composite import phase, smooth
from frame_core.depth import DepthLayer, compose_depth
from frame_core.models import FrameMotionSpec
from frame_core.path import cubic_points
from frame_motions.common import BLUE, PAPER, canvas
from frame_motions.native_utils import paper_blue_stroke


def question_state(frame, size):
    fall = smooth(phase(frame, 1, 10))
    bounce = math.sin(math.pi * phase(frame, 10, 17))
    return {
        "dot": smooth(phase(frame, 1, 6)) * (1-smooth(phase(frame, 35, 41))),
        "dot_y": size * (0.25 + 0.50*fall - 0.05*bounce),
        "curve": smooth(phase(frame, 7, 21)) * (1-smooth(phase(frame, 32, 40))),
        "tilt": 4.0 * math.sin(math.pi * phase(frame, 19, 29)),
    }


def _dot(frame, size):
    state = question_state(frame, size)
    image = canvas(size)
    if state["dot"] <= 0:
        return image
    unit = size/100.0
    radius = (5.5 + 1.5*math.sin(math.pi*phase(frame, 9, 16))) * unit * state["dot"]
    cx, cy = 50*unit, state["dot_y"]
    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse((cx-radius+2*unit, cy-radius+2*unit, cx+radius+2*unit, cy+radius+2*unit), fill=BLUE)
    draw.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), fill=PAPER)
    return image


def _curve(frame, size):
    unit = size/100.0
    state = question_state(frame, size)
    path = np.vstack((
        cubic_points((34*unit, 30*unit), (38*unit, 13*unit), (72*unit, 15*unit), (70*unit, 34*unit), 24),
        cubic_points((70*unit, 34*unit), (69*unit, 47*unit), (51*unit, 47*unit), (50*unit, 60*unit), 22)[1:],
    ))
    center = np.array((50*unit, 43*unit))
    angle = math.radians(state["tilt"])
    rotation = np.array(((math.cos(angle), -math.sin(angle)), (math.sin(angle), math.cos(angle))))
    path = center + (path-center) @ rotation.T
    return paper_blue_stroke(path, size, size*.052, state["curve"])


def question_layers(frame, size):
    return [DepthLayer("falling_dot", _dot(frame, size), 10), DepthLayer("wrapping_curve", _curve(frame, size), 20)]


def draw_frame(frame, size):
    if frame <= 0 or frame >= 41:
        return canvas(size)
    return compose_depth(question_layers(frame, size))


SPEC = FrameMotionSpec("18-question", draw_frame, duration_frames=42, tags=("story", "tactile"))
