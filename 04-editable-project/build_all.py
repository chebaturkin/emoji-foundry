import argparse
from math import ceil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from frame_core.models import FrameMotionSpec
from motion_core.encode import encode_webm
from motion_core.models import MotionSpec
from motion_core.render import render_motion
from motions.registry import SPECS
from pack_registry import select_stems


ROOT = Path(__file__).resolve().parent
FRAMES = ROOT / "frames"
UPLOAD = ROOT / "upload"
PREVIEWS = ROOT / "previews"
INDIVIDUAL = PREVIEWS / "individual"
BACKGROUND = (23, 34, 44, 255)
PREVIEW_FPS = 30
OBSOLETE_MIXED_CONTACT_SHEETS = {
    "all": "contact-sheet.gif",
    "batch1": "contact-sheet-batch1.gif",
    "soft": "contact-sheet-soft.gif",
    "impact": "contact-sheet-impact.gif",
    "story": "contact-sheet-story.gif",
}


def gif_frame_durations(frame_count: int) -> list[int]:
    cumulative_centiseconds = [
        round(index * 100 / PREVIEW_FPS)
        for index in range(frame_count + 1)
    ]
    return [
        (end - start) * 10
        for start, end in zip(cumulative_centiseconds, cumulative_centiseconds[1:])
    ]


def prepare_gif_frames(frames: list[Image.Image]) -> list[Image.Image]:
    if not frames:
        raise ValueError("GIF requires at least one frame")
    rgb_frames = [frame.convert("RGB") for frame in frames]
    width, height = rgb_frames[0].size
    atlas = Image.new("RGB", (width, height * len(rgb_frames)))
    for index, frame in enumerate(rgb_frames):
        atlas.paste(frame, (0, index * height))
    palette = atlas.quantize(
        colors=254,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    ).getpalette()
    palette += [0] * (768 - len(palette))
    marker_color = rgb_frames[0].getpixel((width - 1, height - 1))
    palette[254 * 3:255 * 3] = list(marker_color)
    palette[255 * 3:256 * 3] = list(marker_color)
    palette_image = Image.new("P", (1, 1))
    palette_image.putpalette(palette)

    prepared = []
    for index, frame in enumerate(rgb_frames):
        indexed = frame.quantize(
            palette=palette_image,
            dither=Image.Dither.NONE,
        )
        indexed.putpixel((width - 1, height - 1), 254 + index % 2)
        prepared.append(indexed)
    return prepared


def select_specs(selection: str) -> list[MotionSpec | FrameMotionSpec]:
    return [SPECS[stem] for stem in select_stems(selection, SPECS)]


def save_frames(stem: str, frames: list[Image.Image]) -> Path:
    frame_dir = FRAMES / stem
    frame_dir.mkdir(parents=True, exist_ok=True)
    for path in frame_dir.glob("frame-*.png"):
        path.unlink()
    for index, frame in enumerate(frames):
        frame.save(frame_dir / f"frame-{index:03d}.png", optimize=True)
    return frame_dir


def start_with_strongest_frame(frames: list[Image.Image]) -> list[Image.Image]:
    if not frames:
        raise ValueError("animation requires at least one frame")

    def alpha_mass(frame: Image.Image) -> int:
        return sum(
            alpha * count
            for alpha, count in enumerate(frame.getchannel("A").histogram())
        )

    start = max(range(len(frames)), key=lambda index: alpha_mass(frames[index]))
    return [*frames[start:], *frames[:start]]


def save_individual_preview(stem: str, frames: list[Image.Image]) -> Path:
    INDIVIDUAL.mkdir(parents=True, exist_ok=True)
    preview_frames = []
    for frame in frames:
        canvas = Image.new("RGBA", (200, 200), BACKGROUND)
        icon = frame.resize((160, 160), Image.Resampling.NEAREST)
        canvas.alpha_composite(icon, (20, 20))
        preview_frames.append(canvas)
    preview_frames = prepare_gif_frames(preview_frames)
    output = INDIVIDUAL / f"{stem}.gif"
    preview_frames[0].save(
        output,
        save_all=True,
        append_images=preview_frames[1:],
        duration=gif_frame_durations(len(preview_frames)),
        loop=0,
        disposal=2,
        optimize=False,
    )
    return output


