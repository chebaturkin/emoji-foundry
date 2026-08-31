import gzip
import json

import numpy as np
from PIL import Image

from frame_core.models import FrameMotionSpec
from tgs_core.vectorize import VectorGroup, vectorize_frame


TGS_SIZE = 512
TGS_FPS = 60


def _mount_safe_area(image: Image.Image) -> Image.Image:
    inset = round(image.width * 0.08)
    mounted = Image.new("RGBA", image.size, (0, 0, 0, 0))
    fitted = image.resize(
        (image.width - inset * 2, image.height - inset * 2),
        Image.Resampling.LANCZOS,
    )
    mounted.alpha_composite(fitted, (inset, inset))
    result = mounted.resize((TGS_SIZE, TGS_SIZE), Image.Resampling.LANCZOS)
    pixels = np.asarray(result).copy()
    pixels[pixels[:, :, 3] < 16, 3] = 0
    pixels[pixels[:, :, 3] == 0, :3] = 0
    return Image.fromarray(pixels, "RGBA")


def render_high_resolution(
    spec: FrameMotionSpec,
    *,
    render_size: int = 400,
) -> list[Image.Image]:
    if not isinstance(spec, FrameMotionSpec):
        raise TypeError(f"TGS export requires FrameMotionSpec, found {type(spec).__name__}")
    frames = [
        _mount_safe_area(spec.draw_frame(frame, render_size))
        for frame in range(spec.duration_frames)
    ]
    peak = max(
        range(len(frames)),
        key=lambda index: int(
            np.asarray(frames[index].getchannel("A"), dtype=np.uint64).sum()
        ),
    )
    return frames[peak:] + frames[:peak]


def _path_shape(points: tuple[tuple[float, float], ...], index: int) -> dict:
    zeros = [[0, 0] for _ in points]
    return {
        "ind": index,
        "ty": "sh",
        "ks": {
            "a": 0,
            "k": {
                "i": zeros,
                "o": zeros,
                "v": [list(point) for point in points],
                "c": True,
            },
        },
        "nm": f"Path {index + 1}",
        "hd": False,
    }


def _fill_shape(color: tuple[int, int, int], opacity: float) -> dict:
    return {
        "ty": "fl",
        "c": {"a": 0, "k": [round(channel / 255, 6) for channel in color] + [1]},
        "o": {"a": 0, "k": opacity},
        "r": 1,
        "bm": 0,
        "nm": "Fill 1",
        "hd": False,
    }


def _group_transform() -> dict:
    return {
        "ty": "tr",
        "p": {"a": 0, "k": [0, 0]},
        "a": {"a": 0, "k": [0, 0]},
        "s": {"a": 0, "k": [100, 100]},
        "r": {"a": 0, "k": 0},
        "o": {"a": 0, "k": 100},
        "sk": {"a": 0, "k": 0},
        "sa": {"a": 0, "k": 0},
        "nm": "Transform",
    }


def _group_shape(group: VectorGroup) -> dict:
    items = [_path_shape(path, index) for index, path in enumerate(group.paths)]
    items.extend((_fill_shape(group.color, group.opacity), _group_transform()))
    return {
        "ty": "gr",
        "it": items,
        "nm": "Shape Group",
        "bm": 0,
        "hd": False,
    }


def _layer(
    stem: str,
    frame_index: int,
    color_index: int,
    group: VectorGroup,
    source_fps: int,
    layer_index: int,
) -> dict:
    frame_scale = TGS_FPS // source_fps
    shapes = [_group_shape(group)]
    return {
        "ddd": 0,
        "ind": layer_index,
        "ty": 4,
        "nm": f"{stem}-{frame_index:03d}-{color_index}",
        "sr": 1,
        "ks": {
            "o": {"a": 0, "k": 100},
            "r": {"a": 0, "k": 0},
            "p": {"a": 0, "k": [256, 256, 0]},
            "a": {"a": 0, "k": [256, 256, 0]},
            "s": {"a": 0, "k": [100, 100, 100]},
        },
        "ao": 0,
        "shapes": shapes,
        "ip": frame_index * frame_scale,
        "op": (frame_index + 1) * frame_scale,
        "st": 0,
        "bm": 0,
    }


def build_tgs_document(
    stem: str,
    frames: list[Image.Image],
    *,
    source_fps: int = 30,
    tolerance: float = 2.0,
    minimum_area: float = 3.0,
) -> dict:
    if not frames:
        raise ValueError("TGS requires at least one frame")
    if TGS_FPS % source_fps:
        raise ValueError(f"source FPS {source_fps} must divide {TGS_FPS}")
    layers = []
    for frame_index, frame in enumerate(frames):
        for color_index, group in enumerate(
            vectorize_frame(
                frame,
                tolerance=tolerance,
                minimum_area=minimum_area,
            )
        ):
            layers.append(
                _layer(
                    stem,
                    frame_index,
                    color_index,
                    group,
                    source_fps,
                    len(layers) + 1,
                )
            )
    frame_scale = TGS_FPS // source_fps
    return {
        "tgs": 1,
        "v": "5.5.2",
        "fr": TGS_FPS,
        "ip": 0,
        "op": len(frames) * frame_scale,
        "w": TGS_SIZE,
        "h": TGS_SIZE,
        "nm": stem,
        "ddd": 0,
        "assets": [],
        "layers": layers,
    }


def build_tgs_bytes(
    stem: str,
    frames: list[Image.Image],
    *,
    source_fps: int = 30,
    tolerance: float = 2.0,
    minimum_area: float = 3.0,
) -> bytes:
    document = build_tgs_document(
        stem,
        frames,
        source_fps=source_fps,
        tolerance=tolerance,
        minimum_area=minimum_area,
    )
    raw = json.dumps(
        document,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return gzip.compress(raw, compresslevel=9, mtime=0)
