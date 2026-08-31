from functools import wraps

from frame_core.models import DrawFrame


def virtual_frame(frame: int, target_frames: int, source_frames: int = 60) -> int:
    if target_frames < 2:
        raise ValueError("target_frames must be at least 2")
    if source_frames < 2:
        raise ValueError("source_frames must be at least 2")
    if frame < 0 or frame >= target_frames:
        raise ValueError(f"frame must be between 0 and {target_frames - 1}")
    return round(frame * (source_frames - 1) / (target_frames - 1))


def retime_draw(
    draw_frame: DrawFrame, target_frames: int, source_frames: int = 60
) -> DrawFrame:
    @wraps(draw_frame)
    def draw_retimed(frame: int, size: int):
        mapped_frame = virtual_frame(frame, target_frames, source_frames)
        return draw_frame(mapped_frame, size)

    return draw_retimed
