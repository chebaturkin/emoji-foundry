import numpy as np
from PIL import Image, ImageDraw


def phase(frame, start, end):
    if end <= start:
        raise ValueError("phase end must be greater than start")
    return float(np.clip((frame - start) / (end - start), 0.0, 1.0))


def smooth(value):
    value = float(np.clip(value, 0.0, 1.0))
    return value * value * (3.0 - 2.0 * value)


def polygon_layer(size, points, fill):
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(image, "RGBA").polygon([tuple(point) for point in points], fill=fill)
    return image


def alpha_fade(image, opacity):
    result = image.copy()
    alpha = np.asarray(result.getchannel("A"), dtype=np.float32)
    result.putalpha(Image.fromarray(np.clip(alpha * opacity, 0, 255).astype(np.uint8), "L"))
    return result


def finalize_frame(image):
    inset = round(image.width * 0.08)
    mounted = Image.new("RGBA", image.size, (0, 0, 0, 0))
    fitted = image.resize((image.width - inset * 2, image.height - inset * 2), Image.Resampling.LANCZOS)
    mounted.alpha_composite(fitted, (inset, inset))
    result = mounted.resize((100, 100), Image.Resampling.LANCZOS)
    pixels = np.asarray(result).copy()
    pixels[pixels[:, :, 3] < 16, 3] = 0
    pixels[pixels[:, :, 3] == 0, :3] = 0
    return Image.fromarray(pixels, "RGBA")
