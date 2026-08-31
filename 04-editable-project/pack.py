"""High-level workflows for building, reviewing, and releasing the emoji pack."""

import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
from math import ceil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from frame_core.composite import finalize_frame
from motions.registry import SPECS
from pack_registry import ENTRY_BY_STEM, review_frames, select_stems


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
REVIEW_BACKGROUND_DARK = (23, 34, 45, 255)
REVIEW_BACKGROUND_LIGHT = (242, 240, 233, 255)
RELEASE_DIRECTORIES = (
    "01-ready-to-upload",
    "02-static-png",
    "03-previews",
    "05-ai-handoff",
)


def _slug(stems: tuple[str, ...]) -> str:
    return "all" if len(stems) == len(SPECS) else "-".join(stems)


def _static_icon(stem: str) -> Image.Image:
    entry = ENTRY_BY_STEM[stem]
    if entry.static_source == "master":
        with Image.open(ROOT / "masters" / f"{stem}.png") as master:
            return master.convert("RGBA").resize((100, 100), Image.Resampling.LANCZOS)
    return finalize_frame(SPECS[stem].draw_frame(entry.static_frame, 400))


def _keyframe_icon(stem: str, frame: int) -> Image.Image:
    return finalize_frame(SPECS[stem].draw_frame(frame, 400))


def _static_board(
    stems: tuple[str, ...],
    background: tuple[int, int, int, int],
    output: Path,
) -> Path:
    cols, cell, label_height = min(6, len(stems)), 116, 16
    rows = ceil(len(stems) / cols)
    board = Image.new("RGBA", (cols * cell, rows * (100 + label_height)), background)
    draw = ImageDraw.Draw(board)
    font = ImageFont.load_default()
    label = (242, 240, 233, 255) if background[0] < 100 else (46, 58, 77, 255)
    for index, stem in enumerate(stems):
        x = (index % cols) * cell + 8
        y = (index // cols) * (100 + label_height)
        board.alpha_composite(_static_icon(stem), (x, y))
        draw.text((x + 1, y + 100), stem, fill=label, font=font)
    board.save(output, optimize=True)
    return output


def _keyframe_board(stems: tuple[str, ...], output: Path) -> Path:
    cols, cell, label_height = 3, 116, 16
    board = Image.new(
        "RGBA", (cols * cell, len(stems) * (100 + label_height)), REVIEW_BACKGROUND_DARK
    )
    draw = ImageDraw.Draw(board)
    font = ImageFont.load_default()
    for row, stem in enumerate(stems):
        entry = ENTRY_BY_STEM[stem]
        for column, frame in enumerate(review_frames(entry, SPECS[stem].duration_frames)):
            x = column * cell + 8
            y = row * (100 + label_height)
            board.alpha_composite(_keyframe_icon(stem, frame), (x, y))
            draw.text(
                (x + 1, y + 100), f"{stem} / {frame}",
                fill=(242, 240, 233, 255), font=font,
            )
    board.save(output, optimize=True)
    return output


def create_review_boards(
    stems: tuple[str, ...], output_root: Path = ROOT / "previews"
) -> dict[str, Path]:
    """Create the small-scale static and keyframe boards used for approval."""
    current = output_root / "review" / "current"
    current.mkdir(parents=True, exist_ok=True)
    slug = _slug(stems)
    suffix = "" if slug == "all" else f"-{slug}"
    return {
        "static_dark": _static_board(
            stems, REVIEW_BACKGROUND_DARK, current / f"static-100-dark{suffix}.png"
        ),
        "static_light": _static_board(
            stems, REVIEW_BACKGROUND_LIGHT, current / f"static-100-light{suffix}.png"
        ),
        "keyframes": _keyframe_board(stems, current / f"keyframes-{slug}.png"),
    }


def sync_release_outputs(
    stage: Path, workspace: Path, directories: tuple[str, ...] = RELEASE_DIRECTORIES
) -> None:
    """Replace only generated release directories after a staged export succeeds."""
    for relative in directories:
        source = stage / relative
        destination = workspace / relative
        if not source.is_dir():
            raise FileNotFoundError(f"staged release directory is missing: {relative}")
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)


def write_workspace_checksums(workspace: Path = WORKSPACE) -> Path:
    ignored_parts = {".git", ".superpowers", "__pycache__", ".pytest_cache"}
    checksums = []
    for path in sorted(workspace.rglob("*")):
        if (
            not path.is_file()
            or path.name in {"SHA256SUMS", ".DS_Store"}
            or path.suffix in {".pyc", ".pyo"}
            or ignored_parts.intersection(path.relative_to(workspace).parts)
        ):
            continue
        checksums.append(
            f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(workspace).as_posix()}"
        )
    output = workspace / "SHA256SUMS"
    output.write_text("\n".join(checksums) + "\n", encoding="utf-8")
    return output


def _run(args: list[str]) -> None:
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True)


def build(selection: str) -> None:
    _run(["build_all.py", "--only", selection, "--preview", "--encode"])
    _run(["build_tgs.py", "--only", selection])
    _run(["validate_animated.py", "--only", selection])
    _run(["validate_tgs.py", "--only", selection])


def release() -> Path:
    build("all")
    _run(["-m", "pytest", "-q"])
    create_review_boards(tuple(SPECS))
    with tempfile.TemporaryDirectory(prefix="emoji-release-") as temporary:
        stage = Path(temporary) / "package"
        _run(["export_final_package.py", "--destination", str(stage)])
        sync_release_outputs(stage, WORKSPACE)
    return write_workspace_checksums()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("build", "review"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("--only", default="all")
    subparsers.add_parser("release")
    args = parser.parse_args()
    if args.command == "build":
        build(args.only)
    elif args.command == "review":
        outputs = create_review_boards(select_stems(args.only, SPECS))
        for name, path in outputs.items():
            print(f"{name}: {path}")
    else:
        print(release())


if __name__ == "__main__":
    main()
