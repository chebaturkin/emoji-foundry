from fractions import Fraction
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from motions.registry import SPECS
from build_all import gif_frame_durations, prepare_gif_frames


ROOT = Path(__file__).resolve().parent
FRAMES = ROOT / "frames"
PREVIEWS = ROOT / "previews"

STEMS = (
    "01-heart",
    "04-star",
    "06-spark",
    "09-idea",
    "11-eye",
    "12-smile",
    "14-sad",
)
KEYFRAME_FRACTIONS = tuple(Fraction(index, 8) for index in range(9))

DARK = (23, 34, 45, 255)
PAPER = (242, 240, 233, 255)
BLUE = (46, 58, 77, 255)

FRAME_SIZE = 100
LABEL_WIDTH = 136
CELL_WIDTH = 112
ROW_HEIGHT = 112
HEADER_HEIGHT = 34
FACES_REDESIGN_STEMS = ("12-smile", "14-sad", "15-surprise")
FACES_REDESIGN_FRACTIONS = (Fraction(1, 5), Fraction(9, 20), Fraction(13, 20), Fraction(17, 20))
HANDS_REDESIGN_STEMS = ("16-like", "17-dislike", "20-check")
HANDS_REDESIGN_FRACTIONS = FACES_REDESIGN_FRACTIONS
ENERGY_REDESIGN_STEMS = (
    "07-lightning", "24-explosion-ray", "26-explosion-ring", "05-star-four"
)
ENERGY_REDESIGN_FRACTIONS = FACES_REDESIGN_FRACTIONS
STORY_REDESIGN_STEMS = ("23-launch", "10-bulb-spark", "22-favorite", "27-ira-heart")
STORY_REDESIGN_FRACTIONS = FACES_REDESIGN_FRACTIONS


def keyframe_indices(duration_frames: int) -> tuple[int, ...]:
    return tuple(
        round(fraction * (duration_frames - 1))
        for fraction in KEYFRAME_FRACTIONS
    )


def keyframe_label(fraction: Fraction) -> str:
    return f"{float(fraction * 100):g}%"


def load_frame(stem: str, frame_index: int) -> Image.Image:
    path = FRAMES / stem / f"frame-{frame_index:03d}.png"
    with Image.open(path) as source:
        frame = source.convert("RGBA")
    if frame.size != (FRAME_SIZE, FRAME_SIZE):
        raise ValueError(f"expected 100 x 100 frame, got {frame.size}: {path}")
    return frame


def build_sheet(
    background: tuple[int, int, int, int],
    foreground: tuple[int, int, int, int],
    output: Path,
) -> Path:
    width = LABEL_WIDTH + len(KEYFRAME_FRACTIONS) * CELL_WIDTH
    height = HEADER_HEIGHT + len(STEMS) * ROW_HEIGHT
    sheet = Image.new("RGBA", (width, height), background)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    draw.text((12, 12), "BATCH 1 / 100 x 100", fill=foreground, font=font)
    for column, fraction in enumerate(KEYFRAME_FRACTIONS):
        x = LABEL_WIDTH + column * CELL_WIDTH + FRAME_SIZE // 2
        draw.text(
            (x, 12),
            keyframe_label(fraction),
            fill=foreground,
            font=font,
            anchor="ma",
        )

    for row, stem in enumerate(STEMS):
        y = HEADER_HEIGHT + row * ROW_HEIGHT
        draw.text((10, y + 44), stem, fill=foreground, font=font)
        frame_indices = keyframe_indices(SPECS[stem].duration_frames)
        for column, frame_index in enumerate(frame_indices):
            x = LABEL_WIDTH + column * CELL_WIDTH
            sheet.alpha_composite(load_frame(stem, frame_index), (x, y))

    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, optimize=True)
    return output


