import math

import numpy as np
from PIL import ImageDraw

from frame_core.composite import phase, smooth
from frame_core.depth import DepthLayer, compose_depth
from frame_core.models import FrameMotionSpec
from frame_motions.common import BLUE, PAPER, canvas


def exclamation_state(frame, size):
    fall = phase(frame, 1, 15) ** 1.65
    impact = phase(frame, 14, 22)
    recoil = math.sin(math.pi * impact)
    return {
        "bar_y": size * (0.02 + 0.35*fall - 0.025*recoil),
        "bar": smooth(phase(frame, 1, 7)) * (1-smooth(phase(frame, 33, 41))),
        "dot": smooth(phase(frame, 5, 11)) * (1-smooth(phase(frame, 35, 41))),
        "dot_squash": 1.0 - 0.42*math.sin(math.pi*phase(frame, 13, 23)),
        "recoil": recoil,
    }


def _bar(frame, size):
    state = exclamation_state(frame, size)
    image = canvas(size)
    if state["bar"] <= 0:
        return image
    unit=size/100.0
    cx=50*unit
    top=state["bar_y"]
    height=39*unit*state["bar"]
    half=(7.2-1.3*state["recoil"])*unit
    points=((cx-half,top),(cx+half,top),(cx+4.5*unit,top+height),(cx-4.5*unit,top+height))
    draw=ImageDraw.Draw(image,"RGBA")
    shifted=[(x+2*unit,y+2.3*unit) for x,y in points]
    draw.polygon(shifted,fill=BLUE)
    draw.polygon(points,fill=PAPER)
    return image


def _dot(frame,size):
    state=exclamation_state(frame,size)
    image=canvas(size)
    if state["dot"]<=0:
        return image
    unit=size/100.0
    rx=7*unit*(1.15-state["dot_squash"]*.15)*state["dot"]
    ry=7*unit*state["dot_squash"]*state["dot"]
    cx,cy=50*unit,76*unit+2*unit*(1-state["dot_squash"])
    draw=ImageDraw.Draw(image,"RGBA")
    draw.ellipse((cx-rx+2*unit,cy-ry+2*unit,cx+rx+2*unit,cy+ry+2*unit),fill=BLUE)
    draw.ellipse((cx-rx,cy-ry,cx+rx,cy+ry),fill=PAPER)
    return image


def exclamation_layers(frame,size):
    return [DepthLayer("heavy_bar",_bar(frame,size),10),DepthLayer("catching_dot",_dot(frame,size),20)]


def draw_frame(frame,size):
    if frame<=0 or frame>=41:
        return canvas(size)
    return compose_depth(exclamation_layers(frame,size))


SPEC=FrameMotionSpec("19-exclamation",draw_frame,duration_frames=42,tags=("story","tactile"))
