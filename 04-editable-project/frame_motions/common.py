from PIL import Image
from PIL import ImageDraw
import numpy as np

from frame_core.brush import draw_brush_stroke
from frame_core.composite import alpha_fade, phase, smooth


BLUE = (46, 58, 77, 255)
TAUPE = (196, 193, 180, 255)
PAPER = (242, 240, 233, 255)
INK = (13, 13, 13, 255)


def canvas(size=400):
    return Image.new("RGBA", (size, size), (0, 0, 0, 0))


def px(value, size):
    return value * size / 100.0


def fill_polygon(image, points, color, opacity=1.0):
    rgba = (*color[:3], round(color[3] * opacity))
    ImageDraw.Draw(image, "RGBA").polygon([tuple(map(float, point)) for point in points], fill=rgba)


def draw_closed_shape(image, points, fill, outline=BLUE, width=24, opacity=1.0):
    fill_polygon(image, points, fill, opacity)
    closed = list(points) + [points[0]]
    draw_brush_stroke(image, closed, outline, width, opacity)


def finish(image, frame):
    opacity = 1.0 - smooth(phase(frame, 50, 59))
    result = alpha_fade(image, opacity)
    pixels = np.asarray(result).copy()
    pixels[pixels[:, :, 3] == 0, :3] = 0
    return Image.fromarray(pixels, "RGBA")
