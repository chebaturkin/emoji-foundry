import runpy
import shutil
import subprocess
import sys
from pathlib import Path

from motions.registry import SPECS
from motions.m15_surprise import SPEC as LEGACY_SURPRISE


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_relocated_module(relative_path: str, tmp_path: Path) -> tuple[dict, Path]:
    relocated_root = tmp_path / "relocated-project"
    destination = relocated_root / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PROJECT_ROOT / relative_path, destination)
    return runpy.run_path(str(destination)), relocated_root


def test_build_root_follows_relocated_script(tmp_path: Path):
    namespace, relocated_root = load_relocated_module("build_all.py", tmp_path)

    assert namespace["ROOT"] == relocated_root


def test_validator_root_follows_relocated_script(tmp_path: Path):
    namespace, relocated_root = load_relocated_module("validate_animated.py", tmp_path)

    assert namespace["ROOT"] == relocated_root


def test_encoder_root_and_ffmpeg_follow_relocated_package(tmp_path: Path):
    namespace, relocated_root = load_relocated_module("motion_core/encode.py", tmp_path)

    assert namespace["ROOT"] == relocated_root
    assert namespace["FFMPEG"] == relocated_root / "tools" / "ffmpeg"


def test_project_contains_exact_master_for_raster_authored_stems():
    masters = PROJECT_ROOT / "masters"

    assert {
        master.name for master in masters.glob("*.png")
    } == {f"{stem}.png" for stem in list(SPECS)[:26]}


def test_relocated_legacy_motion_resolves_and_renders_from_copied_master(
    tmp_path: Path,
):
    relocated_root = tmp_path / "relocated-project"
    for package in ("frame_core", "motion_core", "motions"):
        shutil.copytree(PROJECT_ROOT / package, relocated_root / package)
    relocated_masters = relocated_root / "masters"
    relocated_masters.mkdir()
    source = Path(LEGACY_SURPRISE.source)
    shutil.copy2(source, relocated_masters / source.name)

    program = """
from pathlib import Path
from motion_core.render import render_motion
from motions.m15_surprise import SPEC

expected = Path.cwd() / "masters" / "15-surprise.png"
assert SPEC.source == expected, (SPEC.source, expected)
frames = render_motion(SPEC)
assert len(frames) == 60
assert frames[30].getchannel("A").getbbox() is not None
"""
    completed = subprocess.run(
        [sys.executable, "-c", program],
        cwd=relocated_root,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr


def test_authored_hands_do_not_slice_raster_masters():
    for name in ("m16_like.py", "m17_dislike.py"):
        source = (PROJECT_ROOT / "frame_motions" / name).read_text()
        assert "master_image" not in source
        assert "masked_part" not in source
