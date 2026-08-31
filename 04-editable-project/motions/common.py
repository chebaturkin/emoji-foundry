from pathlib import Path

from motion_core.models import Keyframe as K
from motion_core.models import LayerDef as L
from motion_core.models import MotionSpec, Track as T


STATIC = Path(__file__).resolve().parents[1] / "masters"
STEEL = (46, 58, 77)
TAUPE = (196, 193, 180)
PARCHMENT = (242, 240, 233)
OBSIDIAN = (13, 13, 13)
P = (*PARCHMENT, 255)
T_FILL = (*TAUPE, 255)


def make(stem: str, layers: tuple[L, ...], tracks: tuple[T, ...], tag: str) -> MotionSpec:
    return MotionSpec(
        stem,
        STATIC / f"{stem}.png",
        layers,
        tracks,
        duration_frames=60,
        tags=(tag,),
    )
