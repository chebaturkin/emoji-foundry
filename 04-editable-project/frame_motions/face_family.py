"""Shared tactile primitives for the redesigned 07/09/10 face family."""

import math

import numpy as np
from PIL import ImageDraw

from frame_core.brush import draw_pressure_stroke, pressure_profile
from frame_core.path import cubic_points
from frame_motions.common import BLUE, INK, PAPER, TAUPE, canvas


def _ellipse_box(size, cx=50.0, cy=50.0, rx=36.0, ry=36.0):
    unit = size / 100.0
    return (
        (cx - rx) * unit,
        (cy - ry) * unit,
        (cx + rx) * unit,
        (cy + ry) * unit,
    )


def base_face_layers(size, progress, *, drop=0.0, recoil=0.0):
    """Return blue depth, paper fill and tactile blue contour images."""
    if progress <= 0.0:
        blank = canvas(size)
        return blank.copy(), blank.copy(), blank.copy()
    # Keep the silhouette inside the 8 px Telegram safe area at all times.
    scale = 0.90 + 0.10 * min(1.0, progress)
    cy = 50.0 + drop + recoil * 0.55
    rx = 36.0 * scale
    ry = 35.0 * scale * (1.0 + 0.025 * recoil)
    box = _ellipse_box(size, cy=cy, rx=rx, ry=ry)
    offset = (1.8 * size / 100.0, 2.3 * size / 100.0)

    depth = canvas(size)
    ImageDraw.Draw(depth, "RGBA").ellipse(
        tuple(box[index] + (offset[0] if index % 2 == 0 else offset[1]) for index in range(4)),
        fill=BLUE,
    )
    paper = canvas(size)
    ImageDraw.Draw(paper, "RGBA").ellipse(box, fill=PAPER)
    outline = canvas(size)
    ImageDraw.Draw(outline, "RGBA").ellipse(
        box, outline=BLUE, width=max(2, round(size * 0.052))
    )
    return depth, paper, outline


def eye_path(size, left=True, *, openness=1.0, y_shift=0.0, wink=0.0):
    unit = size / 100.0
    x = 35.0 if left else 65.0
    openness = max(0.12, openness)
    half_h = 7.0 * openness
    if wink > 0.5:
        half_h *= 0.18
    return cubic_points(
        ((x - 7.0) * unit, (40.0 + y_shift) * unit),
        ((x - 4.0) * unit, (33.0 - half_h + y_shift) * unit),
        ((x + 4.0) * unit, (33.0 - half_h + y_shift) * unit),
        ((x + 7.0) * unit, (40.0 + y_shift) * unit),
        24,
    )


def mouth_path(size, *, smile=0.0, sad=0.0, open_amount=0.0, y_shift=0.0):
    unit = size / 100.0
    x0, x1 = 31.0 * unit, 69.0 * unit
    y = (61.0 + y_shift) * unit
    curve = 8.5 * smile - 8.5 * sad
    if open_amount > 0.02:
        rx = (8.0 + 6.0 * open_amount) * unit
        ry = (8.0 + 11.0 * open_amount) * unit
        cx = 50.0 * unit
        # Smooth closed contour: many points avoid the hard corners of a box
        # while preserving a hand-drawn, slightly asymmetric oval.
        angles = np.linspace(0.0, math.tau, 41)
        organic = 1.0 + 0.035 * np.sin(angles * 3.0 + 0.4)
        return np.column_stack((cx + np.cos(angles) * rx * organic,
                                y + np.sin(angles) * ry * organic))
    return cubic_points(
        (x0, y), (40.0 * unit, (61.0 + curve) * unit),
        (60.0 * unit, (61.0 + curve) * unit), (x1, y), 32,
    )


def stroke(image, points, color, width, *, opacity=1.0):
    if len(points) < 2:
        return
    draw_pressure_stroke(
        image,
        np.asarray(points, dtype=float),
        color,
        width,
        pressure_profile(len(points), 0.35, 1.08, 0.28),
        opacity,
    )


def draw_cheek_accents(size, lift, *, color=TAUPE):
    image = canvas(size)
    if lift <= 0.0:
        return image
    draw = ImageDraw.Draw(image, "RGBA")
    unit = size / 100.0
    alpha = round(255 * min(1.0, lift))
    radius = 2.0 * unit
    for cx in (25.0, 75.0):
        cy = (59.0 - 2.2 * lift) * unit
        draw.ellipse((cx * unit - radius, cy - radius, cx * unit + radius, cy + radius), fill=(*color[:3], alpha))
    return image
