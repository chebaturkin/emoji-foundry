import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from frame_core.composite import finalize_frame
from motions.registry import SPECS
from pack_registry import PACK_ENTRIES


ROOT = Path(__file__).resolve().parent
DEFAULT_DESTINATION = ROOT.parent / "chebaturkin-telegram-emoji-final"

EXPECTED_DIRECTORIES = (
    "01-ready-to-upload/animated-tgs",
    "01-ready-to-upload/animated-webm",
    "02-static-png/100x100",
    "02-static-png/editable-400x400",
    "03-previews/individual-gif",
    "03-previews/contact-sheets",
    "04-editable-project/frame_core",
    "04-editable-project/frame_motions",
    "04-editable-project/motion_core",
    "04-editable-project/motions",
    "04-editable-project/masters",
    "04-editable-project/frames",
    "04-editable-project/upload",
    "04-editable-project/previews",
    "04-editable-project/tests",
    "04-editable-project/tools",
    "04-editable-project/docs",
    "04-editable-project/tgs_core",
    "04-editable-project/tgs_upload",
    "05-ai-handoff",
)

SOURCE_DIRECTORIES = (
    "frame_core",
    "frame_motions",
    "motion_core",
    "motions",
    "masters",
    "frames",
    "upload",
    "previews",
    "tests",
    "tools",
    "docs",
    "tgs_core",
    "tgs_upload",
)

SOURCE_FILES = (
    "README.md",
    "build_all.py",
    "build_preview.py",
    "validate_animated.py",
    "build_tgs.py",
    "validate_tgs.py",
    "export_final_package.py",
    "pack.py",
    "pack_registry.py",
    "pytest.ini",
    "requirements.txt",
)

def _source_module(stem: str) -> str:
    return f"frame_motions/m{stem.replace('-', '_')}.py"


def _category(tags: tuple[str, ...]) -> str:
    for candidate in ("soft", "impact", "story"):
        if candidate in tags:
            return candidate
    return "uncategorized"


def build_manifest() -> dict:
    items = []
    for index, entry in enumerate(PACK_ENTRIES, start=1):
        stem = entry.stem
        spec = SPECS[stem]
        master = (
            f"04-editable-project/masters/{stem}.png"
            if entry.static_source == "master" else None
        )
        items.append(
            {
                "number": index,
                "stem": stem,
                "display_name": entry.display_name,
                "category": _category(spec.tags),
                "tags": list(spec.tags),
                "duration_frames": spec.duration_frames,
                "fps": spec.fps,
                "duration_seconds": spec.duration_frames / spec.fps,
                "tgs_fps": 60,
                "tgs_duration_frames": spec.duration_frames * 2,
                "animation_summary": entry.animation_summary,
                "static_source": entry.static_source,
                "static_frame": entry.static_frame,
                "source_module": f"04-editable-project/{_source_module(stem)}",
                "master": master,
                "animated_webm": f"01-ready-to-upload/animated-webm/{stem}.webm",
                "animated_tgs": f"01-ready-to-upload/animated-tgs/{stem}.tgs",
                "static_png": f"02-static-png/100x100/{stem}.png",
                "editable_static_png": (
                    f"02-static-png/editable-400x400/{stem}.png"
                ),
                "preview_gif": f"03-previews/individual-gif/{stem}.gif",
                "frames": f"04-editable-project/frames/{stem}",
            }
        )
    return {
        "pack": "Chebaturkin Telegram Emoji",
        "emoji_count": len(items),
        "palette": {
            "brand_blue": "#2E3A4D",
            "taupe_beige": "#C4C1B4",
            "paper": "#F2F0E9",
            "ink": "#0D0D0D",
        },
        "emoji": items,
    }


