from pathlib import Path
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
FRAMES = ROOT / "frames"
PREVIEWS = ROOT / "previews"
FFMPEG = ROOT / "tools" / "ffmpeg"
STEMS = (
    "07-lightning",
    "13-laugh",
    "03-heart-open",
    "25-explosion-cloud",
    "10-bulb-spark",
)
KEYFRAMES = (0, 8, 16, 24, 32, 40, 48, 54, 59)
BLUE = (46, 58, 77, 255)
PAPER = (242, 240, 233, 255)
DARK = (23, 34, 45, 255)


def _frame(stem, index):
    return Image.open(FRAMES / stem / f"frame-{index:03d}.png").convert("RGBA")


def build_sheet(background, foreground, output):
    label_width, cell_width, row_height, header = 136, 112, 128, 34
    sheet = Image.new(
        "RGBA",
        (label_width + len(KEYFRAMES) * cell_width, header + len(STEMS) * row_height),
        background,
    )
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((12, 12), "TACTILE PILOT / 100 x 100", fill=foreground, font=font)
    for column, frame_index in enumerate(KEYFRAMES):
        draw.text((label_width + column*cell_width + 46, 12), str(frame_index), fill=foreground, font=font)
    for row, stem in enumerate(STEMS):
        y = header + row*row_height
        draw.text((10, y+50), stem, fill=foreground, font=font)
        for column, frame_index in enumerate(KEYFRAMES):
            x = label_width + column*cell_width + 6
            sheet.alpha_composite(_frame(stem, frame_index), (x, y+8))
    sheet.convert("RGB").save(output, quality=95)


def build_video(output):
    width, height = len(STEMS)*120, 140
    font = ImageFont.load_default()
    with tempfile.TemporaryDirectory(prefix="tactile-review-") as temporary:
        temporary = Path(temporary)
        for output_index in range(120):
            frame_index = output_index % 60
            canvas = Image.new("RGBA", (width, height), DARK)
            draw = ImageDraw.Draw(canvas)
            for column, stem in enumerate(STEMS):
                x = column*120 + 10
                canvas.alpha_composite(_frame(stem, frame_index), (x, 6))
                draw.text((column*120+8, 114), stem, fill=PAPER, font=font)
            canvas.convert("RGB").save(temporary / f"frame-{output_index:03d}.png")
        subprocess.run(
            (
                str(FFMPEG), "-y", "-hide_banner", "-loglevel", "error",
                "-framerate", "30", "-i", str(temporary / "frame-%03d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                str(output),
            ),
            check=True,
        )


def main():
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    build_sheet(DARK, PAPER, PREVIEWS / "qa-tactile-dark.png")
    build_sheet(PAPER, BLUE, PREVIEWS / "qa-tactile-light.png")
    build_video(PREVIEWS / "tactile-pilot-review.mp4")
    print("built tactile QA")


if __name__ == "__main__":
    main()
