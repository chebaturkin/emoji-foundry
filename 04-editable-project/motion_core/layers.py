import numpy as np
from PIL import Image, ImageDraw

from motion_core.models import LayerDef


def layer_mask(source: Image.Image, definition: LayerDef) -> Image.Image:
    rgba = np.asarray(source.convert("RGBA"))
    height, width = rgba.shape[:2]
    x0, y0, x1, y1 = definition.bbox
    mask = np.zeros((height, width), dtype=bool)
    mask[round(y0 * height):round(y1 * height), round(x0 * width):round(x1 * width)] = True

    if definition.colors:
        color_mask = np.zeros_like(mask)
        rgb = rgba[:, :, :3].astype(np.float32)
        for color in definition.colors:
            distance = np.linalg.norm(rgb - np.array(color, dtype=np.float32), axis=2)
            color_mask |= distance <= definition.tolerance
        mask &= color_mask

    if definition.polygon:
        poly = Image.new("L", (width, height), 0)
        points = [(round(x * width), round(y * height)) for x, y in definition.polygon]
        ImageDraw.Draw(poly).polygon(points, fill=255)
        mask &= np.asarray(poly) > 0

    mask &= rgba[:, :, 3] > 0
    return Image.fromarray(mask.astype(np.uint8) * 255, "L")


def split_layers(source: Image.Image, definitions: tuple[LayerDef, ...]) -> dict[str, Image.Image]:
    rgba = source.convert("RGBA")
    base = rgba.copy()
    result: dict[str, Image.Image] = {}
    for definition in sorted(definitions, key=lambda item: item.z):
        mask = layer_mask(rgba, definition)
        child = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
        child.paste(rgba, (0, 0), mask)
        result[definition.name] = child
        replacement = Image.new("RGBA", rgba.size, definition.fill or (0, 0, 0, 0))
        base.paste(replacement, (0, 0), mask)
    result["base"] = base
    return result
