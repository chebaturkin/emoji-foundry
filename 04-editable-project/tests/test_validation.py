from pathlib import Path

from PIL import Image

from motion_core.encode import VideoInfo
from motions.registry import SPECS
from validate_animated import resolve_stems, validate_frame_directory, validate_pack, validate_webm


def test_validator_resolves_pilot_and_comma_selections():
    assert len(resolve_stems("pilot")) == 5
    assert resolve_stems("07-lightning,03-heart-open") == ["07-lightning", "03-heart-open"]


def test_validator_resolves_batch1_group():
    assert resolve_stems("batch1") == [
        "01-heart", "04-star", "06-spark", "09-idea",
        "11-eye", "12-smile", "14-sad",
    ]


def test_validator_resolves_batch2_group():
    assert resolve_stems("batch2") == [
        "15-surprise", "16-like", "17-dislike", "18-question",
        "19-exclamation", "20-check", "21-cross",
    ]


def test_validator_resolves_batch3_group():
    assert resolve_stems("batch3") == [
        "02-heart-double", "05-star-four", "08-lightning-round",
        "22-favorite", "23-launch", "24-explosion-ray", "26-explosion-ring",
    ]


def test_frame_validator_accepts_60_safe_rgba_frames(tmp_path: Path):
    frame_dir = tmp_path / "demo"
    frame_dir.mkdir()
    for index in range(60):
        image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        for x in range(20, 80):
            for y in range(20, 80):
                image.putpixel((x, y), (242, 240, 233, 255))
        image.save(frame_dir / f"frame-{index:03d}.png")
    assert validate_frame_directory(frame_dir) == []


def test_frame_validator_accepts_exact_configured_frame_count(tmp_path: Path):
    frame_dir = tmp_path / "demo"
    frame_dir.mkdir()
    for index in range(48):
        frame = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        if index == 0:
            frame.putpixel((50, 50), (242, 240, 233, 255))
        frame.save(frame_dir / f"frame-{index:03d}.png")

    assert validate_frame_directory(frame_dir, expected_frames=48) == []
    assert validate_frame_directory(frame_dir) == ["expected 60 frames, found 48"]


def test_frame_validator_rejects_content_outside_safe_area(tmp_path: Path):
    frame_dir = tmp_path / "demo"
    frame_dir.mkdir()
    for index in range(60):
        image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        image.putpixel((3, 50), (242, 240, 233, 255))
        image.save(frame_dir / f"frame-{index:03d}.png")
    issues = validate_frame_directory(frame_dir)
    assert any("safe area" in issue for issue in issues)


def test_frame_validator_ignores_invisible_resampling_bleed(tmp_path: Path):
    frame_dir = tmp_path / "demo"
    frame_dir.mkdir()
    for index in range(60):
        image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        image.putpixel((5, 50), (242, 240, 233, 5))
        if index == 0:
            image.putpixel((50, 50), (242, 240, 233, 255))
        image.save(frame_dir / f"frame-{index:03d}.png")
    assert validate_frame_directory(frame_dir) == []


def test_frame_validator_requires_visible_first_frame_for_telegram_thumbnail(tmp_path: Path):
    frame_dir = tmp_path / "demo"
    frame_dir.mkdir()
    Image.new("RGBA", (100, 100), (0, 0, 0, 0)).save(
        frame_dir / "frame-000.png"
    )
    visible = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    visible.putpixel((50, 50), (242, 240, 233, 255))
    visible.save(frame_dir / "frame-001.png")

    issues = validate_frame_directory(frame_dir, expected_frames=2)

    assert "frame 0 must contain visible content for Telegram thumbnail" in issues


def test_webm_validator_enforces_exact_telegram_release_contract(monkeypatch, tmp_path: Path):
    webm = tmp_path / "demo.webm"
    webm.write_bytes(b"x" * (256 * 1024 + 1))
    monkeypatch.setattr(
        "validate_animated.probe_webm",
        lambda path: VideoInfo("vp9", 100, 100, 30.0, 1.9, True, False, 59),
    )

    issues = validate_webm(webm)

    assert any("duration" in issue and "expected 2.0" in issue for issue in issues)
    assert any("frame count" in issue and "expected 60" in issue for issue in issues)
    assert any("limit is 262144" in issue for issue in issues)


def test_webm_validator_derives_duration_from_expected_frame_count(monkeypatch, tmp_path: Path):
    webm = tmp_path / "demo.webm"
    webm.write_bytes(b"valid-size")
    monkeypatch.setattr(
        "validate_animated.probe_webm",
        lambda path: VideoInfo("vp9", 100, 100, 30.0, 2.0, True, False, 60),
    )

    issues = validate_webm(webm, expected_frames=48)

    assert any("duration" in issue and "expected 1.6" in issue for issue in issues)
    assert any("frame count" in issue and "expected 48" in issue for issue in issues)


def test_webm_validator_accepts_exact_48_frame_contract(monkeypatch, tmp_path: Path):
    webm = tmp_path / "demo.webm"
    webm.write_bytes(b"valid-size")
    monkeypatch.setattr(
        "validate_animated.probe_webm",
        lambda path: VideoInfo("vp9", 100, 100, 30.0, 1.6, True, False, 48),
    )

    assert validate_webm(webm, expected_frames=48) == []


def test_validate_pack_uses_each_specs_duration_for_mixed_all_selection(monkeypatch, tmp_path: Path):
    frame_expectations = {}
    webm_expectations = {}

    def capture_frames(path: Path, expected_frames: int = 60) -> list[str]:
        frame_expectations[path.name] = expected_frames
        return []

    def capture_webm(path: Path, expected_frames: int = 60) -> list[str]:
        webm_expectations[path.stem] = expected_frames
        return []

    monkeypatch.setattr("validate_animated.validate_frame_directory", capture_frames)
    monkeypatch.setattr("validate_animated.validate_webm", capture_webm)

    assert validate_pack(root=tmp_path, stems=None) == {}
    expected = {stem: spec.duration_frames for stem, spec in SPECS.items()}
    assert frame_expectations == expected
    assert webm_expectations == expected
    assert set(expected.values()) == {42, 48, 60}