def validate_source_project(source_root: Path = ROOT) -> None:
    if len(SPECS) != 4 or len(PACK_ENTRIES) != 4:
        raise ValueError("expected exactly 4 registered emoji and metadata entries")
    expected_webm = {f"{stem}.webm" for stem in SPECS}
    actual_webm = {path.name for path in (source_root / "upload").glob("*.webm")}
    if actual_webm != expected_webm:
        raise ValueError("upload WebM inventory does not match the registry")
    expected_tgs = {f"{stem}.tgs" for stem in SPECS}
    actual_tgs = {path.name for path in (source_root / "tgs_upload").glob("*.tgs")}
    if actual_tgs != expected_tgs:
        raise ValueError("upload TGS inventory does not match the registry")
    expected_masters = {
        f"{entry.stem}.png" for entry in PACK_ENTRIES
        if entry.static_source == "master"
    }
    actual_masters = {path.name for path in (source_root / "masters").glob("*.png")}
    if actual_masters != expected_masters:
        raise ValueError("master PNG inventory does not match raster-authored emoji")
    for stem, spec in SPECS.items():
        frame_paths = sorted((source_root / "frames" / stem).glob("frame-*.png"))
        if len(frame_paths) != spec.duration_frames:
            raise ValueError(f"incomplete frame directory: {stem}")
        if not (source_root / "previews" / "individual" / f"{stem}.gif").is_file():
            raise ValueError(f"missing individual GIF: {stem}")
    for relative in SOURCE_DIRECTORIES + SOURCE_FILES:
        if not (source_root / relative).exists():
            raise ValueError(f"missing export source: {relative}")


def export_static_assets(destination: Path, source_root: Path = ROOT) -> None:
    small_root = destination / "100x100"
    editable_root = destination / "editable-400x400"
    small_root.mkdir(parents=True, exist_ok=True)
    editable_root.mkdir(parents=True, exist_ok=True)
    for entry in PACK_ENTRIES:
        if entry.static_source == "vector_static_renderer":
            editable = SPECS[entry.stem].draw_frame(entry.static_frame, 400)
            small = finalize_frame(editable)
        else:
            with Image.open(source_root / "masters" / f"{entry.stem}.png") as source:
                editable = source.convert("RGBA").resize(
                    (400, 400), Image.Resampling.LANCZOS
                )
                small = editable.resize((100, 100), Image.Resampling.LANCZOS)
        stem = entry.stem
        editable.save(editable_root / f"{stem}.png", optimize=True)
        small.save(small_root / f"{stem}.png", optimize=True)


def _ignore_generated(directory: str, names: list[str]) -> set[str]:
    ignored = {
        name
        for name in names
        if name in {"__pycache__", ".pytest_cache", ".DS_Store"}
        or name.endswith((".pyc", ".pyo"))
    }
    return ignored


def _copy_editable_project(stage: Path, source_root: Path) -> None:
    project = stage / "04-editable-project"
    project.mkdir(parents=True, exist_ok=True)
    for relative in SOURCE_DIRECTORIES:
        shutil.copytree(
            source_root / relative,
            project / relative,
            ignore=_ignore_generated,
            dirs_exist_ok=True,
        )
    for relative in SOURCE_FILES:
        shutil.copy2(source_root / relative, project / relative)


def _copy_root_guidance(stage: Path, source_root: Path) -> None:
    guidance = source_root.parent / "AGENTS.md"
    if not guidance.is_file():
        raise ValueError(f"missing root agent guidance: {guidance}")
    stage.mkdir(parents=True, exist_ok=True)
    shutil.copy2(guidance, stage / "AGENTS.md")


def _copy_release_outputs(stage: Path, source_root: Path) -> None:
    tgs_root = stage / "01-ready-to-upload" / "animated-tgs"
    webm_root = stage / "01-ready-to-upload" / "animated-webm"
    gif_root = stage / "03-previews" / "individual-gif"
    contact_root = stage / "03-previews" / "contact-sheets"
    for directory in (tgs_root, webm_root, gif_root, contact_root):
        directory.mkdir(parents=True, exist_ok=True)
    for stem in SPECS:
        shutil.copy2(source_root / "tgs_upload" / f"{stem}.tgs", tgs_root)
        shutil.copy2(source_root / "upload" / f"{stem}.webm", webm_root)
        shutil.copy2(
            source_root / "previews" / "individual" / f"{stem}.gif",
            gif_root,
        )
    for source in sorted((source_root / "previews").glob("contact-sheet*.gif")):
        shutil.copy2(source, contact_root / source.name)
    review_source = source_root / "previews" / "review"
    if review_source.is_dir():
        shutil.copytree(
            review_source,
            stage / "03-previews" / "review",
            dirs_exist_ok=True,
        )


