import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
FFMPEG = ROOT / "tools" / "ffmpeg"
WEBM_CRF = 4
WEBM_CRF_STEP = 4
WEBM_MAX_CRF = 36
MAX_WEBM_BYTES = 256 * 1024


@dataclass(frozen=True)
class VideoInfo:
    codec: str
    width: int
    height: int
    fps: float
    duration: float
    has_alpha: bool
    has_audio: bool
    frame_count: int


def encode_webm(frames: list[Image.Image], output: Path) -> None:
    if not frames:
        raise ValueError("expected at least one frame")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="emoji-webm-") as temporary:
        frame_dir = Path(temporary)
        for index, frame in enumerate(frames):
            if frame.mode != "RGBA" or frame.size != (100, 100):
                raise ValueError(f"invalid frame {index}: {frame.mode} {frame.size}")
            frame.save(frame_dir / f"frame-{index:03d}.png", optimize=True)
        base_command = [
            str(FFMPEG),
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-framerate",
            "30",
            "-i",
            str(frame_dir / "frame-%03d.png"),
            "-an",
            "-c:v",
            "libvpx-vp9",
            "-pix_fmt",
            "yuva420p",
            "-auto-alt-ref",
            "0",
            "-deadline",
            "best",
            "-cpu-used",
            "0",
        ]
        quality_modes = [None, *range(WEBM_CRF, WEBM_MAX_CRF + 1, WEBM_CRF_STEP)]
        for crf in quality_modes:
            quality = (
                ["-lossless", "1"]
                if crf is None
                else ["-b:v", "0", "-crf", str(crf)]
            )
            command = [
                *base_command,
                *quality,
                "-metadata:s:v:0",
                "alpha_mode=1",
                str(output),
            ]
            subprocess.run(command, check=True, capture_output=True)
            output_size = output.stat().st_size
            if output_size <= MAX_WEBM_BYTES:
                return
        raise RuntimeError(
            f"WebM remains over {MAX_WEBM_BYTES} bytes after lossless and CRF "
            f"{WEBM_MAX_CRF}: {output_size} bytes"
        )


def probe_webm(path: Path) -> VideoInfo:
    result = subprocess.run(
        [str(FFMPEG), "-hide_banner", "-i", str(path), "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or f"ffmpeg exited with status {result.returncode}"
        raise RuntimeError(f"WebM decode failed: {detail}")
    text = result.stderr
    resolution = re.search(r"Video: vp9[^\n]*?,\s*(?:yuva?420p[^,]*,\s*)?(\d+)x(\d+)", text)
    if resolution is None:
        resolution = re.search(r"(\d+)x(\d+)[,\s]", text)
    fps_match = re.search(r"([0-9.]+) fps", text)
    duration_match = re.search(r"Duration: 00:00:([0-9.]+)", text)
    frame_matches = re.findall(r"frame=\s*(\d+)", text)
    return VideoInfo(
        codec="vp9" if "Video: vp9" in text else "unknown",
        width=int(resolution.group(1)) if resolution else 0,
        height=int(resolution.group(2)) if resolution else 0,
        fps=float(fps_match.group(1)) if fps_match else 0.0,
        duration=float(duration_match.group(1)) if duration_match else 0.0,
        has_alpha="alpha_mode" in text.lower() or "yuva420p" in text.lower(),
        has_audio="Audio:" in text,
        frame_count=int(frame_matches[-1]) if frame_matches else 0,
    )
