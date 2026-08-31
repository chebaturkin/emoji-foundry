from frame_core.composite import phase, smooth
from frame_core.depth import DepthLayer, compose_depth
from frame_core.models import FrameMotionSpec
from frame_motions.common import INK, canvas
from frame_motions.face_family import base_face_layers, draw_cheek_accents, eye_path, mouth_path, stroke


def smile_state(frame, size):
    del size
    face = smooth(phase(frame, 1, 10)) * (1.0 - smooth(phase(frame, 41, 47)))
    cheek_lift = smooth(phase(frame, 13, 24)) * (1.0 - smooth(phase(frame, 37, 45)))
    wink = smooth(phase(frame, 25, 29)) * (1.0 - smooth(phase(frame, 31, 35)))
    mouth = smooth(phase(frame, 10, 18)) * (1.0 - smooth(phase(frame, 39, 46)))
    return {"face": face, "wink": wink, "cheek_lift": cheek_lift, "mouth": mouth}


def _ink_features(size, state):
    image = canvas(size)
    cheek = state["cheek_lift"]
    y_shift = -2.2 * cheek
    stroke(image, eye_path(size, True, y_shift=y_shift), INK, size * 0.047)
    stroke(image, eye_path(size, False, y_shift=y_shift, wink=state["wink"]), INK, size * 0.047)
    stroke(image, mouth_path(size, smile=state["mouth"], y_shift=-2.4 * cheek), INK, size * 0.052)
    return image


def smile_layers(frame, size):
    state = smile_state(frame, size)
    depth, paper, outline = base_face_layers(size, state["face"], recoil=0.25 * state["cheek_lift"])
    return [
        DepthLayer("blue_depth", depth, 0),
        DepthLayer("paper_face", paper, 10),
        DepthLayer("blue_outline", outline, 20),
        DepthLayer("ink_features", _ink_features(size, state), 30),
        DepthLayer("cheek_lift", draw_cheek_accents(size, state["cheek_lift"]), 40),
    ]


def draw_frame(frame, size):
    if frame <= 0 or frame >= 47:
        return canvas(size)
    return compose_depth(smile_layers(frame, size))


SPEC = FrameMotionSpec("12-smile", draw_frame, duration_frames=48, tags=("batch1", "soft", "tactile"))
