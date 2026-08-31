from dataclasses import dataclass
import math

from PIL import Image


@dataclass(frozen=True)
class DepthLayer:
    name: str
    image: Image.Image
    z: int


def compose_depth(layers):
    ordered = sorted(layers, key=lambda item: item.z)
    if not ordered:
        raise ValueError("at least one depth layer is required")
    result = Image.new("RGBA", ordered[0].image.size, (0, 0, 0, 0))
    for layer in ordered:
        result.alpha_composite(layer.image)
    return result


def glint_window(frame, start, end):
    if frame <= start or frame >= end:
        return 0.0
    progress = (frame - start) / (end - start)
    return math.sin(math.pi * progress)
