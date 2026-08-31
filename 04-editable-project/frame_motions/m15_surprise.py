import math

from PIL import ImageDraw

from frame_core.composite import phase, smooth
from frame_core.depth import DepthLayer, compose_depth
from frame_core.models import FrameMotionSpec
from frame_motions.common import INK, canvas
from frame_motions.face_family import base_face_layers, eye_path, mouth_path, stroke


def surprise_state(frame, size=100):
    del size
    mouth_open = smooth(phase(frame, 8, 16)) * (1.0 - smooth(phase(frame, 40, 47)))
    eyes_wide = smooth(phase(frame, 14, 24)) * (1.0 - smooth(phase(frame, 39, 47)))
    recoil_phase = phase(frame, 24, 38)
    recoil = math.sin(math.pi * recoil_phase) * (1.0 - 0.35 * recoil_phase) if 0.0 < recoil_phase < 1.0 else 0.0
    face = smooth(phase(frame, 1, 10)) * (1.0 - smooth(phase(frame, 41, 47)))
    return {"face": face, "mouth_open": mouth_open, "eyes_wide": eyes_wide, "recoil": recoil}


def _mouth_layer(size, state):
    image = canvas(size)
    recoil = state["recoil"]
    mouth = mouth_path(size, open_amount=state["mouth_open"], y_shift=1.5 * recoil)
    if state["mouth_open"] > 0.02:
        ImageDraw.Draw(image, "RGBA").polygon([tuple(point) for point in mouth], fill=INK)
    stroke(image, mouth, INK, size * 0.044)
    return image


def _ink_features(size, state):
    image = canvas(size)
    recoil = state["recoil"]
    eye_open = 1.0 + 0.45 * state["eyes_wide"]
    y_shift = -2.2 * state["eyes_wide"] - 1.2 * recoil
    stroke(image, eye_path(size, True, openness=eye_open, y_shift=y_shift), INK, size * 0.047)
    stroke(image, eye_path(size, False, openness=eye_open, y_shift=y_shift), INK, size * 0.047)
    return image


def surprise_layers(frame, size):
    state = surprise_state(frame, size)
    depth, paper, outline = base_face_layers(size, state["face"], recoil=2.2 * state["recoil"])
    return [
        DepthLayer("blue_depth", depth, 0),
        DepthLayer("paper_face", paper, 10),
        DepthLayer("blue_outline", outline, 20),
        DepthLayer("mouth_open", _mouth_layer(size, state), 30),
        DepthLayer("ink_features", _ink_features(size, state), 40),
        DepthLayer("recoil", canvas(size), 50),
    ]


def draw_frame(frame, size):
    if frame <= 0 or frame >= 47:
        return canvas(size)
    return compose_depth(surprise_layers(frame, size))


SPEC = FrameMotionSpec("15-surprise", draw_frame, duration_frames=48, tags=("soft", "tactile"))
