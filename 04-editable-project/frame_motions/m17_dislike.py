from frame_core.composite import phase, smooth
from frame_core.depth import DepthLayer, compose_depth
from frame_core.models import FrameMotionSpec
from frame_motions.common import canvas
from frame_motions.hand_geometry import hand_pose, render_hand_layers, transformed_pose


def dislike_state(frame, size=100):
    del size
    palm_entry = smooth(phase(frame, 1, 17)) * (1.0 - smooth(phase(frame, 38, 47)))
    thumb_drop = smooth(phase(frame, 10, 27)) * (1.0 - smooth(phase(frame, 36, 47)))
    cuff_follow = smooth(phase(frame, 13, 31)) * (1.0 - smooth(phase(frame, 38, 47)))
    return {"palm_entry": palm_entry, "thumb_drop": thumb_drop, "cuff_follow": cuff_follow}


def hand_layers(frame, size):
    state = dislike_state(frame, size)
    pose = hand_pose("down", state["thumb_drop"], size)
    dy = size * (0.30 * (1.0 - state["palm_entry"]) + 0.06 * state["thumb_drop"])
    pose = transformed_pose(pose, dy=dy, rotation=6.0 * state["thumb_drop"])
    depth, paper, outline, creases = render_hand_layers(pose, size)
    return [DepthLayer("blue_depth", depth, 0), DepthLayer("paper_hand", paper, 10), DepthLayer("blue_outline", outline, 20), DepthLayer("ink_creases", creases, 30)]


def draw_frame(frame, size):
    if frame <= 0 or frame >= 47:
        return canvas(size)
    return compose_depth(hand_layers(frame, size))


SPEC = FrameMotionSpec("17-dislike", draw_frame, duration_frames=48, tags=("soft", "tactile"))
