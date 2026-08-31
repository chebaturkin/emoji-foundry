import math

import numpy as np

from frame_core.composite import phase, smooth
from frame_core.depth import DepthLayer, compose_depth
from frame_core.models import FrameMotionSpec
from frame_core.path import reveal_points
from frame_motions.common import PAPER, canvas
from frame_motions.native_utils import masked_part, master_image, paper_blue_stroke, transform_image


def lightning_round_state(frame):
    return {
        "ring": smooth(phase(frame, 1, 14)) * (1 - smooth(phase(frame, 34, 41))),
        "bolt": smooth(phase(frame, 12, 21)) * (1 - smooth(phase(frame, 32, 40))),
        "charge": math.sin(math.pi * phase(frame, 18, 34)),
        "charge_angle": 40 + 300 * smooth(phase(frame, 19, 33)),
    }


def _circle(size):
    unit = size / 100
    angles = np.linspace(-math.pi / 2, math.pi * 1.5, 90)
    radii = 33 * unit * (1 + .012 * np.sin(angles * 5))
    return np.column_stack((50*unit + np.cos(angles)*radii, 50*unit + np.sin(angles)*radii))


def _charge(frame, size):
    state = lightning_round_state(frame)
    image = canvas(size)
    if state["charge"] <= 0:
        return image
    unit = size / 100
    angle = math.radians(state["charge_angle"] - 90)
    center = np.array((50 + math.cos(angle)*33, 50 + math.sin(angle)*33)) * unit
    radius = (1.7 + 1.6 * state["charge"]) * unit
    from PIL import ImageDraw
    ImageDraw.Draw(image, "RGBA").ellipse((center[0]-radius, center[1]-radius, center[0]+radius, center[1]+radius), fill=PAPER)
    return image


def draw_frame(frame, size):
    if frame <= 0 or frame >= 41:
        return canvas(size)
    state = lightning_round_state(frame)
    ring = paper_blue_stroke(_circle(size), size, size*.025, state["ring"], offset=(0, 0))
    source = master_image("08-lightning-round", size)
    yy, _ = np.mgrid[0:size, 0:size]
    reveal = yy <= size * (.08 + .84 * state["bolt"])
    bolt = masked_part(source, np.ones((size, size), dtype=bool), reveal)
    bolt = transform_image(bolt, (.84 + .16*state["bolt"], 1.06 - .06*state["bolt"]), opacity=state["bolt"])
    return compose_depth([
        DepthLayer("charged_ring", ring, 0),
        DepthLayer("bolt", bolt, 10),
        DepthLayer("residual_charge", _charge(frame, size), 20),
    ])


SPEC = FrameMotionSpec("08-lightning-round", draw_frame, duration_frames=42, tags=("impact", "tactile"))
