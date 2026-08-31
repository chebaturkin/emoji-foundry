import math

import numpy as np

from frame_core.composite import phase, smooth
from frame_core.depth import DepthLayer, compose_depth
from frame_core.models import FrameMotionSpec
from frame_motions.common import BLUE, TAUPE, canvas
from frame_motions.native_utils import masked_part, master_image, transform_image


def heart_double_state(frame):
    leave = smooth(phase(frame, 34, 41))
    return {
        "inner": smooth(phase(frame, 1, 13)) * (1 - leave),
        "outer": smooth(phase(frame, 8, 20)) * (1 - leave),
        "inner_beat": math.sin(math.pi * phase(frame, 14, 22)),
        "outer_beat": math.sin(math.pi * phase(frame, 21, 30)),
    }


def draw_frame(frame, size):
    if frame <= 0 or frame >= 41:
        return canvas(size)
    state = heart_double_state(frame)
    source = master_image("02-heart-double", size)
    pixels = np.asarray(source)
    rgb = pixels[:, :, :3].astype(np.int16)
    inner_region = np.max(np.abs(rgb - np.array(TAUPE[:3], dtype=np.int16)), axis=2) < 42
    outer_region = (pixels[:, :, 3] > 0) & ~inner_region
    inner = masked_part(source, inner_region)
    outer = masked_part(source, outer_region)
    inner_scale = (.42 + .58 * state["inner"]) * (1 + .10 * state["inner_beat"])
    outer_scale = (.50 + .50 * state["outer"]) * (1 + .075 * state["outer_beat"])
    inner = transform_image(inner, (inner_scale, inner_scale), opacity=state["inner"])
    outer = transform_image(outer, (outer_scale, outer_scale), opacity=state["outer"])
    echo = transform_image(outer, (1.04, 1.04), opacity=.22 * state["outer_beat"])
    tint = canvas(size)
    tint.paste(BLUE, (0, 0, size, size), echo.getchannel("A"))
    return compose_depth([
        DepthLayer("outer_echo", tint, 0),
        DepthLayer("outer_heart", outer, 10),
        DepthLayer("inner_heart", inner, 20),
    ])


SPEC = FrameMotionSpec("02-heart-double", draw_frame, duration_frames=42, tags=("soft", "tactile"))
