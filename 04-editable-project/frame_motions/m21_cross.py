import math

import numpy as np

from frame_core.composite import phase, smooth
from frame_core.depth import DepthLayer, compose_depth
from frame_core.models import FrameMotionSpec
from frame_core.path import cubic_points
from frame_motions.common import BLUE, canvas
from frame_motions.native_utils import paper_blue_stroke


def cross_state(frame,size):
    arrive=smooth(phase(frame,1,17))
    release=smooth(phase(frame,31,41))
    return {
        "stroke_a": smooth(phase(frame,1,13))*(1-release),
        "stroke_b": smooth(phase(frame,5,17))*(1-release),
        "distance": size*.27*(1-arrive+release),
        "impact": math.sin(math.pi*phase(frame,16,25)),
    }


def _strokes(frame,size):
    state=cross_state(frame,size)
    unit=size/100.0
    distance=state["distance"]
    a=cubic_points((27*unit-distance,27*unit),(39*unit-distance*.35,38*unit),(61*unit+distance*.35,62*unit),(73*unit+distance,73*unit),34)
    b=cubic_points((73*unit+distance,27*unit),(61*unit+distance*.35,39*unit),(39*unit-distance*.35,61*unit),(27*unit-distance,73*unit),34)
    return paper_blue_stroke(a,size,size*.052,state["stroke_a"]),paper_blue_stroke(b,size,size*.052,state["stroke_b"])


def _impact(frame,size):
    state=cross_state(frame,size)
    image=canvas(size)
    if state["impact"]<=0:return image
    unit=size/100.0
    for angle in (-80,-10,70,160):
        rad=math.radians(angle)
        start=np.array((50,50))*unit+np.array((math.cos(rad),math.sin(rad)))*8*unit
        end=np.array((50,50))*unit+np.array((math.cos(rad),math.sin(rad)))*(8+9*state["impact"])*unit
        ray=cubic_points(start,start,end,end,9)
        image.alpha_composite(paper_blue_stroke(ray,size,size*.018,state["impact"],offset=(0,0)))
    return image


def cross_layers(frame,size):
    a,b=_strokes(frame,size)
    return [DepthLayer("stroke_a",a,10),DepthLayer("stroke_b",b,20),DepthLayer("collision_sparks",_impact(frame,size),30)]


def draw_frame(frame,size):
    if frame<=0 or frame>=41:return canvas(size)
    return compose_depth(cross_layers(frame,size))


SPEC=FrameMotionSpec("21-cross",draw_frame,duration_frames=42,tags=("story","tactile"))
