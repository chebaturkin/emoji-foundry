from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from motion_core.easing import ease
from motion_core.layers import split_layers
from motion_core.models import Keyframe, LayerDef, MotionSpec, Track
from motion_core.render import render_motion, sample_track
import motions.common as legacy_common


def test_ease_has_locked_endpoints():
    for name in ("linear", "smooth", "out_back", "in_out_sine"):
        assert ease(name, 0.0) == 0.0
        assert ease(name, 1.0) == 1.0


def test_motion_spec_defaults_to_60_frames():
    spec = MotionSpec("demo", Path("demo.png"), (), ())
    assert spec.duration_frames == 60
    assert spec.fps == 30
    assert spec.supersample == 4


def test_legacy_make_passes_explicit_60_frame_duration(monkeypatch):
    captured = {}

    def capture_spec(stem, source, layers, tracks, **kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(legacy_common, "MotionSpec", capture_spec)

    legacy_common.make("demo", (), (), "soft")

    assert captured["duration_frames"] == 60


def test_sample_track_hits_keyframes_and_interpolates():
    track = Track("root", (Keyframe(0, x=0), Keyframe(10, x=20, easing="linear")))
    assert sample_track(track, 0).x == 0
    assert sample_track(track, 5).x == 10
    assert sample_track(track, 10).x == 20


def test_split_layers_removes_and_fills_child():
    source = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    draw = ImageDraw.Draw(source)
    draw.ellipse((10, 10, 90, 90), fill=(242, 240, 233, 255))
    draw.ellipse((42, 42, 58, 58), fill=(13, 13, 13, 255))
    child = LayerDef(
        "pupil",
        (0.35, 0.35, 0.65, 0.65),
        colors=((13, 13, 13),),
        fill=(242, 240, 233, 255),
        z=2,
    )
    layers = split_layers(source, (child,))
    assert layers["pupil"].getchannel("A").getbbox() is not None
    assert layers["base"].getpixel((50, 50)) == (242, 240, 233, 255)


def test_render_motion_stays_inside_safe_area_and_loops(tmp_path: Path):
    source = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    ImageDraw.Draw(source).ellipse((220, 220, 804, 804), fill=(242, 240, 233, 255))
    path = tmp_path / "demo.png"
    source.save(path)
    spec = MotionSpec(
        "demo",
        path,
        (),
        (Track("root", (Keyframe(0), Keyframe(15, sx=1.2, sy=.85), Keyframe(35), Keyframe(59))),),
    )
    frames = render_motion(spec)
    assert len(frames) == 60
    for frame in frames:
        alpha = np.asarray(frame.getchannel("A"))
        assert not np.any(alpha[:8, :])
        assert not np.any(alpha[-8:, :])
        assert not np.any(alpha[:, :8])
        assert not np.any(alpha[:, -8:])
    assert np.mean(np.abs(np.asarray(frames[0], dtype=float) - np.asarray(frames[-1], dtype=float))) < 0.5
