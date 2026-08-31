import numpy as np
from PIL import Image, ImageDraw


def jitter_points(points, seed, amount):
    points = np.asarray(points, dtype=float)
    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, amount, points.shape)
    if len(points) >= 5:
        kernel = np.ones(5) / 5
        noise[:, 0] = np.convolve(noise[:, 0], kernel, mode="same")
        noise[:, 1] = np.convolve(noise[:, 1], kernel, mode="same")
    noise[0] = 0
    noise[-1] = 0
    return points + noise


def draw_brush_stroke(image: Image.Image, points, color, width, opacity=1.0):
    points = np.asarray(points, dtype=float)
    if len(points) < 2:
        return
    rgba = (*color[:3], round(color[3] * opacity))
    xy = [tuple(map(float, point)) for point in points]
    draw = ImageDraw.Draw(image, "RGBA")
    draw.line(xy, fill=rgba, width=max(1, round(width)), joint="curve")
    radius = width / 2
    for point in (points[0], points[-1]):
        draw.ellipse((point[0] - radius, point[1] - radius, point[0] + radius, point[1] + radius), fill=rgba)


def pressure_profile(count, start=0.4, peak=1.0, end=0.3):
    if count < 2:
        raise ValueError("pressure profile requires at least two samples")
    left_count = count // 2 + 1
    right_count = count - left_count + 1
    left = np.linspace(start, peak, left_count)
    right = np.linspace(peak, end, right_count)[1:]
    return np.concatenate((left, right))


def draw_pressure_stroke(image: Image.Image, points, color, width, pressure, opacity=1.0):
    points = np.asarray(points, dtype=float)
    pressure = np.asarray(pressure, dtype=float)
    if len(points) != len(pressure):
        raise ValueError("pressure length must match points")
    if len(points) < 2:
        return
    rgba = (*color[:3], round(color[3] * opacity))
    draw = ImageDraw.Draw(image, "RGBA")
    for index, (a, b) in enumerate(zip(points, points[1:])):
        segment_width = max(1, round(width * (pressure[index] + pressure[index + 1]) / 2))
        draw.line((tuple(a), tuple(b)), fill=rgba, width=segment_width)
        radius = segment_width / 2
        draw.ellipse((b[0]-radius, b[1]-radius, b[0]+radius, b[1]+radius), fill=rgba)
