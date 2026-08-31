import argparse
from pathlib import Path

import numpy as np
from PIL import Image

from motion_core.encode import MAX_WEBM_BYTES, probe_webm
from motions.registry import SPECS
from pack_registry import select_stems


ROOT = Path(__file__).resolve().parent
SAFE_MARGIN = 8
def resolve_stems(selection: str) -> list[str]:
    return list(select_stems(selection, SPECS))


def validate_frame_directory(frame_dir: Path, expected_frames: int = 60) -> list[str]:
    issues: list[str] = []
    paths = sorted(frame_dir.glob("frame-*.png"))
    if len(paths) != expected_frames:
        return [f"expected {expected_frames} frames, found {len(paths)}"]
    for index, path in enumerate(paths):
        with Image.open(path) as image:
            if image.mode != "RGBA" or image.size != (100, 100):
                issues.append(f"frame {index}: expected RGBA 100x100, found {image.mode} {image.size}")
                continue
            alpha = np.asarray(image.getchannel("A"))
            visible = Image.fromarray((alpha >= 24).astype(np.uint8) * 255, "L")
            bbox = visible.getbbox()
            if bbox is None:
                if index == 0:
                    issues.append(
                        "frame 0 must contain visible content for Telegram thumbnail"
                    )
                continue
            elif bbox[0] < SAFE_MARGIN or bbox[1] < SAFE_MARGIN or bbox[2] > 100 - SAFE_MARGIN or bbox[3] > 100 - SAFE_MARGIN:
                issues.append(f"frame {index}: content outside {SAFE_MARGIN}px safe area: {bbox}")
    return issues


def validate_webm(path: Path, expected_frames: int = 60) -> list[str]:
    if not path.exists():
        return ["missing WebM"]
    issues: list[str] = []
    info = probe_webm(path)
    if info.codec != "vp9":
        issues.append(f"codec is {info.codec}, expected vp9")
    if (info.width, info.height) != (100, 100):
        issues.append(f"dimensions are {info.width}x{info.height}, expected 100x100")
    if abs(info.fps - 30) > 0.01:
        issues.append(f"fps is {info.fps}, expected 30")
    expected_duration = expected_frames / 30
    if abs(info.duration - expected_duration) > 0.01:
        issues.append(f"duration is {info.duration}s, expected {expected_duration}s")
    if info.frame_count != expected_frames:
        issues.append(f"frame count is {info.frame_count}, expected {expected_frames}")
    if not info.has_alpha:
        issues.append("alpha metadata missing")
    if info.has_audio:
        issues.append("audio stream present")
    if path.stat().st_size > MAX_WEBM_BYTES:
        issues.append(
            f"file is {path.stat().st_size} bytes, limit is {MAX_WEBM_BYTES}"
        )
    return issues


def validate_pack(root: Path = ROOT, stems: list[str] | None = None) -> dict[str, list[str]]:
    report: dict[str, list[str]] = {}
    selected = stems or list(SPECS)
    for stem in selected:
        expected_frames = SPECS[stem].duration_frames
        issues = validate_frame_directory(
            root / "frames" / stem,
            expected_frames=expected_frames,
        )
        issues.extend(
            validate_webm(
                root / "upload" / f"{stem}.webm",
                expected_frames=expected_frames,
            )
        )
        if issues:
            report[stem] = issues
    if stems is None:
        expected = {f"{stem}.webm" for stem in SPECS}
        actual = {path.name for path in (root / "upload").glob("*.webm")}
        extras = sorted(actual - expected)
        if extras:
            report["unexpected-files"] = extras
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default="all")
    args = parser.parse_args()
    stems = resolve_stems(args.only)
    report = validate_pack(stems=None if args.only == "all" else stems)
    if report:
        for stem, issues in report.items():
            for issue in issues:
                print(f"FAIL {stem}: {issue}")
        raise SystemExit(1)
    sizes = [(ROOT / "upload" / f"{stem}.webm").stat().st_size for stem in stems]
    print(f"PASS: {len(stems)} animated emoji, largest WebM {max(sizes)} bytes")


if __name__ == "__main__":
    main()
