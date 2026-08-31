import numpy as np
from PIL import Image, ImageChops, ImageDraw

from frame_core.brush import draw_pressure_stroke, jitter_points, pressure_profile
from frame_core.composite import phase, smooth
from frame_core.deform import deform_points
from frame_core.depth import DepthLayer, compose_depth, glint_window
from frame_core.models import FrameMotionSpec
from frame_core.path import cubic_points
from frame_core.retime import retime_draw
from frame_motions.common import BLUE, INK, PAPER, TAUPE, canvas


SHADOW_BLUE = (46, 58, 77, 158)


def _has_span(points, minimum=1.0):
    points = np.asarray(points)
    return len(points) >= 2 and float(np.ptp(points, axis=0).max()) >= minimum


def eye_state(frame, size):
    search_left = smooth(phase(frame, 17, 22))
    search_right = smooth(phase(frame, 22, 28))
    pupil_x = (-5 * search_left + 8 * search_right) * size / 100
    if frame >= 28:
        pupil_x *= 1 - smooth(phase(frame, 28, 34))
    return {
        "open": smooth(phase(frame, 2, 17))
        * (1 - smooth(phase(frame, 49, 59))),
        "pupil_x": pupil_x,
        "iris_scale": 1 - 0.22 * smooth(phase(frame, 30, 37)),
    }


def _lid_geometry(frame, size):
    state = eye_state(frame, size)
    unit = size / 100.0
    opening = state["open"]
    upper = cubic_points(
        (15 * unit, 50 * unit),
        (31 * unit, (50 - 31 * opening) * unit),
        (67 * unit, (50 - 31 * opening) * unit),
        (85 * unit, 50 * unit),
        49,
    )
    lower = cubic_points(
        (15 * unit, 50 * unit),
        (31 * unit, (50 + 25 * opening) * unit),
        (68 * unit, (50 + 25 * opening) * unit),
        (85 * unit, 50 * unit),
        49,
    )
    upper = jitter_points(upper, seed=601, amount=size / 1700)
    lower = jitter_points(lower, seed=607, amount=size / 1600)

    focus = (1.0 - state["iris_scale"]) / 0.22
    local_index = int(np.clip(24 + state["pupil_x"] / unit * 0.45, 14, 34))
    upper = deform_points(
        upper,
        controls=((local_index, (0, 2.1 * unit * focus * opening), 6),),
        anchors=(0, len(upper) - 1),
    )
    lower = deform_points(
        lower,
        controls=((local_index, (0, -1.3 * unit * focus * opening), 7),),
        anchors=(0, len(lower) - 1),
    )
    target = np.array((50 * unit, 50 * unit))
    remain = 1.0 - smooth(phase(frame, 49, 57))
    upper = target + (upper - target) * remain
    lower = target + (lower - target) * remain
    return upper, lower


def _surface_layer(frame, size):
    result = canvas(size)
    if eye_state(frame, size)["open"] <= 0:
        return result
    upper, lower = _lid_geometry(frame, size)
    polygon = np.vstack((upper, lower[::-1]))
    if np.ptp(polygon[:, 0]) < 1 or np.ptp(polygon[:, 1]) < 1:
        return result
    ImageDraw.Draw(result, "RGBA").polygon(
        [tuple(point) for point in polygon], fill=PAPER
    )
    return result


def _shadow_layer(frame, size):
    lagged_surface = _surface_layer(max(0, frame - 2), size)
    alpha = ImageChops.offset(
        lagged_surface.getchannel("A"), round(size * 0.02), round(size * 0.03)
    )
    alpha = alpha.point(lambda value: round(value * SHADOW_BLUE[3] / 255))
    result = Image.new("RGBA", (size, size), SHADOW_BLUE)
    result.putalpha(alpha)
    return result


def _lid_layer(frame, size, upper_lid):
    result = canvas(size)
    state = eye_state(frame, size)
    if state["open"] <= 0:
        return result
    upper, lower = _lid_geometry(frame, size)
    points = upper if upper_lid else lower
    if not _has_span(points):
        return result
    pressure = (0.30, 1.12, 0.22) if upper_lid else (0.20, 0.90, 0.28)
    draw_pressure_stroke(
        result,
        points,
        BLUE,
        size * (0.059 if upper_lid else 0.047),
        pressure_profile(len(points), *pressure),
    )
    return result


def _clipped_disc(frame, size, radius, color, pupil=False):
    result = canvas(size)
    state = eye_state(frame, size)
    opening = state["open"]
    if opening <= 0:
        return result
    unit = size / 100.0
    center_x = 50 * unit + state["pupil_x"]
    focus = (1.0 - state["iris_scale"]) / 0.22
    center_y = (50 + 0.7 * focus) * unit
    scale = 1.0 if pupil else state["iris_scale"]
    horizontal = radius * unit * scale
    vertical = radius * unit * scale * min(1.0, opening * 1.55)
    ImageDraw.Draw(result, "RGBA").ellipse(
        (
            center_x - horizontal,
            center_y - vertical,
            center_x + horizontal,
            center_y + vertical,
        ),
        fill=color,
    )
    clipped = ImageChops.multiply(
        result.getchannel("A"), _surface_layer(frame, size).getchannel("A")
    )
    result.putalpha(clipped)
    return result


def _glint_layer(frame, size):
    result = canvas(size)
    strength = glint_window(frame, 31, 41)
    state = eye_state(frame, size)
    if strength <= 0 or state["open"] <= 0:
        return result
    unit = size / 100.0
    center_x = 50 * unit + state["pupil_x"]
    center_y = 50 * unit
    radius = 1.8 * unit
    ImageDraw.Draw(result, "RGBA").ellipse(
        (
            center_x - 5.0 * unit - radius,
            center_y - 7.0 * unit - radius,
            center_x - 5.0 * unit + radius,
            center_y - 7.0 * unit + radius,
        ),
        fill=(*PAPER[:3], round(PAPER[3] * strength)),
    )
    result.putalpha(
        ImageChops.multiply(
            result.getchannel("A"), _surface_layer(frame, size).getchannel("A")
        )
    )
    return result


def eye_layers(frame, size):
    return [
        DepthLayer("blue_shadow", _shadow_layer(frame, size), 0),
        DepthLayer("paper_surface", _surface_layer(frame, size), 10),
        DepthLayer("iris", _clipped_disc(frame, size, 15.0, TAUPE), 20),
        DepthLayer("pupil", _clipped_disc(frame, size, 7.0, INK, pupil=True), 30),
        DepthLayer("upper_lid", _lid_layer(frame, size, True), 40),
        DepthLayer("lower_lid", _lid_layer(frame, size, False), 41),
        DepthLayer("directional_glint", _glint_layer(frame, size), 50),
    ]


def draw_frame(frame, size):
    if frame <= 0 or frame >= 59:
        return canvas(size)
    return compose_depth(eye_layers(frame, size))


SPEC = FrameMotionSpec(
    "11-eye",
    retime_draw(draw_frame, 48),
    duration_frames=48,
    tags=("batch1", "story", "tactile"),
)