def _static_contact_sheet(stage: Path, background: tuple[int, int, int, int], name: str) -> None:
    cols, cell, label_height = 6, 116, 18
    rows = (len(SPECS) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * cell, rows * cell), background)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    foreground = (242, 240, 233, 255) if background[0] < 100 else (46, 58, 77, 255)
    for index, stem in enumerate(SPECS):
        with Image.open(stage / "02-static-png" / "100x100" / f"{stem}.png") as source:
            icon = source.convert("RGBA")
        x = (index % cols) * cell + 8
        y = (index // cols) * cell
        sheet.alpha_composite(icon, (x, y))
        draw.text((x + 2, y + 100), stem, fill=foreground, font=font)
    output = stage / "03-previews" / "contact-sheets" / name
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, optimize=True)


HANDOFF_SOURCE_FILES = (
    "START_HERE.md",
    "AI_EDITING_PROMPT.md",
    "EDITING_GUIDE.md",
    "PALETTE.md",
    "CURRENT_STATE.md",
    "STYLE_SYSTEM.md",
)


def _write_handoff(stage: Path, source_root: Path = ROOT) -> None:
    handoff = stage / "05-ai-handoff"
    handoff.mkdir(parents=True, exist_ok=True)
    source_handoff = source_root.parent / "05-ai-handoff"
    for name in HANDOFF_SOURCE_FILES:
        source = source_handoff / name
        if not source.is_file():
            raise ValueError(f"missing active handoff document: {name}")
        shutil.copy2(source, handoff / name)
    manifest = build_manifest()
    (handoff / "emoji-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    package_manifest = f"""# Package Manifest

- animated WebM: {len(list((stage / '01-ready-to-upload/animated-webm').glob('*.webm')))}
- animated TGS: {len(list((stage / '01-ready-to-upload/animated-tgs').glob('*.tgs')))}
- static PNG 100 x 100: {len(list((stage / '02-static-png/100x100').glob('*.png')))}
- editable static PNG 400 x 400: {len(list((stage / '02-static-png/editable-400x400').glob('*.png')))}
- individual GIF: {len(list((stage / '03-previews/individual-gif').glob('*.gif')))}
- registered emoji: {len(SPECS)}

Primary vector files are isolated in `01-ready-to-upload/animated-tgs`.
Fallback video files are isolated in `01-ready-to-upload/animated-webm`.
The editable project starts at `04-editable-project/README.md`.
"""
    (handoff / "PACKAGE_MANIFEST.md").write_text(
        package_manifest, encoding="utf-8"
    )


def _write_checksums(stage: Path) -> None:
    lines = []
    for path in sorted(item for item in stage.rglob("*") if item.is_file()):
        if path.name == "SHA256SUMS":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(stage).as_posix()}")
    (stage / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def export_package(destination: Path, source_root: Path = ROOT) -> Path:
    destination = destination.resolve()
    if destination.exists():
        raise FileExistsError(f"destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    validate_source_project(source_root)
    with tempfile.TemporaryDirectory(
        prefix=f"{destination.name}-export-", dir=destination.parent
    ) as temporary:
        stage = Path(temporary) / destination.name
        for relative in EXPECTED_DIRECTORIES:
            (stage / relative).mkdir(parents=True, exist_ok=True)
        export_static_assets(stage / "02-static-png", source_root)
        _copy_release_outputs(stage, source_root)
        _copy_editable_project(stage, source_root)
        _copy_root_guidance(stage, source_root)
        _static_contact_sheet(
            stage, (242, 240, 233, 255), "static-contact-light.png"
        )
        _static_contact_sheet(
            stage, (23, 34, 45, 255), "static-contact-dark.png"
        )
        _write_handoff(stage, source_root)
        _write_checksums(stage)
        stage.rename(destination)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--destination", type=Path, default=DEFAULT_DESTINATION
    )
    args = parser.parse_args()
    print(export_package(args.destination))


if __name__ == "__main__":
    main()
