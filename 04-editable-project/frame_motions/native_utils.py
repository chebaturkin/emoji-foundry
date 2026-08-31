from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops

from frame_core.brush import draw_pressure_stroke, pressure_profile
from frame_core.path import reveal_points
from frame_motions.common import BLUE, PAPER, canvas


ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=64)
def _master(stem: str, size: int) -> Image.Image:
    with Image.open(ROOT / "masters" / f"{stem}.png") as source:
        return source.convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)


def master_image(stem: str, size: int) -> Image.Image:
    return _master(stem, size).copy()


def masked_part(
    source: Image.Image,
    region: np.ndarray,
    reveal: np.ndarray | None = None,
    offset: tuple[int, int] = (0, 0),
) -> Image.Image:
    alpha = np.asarray(source.getchannel("A"), dtype=np.uint8)
    mask = np.asarray(region, dtype=bool)
    if reveal is not None:
        mask &= np.asarray(reveal, dtype=bool)
    result = source.copy()
    result.putalpha(Image.fromarray(np.where(mask, alpha, 0).astype(np.uint8), "L"))
    if offset != (0, 0):
        moved = canvas(source.width)
        moved.alpha_composite(result, offset)
        return moved
    return result


def blue_depth(image: Image.Image, dx: int, dy: int, opacity: int = 105) -> Image.Image:
    alpha = ImageChops.offset(image.getchannel("A"), dx, dy)
    alpha = alpha.point(lambda value: round(value * opacity / 255))
    result = Image.new("RGBA", image.size, BLUE)
    result.putalpha(alpha)
    return result


def paper_blue_stroke(
    points,
    size: int,
    width: float,
    progress: float = 1.0,
    opacity: float = 1.0,
    offset: tuple[float, float] = (1.7, 2.1),
) -> Image.Image:
    result = canvas(size)
    visible = reveal_points(points, progress)
    if len(visible) < 2:
        return result
    pressure = pressure_profile(len(visible), 0.24, 1.08, 0.28)
    shifted = np.asarray(visible) + np.asarray(offset) * size / 100.0
    draw_pressure_stroke(result, shifted, BLUE, width * 1.12, pressure, opacity)
    draw_pressure_stroke(result, visible, PAPER, width, pressure, opacity)
    return result


def alpha_union(images: list[Image.Image], size: int) -> Image.Image:
    result = canvas(size)
    for image in images:
        result.alpha_composite(image)
    return result


def transform_image(
    image: Image.Image,
    scale: tuple[float, float] = (1.0, 1.0),
    rotation: float = 0.0,
    offset: tuple[float, float] = (0.0, 0.0),
    opacity: float = 1.0,
) -> Image.Image:
    result = canvas(image.width)
    bbox = image.getchannel("A").getbbox()
    if bbox is None or opacity <= 0:
        return result
    crop = image.crop(bbox)
    crop = crop.resize(
        (
            max(1, round(crop.width * scale[0])),
            max(1, round(crop.height * scale[1])),
        ),
        Image.Resampling.BICUBIC,
    )
    if rotation:
        crop = crop.rotate(-rotation, Image.Resampling.BICUBIC, expand=True)
    if opacity < 1:
        alpha = np.asarray(crop.getchannel("A"), dtype=np.float32)
        crop.putalpha(
            Image.fromarray(np.clip(alpha * opacity, 0, 255).astype(np.uint8), "L")
        )
    center = np.array(((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2))
    center += np.asarray(offset) * image.width / 100.0
    result.alpha_composite(
        crop,
        (round(center[0] - crop.width / 2), round(center[1] - crop.height / 2)),
    )
    return result
