import numpy as np
from PIL import ImageDraw

from frame_core.composite import phase, smooth
from frame_core.depth import DepthLayer, compose_depth
from frame_core.models import FrameMotionSpec
from frame_motions.common import BLUE, INK, TAUPE, canvas
from frame_motions.face_family import base_face_layers, eye_path, mouth_path, stroke

def sad_state(frame, size):
    del size
    face = smooth(phase(frame, 1, 10)) * (1.0 - smooth(phase(frame, 41, 47)))
    face_drop = smooth(phase(frame, 11, 27)) * (1.0 - smooth(phase(frame, 37, 46)))
    tear_fall = smooth(phase(frame, 26, 39)) * (1.0 - smooth(phase(frame, 40, 46)))
    return {"face": face, "tear_fall": tear_fall, "face_drop": face_drop}


def _ink_features(size, state):
    image = canvas(size)
    drop = state["face_drop"]
    unit = size / 100.0
    # Brows converge as the paper face settles; they remain intact throughout.
    left = eye_path(size, True, openness=0.78, y_shift=3.0 * drop)
    right = eye_path(size, False, openness=0.78, y_shift=3.0 * drop)
    left[:, 1] += (left[:, 0] - 35 * unit) * 0.10 * drop
    right[:, 1] -= (right[:, 0] - 65 * unit) * 0.10 * drop
    stroke(image, left, INK, size * 0.047)
    stroke(image, right, INK, size * 0.047)
    stroke(image, mouth_path(size, sad=state["face_drop"], y_shift=4.0 * drop), INK, size * 0.052)
    return image


def _tear_layer(size, fall):
    image = canvas(size)
    if fall <= 0.0:
        return image
    unit = size / 100.0
    x = 74.0 * unit
    y = (46.0 + 31.0 * fall) * unit
    width = (4.4 - 1.0 * fall) * unit
    height = (5.0 + 3.4 * fall) * unit
    points = np.array(((x, y - height), (x + width, y), (x, y + height), (x - width, y)), dtype=float)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.polygon([tuple(point) for point in points], fill=BLUE)
    stroke(image, np.vstack((points, points[0])), BLUE, size * 0.016)
    return image


def _face_drop_layer(size, drop):
    image = canvas(size)
    if drop <= 0.0:
        return image
    draw = ImageDraw.Draw(image, "RGBA")
    unit = size / 100.0
    alpha = round(115 * min(1.0, drop))
    for cx in (28.0, 72.0):
        cy = (61.0 + 2.0 * drop) * unit
        r = 1.8 * unit
        draw.ellipse((cx * unit - r, cy - r, cx * unit + r, cy + r), fill=(*TAUPE[:3], alpha))
    return image


def sad_layers(frame, size):
    state = sad_state(frame, size)
    drop = 3.2 * state["face_drop"]
    depth, paper, outline = base_face_layers(size, state["face"], drop=drop)
    return [
        DepthLayer("blue_depth", depth, 0),
        DepthLayer("paper_face", paper, 10),
        DepthLayer("blue_outline", outline, 20),
        DepthLayer("ink_features", _ink_features(size, state), 30),
        DepthLayer("tear_fall", _tear_layer(size, state["tear_fall"]), 40),
        DepthLayer("face_drop", _face_drop_layer(size, state["face_drop"]), 50),
    ]


def draw_frame(frame, size):
    if frame <= 0 or frame >= 47:
        return canvas(size)
    return compose_depth(sad_layers(frame, size))


SPEC = FrameMotionSpec("14-sad", draw_frame, duration_frames=48, tags=("batch1", "soft", "tactile"))
