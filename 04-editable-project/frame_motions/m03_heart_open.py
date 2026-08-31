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


SHADOW_BLUE = (46, 58, 77, 176)


def heart_path(size):
    s = size / 100.0
    parts = [
        cubic_points((62*s,88*s),(48*s,84*s),(15*s,58*s),(16*s,32*s),32),
        cubic_points((16*s,32*s),(16*s,14*s),(39*s,11*s),(49*s,31*s),28),
        cubic_points((49*s,31*s),(61*s,11*s),(85*s,16*s),(84*s,37*s),30),
        cubic_points((84*s,37*s),(83*s,56*s),(67*s,68*s),(59*s,77*s),28),
    ]
    joined = np.vstack([part if index == 0 else part[1:] for index, part in enumerate(parts)])
    return jitter_points(joined, seed=1901, amount=size / 600)


def highlight_path(size):
    s = size / 100.0
    return cubic_points((28*s,42*s),(23*s,32*s),(30*s,23*s),(41*s,22*s),24)


def heart_geometry(frame, size):
    """Locally squash and release the lobes while the open tail stays anchored."""
    points = heart_path(size)
    unit = size / 100.0
    anticipation = math.sin(math.pi * smooth(phase(frame, 30, 36)))
    release = math.sin(math.pi * smooth(phase(frame, 36, 45)))
    controls = [
        (48, (1.8 * unit * anticipation - 2.4 * unit * release,
              2.8 * unit * anticipation - 3.8 * unit * release), 13),
        (70, (-1.6 * unit * anticipation + 2.8 * unit * release,
              2.4 * unit * anticipation - 4.6 * unit * release), 14),
        (94, (-0.7 * unit * release, 1.3 * unit * release), 10),
    ]
    return deform_points(points, controls, anchors=(0, len(points) - 1))


def _pressure_for(points, start=0.46, peak=1.0, end=0.34):
    return pressure_profile(len(points), start=start, peak=peak, end=end)


def _stroke_layer(points, progress, size, color, width, opacity=1.0):
    layer = canvas(size)
    revealed = reveal_points(points, progress)
    if len(revealed) >= 2:
        draw_pressure_stroke(
            layer, revealed, color, width, _pressure_for(revealed), opacity
        )
    return layer


def _fill_layer(path, frame, size):
    progress = smooth(phase(frame, 22, 38))
    result = canvas(size)
    if progress <= 0:
        return result
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).polygon([tuple(point) for point in path], fill=255)
    polygon_alpha = np.asarray(mask, dtype=np.float32)
    yy = np.arange(size, dtype=np.float32)[:, None]
    xx = np.arange(size, dtype=np.float32)
    base_top = size * (0.90 - 0.72 * progress)
    front = base_top + np.sin(xx / size * math.tau * 1.7 + progress * 2.1) * size * 0.020
    front += np.sin(xx / size * math.tau * 4.3 + 0.8) * size * 0.009
    vertical = np.clip((yy - front[None, :]) / max(1.0, size * 0.025), 0.0, 1.0)
    alpha = np.clip(polygon_alpha * vertical, 0, 255).astype(np.uint8)
    fill = Image.new("RGBA", (size, size), PAPER)
    fill.putalpha(Image.fromarray(alpha, "L"))
    result.alpha_composite(fill)
    return result


def _shadow_path(path, frame, size):
    pressure = math.sin(math.pi * smooth(phase(frame, 30, 45)))
    offset = np.array(((1.8 + 1.5 * pressure) * size / 100,
                       (2.8 - 0.8 * pressure) * size / 100))
    return path + offset


def heart_layers(frame, size):
    path = heart_geometry(frame, size)
    shadow_progress = smooth(phase(frame, 0, 24))
    outline_progress = smooth(phase(frame, 3, 28))
    shadow = _stroke_layer(
        _shadow_path(path, frame, size), shadow_progress, size,
        SHADOW_BLUE, size * 0.096, 0.88,
    )
    fill = _fill_layer(path, frame, size)
    outline = _stroke_layer(path, outline_progress, size, BLUE, size * 0.078)

    accent = highlight_path(size)
    accent_progress = smooth(phase(frame, 13, 31))
    highlight = _stroke_layer(accent, accent_progress, size, TAUPE, size * 0.042)

    glint = canvas(size)
    glint_strength = glint_window(frame, 35, 44)
    if glint_strength > 0:
        unit = size / 100.0
        streak = np.array(((57*unit, 22*unit), (62*unit, 18*unit), (66*unit, 17*unit)))
        draw_pressure_stroke(
            glint, streak, PAPER, size * 0.025,
            np.array((0.35, 1.0, 0.22)), glint_strength,
        )

    return [
        DepthLayer("shadow", shadow, 0),
        DepthLayer("fill", fill, 10),
        DepthLayer("outline", outline, 20),
        DepthLayer("highlight", highlight, 30),
        DepthLayer("glint", glint, 40),
    ]


def _spatial_retract(image, frame, size):
    """Erase the settled heart with a moving edge while preserving solid ink."""
    if frame < 50:
        return image
    if frame >= 59:
        return canvas(size)
    progress = smooth(phase(frame, 50, 59))
    yy, xx = np.mgrid[0:size, 0:size]
    score = (xx + 0.82 * yy) / size
    threshold = progress * 1.58
    keep = (score >= threshold).astype(np.uint8) * 255
    source_alpha = np.asarray(image.getchannel("A"), dtype=np.uint16)
    clipped = (source_alpha * keep.astype(np.uint16) // 255).astype(np.uint8)
    result = image.copy()
    result.putalpha(Image.fromarray(clipped, "L"))
    pixels = np.asarray(result).copy()
    pixels[pixels[:, :, 3] == 0, :3] = 0
    return Image.fromarray(pixels, "RGBA")


def draw_frame(frame, size):
    return _spatial_retract(compose_depth(heart_layers(frame, size)), frame, size)


SPEC = FrameMotionSpec(
    "03-heart-open",
    draw_frame,
    duration_frames=60,
    tags=("pilot", "soft", "tactile"),
)
