from fractions import Fraction
from pathlib import Path

import numpy as np
from PIL import Image

import build_batch_qa
from build_batch_qa import CELL_WIDTH, HEADER_HEIGHT, LABEL_WIDTH, ROW_HEIGHT, build_sheet


def write_indexed_frames(root: Path, stem: str, frame_count: int) -> None:
    frame_dir = root / stem
    frame_dir.mkdir(parents=True)
    for index in range(frame_count):
        Image.new("RGBA", (100, 100), (index, 0, 0, 255)).save(
            frame_dir / f"frame-{index:03d}.png"
        )


def test_keyframe_fractions_and_duration_mapping_cover_exact_endpoints():
    assert build_batch_qa.KEYFRAME_FRACTIONS == tuple(
        Fraction(index, 8) for index in range(9)
    )
    assert build_batch_qa.keyframe_indices(42) == (
        0, 5, 10, 15, 20, 26, 31, 36, 41,
    )
    assert build_batch_qa.keyframe_indices(48) == (
        0, 6, 12, 18, 24, 29, 35, 41, 47,
    )
    assert build_batch_qa.keyframe_indices(60) == (
        0, 7, 15, 22, 30, 37, 44, 52, 59,
    )


def test_batch_qa_reads_real_mixed_42_and_48_frame_directories(
    monkeypatch, tmp_path: Path
):
    frames_root = tmp_path / "frames"
    write_indexed_frames(frames_root, "12-smile", 48)
    write_indexed_frames(frames_root, "01-heart", 48)
    monkeypatch.setattr(build_batch_qa, "FRAMES", frames_root)
    monkeypatch.setattr(build_batch_qa, "STEMS", ("12-smile", "01-heart"))

    output = build_sheet(
        build_batch_qa.DARK,
        build_batch_qa.PAPER,
        tmp_path / "mixed.png",
    )

    expected_by_row = (
        build_batch_qa.keyframe_indices(48),
        build_batch_qa.keyframe_indices(48),
    )
    with Image.open(output) as sheet:
        for row, expected_indices in enumerate(expected_by_row):
            y = HEADER_HEIGHT + row * ROW_HEIGHT + 1
            for column, expected_index in enumerate(expected_indices):
                x = LABEL_WIDTH + column * CELL_WIDTH + 1
                assert sheet.getpixel((x, y))[:3] == (expected_index, 0, 0)


def test_faces_redesign_qa_uses_four_proportional_samples(monkeypatch, tmp_path: Path):
    frames_root = tmp_path / "frames"
    for stem in build_batch_qa.FACES_REDESIGN_STEMS:
        write_indexed_frames(frames_root, stem, 48)
    monkeypatch.setattr(build_batch_qa, "FRAMES", frames_root)
    calls = []
    original_load = build_batch_qa.load_frame
    def record_load(stem, index):
        calls.append((stem, index))
        return original_load(stem, index)
    monkeypatch.setattr(build_batch_qa, "load_frame", record_load)
    output = build_batch_qa.build_faces_redesign_sheet(
        build_batch_qa.DARK, build_batch_qa.PAPER, tmp_path / "faces.png"
    )
    assert output.exists()
    assert len(build_batch_qa.FACES_REDESIGN_FRACTIONS) == 4
    expected = [
        (stem, round(fraction * 47))
        for stem in build_batch_qa.FACES_REDESIGN_STEMS
        for fraction in build_batch_qa.FACES_REDESIGN_FRACTIONS
    ]
    assert calls == expected


def test_faces_redesign_contact_places_samples_in_all_four_columns(monkeypatch, tmp_path: Path):
    frames_root = tmp_path / "frames"
    for stem in build_batch_qa.FACES_REDESIGN_STEMS:
        write_indexed_frames(frames_root, stem, 48)
    monkeypatch.setattr(build_batch_qa, "FRAMES", frames_root)
    output = build_batch_qa.build_faces_redesign_contact(tmp_path / "faces.gif")
    with Image.open(output) as animation:
        animation.seek(0)
        image = animation.convert("RGB")
        background = np.asarray(build_batch_qa.DARK[:3])
        for column in range(4):
            x0 = build_batch_qa.LABEL_WIDTH + column * build_batch_qa.CELL_WIDTH
            region = np.asarray(image)[build_batch_qa.HEADER_HEIGHT:, x0:x0 + build_batch_qa.FRAME_SIZE]
            assert np.any(np.any(region != background, axis=2)), column


