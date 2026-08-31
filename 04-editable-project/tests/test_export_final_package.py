from pathlib import Path

import numpy as np
import pytest
from PIL import Image


def test_manifest_has_27_unique_complete_entries():
    from export_final_package import build_manifest

    manifest = build_manifest()
    assert len(manifest["emoji"]) == 27
    assert len({item["stem"] for item in manifest["emoji"]}) == 27
    ira = manifest["emoji"][-1]
    assert ira["stem"] == "27-ira-heart"
    assert ira["static_source"] == "vector_static_renderer"
    assert ira["master"] is None
    assert ira["animated_tgs"] == "01-ready-to-upload/animated-tgs/27-ira-heart.tgs"
    assert ira["tgs_fps"] == 60
    assert ira["tgs_duration_frames"] == 84


def test_manifest_declares_an_explicit_static_source_for_every_emoji():
    from export_final_package import build_manifest

    manifest = build_manifest()
    vector_stems = {
        item["stem"]
        for item in manifest["emoji"]
        if item["static_source"] == "vector_static_renderer"
    }
    assert vector_stems == {"20-check", "22-favorite", "27-ira-heart"}
    for item in manifest["emoji"]:
        assert item["static_source"] in {"master", "vector_static_renderer"}
        if item["static_source"] == "vector_static_renderer":
            assert 0 < item["static_frame"] < item["duration_frames"]


def test_export_refuses_existing_destination(tmp_path: Path):
    from export_final_package import export_package

    destination = tmp_path / "existing"
    destination.mkdir()
    with pytest.raises(FileExistsError, match="already exists"):
        export_package(destination)


def test_expected_layout_is_explicit():
    from export_final_package import EXPECTED_DIRECTORIES

    assert "01-ready-to-upload/animated-webm" in EXPECTED_DIRECTORIES
    assert "01-ready-to-upload/animated-tgs" in EXPECTED_DIRECTORIES
    assert "02-static-png/100x100" in EXPECTED_DIRECTORIES
    assert "04-editable-project/frame_motions" in EXPECTED_DIRECTORIES
    assert "04-editable-project/tgs_core" in EXPECTED_DIRECTORIES
    assert "04-editable-project/tgs_upload" in EXPECTED_DIRECTORIES
    assert "05-ai-handoff" in EXPECTED_DIRECTORIES


def test_static_export_creates_27_transparent_assets_at_both_sizes(tmp_path: Path):
    from export_final_package import export_static_assets

    export_static_assets(tmp_path)
    small = sorted((tmp_path / "100x100").glob("*.png"))
    editable = sorted((tmp_path / "editable-400x400").glob("*.png"))
    assert len(small) == 27
    assert len(editable) == 27
    for path in small:
        with Image.open(path) as image:
            assert image.mode == "RGBA"
            assert image.size == (100, 100)
            assert image.getpixel((0, 0))[3] == 0
    with Image.open(small[-1]) as ira:
        rgba = np.asarray(ira.convert("RGBA"))
    pixels = rgba[:, :, :3].astype(np.int16)
    alpha = rgba[:, :, 3] > 32
    beige = np.all(pixels == np.array((196, 193, 180)), axis=2) & alpha
    paper = (
        np.max(np.abs(pixels - np.array((242, 240, 233))), axis=2) < 20
    ) & alpha
    assert int(np.count_nonzero(beige)) == 0
    assert int(np.count_nonzero(paper)) >= 20


def test_static_check_and_favorite_match_their_redesigned_vector_materials(tmp_path: Path):
    from export_final_package import export_static_assets

    export_static_assets(tmp_path)
    with Image.open(tmp_path / "100x100" / "20-check.png") as check:
        check_pixels = np.asarray(check.convert("RGBA"))
    with Image.open(tmp_path / "100x100" / "22-favorite.png") as favorite:
        favorite_pixels = np.asarray(favorite.convert("RGBA"))
    check_visible = check_pixels[:, :, 3] > 32
    favorite_visible = favorite_pixels[:, :, 3] > 32
    paper = np.array((242, 240, 233))
    blue = np.array((46, 58, 77))
    assert np.any(np.all(check_pixels[:, :, :3] == paper, axis=2) & check_visible)
    assert np.any(np.all(favorite_pixels[:, :, :3] == blue, axis=2) & favorite_visible)
    paper_like = np.max(
        np.abs(favorite_pixels[:, :, :3].astype(np.int16) - paper), axis=2
    ) < 20
    assert np.any(paper_like & favorite_visible)


def test_editable_copy_accepts_precreated_empty_layout_directories(tmp_path: Path):
    from export_final_package import (
        SOURCE_DIRECTORIES,
        SOURCE_FILES,
        _copy_editable_project,
    )

    source = tmp_path / "source"
    stage = tmp_path / "stage"
    for relative in SOURCE_DIRECTORIES:
        directory = source / relative
        directory.mkdir(parents=True)
        (directory / "keep.txt").write_text(relative, encoding="utf-8")
    for relative in SOURCE_FILES:
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative, encoding="utf-8")
    (stage / "04-editable-project" / "frame_core").mkdir(parents=True)

    _copy_editable_project(stage, source)

    assert (
        stage / "04-editable-project" / "frame_core" / "keep.txt"
    ).read_text(encoding="utf-8") == "frame_core"


def test_export_copies_root_agent_guidance(tmp_path: Path):
    from export_final_package import _copy_root_guidance

    package = tmp_path / "package"
    source = package / "04-editable-project"
    stage = tmp_path / "stage"
    source.mkdir(parents=True)
    (package / "AGENTS.md").write_text("project guidance", encoding="utf-8")

    _copy_root_guidance(stage, source)

    assert (stage / "AGENTS.md").read_text(encoding="utf-8") == "project guidance"


def test_export_copies_active_handoff_documents_from_the_workspace(tmp_path: Path):
    from export_final_package import _write_handoff

    source = tmp_path / "package" / "04-editable-project"
    stage = tmp_path / "stage"
    source.mkdir(parents=True)
    handoff = source.parent / "05-ai-handoff"
    handoff.mkdir()
    for name in (
        "START_HERE.md", "AI_EDITING_PROMPT.md", "EDITING_GUIDE.md",
        "PALETTE.md", "CURRENT_STATE.md", "STYLE_SYSTEM.md",
    ):
        (handoff / name).write_text(name, encoding="utf-8")

    _write_handoff(stage, source)

    assert (stage / "05-ai-handoff" / "CURRENT_STATE.md").read_text() == "CURRENT_STATE.md"
    assert (stage / "05-ai-handoff" / "STYLE_SYSTEM.md").read_text() == "STYLE_SYSTEM.md"
