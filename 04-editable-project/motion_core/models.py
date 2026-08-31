from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class LayerDef:
    name: str
    bbox: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)
    colors: tuple[tuple[int, int, int], ...] = ()
    polygon: tuple[tuple[float, float], ...] = ()
    fill: tuple[int, int, int, int] | None = None
    tolerance: float = 34.0
    z: int = 0


@dataclass(frozen=True)
class Keyframe:
    frame: int
    x: float = 0.0
    y: float = 0.0
    sx: float = 1.0
    sy: float = 1.0
    rotation: float = 0.0
    opacity: float = 1.0
    reveal: float = 1.0
    easing: str = "smooth"


@dataclass(frozen=True)
class Track:
    layer: str
    keyframes: tuple[Keyframe, ...]
    reveal_mode: str = "none"
    reveal_origin: tuple[float, float] = (0.5, 0.5)


@dataclass(frozen=True)
class MotionSpec:
    stem: str
    source: Path | None
    layers: tuple[LayerDef, ...]
    tracks: tuple[Track, ...]
    duration_frames: int = 60
    fps: int = 30
    supersample: int = 4
    tags: tuple[str, ...] = field(default_factory=tuple)
