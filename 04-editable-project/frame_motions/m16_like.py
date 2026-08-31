from frame_core.composite import phase, smooth
from frame_core.depth import DepthLayer, compose_depth
from frame_core.models import FrameMotionSpec
from frame_motions.common import canvas
from frame_motions.hand_geometry import hand_pose, render_hand_layers, transformed_pose


def like_state(frame, size=100):
    del size
    wrist_turn = smooth(phase(frame, 3, 18)) * (1.0 - 0.22 * smooth(phase(frame, 31, 47)))
    thumb_extension = smooth(phase(frame, 13, 29)) * (1.0 - smooth(phase(frame, 35, 47)))
    palm_entry = smooth(phase(frame, 1, 15)) * (1.0 - smooth(phase(frame, 37, 47)))
    return {"palm_entry": palm_entry, "wrist_turn": wrist_turn, "thumb_extension": thumb_extension}


def hand_layers(frame, size):
    state = like_state(frame, size)
    pose = hand_pose("up", state["thumb_extension"], size)
    dy = size * (0.28 * (1.0 - state["palm_entry"]))
    pose = transformed_pose(pose, dy=dy, rotation=-4.0 * state["wrist_turn"])
    depth, paper, outline, creases = render_hand_layers(pose, size)
    return [DepthLayer("blue_depth", depth, 0), DepthLayer("paper_hand", paper, 10), DepthLayer("blue_outline", outline, 20), DepthLayer("ink_creases", creases, 30)]


def draw_frame(frame, size):
    if frame <= 0 or frame >= 47:
        return canvas(size)
    return compose_depth(hand_layers(frame, size))


SPEC = FrameMotionSpec("16-like", draw_frame, duration_frames=48, tags=("soft", "tactile"))
