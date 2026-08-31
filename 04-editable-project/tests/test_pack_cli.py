from pathlib import Path

from PIL import Image


def test_review_creates_100px_dark_light_and_keyframe_boards(tmp_path: Path):
    from pack import create_review_boards

    outputs = create_review_boards(("20-check", "22-favorite"), tmp_path)
    assert set(outputs) == {"static_dark", "static_light", "keyframes"}
    for path in outputs.values():
        assert path.is_file()
        with Image.open(path) as image:
            assert image.mode == "RGBA"
            assert image.width >= 100
            assert image.height >= 100


def test_review_static_icon_uses_the_same_source_as_release_static():
    from pack import ROOT, _static_icon

    with Image.open(ROOT / "masters" / "01-heart.png") as master:
        expected = master.convert("RGBA").resize((100, 100), Image.Resampling.LANCZOS)
    assert _static_icon("01-heart").tobytes() == expected.tobytes()


def test_release_sync_replaces_only_declared_generated_directories(tmp_path: Path):
    from pack import sync_release_outputs

    stage = tmp_path / "stage"
    workspace = tmp_path / "workspace"
    (stage / "01-ready-to-upload" / "animated-tgs").mkdir(parents=True)
    (stage / "01-ready-to-upload" / "animated-tgs" / "new.tgs").write_text("new")
    (workspace / "01-ready-to-upload" / "animated-tgs").mkdir(parents=True)
    (workspace / "01-ready-to-upload" / "animated-tgs" / "old.tgs").write_text("old")
    (workspace / "04-editable-project").mkdir(parents=True)
    (workspace / "04-editable-project" / "source.py").write_text("keep")

    sync_release_outputs(stage, workspace, ("01-ready-to-upload",))

    assert (workspace / "01-ready-to-upload" / "animated-tgs" / "new.tgs").is_file()
    assert not (workspace / "01-ready-to-upload" / "animated-tgs" / "old.tgs").exists()
    assert (workspace / "04-editable-project" / "source.py").read_text() == "keep"


def test_workspace_checksums_exclude_git_metadata(tmp_path: Path):
    from pack import write_workspace_checksums

    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "HEAD").write_text("private metadata")
    (tmp_path / "visible.txt").write_text("release file")

    checksum_file = write_workspace_checksums(tmp_path)

    text = checksum_file.read_text(encoding="utf-8")
    assert "visible.txt" in text
    assert ".git/HEAD" not in text