def build_faces_redesign_sheet(
    background: tuple[int, int, int, int],
    foreground: tuple[int, int, int, int],
    output: Path,
) -> Path:
    """Compact four-sample QA sheet for the redesigned face family."""
    width = LABEL_WIDTH + len(FACES_REDESIGN_FRACTIONS) * CELL_WIDTH
    height = HEADER_HEIGHT + len(FACES_REDESIGN_STEMS) * ROW_HEIGHT
    sheet = Image.new("RGBA", (width, height), background)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((12, 12), "FACES REDESIGN / 100 x 100", fill=foreground, font=font)
    for column, fraction in enumerate(FACES_REDESIGN_FRACTIONS):
        x = LABEL_WIDTH + column * CELL_WIDTH + FRAME_SIZE // 2
        draw.text((x, 12), f"{float(fraction) * 100:g}%", fill=foreground, font=font, anchor="ma")
    for row, stem in enumerate(FACES_REDESIGN_STEMS):
        y = HEADER_HEIGHT + row * ROW_HEIGHT
        draw.text((10, y + 44), stem, fill=foreground, font=font)
        indices = tuple(round(f * (SPECS[stem].duration_frames - 1)) for f in FACES_REDESIGN_FRACTIONS)
        for column, frame_index in enumerate(indices):
            x = LABEL_WIDTH + column * CELL_WIDTH
            sheet.alpha_composite(load_frame(stem, frame_index), (x, y))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, optimize=True)
    return output


