from dataclasses import dataclass

import numpy as np
from PIL import Image
from skimage.measure import approximate_polygon, find_contours, label, regionprops

from frame_motions.common import BLUE, INK, PAPER, TAUPE


PALETTE = (BLUE[:3], TAUPE[:3], PAPER[:3], INK[:3])


@dataclass(frozen=True)
class VectorGroup:
    color: tuple[int, int, int]
    opacity: float
    paths: tuple[tuple[tuple[float, float], ...], ...]


def _signed_area(points: np.ndarray) -> float:
    x = points[:, 0]
    y = points[:, 1]
    return float((x @ np.roll(y, 1) - y @ np.roll(x, 1)) / 2)


def _paths_for_mask(
    mask: np.ndarray,
    *,
    tolerance: float,
    minimum_area: float,
    offset: tuple[int, int] = (0, 0),
) -> tuple[tuple[tuple[float, float], ...], ...]:
    padded = np.pad(mask.astype(np.uint8), 1)
    paths = []
    for contour in find_contours(padded, 0.5):
        contour = contour - 1
        simplified = approximate_polygon(contour, tolerance=tolerance)
        if len(simplified) > 1 and np.allclose(simplified[0], simplified[-1]):
            simplified = simplified[:-1]
        if len(simplified) < 3:
            continue
        xy = np.column_stack((simplified[:, 1], simplified[:, 0]))
        if abs(_signed_area(xy)) < minimum_area:
            continue
        xy += np.asarray(offset)
        paths.append(
            tuple((round(float(x), 2), round(float(y), 2)) for x, y in xy)
        )
    return tuple(paths)


def vectorize_frame(
    image: Image.Image,
    *,
    tolerance: float = 2.0,
    minimum_area: float = 3.0,
    alpha_threshold: int = 32,
) -> tuple[VectorGroup, ...]:
    if image.mode != "RGBA" or image.size != (512, 512):
        raise ValueError(f"expected RGBA 512x512, found {image.mode} {image.size}")
    pixels = np.asarray(image)
    visible = pixels[:, :, 3] >= alpha_threshold
    if not visible.any():
        return ()
    colors = pixels[:, :, :3].astype(np.int32)
    palette = np.asarray(PALETTE, dtype=np.int32)
    distance = np.sum((colors[:, :, None, :] - palette[None, None, :, :]) ** 2, axis=3)
    nearest = np.argmin(distance, axis=2)
    grouped_paths = {}
    for index, color in enumerate(PALETTE):
        color_mask = visible & (nearest == index)
        components = label(color_mask, connectivity=2)
        for region in regionprops(components):
            if region.area < minimum_area:
                continue
            min_y, min_x, max_y, max_x = region.bbox
            component = region.image
            paths = _paths_for_mask(
                component,
                tolerance=tolerance,
                minimum_area=minimum_area,
                offset=(min_x, min_y),
            )
            if not paths:
                continue
            alpha = pixels[min_y:max_y, min_x:max_x, 3][component]
            opacity = min(100.0, round(float(np.quantile(alpha, 0.75)) / 255 * 20) * 5)
            grouped_paths.setdefault((color, opacity), []).extend(paths)
    return tuple(
        VectorGroup(color, opacity, tuple(paths))
        for (color, opacity), paths in grouped_paths.items()
    )
