import math


def ease(name: str, t: float) -> float:
    t = min(1.0, max(0.0, t))
    if name == "linear":
        return t
    if name == "smooth":
        return t * t * (3.0 - 2.0 * t)
    if name == "in_out_sine":
        return -(math.cos(math.pi * t) - 1.0) / 2.0
    if name == "out_back":
        if t in (0.0, 1.0):
            return t
        c1, c3 = 1.70158, 2.70158
        return 1.0 + c3 * (t - 1.0) ** 3 + c1 * (t - 1.0) ** 2
    raise ValueError(f"unknown easing: {name}")
