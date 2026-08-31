from dataclasses import replace
from pathlib import Path

import pytest
import numpy as np
from PIL import Image

import build_all
from build_all import build_contact_sheet, save_individual_preview, select_specs
from frame_core.models import FrameMotionSpec
from motion_core.render import render_motion
from motions.registry import SPECS


EXPECTED_GROUP_STEMS = {
    "soft": [
        "01-heart",
        "02-heart-double",
        "03-heart-open",
        "12-smile",
        "13-laugh",
        "14-sad",
        "15-surprise",
        "16-like",
        "17-dislike",
        "22-favorite",
        "27-ira-heart",
    ],
    "impact": [
        "04-star",
        "05-star-four",
        "06-spark",
        "07-lightning",
        "08-lightning-round",
        "24-explosion-ray",
        "25-explosion-cloud",
        "26-explosion-ring",
    ],
    "story": [
        "09-idea",
        "10-bulb-spark",
        "11-eye",
        "18-question",
        "19-exclamation",
        "20-check",
        "21-cross",
        "23-launch",
    ],
    "pilot": [
        "03-heart-open",
        "07-lightning",
        "10-bulb-spark",
        "13-laugh",
        "25-explosion-cloud",
    ],
}

BATCH1_STEMS = {
    "01-heart",
    "04-star",
    "06-spark",
    "09-idea",
    "11-eye",
    "12-smile",
    "14-sad",
}
NATIVE_42_STEMS = {"27-ira-heart"}
BATCH2_STEMS = {
    "15-surprise", "16-like", "17-dislike", "18-question",
    "19-exclamation", "20-check", "21-cross",
}
BATCH3_STEMS = {
    "02-heart-double", "05-star-four", "08-lightning-round", "22-favorite",
    "23-launch", "24-explosion-ray", "26-explosion-ring",
}
PERSONAL_STEMS = {"27-ira-heart"}
NATIVE_42_STEMS |= (
    BATCH2_STEMS - {"15-surprise", "16-like", "17-dislike"}
) | (BATCH3_STEMS - {"24-explosion-ray", "26-explosion-ring", "05-star-four"}) | PERSONAL_STEMS
RETIMED_48_STEMS = (BATCH1_STEMS - NATIVE_42_STEMS) | {
    "15-surprise", "16-like", "17-dislike", "23-launch", "24-explosion-ray",
    "26-explosion-ring", "05-star-four", "22-favorite",
}
NATIVE_42_STEMS -= {"23-launch", "22-favorite"}


def assert_exact_group_membership():
    for group, expected_stems in EXPECTED_GROUP_STEMS.items():
        assert [spec.stem for spec in select_specs(group)] == expected_stems


def test_select_specs_supports_groups_and_single_stem():
    assert len(select_specs("all")) == 27
    assert_exact_group_membership()
    assert [spec.stem for spec in select_specs("01-heart")] == ["01-heart"]


def test_exact_group_membership_rejects_balanced_tag_move(monkeypatch):
    heart = SPECS["01-heart"]
    star = SPECS["04-star"]
    monkeypatch.setitem(
        SPECS,
        "01-heart",
        replace(heart, tags=tuple(tag for tag in heart.tags if tag != "soft")),
    )
    monkeypatch.setitem(
        SPECS,
        "04-star",
        replace(star, tags=star.tags + ("soft",)),
    )

    assert len(select_specs("soft")) == len(EXPECTED_GROUP_STEMS["soft"])
    with pytest.raises(AssertionError):
        assert_exact_group_membership()


def test_select_specs_supports_batch1_group():
    expected_stems = [
        "01-heart", "04-star", "06-spark", "09-idea",
        "11-eye", "12-smile", "14-sad",
    ]
    selected_stems = [spec.stem for spec in select_specs("batch1")]
    tagged_stems = [
        spec.stem for spec in SPECS.values() if "batch1" in spec.tags
    ]
    assert selected_stems == expected_stems
    assert selected_stems == tagged_stems


def test_select_specs_supports_batch2_group():
    assert [spec.stem for spec in select_specs("batch2")] == sorted(BATCH2_STEMS)


def test_select_specs_supports_batch3_group():
    expected = [stem for stem in SPECS if stem in BATCH3_STEMS]
    assert [spec.stem for spec in select_specs("batch3")] == expected


def test_new_specs_keep_their_authored_durations_and_legacy_specs_keep_60():
    durations = {stem: spec.duration_frames for stem, spec in SPECS.items()}
    assert {stem for stem, duration in durations.items() if duration == 42} == NATIVE_42_STEMS
    assert {stem for stem, duration in durations.items() if duration == 48} == RETIMED_48_STEMS
    assert all(
        duration == 60
        for stem, duration in durations.items()
        if stem not in BATCH1_STEMS | BATCH2_STEMS | BATCH3_STEMS | PERSONAL_STEMS
    )


