from pathlib import Path
import subprocess

import pytest

from PIL import Image, ImageDraw

import motion_core.encode as encode_module
from motion_core.encode import MAX_WEBM_BYTES, WEBM_CRF, encode_webm, probe_webm


def make_frames(count: int) -> list[Image.Image]:
    frames = []
    for index in range(count):
        image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        midpoint = count / 2
        radius = 10 + round(8 * abs(midpoint - index) / midpoint)
        ImageDraw.Draw(image).ellipse((50 - radius, 50 - radius, 50 + radius, 50 + radius), fill=(242, 240, 233, 255))
        frames.append(image)
    return frames


def test_webm_quality_standard_uses_practical_custom_emoji_upload_gate():
    assert MAX_WEBM_BYTES == 256 * 1024
    assert WEBM_CRF == 4


def fake_ffmpeg_with_sizes(monkeypatch, sizes_by_mode: dict[object, int]) -> list[object]:
    attempted_modes = []

    def run(command, check, capture_output):
        mode = "lossless" if "-lossless" in command else int(command[command.index("-crf") + 1])
        attempted_modes.append(mode)
        Path(command[-1]).write_bytes(
            b"x" * sizes_by_mode.get(mode, MAX_WEBM_BYTES + 1)
        )
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr("motion_core.encode.subprocess.run", run)
    return attempted_modes


def test_encode_webm_starts_lossless_without_retry_when_output_fits(
    monkeypatch, tmp_path: Path
):
    attempted_modes = fake_ffmpeg_with_sizes(monkeypatch, {"lossless": MAX_WEBM_BYTES})

    encode_webm(make_frames(2), tmp_path / "small.webm")

    assert attempted_modes == ["lossless"]


def test_encode_webm_falls_back_to_deterministic_crf_steps_only_if_lossless_is_oversized(
    monkeypatch, tmp_path: Path
):
    attempted_modes = fake_ffmpeg_with_sizes(
        monkeypatch,
        {
            "lossless": MAX_WEBM_BYTES + 3,
            4: MAX_WEBM_BYTES + 2,
            8: MAX_WEBM_BYTES,
        },
    )
    output = tmp_path / "retried.webm"

    encode_webm(make_frames(2), output)

    assert attempted_modes == ["lossless", 4, 8]
    assert output.stat().st_size == MAX_WEBM_BYTES


def test_encode_webm_fails_clearly_after_bounded_crf_retries(
    monkeypatch, tmp_path: Path
):
    attempted_modes = fake_ffmpeg_with_sizes(monkeypatch, {})

    with pytest.raises(
        RuntimeError,
        match=r"WebM remains over 262144 bytes after lossless and CRF 36: 262145 bytes",
    ):
        encode_webm(make_frames(2), tmp_path / "too-large.webm")

    assert attempted_modes == ["lossless", 4, 8, 12, 16, 20, 24, 28, 32, 36]


def test_validator_and_encoder_share_the_practical_upload_size_limit():
    from validate_animated import MAX_WEBM_BYTES as validator_limit

    assert encode_module.MAX_WEBM_BYTES == 256 * 1024
    assert validator_limit is encode_module.MAX_WEBM_BYTES


@pytest.mark.parametrize(("frame_count", "expected_duration"), [(48, 1.6), (60, 2.0)])
def test_encode_webm_preserves_frame_count_at_30_fps(
    tmp_path: Path,
    frame_count: int,
    expected_duration: float,
):
    frames = make_frames(frame_count)
    output = tmp_path / "demo.webm"
    encode_webm(frames, output)
    info = probe_webm(output)
    assert info.codec == "vp9"
    assert info.width == 100 and info.height == 100
    assert info.fps == 30
    assert info.duration == pytest.approx(expected_duration, abs=0.01)
    assert info.frame_count == frame_count
    assert info.has_alpha
    assert not info.has_audio
    assert output.stat().st_size <= MAX_WEBM_BYTES


def test_encode_webm_accepts_arbitrary_nonempty_frame_count(tmp_path: Path):
    output = tmp_path / "seven.webm"

    encode_webm(make_frames(7), output)

    info = probe_webm(output)
    assert info.fps == 30
    assert info.frame_count == 7
    assert info.duration == pytest.approx(7 / 30, abs=0.01)


def test_encode_webm_rejects_empty_frame_list(tmp_path: Path):
    with pytest.raises(ValueError, match="at least one frame"):
        encode_webm([], tmp_path / "empty.webm")


def test_encode_webm_validates_every_frame(tmp_path: Path):
    frames = make_frames(48)
    frames[-1] = Image.new("RGB", (100, 100))

    with pytest.raises(ValueError, match="invalid frame 47: RGB"):
        encode_webm(frames, tmp_path / "invalid.webm")


def test_probe_webm_rejects_failed_decode(monkeypatch, tmp_path: Path):
    failed = subprocess.CompletedProcess([], 1, stdout="", stderr="decode failed")
    monkeypatch.setattr("motion_core.encode.subprocess.run", lambda *args, **kwargs: failed)

    with pytest.raises(RuntimeError, match="decode failed"):
        probe_webm(tmp_path / "broken.webm")
