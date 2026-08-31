from pathlib import Path

import numpy as np
from PIL import Image

from frame_core.composite import finalize_frame
from frame_core.models import FrameMotionSpec
from motion_core.easing import ease
from motion_core.layers import split_layers
from motion_core.models import Keyframe, MotionSpec, Track


def sample_track(track: Track, frame: int) -> Keyframe:
    keys = track.keyframes
    if frame <= keys[0].frame:
        return keys[0]
    if frame >= keys[-1].frame:
        return keys[-1]
    left, right = keys[0], keys[-1]
    for a, b in zip(keys, keys[1:]):
        if a.frame <= frame <= b.frame:
            left, right = a, b
            break
    raw = (frame - left.frame) / (right.frame - left.frame)
    t = ease(right.easing, raw)
    values = {"frame": frame, "easing": right.easing}
    for name in ("x", "y", "sx", "sy", "rotation", "opacity", "reveal"):
        values[name] = getattr(left, name) + (getattr(right, name) - getattr(left, name)) * t
    return Keyframe(**values)


def _reveal_mask(size: tuple[int, int], value: float, mode: str, origin: tuple[float, float]) -> Image.Image:
    width, height = size
    value = min(1.0, max(0.0, value))
    if mode == "none" or value >= 1.0:
        return Image.new("L", size, 255)
    if value <= 0.0:
        return Image.new("L", size, 0)
    yy, xx = np.mgrid[0:height, 0:width]
    if mode == "left_to_right":
        progress = xx / max(1, width - 1)
    elif mode == "top_to_bottom":
        progress = yy / max(1, height - 1)
    elif mode == "bottom_to_top":
        progress = 1.0 - yy / max(1, height - 1)
    elif mode in ("clockwise", "counterclockwise"):
        ox, oy = origin[0] * width, origin[1] * height
        angle = (np.arctan2(yy - oy, xx - ox) + np.pi / 2.0) % (2.0 * np.pi)
        progress = angle / (2.0 * np.pi)
        if mode == "counterclockwise":
            progress = 1.0 - progress
    else:
        raise ValueError(f"unknown reveal mode: {mode}")
    return Image.fromarray((progress <= value).astype(np.uint8) * 255, "L")


def _apply_reveal(image: Image.Image, value: float, mode: str, origin: tuple[float, float]) -> Image.Image:
    if mode == "none" and value >= 1.0:
        return image
    result = image.copy()
    alpha = np.asarray(result.getchannel("A"), dtype=np.uint16)
    reveal = np.asarray(_reveal_mask(result.size, value, mode, origin), dtype=np.uint16)
    result.putalpha(Image.fromarray((alpha * reveal // 255).astype(np.uint8), "L"))
    return result


def transform_layer(
    image: Image.Image,
    keyframe: Keyframe,
    supersample: int,
    reveal_mode: str = "none",
    reveal_origin: tuple[float, float] = (0.5, 0.5),
) -> Image.Image:
    canvas = Image.new("RGBA", image.size, (0, 0, 0, 0))
    visible = _apply_reveal(image, keyframe.reveal, reveal_mode, reveal_origin)
    bbox = visible.getchannel("A").getbbox()
    if bbox is None or keyframe.opacity <= 0.0:
        return canvas
    crop = visible.crop(bbox)
    new_size = (
        max(1, round(crop.width * keyframe.sx)),
        max(1, round(crop.height * keyframe.sy)),
    )
    crop = crop.resize(new_size, Image.Resampling.BICUBIC)
    if keyframe.rotation:
        crop = crop.rotate(-keyframe.rotation, resample=Image.Resampling.BICUBIC, expand=True)
    if keyframe.opacity < 1.0:
        alpha = np.asarray(crop.getchannel("A"), dtype=np.float32)
        crop.putalpha(Image.fromarray(np.clip(alpha * keyframe.opacity, 0, 255).astype(np.uint8), "L"))
    center_x = (bbox[0] + bbox[2]) / 2.0 + keyframe.x * supersample
    center_y = (bbox[1] + bbox[3]) / 2.0 + keyframe.y * supersample
    position = (round(center_x - crop.width / 2), round(center_y - crop.height / 2))
    canvas.alpha_composite(crop, position)
    return canvas


def _fit_safe_area(image: Image.Image, margin: int) -> Image.Image:
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        return image
    available_w = image.width - 2 * margin
    available_h = image.height - 2 * margin
    width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    scale = min(1.0, available_w / width, available_h / height)
    crop = image.crop(bbox)
    if scale < 1.0:
        crop = crop.resize((max(1, round(width * scale)), max(1, round(height * scale))), Image.Resampling.LANCZOS)
    output = Image.new("RGBA", image.size, (0, 0, 0, 0))
    output.alpha_composite(crop, ((image.width - crop.width) // 2, (image.height - crop.height) // 2))
    return output


def render_motion(spec: MotionSpec | FrameMotionSpec) -> list[Image.Image]:
    if isinstance(spec, FrameMotionSpec):
        size = 100 * spec.supersample
        return [finalize_frame(spec.draw_frame(frame, size)) for frame in range(spec.duration_frames)]
    if spec.source is None:
        raise ValueError(f"source is required for {spec.stem}")
    source = Image.open(Path(spec.source)).convert("RGBA").resize(
        (100 * spec.supersample, 100 * spec.supersample), Image.Resampling.LANCZOS
    )
    layers = split_layers(source, spec.layers)
    definitions = {definition.name: definition for definition in spec.layers}
    tracks = {track.layer: track for track in spec.tracks}
    root_track = tracks.get("root", Track("root", (Keyframe(0), Keyframe(spec.duration_frames - 1))))
    order = ["base"] + [item.name for item in sorted(spec.layers, key=lambda item: item.z)]
    frames: list[Image.Image] = []

    for frame_number in range(spec.duration_frames):
        composed = Image.new("RGBA", source.size, (0, 0, 0, 0))
        for name in order:
            track = tracks.get(name)
            key = sample_track(track, frame_number) if track else Keyframe(frame_number)
            definition = definitions.get(name)
            transformed = transform_layer(
                layers[name],
                key,
                spec.supersample,
                track.reveal_mode if track else "none",
                track.reveal_origin if track else (0.5, 0.5),
            )
            composed.alpha_composite(transformed)
        composed = transform_layer(composed, sample_track(root_track, frame_number), spec.supersample)
        composed = _fit_safe_area(composed, margin=8 * spec.supersample)
        final = composed.resize((100, 100), Image.Resampling.LANCZOS)
        pixels = np.asarray(final).copy()
        pixels[pixels[:, :, 3] == 0, :3] = 0
        frames.append(Image.fromarray(pixels, "RGBA"))
    return frames
