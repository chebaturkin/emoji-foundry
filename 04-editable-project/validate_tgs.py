import argparse
import gzip
import json
from pathlib import Path

from frame_motions.common import BLUE, INK, PAPER, TAUPE
from motions.registry import SPECS
from validate_animated import resolve_stems


ROOT = Path(__file__).resolve().parent
TGS_UPLOAD = ROOT / "tgs_upload"
MAX_TGS_BYTES = 64 * 1024
ALLOWED_COLORS = {BLUE[:3], TAUPE[:3], PAPER[:3], INK[:3]}


def _validate_group(group: dict, layer_name: str) -> list[str]:
    issues = []
    if group.get("ty") != "gr":
        return [f"layer {layer_name} must contain shape groups"]
    items = group.get("it", [])
    if not items or items[-1].get("ty") != "tr":
        issues.append(f"layer {layer_name} group must end with transform")
    for shape in items[:-1]:
        if shape.get("ty") not in {"sh", "fl"}:
            issues.append(
                f"layer {layer_name} uses unsupported shape {shape.get('ty')}"
            )
        if shape.get("ty") == "fl":
            raw = shape.get("c", {}).get("k", [])[:3]
            color = tuple(round(channel * 255) for channel in raw)
            if color not in ALLOWED_COLORS:
                issues.append(f"layer {layer_name} uses color {color}")
    return issues


def _load_document(path: Path) -> dict:
    return json.loads(gzip.decompress(path.read_bytes()))


def validate_tgs(path: Path, *, expected_source_frames: int) -> list[str]:
    if not path.exists():
        return ["missing TGS"]
    issues = []
    if path.stat().st_size > MAX_TGS_BYTES:
        issues.append(
            f"file is {path.stat().st_size} bytes, limit is {MAX_TGS_BYTES}"
        )
    try:
        document = _load_document(path)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        return issues + [f"invalid gzip JSON: {error}"]
    if document.get("tgs") != 1:
        issues.append("top-level tgs marker must equal 1")
    if (document.get("w"), document.get("h")) != (512, 512):
        issues.append("canvas must be 512x512")
    if document.get("fr") != 60:
        issues.append(f"FPS is {document.get('fr')}, expected 60")
    if document.get("ip") != 0 or document.get("op") != expected_source_frames * 2:
        issues.append(
            f"timeline is {document.get('ip')}..{document.get('op')}, "
            f"expected 0..{expected_source_frames * 2}"
        )
    if document.get("assets"):
        issues.append("assets are forbidden in vector TGS")
    layers = document.get("layers", [])
    for layer in layers:
        if layer.get("ty") != 4:
            issues.append(f"layer {layer.get('nm')} is not a shape layer")
            continue
        for group in layer.get("shapes", []):
            issues.extend(_validate_group(group, layer.get("nm")))
    if not any(layer.get("ip", 0) <= 0 < layer.get("op", 0) for layer in layers):
        issues.append("first frame must contain a visible thumbnail shape")
    return issues


def validate_pack(
    root: Path = TGS_UPLOAD,
    stems: list[str] | None = None,
) -> dict[str, list[str]]:
    selected = stems or list(SPECS)
    report = {}
    for stem in selected:
        issues = validate_tgs(
            root / f"{stem}.tgs",
            expected_source_frames=SPECS[stem].duration_frames,
        )
        if issues:
            report[stem] = issues
    if stems is None:
        expected = {f"{stem}.tgs" for stem in SPECS}
        actual = {path.name for path in root.glob("*.tgs")}
        extras = sorted(actual - expected)
        if extras:
            report["unexpected-files"] = extras
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default="all")
    parser.add_argument("--root", type=Path, default=TGS_UPLOAD)
    args = parser.parse_args()
    stems = resolve_stems(args.only)
    report = validate_pack(args.root, None if args.only == "all" else stems)
    if report:
        for stem, issues in report.items():
            for issue in issues:
                print(f"FAIL {stem}: {issue}")
        raise SystemExit(1)
    sizes = [(args.root / f"{stem}.tgs").stat().st_size for stem in stems]
    print(f"PASS: {len(stems)} vector TGS emoji, largest {max(sizes)} bytes")


if __name__ == "__main__":
    main()
