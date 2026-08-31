import argparse
from pathlib import Path

from motions.registry import SPECS
from tgs_core.build import build_tgs_bytes, render_high_resolution
from validate_animated import resolve_stems


ROOT = Path(__file__).resolve().parent
TGS_UPLOAD = ROOT / "tgs_upload"
MAX_TGS_BYTES = 64 * 1024
QUALITY_PROFILES = (
    (2.0, 3.0),
    (2.5, 4.0),
    (3.0, 5.0),
    (4.0, 7.0),
)


def select_stems(selection: str) -> list[str]:
    return resolve_stems(selection)


def build_stem(stem: str, output_root: Path = TGS_UPLOAD) -> Path:
    spec = SPECS[stem]
    frames = render_high_resolution(spec)
    output_root.mkdir(parents=True, exist_ok=True)
    output = output_root / f"{stem}.tgs"
    last_size = 0
    for tolerance, minimum_area in QUALITY_PROFILES:
        data = build_tgs_bytes(
            stem,
            frames,
            source_fps=spec.fps,
            tolerance=tolerance,
            minimum_area=minimum_area,
        )
        last_size = len(data)
        if last_size <= MAX_TGS_BYTES:
            output.write_bytes(data)
            return output
    raise RuntimeError(
        f"{stem}.tgs remains over {MAX_TGS_BYTES} bytes: {last_size}"
    )


def build_selection(
    selection: str,
    output_root: Path = TGS_UPLOAD,
) -> dict[str, Path]:
    return {
        stem: build_stem(stem, output_root)
        for stem in select_stems(selection)
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default="all")
    parser.add_argument("--output", type=Path, default=TGS_UPLOAD)
    args = parser.parse_args()
    for stem, output in build_selection(args.only, args.output).items():
        print(f"built {stem}: {output.stat().st_size} bytes", flush=True)


if __name__ == "__main__":
    main()
