import math

import numpy as np
from PIL import Image

from frame_core.brush import draw_pressure_stroke, pressure_profile
from frame_core.composite import phase, smooth
from frame_core.depth import DepthLayer, compose_depth
from frame_core.models import FrameMotionSpec
from frame_core.path import cubic_points
from frame_motions.common import BLUE, PAPER, canvas


def check_state(frame):
    reveal=smooth(phase(frame,1,17))
    return {
        "reveal": reveal*(1-smooth(phase(frame,34,41))),
        "shadow_reveal": smooth(phase(frame,3,19))*(1-smooth(phase(frame,31,38))),
        "whip": math.sin(math.pi*phase(frame,17,28)),
    }


def _path(frame,size):
    unit=size/100.0
    whip=check_state(frame)["whip"]
    return np.vstack((
        cubic_points((20*unit,53*unit),(26*unit,56*unit),(32*unit,65*unit),(42*unit,72*unit),18),
        cubic_points((42*unit,72*unit),(54*unit,56*unit),(69*unit,37*unit),(82*unit,(22-4*whip)*unit),31)[1:],
    ))


def _shadow(frame,size):
    state=check_state(frame)
    path=_path(max(0,frame-2),size)+np.array((2.5,3.0))*size/100.0
    image=canvas(size)
    draw_pressure_stroke(
        image, path, BLUE, size*.052,
        pressure_profile(len(path), .28, 1.0, .22), state["shadow_reveal"],
    )
    alpha=np.asarray(image.getchannel("A"),dtype=np.float32)
    image.putalpha(Image.fromarray(np.clip(alpha*.5,0,255).astype(np.uint8),'L'))
    return image


def _outline(frame,size):
    state=check_state(frame)
    image=canvas(size)
    path=_path(frame,size)
    draw_pressure_stroke(
        image, path, BLUE, size*.125,
        pressure_profile(len(path), .3, 1.03, .25), state["reveal"],
    )
    return image


def _paper_face(frame,size):
    state=check_state(frame)
    image=canvas(size)
    path=_path(frame,size)
    draw_pressure_stroke(
        image, path, PAPER, size*.075,
        pressure_profile(len(path), .3, 1.03, .25), state["reveal"],
    )
    return image


def check_layers(frame,size):
    return [
        DepthLayer("lagging_shadow",_shadow(frame,size),0),
        DepthLayer("blue_outline",_outline(frame,size),10),
        DepthLayer("paper_check",_paper_face(frame,size),20),
    ]


def draw_frame(frame,size):
    if frame<=0 or frame>=41:
        return canvas(size)
    return compose_depth(check_layers(frame,size))


SPEC=FrameMotionSpec("20-check",draw_frame,duration_frames=42,tags=("story","tactile"))
