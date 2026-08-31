"""Continuous, authored geometry for the like/dislike hand gestures."""

from dataclasses import dataclass
from typing import Literal, Sequence

import numpy as np

from frame_core.brush import draw_brush_stroke
from frame_core.path import morph_points
from frame_motions.common import BLUE, INK, PAPER, canvas


@dataclass(frozen=True)
class HandPose:
    silhouette: np.ndarray
    thumb_joint: np.ndarray
    crease_paths: Sequence[np.ndarray]


# Coordinates are authored on a 100-unit board. Paths are closed and deliberately
# continuous: the cuff, wrist, palm, grouped fingers and thumb are one silhouette.
_UP_RELAXED = np.array([
    [34, 90], [33, 80], [35, 70], [37, 61], [35, 53], [34, 45],
    [36, 35], [39, 24], [43, 18], [47, 17], [50, 22], [51, 34],
    [54, 20], [58, 16], [62, 18], [62, 34], [65, 22], [69, 20],
    [73, 23], [71, 39], [75, 31], [80, 30], [82, 34], [76, 46],
    [72, 53], [68, 61], [63, 67], [61, 76], [59, 90], [34, 90],
])
_UP_FINAL = np.array([
    [35, 90], [34, 80], [36, 69], [40, 59], [39, 51], [39, 43],
    [40, 29], [44, 18], [48, 16], [52, 20], [53, 35], [56, 20],
    [60, 15], [64, 17], [64, 34], [67, 20], [71, 18], [75, 22],
    [73, 39], [77, 29], [82, 28], [85, 33], [79, 46], [74, 53],
    [70, 60], [65, 67], [63, 77], [61, 90], [35, 90],
])
_DOWN_RELAXED = np.array([
    [34, 90], [33, 80], [34, 70], [37, 61], [39, 53], [38, 46],
    [39, 38], [42, 31], [46, 29], [50, 32], [51, 43], [54, 31],
    [58, 28], [62, 31], [62, 45], [66, 33], [70, 31], [74, 35],
    [72, 48], [77, 55], [82, 61], [84, 68], [79, 72], [73, 70],
    [68, 68], [64, 77], [62, 90], [34, 90],
])
_DOWN_FINAL = np.array([
    [34, 90], [33, 81], [34, 71], [37, 62], [41, 56], [43, 49],
    [43, 41], [45, 34], [49, 31], [53, 35], [53, 48], [56, 37],
    [60, 34], [64, 38], [63, 51], [67, 40], [71, 38], [75, 42],
    [73, 55], [77, 60], [82, 66], [84, 73], [79, 77], [73, 75],
    [69, 74], [65, 82], [63, 90], [34, 90],
])

_UP_CREASES = (
    np.array([[43, 52], [49, 49], [55, 50]], dtype=float),
    np.array([[57, 57], [63, 54], [69, 55]], dtype=float),
)
_DOWN_CREASES = (
    np.array([[43, 55], [49, 58], [55, 57]], dtype=float),
    np.array([[57, 62], [63, 60], [69, 61]], dtype=float),
)

HAND_CONTROLS = {
    "up": (_UP_RELAXED, _UP_FINAL, np.array([53, 53.0]), np.array([57, 43.0]), _UP_CREASES),
    "down": (_DOWN_RELAXED, _DOWN_FINAL, np.array([54, 52.0]), np.array([59, 61.0]), _DOWN_CREASES),
}


def hand_pose(direction: Literal["up", "down"], progress: float, size: int) -> HandPose:
    if direction not in HAND_CONTROLS:
        raise ValueError(f"unknown hand direction: {direction}")
    progress = float(np.clip(progress, 0.0, 1.0))
    relaxed, final, relaxed_joint, final_joint, creases = HAND_CONTROLS[direction]
    # Smooth interpolation keeps thumb articulation organic while retaining one
    # closed path for the entire hand.
    eased = progress * progress * (3.0 - 2.0 * progress)
    silhouette = morph_points(relaxed, final, eased, count=96) * size / 100.0
    thumb_joint = (relaxed_joint + (final_joint - relaxed_joint) * eased) * size / 100.0
    scaled_creases = tuple(path * size / 100.0 for path in creases)
    return HandPose(silhouette, thumb_joint, scaled_creases)


def transformed_pose(pose: HandPose, *, dy: float = 0.0, rotation: float = 0.0) -> HandPose:
    points = pose.silhouette
    scale = float(points[:, 1].max()) / 90.0 if points.size else 1.0
    center = np.array([50.0, 58.0]) * scale
    radians = np.deg2rad(rotation)
    matrix = np.array([[np.cos(radians), -np.sin(radians)], [np.sin(radians), np.cos(radians)]])
    moved = (points - center) @ matrix.T + center
    moved[:, 1] += dy
    joint = (pose.thumb_joint - center) @ matrix.T + center
    joint[1] += dy
    creases = []
    for path in pose.crease_paths:
        item = (path - center) @ matrix.T + center
        item[:, 1] += dy
        creases.append(item)
    return HandPose(moved, joint, tuple(creases))


def render_hand_layers(pose: HandPose, size: int):
    paper = canvas(size)
    paper_points = [tuple(point) for point in pose.silhouette]
    from PIL import ImageDraw
    ImageDraw.Draw(paper, "RGBA").polygon(paper_points, fill=PAPER)
    outline = canvas(size)
    draw_brush_stroke(outline, np.vstack((pose.silhouette, pose.silhouette[:1])), BLUE, size * 0.045)
    creases = canvas(size)
    for path in pose.crease_paths:
        draw_brush_stroke(creases, path, INK, size * 0.018)
    from frame_motions.native_utils import blue_depth
    depth = blue_depth(paper, round(size * 0.014), round(size * 0.020), 105)
    return depth, paper, outline, creases
