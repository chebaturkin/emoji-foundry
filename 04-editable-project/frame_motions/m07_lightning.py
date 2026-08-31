import math

import numpy as np
from PIL import Image, ImageDraw

from frame_core.brush import draw_pressure_stroke, jitter_points, pressure_profile
from frame_core.composite import phase, smooth
from frame_core.deform import deform_points
from frame_core.depth import DepthLayer, compose_depth, glint_window
from frame_core.models import FrameMotionSpec
from frame_core.path import reveal_points
from frame_motions.common import BLUE, PAPER, canvas


ECHO_BLUE = (46, 58, 77, 164)


def lightning_shape(size):
    points = np.array([
        (58, 7), (28, 48), (46, 46), (32, 91),
        (73, 39), (55, 41), (68, 7),
    ], dtype=float) * size / 100
    return jitter_points(points, seed=401, amount=size / 700)


def lightning_geometry(frame, size):
    points = lightning_shape(size)
    unit = size / 100.0
    bend = math.sin(math.pi * smooth(phase(frame, 26, 36)))
    return deform_points(
        points,
        controls=((3, (-4.8 * unit * bend, 1.5 * unit * bend), 0.72),),
        anchors=(0, 5, 6),
    )


def _stroke(points, progress, size, color, width, opacity=1.0):
    layer = canvas(size)
    visible = reveal_points(points, progress)
    if len(visible) >= 2:
        draw_pressure_stroke(
            layer, visible, color, width,
            pressure_profile(len(visible), 0.38, 1.12, 0.28), opacity,
        )
    return layer


def _fill(shape, frame, size):
    build = smooth(phase(frame, 14, 29))
    retract = smooth(phase(frame, 51, 59))
    result = canvas(size)
    if build <= 0 or retract >= 1:
        return result
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).polygon([tuple(point) for point in shape], fill=255)
    alpha = np.asarray(mask).copy()
    yy = np.arange(size)[:, None]
    build_edge = size * (0.05 + 0.92 * build)
    retract_edge = size * (0.97 - 0.92 * retract)
    alpha[(yy > min(build_edge, retract_edge)).repeat(size, axis=1)] = 0
    fill = Image.new("RGBA", (size, size), PAPER)
    fill.putalpha(Image.fromarray(alpha, "L"))
    result.alpha_composite(fill)
    return result


def lightning_layers(frame, size):
    shape = lightning_geometry(frame, size)
    closed = np.vstack((shape, shape[0]))
    outline_exit = 1.0 - smooth(phase(frame, 52, 59))
    shadow_exit = 1.0 - smooth(phase(frame, 49, 57))

    kick = math.sin(math.pi * smooth(phase(frame, 26, 36)))
    echo_offset = np.array(((2.5 + 2.0 * kick) * size / 100,
                            (1.4 - 0.5 * kick) * size / 100))
    shadow = _stroke(
        closed + echo_offset,
        smooth(phase(frame, 0, 20)) * shadow_exit,
        size, ECHO_BLUE, size * 0.075, 0.92,
    )
    fill = _fill(shape, frame, size)
    outline = _stroke(
        closed,
        smooth(phase(frame, 2, 20)) * outline_exit,
        size, BLUE, size * 0.058,
    )

    charge_points = np.array([(61,13),(40,45),(53,43),(41,75)], dtype=float) * size / 100
    charge_exit = 1.0 - smooth(phase(frame, 49, 55))
    charge = _stroke(
        charge_points,
        smooth(phase(frame, 10, 24)) * charge_exit,
        size, PAPER, size * 0.025,
    )

    glint = canvas(size)
    glint_strength = glint_window(frame, 29, 37)
    if glint_strength > 0:
        streak = np.array([(48,32),(54,25),(58,20)], dtype=float) * size / 100
        draw_pressure_stroke(
            glint, streak, PAPER, size * 0.018,
            np.array((0.2, 1.0, 0.15)), glint_strength,
        )

    return [
        DepthLayer("echo", shadow, 0),
        DepthLayer("fill", fill, 10),
        DepthLayer("outline", outline, 20),
        DepthLayer("charge", charge, 30),
        DepthLayer("glint", glint, 35),
    ]


def draw_frame(frame, size):
    if frame >= 59:
        return canvas(size)
    return compose_depth(lightning_layers(frame, size))


SPEC = FrameMotionSpec(
    "07-lightning",
    draw_frame,
    duration_frames=60,
    tags=("pilot", "impact", "tactile"),
)
