import math

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from frame_core.brush import draw_pressure_stroke, jitter_points, pressure_profile
from frame_core.composite import phase, smooth
from frame_core.depth import DepthLayer, compose_depth, glint_window
from frame_core.models import FrameMotionSpec
from frame_core.path import cubic_points, reveal_points
from frame_motions.common import BLUE, PAPER, TAUPE, canvas


LOBE_CONFIG = {
    "back_left": (31, 38, 19, 17, 2201, TAUPE),
    "back_right": (68, 39, 20, 17, 2203, BLUE),
    "top": (49, 27, 18, 21, 2202, PAPER),
    "front_left": (35, 62, 21, 18, 2205, PAPER),
    "front_right": (61, 61, 19, 19, 2204, PAPER),
    "core": (49, 49, 18, 17, 2299, PAPER),
}


def lobe_timeline():
    return {
        "back_left": (1, 12, 52, 58),
        "back_right": (2, 13, 51, 58),
        "top": (5, 17, 50, 57),
        "front_left": (9, 20, 46, 54),
        "front_right": (10, 21, 47, 54),
        "core": (14, 24, 48, 55),
    }


def lobe_path(cx, cy, rx, ry, seed, size):
    rng = np.random.default_rng(seed)
    points = []
    for index in range(65):
        angle = math.tau * index / 64
        wobble = 1.0 + 0.07 * math.sin(angle * 3 + seed) + rng.normal(0, 0.008)
        points.append(((cx + math.cos(angle)*rx*wobble)*size/100,
                       (cy + math.sin(angle)*ry*wobble)*size/100))
    return jitter_points(np.asarray(points), seed=seed, amount=size / 1200)


def _lobe_geometry(name, frame, size, lag=0):
    cx, cy, rx, ry, seed, _ = LOBE_CONFIG[name]
    start, built, exit_start, exit_end = lobe_timeline()[name]
    local_frame = max(0, frame-lag)
    enter = smooth(phase(local_frame, start, built))
    leave = smooth(phase(frame, exit_start, exit_end))
    if enter <= 0 or leave >= 1:
        return None
    spring = math.sin(math.pi * phase(local_frame, start, built+5))
    scale = (0.12 + 0.93*enter + 0.10*spring) * (1.0-leave)
    path = lobe_path(cx, cy, rx, ry, seed, size)
    center = np.array((cx*size/100, cy*size/100))
    outward = (center - np.array((49*size/100, 49*size/100))) * (0.09*spring)
    return center + (path-center)*scale + outward


def _polygon_layer(path, color, size):
    layer = canvas(size)
    if path is not None:
        ImageDraw.Draw(layer, "RGBA").polygon([tuple(point) for point in path], fill=color)
    return layer


def explosion_layers(frame, size):
    layers = []
    union = Image.new("L", (size, size), 0)

    for z, name in enumerate(("back_left", "back_right", "top", "front_left", "front_right", "core"), 10):
        path = _lobe_geometry(name, frame, size)
        if path is None:
            continue
        _, _, _, _, _, color = LOBE_CONFIG[name]
        layers.append(DepthLayer(name, _polygon_layer(path, color, size), z))
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).polygon([tuple(point) for point in path], fill=255)
        union = ImageChops.lighter(union, mask)

    shadow_union = Image.new("L", (size, size), 0)
    for name in LOBE_CONFIG:
        lagged = _lobe_geometry(name, frame, size, lag=2)
        if lagged is None:
            continue
        lagged = lagged + np.array((2.4, 3.0))*size/100
        ImageDraw.Draw(shadow_union).polygon([tuple(point) for point in lagged], fill=135)
    shadow = Image.new("RGBA", (size, size), BLUE)
    shadow.putalpha(shadow_union)
    layers.append(DepthLayer("shadow", shadow, 0))

    if union.getbbox() is not None:
        border_width = max(3, round(size*.055))
        if border_width % 2 == 0:
            border_width += 1
        expanded = union.filter(ImageFilter.MaxFilter(border_width))
        border = ImageChops.subtract(expanded, union)
        outline = Image.new("RGBA", (size, size), BLUE)
        outline.putalpha(border)
        layers.append(DepthLayer("outer_ink", outline, 30))

    rays = canvas(size)
    ray_enter = smooth(phase(frame, 19, 31))
    ray_exit = 1.0 - smooth(phase(frame, 45, 52))
    for a, b in (((16,25),(9,18)),((78,24),(88,17)),((82,61),(92,64)),((19,75),(11,84))):
        ray = np.array((a,b), dtype=float)*size/100
        visible = reveal_points(ray, ray_enter*ray_exit)
        if len(visible) >= 2:
            draw_pressure_stroke(
                rays, visible, BLUE, size*.027,
                pressure_profile(len(visible), .25, 1.15, .18),
            )
    layers.append(DepthLayer("rays", rays, 35))

    glint = canvas(size)
    strength = glint_window(frame, 29, 40)
    if strength > 0:
        streak = cubic_points(
            (37*size/100,48*size/100), (34*size/100,42*size/100),
            (36*size/100,35*size/100), (41*size/100,32*size/100), 12,
        )
        draw_pressure_stroke(
            glint, streak, PAPER, size*.020,
            pressure_profile(len(streak), .2, .9, .12), strength,
        )
    layers.append(DepthLayer("glint", glint, 40))
    return layers


def draw_frame(frame, size):
    if frame <= 0 or frame >= 59:
        return canvas(size)
    return compose_depth(explosion_layers(frame, size))


SPEC = FrameMotionSpec(
    "25-explosion-cloud",
    draw_frame,
    duration_frames=60,
    tags=("pilot", "impact", "tactile"),
)