def load_saved_frames(spec: MotionSpec | FrameMotionSpec) -> list[Image.Image]:
    frames = []
    for frame_index in range(spec.duration_frames):
        source_path = FRAMES / spec.stem / f"frame-{frame_index:03d}.png"
        with Image.open(source_path) as source:
            frames.append(source.convert("RGBA"))
    return frames


def build_individual_previews(
    specs: list[MotionSpec | FrameMotionSpec],
) -> list[Path]:
    outputs = []
    for spec in specs:
        outputs.append(
            save_individual_preview(spec.stem, load_saved_frames(spec))
        )
    return outputs


def group_specs_by_duration(
    specs: list[MotionSpec | FrameMotionSpec],
) -> dict[int, list[MotionSpec | FrameMotionSpec]]:
    grouped: dict[int, list[MotionSpec | FrameMotionSpec]] = {}
    for spec in specs:
        grouped.setdefault(spec.duration_frames, []).append(spec)
    return {duration: grouped[duration] for duration in sorted(grouped)}


def build_contact_sheet(
    specs: list[MotionSpec | FrameMotionSpec],
    selection: str,
    *,
    include_duration: bool = False,
) -> Path:
    durations = {spec.duration_frames for spec in specs}
    if len(durations) != 1:
        raise ValueError("mixed durations require build_contact_sheets")
    cols, cell = 6, 112
    rows = ceil(len(specs) / cols)
    font = ImageFont.load_default()
    animation = []
    loop_frames = durations.pop()
    for frame_index in range(loop_frames):
        sheet = Image.new("RGBA", (cols * cell, rows * cell), BACKGROUND)
        draw = ImageDraw.Draw(sheet)
        for index, spec in enumerate(specs):
            path = FRAMES / spec.stem / f"frame-{frame_index:03d}.png"
            with Image.open(path) as source:
                icon = source.convert("RGBA").resize((88, 88), Image.Resampling.NEAREST)
            x = (index % cols) * cell + 12
            y = (index // cols) * cell + 3
            sheet.alpha_composite(icon, (x, y))
            draw.text((index % cols * cell + 5, index // cols * cell + 94), spec.stem, fill=(242, 240, 233), font=font)
        animation.append(sheet)
    animation = prepare_gif_frames(animation)
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    if include_duration:
        name = f"contact-sheet-{selection}-{loop_frames}.gif"
    else:
        name = (
            "contact-sheet.gif"
            if selection == "all"
            else f"contact-sheet-{selection}.gif"
        )
    output = PREVIEWS / name
    animation[0].save(
        output,
        save_all=True,
        append_images=animation[1:],
        duration=gif_frame_durations(len(animation)),
        loop=0,
        disposal=2,
        optimize=False,
    )
    return output


def build_contact_sheets(
    specs: list[MotionSpec | FrameMotionSpec], selection: str
) -> list[Path]:
    grouped = group_specs_by_duration(specs)
    mixed = len(grouped) > 1
    outputs = [
        build_contact_sheet(
            duration_specs,
            selection,
            include_duration=mixed,
        )
        for duration_specs in grouped.values()
    ]
    if mixed and selection in OBSOLETE_MIXED_CONTACT_SHEETS:
        obsolete = PREVIEWS / OBSOLETE_MIXED_CONTACT_SHEETS[selection]
        if obsolete.exists():
            obsolete.unlink()
    return outputs


def build(selection: str, preview: bool, encode: bool) -> None:
    specs = select_specs(selection)
    UPLOAD.mkdir(parents=True, exist_ok=True)
    for spec in specs:
        frames = start_with_strongest_frame(render_motion(spec))
        save_frames(spec.stem, frames)
        if preview:
            save_individual_preview(spec.stem, frames)
        if encode:
            encode_webm(frames, UPLOAD / f"{spec.stem}.webm")
        print(f"built {spec.stem}", flush=True)
    if preview:
        build_contact_sheets(specs, selection)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default="all")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--encode", action="store_true")
    args = parser.parse_args()
    build(args.only, args.preview, args.encode)


if __name__ == "__main__":
    main()
