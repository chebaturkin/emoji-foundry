from collections.abc import Callable
from dataclasses import dataclass, field

from PIL import Image


DrawFrame = Callable[[int, int], Image.Image]


@dataclass(frozen=True)
class FrameMotionSpec:
    stem: str
    draw_frame: DrawFrame
    duration_frames: int = 42
    fps: int = 30
    supersample: int = 4
    tags: tuple[str, ...] = field(default_factory=tuple)