def test_hands_redesign_qa_uses_exact_proportional_samples(monkeypatch, tmp_path: Path):
    frames_root = tmp_path / "frames"
    for stem in build_batch_qa.HANDS_REDESIGN_STEMS:
        write_indexed_frames(frames_root, stem, 48 if stem != "20-check" else 42)
    monkeypatch.setattr(build_batch_qa, "FRAMES", frames_root)
    calls = []
    original_load = build_batch_qa.load_frame

    def record_load(stem, index):
        calls.append((stem, index))
        return original_load(stem, index)

    monkeypatch.setattr(build_batch_qa, "load_frame", record_load)
    output = build_batch_qa.build_hands_redesign_sheet(
        build_batch_qa.DARK,
        build_batch_qa.PAPER,
        tmp_path / "hands.png",
    )

    expected = [
        (stem, round(fraction * (build_batch_qa.SPECS[stem].duration_frames - 1)))
        for stem in build_batch_qa.HANDS_REDESIGN_STEMS
        for fraction in build_batch_qa.HANDS_REDESIGN_FRACTIONS
    ]
    assert output.exists()
    assert calls == expected


def test_hands_redesign_contact_places_samples_in_all_four_columns(monkeypatch, tmp_path: Path):
    frames_root = tmp_path / "frames"
    for stem in build_batch_qa.HANDS_REDESIGN_STEMS:
        write_indexed_frames(frames_root, stem, 48 if stem != "20-check" else 42)
    monkeypatch.setattr(build_batch_qa, "FRAMES", frames_root)

    output = build_batch_qa.build_hands_redesign_contact(tmp_path / "hands.gif")

    with Image.open(output) as animation:
        animation.seek(0)
        image = animation.convert("RGB")
        background = np.asarray(build_batch_qa.DARK[:3])
        for column in range(4):
            x0 = build_batch_qa.LABEL_WIDTH + column * build_batch_qa.CELL_WIDTH
            region = np.asarray(image)[
                build_batch_qa.HEADER_HEIGHT:,
                x0:x0 + build_batch_qa.FRAME_SIZE,
            ]
            assert np.any(np.any(region != background, axis=2)), column


def test_energy_redesign_qa_uses_exact_proportional_samples(monkeypatch, tmp_path: Path):
    frames_root = tmp_path / "frames"
    for stem in build_batch_qa.ENERGY_REDESIGN_STEMS:
        write_indexed_frames(
            frames_root, stem, build_batch_qa.SPECS[stem].duration_frames
        )
    monkeypatch.setattr(build_batch_qa, "FRAMES", frames_root)
    calls = []
    original_load = build_batch_qa.load_frame

    def record_load(stem, index):
        calls.append((stem, index))
        return original_load(stem, index)

    monkeypatch.setattr(build_batch_qa, "load_frame", record_load)
    output = build_batch_qa.build_energy_redesign_sheet(
        build_batch_qa.DARK, build_batch_qa.PAPER, tmp_path / "energy.png"
    )
    expected = [
        (stem, round(fraction * (build_batch_qa.SPECS[stem].duration_frames - 1)))
        for stem in build_batch_qa.ENERGY_REDESIGN_STEMS
        for fraction in build_batch_qa.ENERGY_REDESIGN_FRACTIONS
    ]
    assert output.exists()
    assert calls == expected


def test_story_redesign_qa_uses_exact_proportional_samples(monkeypatch, tmp_path: Path):
    frames_root = tmp_path / "frames"
    for stem in build_batch_qa.STORY_REDESIGN_STEMS:
        write_indexed_frames(
            frames_root, stem, build_batch_qa.SPECS[stem].duration_frames
        )
    monkeypatch.setattr(build_batch_qa, "FRAMES", frames_root)
    calls = []
    original_load = build_batch_qa.load_frame

    def record_load(stem, index):
        calls.append((stem, index))
        return original_load(stem, index)

    monkeypatch.setattr(build_batch_qa, "load_frame", record_load)
    output = build_batch_qa.build_story_redesign_sheet(
        build_batch_qa.DARK, build_batch_qa.PAPER, tmp_path / "story.png"
    )
    expected = [
        (stem, round(fraction * (build_batch_qa.SPECS[stem].duration_frames - 1)))
        for stem in build_batch_qa.STORY_REDESIGN_STEMS
        for fraction in build_batch_qa.STORY_REDESIGN_FRACTIONS
    ]
    assert output.exists()
    assert calls == expected
