import math

import numpy as np
from PIL import Image, ImageDraw

from frame_core.brush import draw_pressure_stroke, jitter_points, pressure_profile
from frame_core.composite import phase, smooth
from frame_core.deform import deform_points
from frame_core.depth import DepthLayer, compose_depth, glint_window
from frame_core.models import FrameMotionSpec
from frame_core.path import cubic_points, reveal_points
from frame_motions.common import BLUE, PAPER, TAUPE, canvas


def bulb_state(frame, size):
    del size
    exit_progress = smooth(phase(frame, 51, 59))
    return {
        "glass": smooth(phase(frame, 3, 18)) * (1.0 - exit_progress),
        "spark": smooth(phase(frame, 20, 32)) * (1.0 - smooth(phase(frame, 47, 55))),
        "light": smooth(phase(frame, 27, 42)) * (1.0 - smooth(phase(frame, 48, 57))),
        "glass_flex": math.sin(math.pi * phase(frame, 31, 45)),
        "base_click": smooth(phase(frame, 10, 23)) * (1.0 - exit_progress),
    }


def _join(parts):
    return np.vstack([part if index == 0 else part[1:] for index, part in enumerate(parts)])


def glass_path(size):
    s = size / 100
    path = _join([
        cubic_points((40*s,68*s),(39*s,59*s),(24*s,55*s),(22*s,38*s),24),
        cubic_points((22*s,38*s),(19*s,18*s),(34*s,8*s),(50*s,8*s),24),
        cubic_points((50*s,8*s),(69*s,8*s),(82*s,23*s),(77*s,43*s),24),
        cubic_points((77*s,43*s),(74*s,56*s),(61*s,59*s),(60*s,68*s),22),
    ])
    return jitter_points(path, seed=2401, amount=size / 750)


def bulb_geometry(frame, size):
    path = glass_path(size)
    unit = size / 100.0
    bloom = bulb_state(frame, size)["glass_flex"]
    return deform_points(
        path,
        controls=(
            (31, (-1.8 * unit * bloom, -1.0 * unit * bloom), 12),
            (62, (2.2 * unit * bloom, -1.2 * unit * bloom), 12),
        ),
        anchors=(0, len(path)-1),
    )


def star_path(size):
    return np.array([
        (50,24),(53,39),(65,45),(54,49),(50,64),(46,50),(35,45),(46,40),(50,24)
    ], dtype=float) * size / 100


def _stroke(points, progress, size, color, width, opacity=1.0, pressure=(0.38, 1.08, 0.30)):
    layer = canvas(size)
    visible = reveal_points(points, progress)
    if len(visible) >= 2:
        draw_pressure_stroke(
            layer, visible, color, width,
            pressure_profile(len(visible), *pressure), opacity,
        )
    return layer


def _radial_fill(path, frame, size):
    build = bulb_state(frame, size)["light"]
    retract = smooth(phase(frame, 50, 58))
    result = canvas(size)
    if build <= 0 or retract >= 1:
        return result
    polygon = Image.new("L", (size, size), 0)
    ImageDraw.Draw(polygon).polygon([tuple(point) for point in path], fill=255)
    yy, xx = np.mgrid[0:size, 0:size]
    cx, cy = size * 0.5, size * 0.45
    distance = np.sqrt((xx-cx)**2 + (yy-cy)**2)
    radius = size * (0.06 + 0.48 * build) * (1.0 - 0.72 * retract)
    alpha = np.asarray(polygon).copy()
    alpha[distance > radius] = 0
    fill = Image.new("RGBA", (size, size), PAPER)
    fill.putalpha(Image.fromarray(alpha, "L"))
    result.alpha_composite(fill)
    return result


def _base_layer(frame, size):
    result = canvas(size)
    exit_progress = smooth(phase(frame, 54, 59))
    lines = (
        np.array([(38,72),(62,72)], dtype=float) * size / 100,
        np.array([(40,79),(60,79)], dtype=float) * size / 100,
        np.array([(44,86),(56,86)], dtype=float) * size / 100,
    )
    for index, line in enumerate(lines):
        build = bulb_state(frame, size)["base_click"] * smooth(
            phase(frame, 8 + index * 2, 16 + index * 2)
        )
        local_exit = np.clip(exit_progress * 1.25 - index * 0.12, 0.0, 1.0)
        visible = reveal_points(line, build * (1.0 - local_exit))
        if len(visible) >= 2:
            draw_pressure_stroke(
                result, visible, BLUE, size * 0.055,
                pressure_profile(len(visible), 0.35, 1.0, 0.28),
            )
    return result


def bulb_layers(frame, size):
    state = bulb_state(frame, size)
    glass = bulb_geometry(frame, size)
    glass_closed = np.vstack((glass, glass[0]))
    lagged = bulb_geometry(max(0, frame - 2), size)
    lagged_closed = np.vstack((lagged, lagged[0]))

    bloom = state["glass_flex"]
    shadow_exit = 1.0 - smooth(phase(frame, 49, 56))
    shadow_offset = np.array(((2.0 + 1.4*bloom) * size / 100,
                              (2.8 - 0.5*bloom) * size / 100))
    shadow = _stroke(
        lagged_closed + shadow_offset,
        state["glass"] * shadow_exit,
        size, BLUE, size * (0.066 + 0.026*bloom), 0.58,
    )

    fill = _radial_fill(glass, frame, size)
    glass_exit = 1.0 - smooth(phase(frame, 51, 58))
    outline = _stroke(
        glass_closed,
        state["glass"] * glass_exit,
        size, BLUE, size * 0.060,
    )

    star_exit = 1.0 - smooth(phase(frame, 47, 54))
    star = _stroke(
        star_path(size),
        state["spark"] * star_exit,
        size, TAUPE, size * 0.038,
        pressure=(0.28, 1.0, 0.22),
    )

    glint = canvas(size)
    strength = glint_window(frame, 34, 44)
    if strength > 0:
        streak = cubic_points(
            (31*size/100,35*size/100), (28*size/100,27*size/100),
            (34*size/100,19*size/100), (41*size/100,17*size/100), 12,
        )
        draw_pressure_stroke(
            glint, streak, PAPER, size * 0.022,
            pressure_profile(len(streak), 0.18, 0.9, 0.12), strength,
        )

    return [
        DepthLayer("glass_shadow", shadow, 0),
        DepthLayer("base", _base_layer(frame, size), 5),
        DepthLayer("light", fill, 10),
        DepthLayer("glass", outline, 20),
        DepthLayer("star", star, 30),
        DepthLayer("glint", glint, 40),
    ]


def draw_frame(frame, size):
    if frame >= 59:
        return canvas(size)
    return compose_depth(bulb_layers(frame, size))


SPEC = FrameMotionSpec(
    "10-bulb-spark",
    draw_frame,
    duration_frames=60,
    tags=("pilot", "story", "tactile"),
)
