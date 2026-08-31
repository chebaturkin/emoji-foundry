import pytest

from frame_core.retime import retime_draw, virtual_frame


def test_virtual_frame_locks_source_endpoints():
    assert virtual_frame(0, 48) == 0
    assert virtual_frame(47, 48) == 59


def test_virtual_frame_is_monotonic_across_target_timeline():
    mapped = [virtual_frame(frame, 48) for frame in range(48)]
    assert mapped == sorted(mapped)


@pytest.mark.parametrize(
    ("frame", "target_frames", "source_frames"),
    [
        (0, 1, 60),
        (0, 48, 1),
        (-1, 48, 60),
        (48, 48, 60),
    ],
)
def test_virtual_frame_rejects_invalid_timelines_and_frame_ranges(
    frame, target_frames, source_frames
):
    with pytest.raises(ValueError):
        virtual_frame(frame, target_frames, source_frames)


def test_retime_draw_calls_author_draw_with_virtual_frame():
    calls = []

    def draw_frame(frame, size):
        calls.append((frame, size))
        return "frame"

    draw_retimed = retime_draw(draw_frame, target_frames=48)

    assert draw_retimed(24, 400) == "frame"
    assert calls == [(30, 400)]