def test_future_frame_motion_default_is_native_42_frames():
    spec = FrameMotionSpec(
        "future",
        lambda frame, size: Image.new("RGBA", (size, size)),
    )

    assert spec.duration_frames == 42


def test_render_motion_keeps_batch1_specs_readable_at_their_authored_duration():
    for stem in sorted(BATCH1_STEMS):
        spec = SPECS[stem]
        frames = render_motion(spec)
        assert len(frames) == spec.duration_frames, stem
        assert frames[0].getchannel("A").getbbox() is None, stem
        assert frames[-1].getchannel("A").getbbox() is None, stem

        middle_bbox = frames[spec.duration_frames // 2].getchannel("A").getbbox()
        assert middle_bbox is not None, stem
        assert middle_bbox[2] - middle_bbox[0] >= 20, stem
        assert middle_bbox[3] - middle_bbox[1] >= 20, stem


def test_select_specs_rejects_unknown_name():
    with pytest.raises(ValueError, match="unknown selection"):
        select_specs("missing")


def test_select_specs_accepts_multiple_explicit_stems():
    assert [spec.stem for spec in select_specs("20-check,22-favorite")] == [
        "20-check", "22-favorite"
    ]


def test_registry_replaces_all_legacy_specs():
    pilot = {
        "07-lightning",
        "13-laugh",
        "03-heart-open",
        "25-explosion-cloud",
        "10-bulb-spark",
    }
    frame_motion_stems = {
        stem for stem, spec in SPECS.items() if isinstance(spec, FrameMotionSpec)
    }
    assert frame_motion_stems == set(SPECS)
    assert pilot <= frame_motion_stems
    assert len(SPECS) == 27


def write_indexed_frames(root: Path, stem: str, count: int, channel: int) -> None:
    frame_dir = root / stem
    frame_dir.mkdir(parents=True)
    for index in range(count):
        color = [0, 0, 0, 255]
        color[channel] = index * 4
        Image.new("RGBA", (100, 100), tuple(color)).save(
            frame_dir / f"frame-{index:03d}.png"
        )


def gif_durations(path: Path) -> list[int]:
    with Image.open(path) as animation:
        durations = []
        for frame_index in range(animation.n_frames):
            animation.seek(frame_index)
            durations.append(animation.info["duration"])
    return durations


@pytest.mark.parametrize(("frame_count", "expected_total_ms"), [(48, 1600), (60, 2000)])
def test_individual_preview_preserves_30_fps_timeline(
    monkeypatch,
    tmp_path: Path,
    frame_count: int,
    expected_total_ms: int,
):
    frames = [
        Image.new("RGBA", (100, 100), (index * 4, 0, 0, 255))
        for index in range(frame_count)
    ]
    monkeypatch.setattr(build_all, "INDIVIDUAL", tmp_path / "individual")

    output = save_individual_preview("demo", frames)

    durations = gif_durations(output)
    assert len(durations) == frame_count
    assert set(durations) <= {30, 40}
    assert sum(durations) == expected_total_ms


def test_individual_preview_preserves_identical_frames_without_visible_marker(
    monkeypatch, tmp_path: Path
):
    frames = [Image.new("RGBA", (100, 100), (0, 0, 0, 0)) for _ in range(42)]
    monkeypatch.setattr(build_all, "INDIVIDUAL", tmp_path / "individual")

    output = save_individual_preview("identical", frames)

    with Image.open(output) as animation:
        assert animation.n_frames == 42
        for frame_index in range(animation.n_frames):
            animation.seek(frame_index)
            assert animation.convert("RGBA").getpixel((199, 199)) == build_all.BACKGROUND
    assert sum(gif_durations(output)) == 1400


def test_start_with_strongest_frame_rotates_loop_without_dropping_frames():
    empty = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    small = empty.copy()
    small.putpixel((50, 50), (242, 240, 233, 128))
    strong = empty.copy()
    for x in range(40, 60):
        for y in range(40, 60):
            strong.putpixel((x, y), (242, 240, 233, 255))

    rotated = build_all.start_with_strongest_frame([empty, small, strong])

    assert rotated == [strong, empty, small]


def test_preview_only_individual_rebuild_reads_saved_frames_without_render_or_encode(
    monkeypatch, tmp_path: Path
):
    frames_root = tmp_path / "frames"
    write_indexed_frames(frames_root, "saved", 42, 0)
    spec = FrameMotionSpec(
        "saved",
        lambda frame, size: Image.new("RGBA", (size, size)),
        duration_frames=42,
    )
    monkeypatch.setattr(build_all, "FRAMES", frames_root)
    monkeypatch.setattr(build_all, "INDIVIDUAL", tmp_path / "individual")
    monkeypatch.setattr(
        build_all,
        "render_motion",
        lambda spec: pytest.fail("preview-only rebuild rendered source art"),
    )
    monkeypatch.setattr(
        build_all,
        "encode_webm",
        lambda frames, output: pytest.fail("preview-only rebuild encoded WebM"),
    )

    outputs = build_all.build_individual_previews([spec])

    assert [output.name for output in outputs] == ["saved.gif"]
    with Image.open(outputs[0]) as animation:
        assert animation.n_frames == 42
    assert sum(gif_durations(outputs[0])) == 1400


def test_group_specs_by_duration_preserves_duration_and_registry_order():
    grouped = build_all.group_specs_by_duration(select_specs("all"))

    assert list(grouped) == [42, 48, 60]
    assert [spec.stem for spec in grouped[42]] == [
        "02-heart-double", "08-lightning-round", "18-question",
        "19-exclamation", "20-check", "21-cross", "27-ira-heart",
    ]
    assert [spec.stem for spec in grouped[48]] == [
        "01-heart", "04-star", "05-star-four", "06-spark", "09-idea",
        "11-eye", "12-smile", "14-sad", "15-surprise", "16-like",
        "17-dislike", "22-favorite", "23-launch", "24-explosion-ray",
        "26-explosion-ring",
    ]
    assert [spec.stem for spec in grouped[60]] == [
            stem for stem in SPECS
            if stem not in BATCH1_STEMS | BATCH2_STEMS | BATCH3_STEMS | PERSONAL_STEMS
        ]


def test_mixed_contact_sheets_split_by_exact_duration_with_no_tempo_mapping(
    monkeypatch, tmp_path: Path
):
    frames_root = tmp_path / "frames"
    previews_root = tmp_path / "previews"
    specs = []
    for channel, frame_count in enumerate((42, 48, 60)):
        stem = f"duration-{frame_count}"
        write_indexed_frames(frames_root, stem, frame_count, channel)
        specs.append(
            FrameMotionSpec(
                stem,
                lambda frame, size: Image.new("RGBA", (size, size)),
                duration_frames=frame_count,
            )
        )
    monkeypatch.setattr(build_all, "FRAMES", frames_root)
    monkeypatch.setattr(build_all, "PREVIEWS", previews_root)

    outputs = build_all.build_contact_sheets(specs, "mixed")

    assert [output.name for output in outputs] == [
        "contact-sheet-mixed-42.gif",
        "contact-sheet-mixed-48.gif",
        "contact-sheet-mixed-60.gif",
    ]
    for channel, (frame_count, expected_total_ms) in enumerate(
        ((42, 1400), (48, 1600), (60, 2000))
    ):
        output = previews_root / f"contact-sheet-mixed-{frame_count}.gif"
        with Image.open(output) as sheet:
            assert sheet.n_frames == frame_count
            assert sheet.info["loop"] == 0
            for output_index in (0, frame_count // 2, frame_count - 1):
                sheet.seek(output_index)
                expected_rgb = [0, 0, 0]
                expected_rgb[channel] = output_index * 4
                assert sheet.convert("RGBA").getpixel((20, 20))[:3] == tuple(
                    expected_rgb
                )
        assert sum(gif_durations(output)) == expected_total_ms


def test_supported_mixed_sheet_cleanup_has_explicit_inventory(
    monkeypatch, tmp_path: Path
):
    assert build_all.OBSOLETE_MIXED_CONTACT_SHEETS == {
        "all": "contact-sheet.gif",
        "batch1": "contact-sheet-batch1.gif",
        "soft": "contact-sheet-soft.gif",
        "impact": "contact-sheet-impact.gif",
        "story": "contact-sheet-story.gif",
    }

    frames_root = tmp_path / "frames"
    previews_root = tmp_path / "previews"
    write_indexed_frames(frames_root, "short", 42, 0)
    write_indexed_frames(frames_root, "long", 48, 1)
    specs = [
        FrameMotionSpec(
            "short",
            lambda frame, size: Image.new("RGBA", (size, size)),
            duration_frames=42,
        ),
        FrameMotionSpec(
            "long",
            lambda frame, size: Image.new("RGBA", (size, size)),
            duration_frames=48,
        ),
    ]
    previews_root.mkdir()
    obsolete = previews_root / "contact-sheet.gif"
    unrelated = previews_root / "contact-sheet-user-review.gif"
    obsolete.write_bytes(b"obsolete")
    unrelated.write_bytes(b"keep")
    monkeypatch.setattr(build_all, "FRAMES", frames_root)
    monkeypatch.setattr(build_all, "PREVIEWS", previews_root)

    outputs = build_all.build_contact_sheets(specs, "all")

    assert [output.name for output in outputs] == [
        "contact-sheet-all-42.gif",
        "contact-sheet-all-48.gif",
    ]
    assert not obsolete.exists()
    assert unrelated.read_bytes() == b"keep"


@pytest.mark.parametrize(
    ("frame_count", "expected_total_ms"),
    [(48, 1600), (60, 2000)],
)
def test_contact_sheet_preserves_homogeneous_timeline(
    monkeypatch,
    tmp_path: Path,
    frame_count: int,
    expected_total_ms: int,
):
    frames_root = tmp_path / "frames"
    previews_root = tmp_path / "previews"
    write_indexed_frames(frames_root, "same", frame_count, 0)
    same = FrameMotionSpec(
        "same",
        lambda frame, size: Image.new("RGBA", (size, size)),
        duration_frames=frame_count,
    )
    monkeypatch.setattr(build_all, "FRAMES", frames_root)
    monkeypatch.setattr(build_all, "PREVIEWS", previews_root)

    output = build_contact_sheet([same], "homogeneous")

    with Image.open(output) as sheet:
        assert sheet.n_frames == frame_count
        sheet.seek(0)
        assert sheet.convert("RGBA").getpixel((20, 20))[:3] == (0, 0, 0)
        sheet.seek(frame_count - 1)
        assert sheet.convert("RGBA").getpixel((20, 20))[:3] == (
            (frame_count - 1) * 4,
            0,
            0,
        )
    assert sum(gif_durations(output)) == expected_total_ms


def test_contact_sheet_preserves_identical_frames_at_native_count(
    monkeypatch, tmp_path: Path
):
    frames_root = tmp_path / "frames"
    previews_root = tmp_path / "previews"
    frame_dir = frames_root / "same"
    frame_dir.mkdir(parents=True)
    for index in range(42):
        Image.new("RGBA", (100, 100), (0, 0, 0, 0)).save(
            frame_dir / f"frame-{index:03d}.png"
        )
    same = FrameMotionSpec(
        "same",
        lambda frame, size: Image.new("RGBA", (size, size)),
        duration_frames=42,
    )
    monkeypatch.setattr(build_all, "FRAMES", frames_root)
    monkeypatch.setattr(build_all, "PREVIEWS", previews_root)

    output = build_contact_sheet([same], "same")

    with Image.open(output) as animation:
        assert animation.n_frames == 42
        assert animation.convert("RGBA").getpixel(
            (animation.width - 1, animation.height - 1)
        ) == build_all.BACKGROUND
    assert sum(gif_durations(output)) == 1400


def test_contact_sheet_rejects_mixed_durations_without_split():
    short = FrameMotionSpec(
        "short",
        lambda frame, size: Image.new("RGBA", (size, size)),
        duration_frames=42,
    )
    long = replace(short, stem="long", duration_frames=48)

    with pytest.raises(ValueError, match="build_contact_sheets"):
        build_contact_sheet([short, long], "mixed")


def test_live_individual_gifs_match_saved_frames_and_exact_timelines():
    if not build_all.FRAMES.exists() or not build_all.INDIVIDUAL.exists():
        pytest.skip("generated individual previews are not built yet")
    approved_rendered = {
        stem: build_all.start_with_strongest_frame(render_motion(SPECS[stem]))
        for stem in sorted(RETIMED_48_STEMS)
    }
    for spec in SPECS.values():
        output = build_all.INDIVIDUAL / f"{spec.stem}.gif"
        with Image.open(output) as animation:
            assert animation.n_frames == spec.duration_frames, spec.stem
            durations = []
            for frame_index in range(animation.n_frames):
                animation.seek(frame_index)
                durations.append(animation.info["duration"])
                actual = np.asarray(
                    animation.convert("RGB"),
                    dtype=np.int16,
                )
                with Image.open(
                    build_all.FRAMES
                    / spec.stem
                    / f"frame-{frame_index:03d}.png"
                ) as source:
                    saved_frame = source.convert("RGBA")
                    if spec.stem in approved_rendered:
                        assert np.array_equal(
                            np.asarray(saved_frame),
                            np.asarray(approved_rendered[spec.stem][frame_index]),
                        ), (spec.stem, frame_index)
                    canvas = Image.new("RGBA", (200, 200), build_all.BACKGROUND)
                    canvas.alpha_composite(
                        saved_frame.resize(
                            (160, 160),
                            Image.Resampling.NEAREST,
                        ),
                        (20, 20),
                    )
                expected = np.asarray(canvas.convert("RGB"), dtype=np.int16)
                difference = np.abs(actual - expected)
                assert difference.mean() <= 4.0, (spec.stem, frame_index)
                assert np.quantile(difference, 0.99) <= 8, (
                    spec.stem,
                    frame_index,
                )
            assert sum(durations) == round(
                spec.duration_frames / spec.fps * 1000
            ), spec.stem
