import math

import numpy as np
from PIL import ImageDraw

from frame_core.brush import draw_pressure_stroke, jitter_points, pressure_profile
from frame_core.composite import phase, smooth
from frame_core.deform import deform_points
from frame_core.depth import DepthLayer, compose_depth, glint_window
from frame_core.models import FrameMotionSpec
from frame_core.path import cubic_points, morph_points, reveal_points
from frame_motions.common import BLUE, INK, PAPER, TAUPE, canvas


def _circle(size):
    s = size / 100
    points = []
    for index in range(97):
        angle = math.tau * index / 96 - math.pi / 2
        points.append((50*s + math.cos(angle)*38*s, 50*s + math.sin(angle)*38*s))
    return jitter_points(np.asarray(points), seed=801, amount=size / 900)


def face_geometry(frame, size):
    opening = smooth(phase(frame, 20, 31))
    recovery = smooth(phase(frame, 38, 47))
    cheek_lift = (4.8 * opening - 1.4 * recovery) * size / 100
    tongue_lag = 1.6 * smooth(phase(frame, 26, 37)) * size / 100
    circle = deform_points(
        _circle(size),
        controls=(
            (31, (1.4*opening*size/100, cheek_lift), 11),
            (65, (-1.4*opening*size/100, cheek_lift), 11),
            (48, (0, 1.5*opening*size/100), 9),
        ),
        anchors=(0, 96),
    )
    return {
        "circle": circle,
        "cheek_y": 50 * size / 100 + cheek_lift,
        "tongue_y": 70 * size / 100 + tongue_lag,
        "opening": opening,
    }


def _eye(left, size, cheek_lift=0.0):
    s = size / 100
    x = 35 if left else 65
    return cubic_points(
        ((x-7)*s, (39+cheek_lift)*s), ((x-4)*s, (29+cheek_lift*.35)*s),
        ((x+4)*s, (29+cheek_lift*.35)*s), ((x+7)*s, (39+cheek_lift)*s), 24,
    )


def _mouth_shapes(size):
    s = size / 100
    smile = np.array([(30,56),(38,65),(50,68),(62,65),(70,56),(30,56)], dtype=float) * s
    opened = np.array([
        (27,54),(34,72),(49,80),(66,74),(74,55),(66,51),(50,50),(34,51),(27,54)
    ], dtype=float) * s
    return smile, opened


def _scale(points, center, amount):
    return center + (np.asarray(points) - center) * amount


def _pressure_stroke(layer, points, color, width, opacity=1.0):
    if len(points) < 2:
        return
    draw_pressure_stroke(
        layer, points, color, width,
        pressure_profile(len(points), 0.42, 1.05, 0.34), opacity,
    )


def laugh_layers(frame, size):
    geometry = face_geometry(frame, size)
    center = np.array((size/2, size/2))
    enter = smooth(phase(frame, 2, 14))
    face_exit = 1.0 - smooth(phase(frame, 52, 59))
    body_scale = enter * face_exit
    body = _scale(geometry["circle"], center, body_scale)

    shadow = canvas(size)
    lagged = face_geometry(max(0, frame-2), size)["circle"]
    shadow_body = _scale(lagged, center, body_scale) + np.array((2.2, 3.0))*size/100
    shadow_visible = reveal_points(shadow_body, smooth(phase(frame, 0, 15)))
    _pressure_stroke(shadow, shadow_visible, BLUE, size*.078, .58)

    fill = canvas(size)
    if body_scale > 0:
        ImageDraw.Draw(fill, "RGBA").polygon([tuple(point) for point in body[:-1]], fill=PAPER)

    outline = canvas(size)
    outline_visible = reveal_points(body, smooth(phase(frame, 1, 15)))
    _pressure_stroke(outline, outline_visible, BLUE, size*.058)

    eyes = canvas(size)
    eyes_exit = 1.0 - smooth(phase(frame, 53, 57))
    cheek_units = (geometry["cheek_y"] / (size/100) - 50) * .28
    for left in (True, False):
        eye = _eye(left, size, cheek_units)
        visible = reveal_points(eye, smooth(phase(frame, 8, 17))*eyes_exit)
        _pressure_stroke(eyes, visible, INK, size*.050)

    mouth_layer = canvas(size)
    mouth_exit = 1.0 - smooth(phase(frame, 50, 56))
    if frame >= 12 and mouth_exit > 0:
        smile, opened = _mouth_shapes(size)
        mouth = morph_points(smile, opened, geometry["opening"], count=80)
        mouth = _scale(mouth, np.array((size*.5, size*.62)), mouth_exit)
        if geometry["opening"] > .08:
            ImageDraw.Draw(mouth_layer, "RGBA").polygon(
                [tuple(point) for point in mouth[:-1]], fill=INK
            )
        visible = reveal_points(mouth, smooth(phase(frame, 12, 16))*mouth_exit)
        _pressure_stroke(mouth_layer, visible, INK, size*.050)

    tongue = canvas(size)
    tongue_enter = smooth(phase(frame, 24, 35))
    tongue_exit = 1.0 - smooth(phase(frame, 47, 53))
    tongue_scale = tongue_enter * tongue_exit
    if tongue_scale > 0:
        bounce = math.sin(math.pi * phase(frame, 26, 42)) * 2.5
        lag = geometry["tongue_y"] / (size/100) - 70
        path = np.array([
            (38,69+bounce+lag),(50,65-bounce+lag),(63,70+bounce+lag),
            (56,77+lag),(44,77+lag),(38,69+bounce+lag),
        ], dtype=float) * size/100
        path = _scale(path, np.array((size*.5, size*.71)), tongue_scale)
        ImageDraw.Draw(tongue, "RGBA").polygon([tuple(point) for point in path], fill=TAUPE)
        _pressure_stroke(tongue, path, INK, size*.025)

    glint = canvas(size)
    strength = glint_window(frame, 31, 42)
    if strength > 0:
        streak = cubic_points(
            (24*size/100,45*size/100), (20*size/100,35*size/100),
            (24*size/100,25*size/100), (31*size/100,21*size/100), 14,
        )
        _pressure_stroke(glint, streak, PAPER, size*.020, strength)

    return [
        DepthLayer("shadow", shadow, 0),
        DepthLayer("face", fill, 10),
        DepthLayer("outline", outline, 20),
        DepthLayer("mouth", mouth_layer, 30),
        DepthLayer("tongue", tongue, 35),
        DepthLayer("eyes", eyes, 40),
        DepthLayer("glint", glint, 50),
    ]


def draw_frame(frame, size):
    if frame >= 59:
        return canvas(size)
    return compose_depth(laugh_layers(frame, size))


SPEC = FrameMotionSpec(
    "13-laugh",
    draw_frame,
    duration_frames=60,
    tags=("pilot", "soft", "tactile"),
)