def build_faces_redesign_contact(output: Path) -> Path:
    """Animated contact sheet alternating dark and paper QA backgrounds."""
    frames = []
    for background, foreground in ((DARK, PAPER), (PAPER, BLUE)):
        frame = Image.new("RGBA", (LABEL_WIDTH + len(FACES_REDESIGN_FRACTIONS) * CELL_WIDTH, HEADER_HEIGHT + len(FACES_REDESIGN_STEMS) * ROW_HEIGHT), background)
        draw = ImageDraw.Draw(frame)
        font = ImageFont.load_default()
        draw.text((12, 12), "FACES REDESIGN", fill=foreground, font=font)
        for column, fraction in enumerate(FACES_REDESIGN_FRACTIONS):
            draw.text((LABEL_WIDTH + column * CELL_WIDTH + FRAME_SIZE // 2, 12), f"{float(fraction) * 100:g}%", fill=foreground, font=font, anchor="ma")
        for row, stem in enumerate(FACES_REDESIGN_STEMS):
            y = HEADER_HEIGHT + row * ROW_HEIGHT
            draw.text((10, y + 44), stem, fill=foreground, font=font)
            for column, fraction in enumerate(FACES_REDESIGN_FRACTIONS):
                index = round(fraction * (SPECS[stem].duration_frames - 1))
                frame.alpha_composite(load_frame(stem, index), (LABEL_WIDTH + column * CELL_WIDTH, y))
        frames.append(frame)
    prepared = prepare_gif_frames(frames)
    output.parent.mkdir(parents=True, exist_ok=True)
    prepared[0].save(output, save_all=True, append_images=prepared[1:], duration=gif_frame_durations(len(prepared)), loop=0, disposal=2, optimize=False)
    return output


def build_hands_redesign_sheet(background, foreground, output: Path) -> Path:
    width = LABEL_WIDTH + len(HANDS_REDESIGN_FRACTIONS) * CELL_WIDTH
    height = HEADER_HEIGHT + len(HANDS_REDESIGN_STEMS) * ROW_HEIGHT
    sheet = Image.new("RGBA", (width, height), background)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((12, 12), "HANDS REDESIGN / 100 x 100", fill=foreground, font=font)
    for column, fraction in enumerate(HANDS_REDESIGN_FRACTIONS):
        x = LABEL_WIDTH + column * CELL_WIDTH + FRAME_SIZE // 2
        draw.text((x, 12), f"{float(fraction) * 100:g}%", fill=foreground, font=font, anchor="ma")
    for row, stem in enumerate(HANDS_REDESIGN_STEMS):
        y = HEADER_HEIGHT + row * ROW_HEIGHT
        draw.text((10, y + 44), stem, fill=foreground, font=font)
        for column, fraction in enumerate(HANDS_REDESIGN_FRACTIONS):
            index = round(fraction * (SPECS[stem].duration_frames - 1))
            sheet.alpha_composite(load_frame(stem, index), (LABEL_WIDTH + column * CELL_WIDTH, y))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, optimize=True)
    return output


def build_hands_redesign_contact(output: Path) -> Path:
    frames = []
    width = LABEL_WIDTH + len(HANDS_REDESIGN_FRACTIONS) * CELL_WIDTH
    height = HEADER_HEIGHT + len(HANDS_REDESIGN_STEMS) * ROW_HEIGHT
    for background, foreground in ((DARK, PAPER), (PAPER, BLUE)):
        frame = Image.new("RGBA", (width, height), background)
        draw = ImageDraw.Draw(frame)
        font = ImageFont.load_default()
        draw.text((12, 12), "HANDS REDESIGN", fill=foreground, font=font)
        for column, fraction in enumerate(HANDS_REDESIGN_FRACTIONS):
            draw.text((LABEL_WIDTH + column * CELL_WIDTH + FRAME_SIZE // 2, 12), f"{float(fraction) * 100:g}%", fill=foreground, font=font, anchor="ma")
        for row, stem in enumerate(HANDS_REDESIGN_STEMS):
            y = HEADER_HEIGHT + row * ROW_HEIGHT
            draw.text((10, y + 44), stem, fill=foreground, font=font)
            for column, fraction in enumerate(HANDS_REDESIGN_FRACTIONS):
                index = round(fraction * (SPECS[stem].duration_frames - 1))
                frame.alpha_composite(load_frame(stem, index), (LABEL_WIDTH + column * CELL_WIDTH, y))
        frames.append(frame)
    prepared = prepare_gif_frames(frames)
    output.parent.mkdir(parents=True, exist_ok=True)
    prepared[0].save(output, save_all=True, append_images=prepared[1:], duration=gif_frame_durations(len(prepared)), loop=0, disposal=2, optimize=False)
    return output


def build_energy_redesign_sheet(background, foreground, output: Path) -> Path:
    width = LABEL_WIDTH + len(ENERGY_REDESIGN_FRACTIONS) * CELL_WIDTH
    height = HEADER_HEIGHT + len(ENERGY_REDESIGN_STEMS) * ROW_HEIGHT
    sheet = Image.new("RGBA", (width, height), background)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((12, 12), "ENERGY REDESIGN / 100 x 100", fill=foreground, font=font)
    for column, fraction in enumerate(ENERGY_REDESIGN_FRACTIONS):
        x = LABEL_WIDTH + column * CELL_WIDTH + FRAME_SIZE // 2
        draw.text(
            (x, 12), f"{float(fraction) * 100:g}%",
            fill=foreground, font=font, anchor="ma",
        )
    for row, stem in enumerate(ENERGY_REDESIGN_STEMS):
        y = HEADER_HEIGHT + row * ROW_HEIGHT
        draw.text((10, y + 44), stem, fill=foreground, font=font)
        for column, fraction in enumerate(ENERGY_REDESIGN_FRACTIONS):
            index = round(fraction * (SPECS[stem].duration_frames - 1))
            sheet.alpha_composite(
                load_frame(stem, index), (LABEL_WIDTH + column * CELL_WIDTH, y)
            )
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, optimize=True)
    return output


def build_energy_redesign_contact(output: Path) -> Path:
    frames = []
    width = LABEL_WIDTH + len(ENERGY_REDESIGN_FRACTIONS) * CELL_WIDTH
    height = HEADER_HEIGHT + len(ENERGY_REDESIGN_STEMS) * ROW_HEIGHT
    for background, foreground in ((DARK, PAPER), (PAPER, BLUE)):
        frame = Image.new("RGBA", (width, height), background)
        draw = ImageDraw.Draw(frame)
        font = ImageFont.load_default()
        draw.text((12, 12), "ENERGY REDESIGN", fill=foreground, font=font)
        for column, fraction in enumerate(ENERGY_REDESIGN_FRACTIONS):
            x = LABEL_WIDTH + column * CELL_WIDTH + FRAME_SIZE // 2
            draw.text(
                (x, 12), f"{float(fraction) * 100:g}%",
                fill=foreground, font=font, anchor="ma",
            )
        for row, stem in enumerate(ENERGY_REDESIGN_STEMS):
            y = HEADER_HEIGHT + row * ROW_HEIGHT
            draw.text((10, y + 44), stem, fill=foreground, font=font)
            for column, fraction in enumerate(ENERGY_REDESIGN_FRACTIONS):
                index = round(fraction * (SPECS[stem].duration_frames - 1))
                frame.alpha_composite(
                    load_frame(stem, index),
                    (LABEL_WIDTH + column * CELL_WIDTH, y),
                )
        frames.append(frame)
    prepared = prepare_gif_frames(frames)
    output.parent.mkdir(parents=True, exist_ok=True)
    prepared[0].save(
        output, save_all=True, append_images=prepared[1:],
        duration=gif_frame_durations(len(prepared)), loop=0,
        disposal=2, optimize=False,
    )
    return output


def build_story_redesign_sheet(background, foreground, output: Path) -> Path:
    width = LABEL_WIDTH + len(STORY_REDESIGN_FRACTIONS) * CELL_WIDTH
    height = HEADER_HEIGHT + len(STORY_REDESIGN_STEMS) * ROW_HEIGHT
    sheet = Image.new("RGBA", (width, height), background)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((12, 12), "STORY REDESIGN / 100 x 100", fill=foreground, font=font)
    for column, fraction in enumerate(STORY_REDESIGN_FRACTIONS):
        x = LABEL_WIDTH + column * CELL_WIDTH + FRAME_SIZE // 2
        draw.text(
            (x, 12), f"{float(fraction) * 100:g}%",
            fill=foreground, font=font, anchor="ma",
        )
    for row, stem in enumerate(STORY_REDESIGN_STEMS):
        y = HEADER_HEIGHT + row * ROW_HEIGHT
        draw.text((10, y + 44), stem, fill=foreground, font=font)
        for column, fraction in enumerate(STORY_REDESIGN_FRACTIONS):
            index = round(fraction * (SPECS[stem].duration_frames - 1))
            sheet.alpha_composite(
                load_frame(stem, index), (LABEL_WIDTH + column * CELL_WIDTH, y)
            )
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, optimize=True)
    return output


def build_story_redesign_contact(output: Path) -> Path:
    frames = []
    width = LABEL_WIDTH + len(STORY_REDESIGN_FRACTIONS) * CELL_WIDTH
    height = HEADER_HEIGHT + len(STORY_REDESIGN_STEMS) * ROW_HEIGHT
    for background, foreground in ((DARK, PAPER), (PAPER, BLUE)):
        frame = Image.new("RGBA", (width, height), background)
        draw = ImageDraw.Draw(frame)
        font = ImageFont.load_default()
        draw.text((12, 12), "STORY REDESIGN", fill=foreground, font=font)
        for column, fraction in enumerate(STORY_REDESIGN_FRACTIONS):
            x = LABEL_WIDTH + column * CELL_WIDTH + FRAME_SIZE // 2
            draw.text(
                (x, 12), f"{float(fraction) * 100:g}%",
                fill=foreground, font=font, anchor="ma",
            )
        for row, stem in enumerate(STORY_REDESIGN_STEMS):
            y = HEADER_HEIGHT + row * ROW_HEIGHT
            draw.text((10, y + 44), stem, fill=foreground, font=font)
            for column, fraction in enumerate(STORY_REDESIGN_FRACTIONS):
                index = round(fraction * (SPECS[stem].duration_frames - 1))
                frame.alpha_composite(
                    load_frame(stem, index),
                    (LABEL_WIDTH + column * CELL_WIDTH, y),
                )
        frames.append(frame)
    prepared = prepare_gif_frames(frames)
    output.parent.mkdir(parents=True, exist_ok=True)
    prepared[0].save(
        output, save_all=True, append_images=prepared[1:],
        duration=gif_frame_durations(len(prepared)), loop=0,
        disposal=2, optimize=False,
    )
    return output


def main() -> None:
    dark = build_sheet(DARK, PAPER, PREVIEWS / "qa-batch1-dark.png")
    light = build_sheet(PAPER, BLUE, PREVIEWS / "qa-batch1-light.png")
    build_faces_redesign_sheet(DARK, PAPER, PREVIEWS / "qa-faces-redesign-dark.png")
    build_faces_redesign_sheet(PAPER, BLUE, PREVIEWS / "qa-faces-redesign-light.png")
    build_faces_redesign_contact(PREVIEWS / "contact-sheet-faces-redesign.gif")
    build_hands_redesign_sheet(DARK, PAPER, PREVIEWS / "qa-hands-redesign-dark.png")
    build_hands_redesign_sheet(PAPER, BLUE, PREVIEWS / "qa-hands-redesign-light.png")
    build_hands_redesign_contact(PREVIEWS / "contact-sheet-hands-redesign.gif")
    build_energy_redesign_sheet(DARK, PAPER, PREVIEWS / "qa-energy-redesign-dark.png")
    build_energy_redesign_sheet(PAPER, BLUE, PREVIEWS / "qa-energy-redesign-light.png")
    build_energy_redesign_contact(PREVIEWS / "contact-sheet-energy-redesign.gif")
    build_story_redesign_sheet(DARK, PAPER, PREVIEWS / "qa-story-redesign-dark.png")
    build_story_redesign_sheet(PAPER, BLUE, PREVIEWS / "qa-story-redesign-light.png")
    build_story_redesign_contact(PREVIEWS / "contact-sheet-story-redesign.gif")
    print(dark)
    print(light)


if __name__ == "__main__":
    main()
