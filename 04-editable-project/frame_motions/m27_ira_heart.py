import math

import numpy as np

from frame_core.brush import draw_pressure_stroke, jitter_points, pressure_profile
from frame_core.composite import phase, smooth
from frame_core.depth import DepthLayer, compose_depth
from frame_core.models import FrameMotionSpec
from frame_core.path import cubic_points, resample_points, reveal_points
from frame_motions.common import BLUE, PAPER, canvas


def ira_heart_state(frame):
    return {
        "letters": (
            smooth(phase(frame, 1, 9)) * (1 - smooth(phase(frame, 37, 41))),
            smooth(phase(frame, 5, 13)) * (1 - smooth(phase(frame, 35, 40))),
            smooth(phase(frame, 9, 17)) * (1 - smooth(phase(frame, 33, 39))),
        ),
        "heart_top": smooth(phase(frame, 14, 25))
        * (1 - smooth(phase(frame, 33, 40))),
        "heart_bottom": smooth(phase(frame, 16, 27))
        * (1 - smooth(phase(frame, 32, 39))),
        "closure": math.sin(math.pi * phase(frame, 25, 33)),
    }


def _letter_paths(size):
    unit = size / 100.0
    authored = (
        (
            np.array(((33, 42), (33, 61)), dtype=float) * unit,
            np.array(((33, 61), (43, 42)), dtype=float) * unit,
            np.array(((43, 42), (43, 61)), dtype=float) * unit,
        ),
        (
            np.array(((47, 61), (47, 42)), dtype=float) * unit,
            cubic_points(
                (47 * unit, 42 * unit),
                (59 * unit, 39 * unit),
                (59 * unit, 52 * unit),
                (47 * unit, 51 * unit),
                20,
            ),
        ),
        (
            np.array(((58, 61), (65, 42), (72, 61)), dtype=float) * unit,
            np.array(((61, 53), (69, 53)), dtype=float) * unit,
        ),
    )
    center_x = 50 * unit
    return tuple(
        tuple(
            np.column_stack(
                (
                    center_x + (stroke[:, 0] - center_x) * 1.4,
                    stroke[:, 1],
                )
            )
            for stroke in letter
        )
        for letter in authored
    )


def _heart_paths(size, closure):
    unit = size / 100.0
    recoil = math.sin(math.pi * closure) if closure < 1 else 0.0
    top = np.vstack(
        (
            cubic_points(
                (18 * unit, (46 + recoil) * unit),
                (13 * unit, 27 * unit),
                (34 * unit, 18 * unit),
                (48 * unit, 37 * unit),
                28,
            ),
            cubic_points(
                (48 * unit, 37 * unit),
                (62 * unit, 16 * unit),
                (88 * unit, 26 * unit),
                (82 * unit, (48 + recoil) * unit),
                32,
            )[1:],
        )
    )
    bottom = np.vstack(
        (
            cubic_points(
                (21 * unit, (62 - recoil) * unit),
                ((31 - closure) * unit, 73 * unit),
                ((42 + closure) * unit, 79 * unit),
                (50 * unit, 84 * unit),
                24,
            ),
            cubic_points(
                (50 * unit, 84 * unit),
                ((61 - closure) * unit, 77 * unit),
                ((73 + closure) * unit, 69 * unit),
                (80 * unit, (58 - recoil) * unit),
                24,
            )[1:],
        )
    )
    return top, bottom


def _stroke(points, size, progress, width, seed, opacity=1.0, color=BLUE):
    image = canvas(size)
    if progress <= 0 or opacity <= 0:
        return image
    authored = jitter_points(
        resample_points(points, max(18, len(points))),
        seed=seed,
        amount=size / 2600.0,
    )
    visible = reveal_points(authored, progress)
    if len(visible) < 2:
        return image
    draw_pressure_stroke(
        image,
        visible,
        color,
        size * width,
        pressure_profile(len(visible), .28, 1.08, .25),
        opacity,
    )
    return image


def _sequential_progress(progress, index, count):
    return smooth(phase(progress, index / count, (index + 1) / count))


def _letter_image(size, letter_index, progress, color, width, seed_offset=0):
    result = canvas(size)
    paths = _letter_paths(size)[letter_index]
    for stroke_index, points in enumerate(paths):
        result.alpha_composite(
            _stroke(
                points,
                size,
                _sequential_progress(
                    progress, stroke_index, len(paths)
                ),
                width,
                seed=2700 + seed_offset + letter_index * 10 + stroke_index,
                color=color,
            )
        )
    return result


def _letter_layer(frame, size, letter_index, progress_key, color, width):
    state = ira_heart_state(frame)
    return _letter_image(
        size,
        letter_index,
        state[progress_key][letter_index],
        color,
        width,
        seed_offset=0,
    )


def _heart_layer(frame, size, name):
    state = ira_heart_state(frame)
    top, bottom = _heart_paths(size, state["closure"])
    if name == "top":
        return _stroke(top, size, state["heart_top"], .050, 2731)
    return _stroke(bottom, size, state["heart_bottom"], .050, 2737)


def _closure_layer(frame, size):
    strength = ira_heart_state(frame)["closure"]
    result = canvas(size)
    if strength <= 0:
        return result
    unit = size / 100.0
    for index, (start, end) in enumerate(
        (
            ((18.5, 52.0), (22.0, 55.0)),
            ((81.5, 52.0), (78.0, 55.0)),
        )
    ):
        result.alpha_composite(
            _stroke(
                np.array((start, end), dtype=float) * unit,
                size,
                strength,
                .021,
                2741 + index,
                opacity=.9,
            )
        )
    return result


def static_layers(size):
    layers = []
    for index in range(3):
        layers.append(
            DepthLayer(
                f"letter_{index}_paper",
                _letter_image(size, index, 1.0, PAPER, .037),
                10 + index,
            )
        )
    top, bottom = _heart_paths(size, 0.0)
    layers.extend(
        (
            DepthLayer("heart_top", _stroke(top, size, 1.0, .050, 2731), 20),
            DepthLayer(
                "heart_bottom", _stroke(bottom, size, 1.0, .050, 2737), 21
            ),
        )
    )
    return layers


def draw_static_frame(size):
    return compose_depth(static_layers(size))


def draw_frame(frame, size):
    if frame <= 0 or frame >= 41:
        return canvas(size)
    return compose_depth(
        [
            DepthLayer(
                "letter_i_paper",
                _letter_layer(frame, size, 0, "letters", PAPER, .037),
                10,
            ),
            DepthLayer(
                "letter_r_paper",
                _letter_layer(frame, size, 1, "letters", PAPER, .037),
                11,
            ),
            DepthLayer(
                "letter_a_paper",
                _letter_layer(frame, size, 2, "letters", PAPER, .037),
                12,
            ),
            DepthLayer("heart_top", _heart_layer(frame, size, "top"), 20),
            DepthLayer("heart_bottom", _heart_layer(frame, size, "bottom"), 21),
            DepthLayer("closure_accents", _closure_layer(frame, size), 30),
        ]
    )


SPEC = FrameMotionSpec(
    "27-ira-heart",
    draw_frame,
    duration_frames=42,
    tags=("soft", "tactile"),
)
