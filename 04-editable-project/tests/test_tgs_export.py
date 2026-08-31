import gzip
import json

import numpy as np
from PIL import Image, ImageDraw

from frame_motions.common import BLUE, PAPER, TAUPE
from motions.registry import SPECS
from tgs_core.build import build_tgs_bytes, render_high_resolution
from tgs_core.vectorize import vectorize_frame


ALLOWED_EXPORTED_COLORS = {
    (46, 58, 77),
    (196, 193, 180),
    (242, 240, 233),
    (13, 13, 13),
}


def test_high_resolution_tgs_source_uses_native_geometry_not_100px_frames():
    frames = render_high_resolution(SPECS["27-ira-heart"])

    assert len(frames) == 42
    assert all(frame.mode == "RGBA" and frame.size == (512, 512) for frame in frames)
    assert frames[0].getchannel("A").getbbox() is not None
    assert frames[0].getchannel("A").getextrema()[1] == 255
    assert any(frame.getchannel("A").getbbox() is None for frame in frames)


def test_vectorizer_emits_only_palette_fills_and_closed_paths():
    image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((80, 90, 260, 290), fill=BLUE)
    draw.polygon(((280, 80), (440, 250), (300, 390)), fill=TAUPE)
    draw.rectangle((40, 350, 180, 470), fill=(255, 255, 255, 255))

    groups = vectorize_frame(image)

    exported_colors = {group.color for group in groups}
    assert exported_colors == {BLUE[:3], TAUPE[:3], PAPER[:3]}
    assert exported_colors <= ALLOWED_EXPORTED_COLORS
    assert (255, 255, 255) not in exported_colors
    assert all(group.paths for group in groups)
    assert all(len(path) >= 3 for group in groups for path in group.paths)


def test_vectorizer_preserves_translucent_effect_opacity():
    image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    ImageDraw.Draw(image).ellipse((100, 100, 400, 400), fill=(*BLUE[:3], 96))

    groups = vectorize_frame(image)

    assert len(groups) == 1
    assert 35 <= groups[0].opacity <= 40


def test_vectorizer_traces_connected_components_in_local_crops(monkeypatch):
    import tgs_core.vectorize as vectorize_module

    image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((20, 20, 80, 80), fill=BLUE)
    draw.ellipse((420, 420, 490, 490), fill=BLUE)
    original = vectorize_module.find_contours
    shapes = []

    def capture(mask, level):
        shapes.append(mask.shape)
        return original(mask, level)

    monkeypatch.setattr(vectorize_module, "find_contours", capture)
    vectorize_module.vectorize_frame(image)

    assert shapes
    assert max(height * width for height, width in shapes) < 100 * 100


def test_tgs_is_deterministic_shape_only_512px_60fps_gzip():
    empty = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    visible = empty.copy()
    ImageDraw.Draw(visible).ellipse((128, 128, 384, 384), fill=BLUE)
    frames = [empty, visible, empty]

    first = build_tgs_bytes("demo", frames, source_fps=30)
    second = build_tgs_bytes("demo", frames, source_fps=30)
    document = json.loads(gzip.decompress(first))

    assert first == second
    assert document["tgs"] == 1
    assert document["w"] == 512 and document["h"] == 512
    assert document["fr"] == 60
    assert document["ip"] == 0 and document["op"] == 6
    assert document["assets"] == []
    assert {layer["ty"] for layer in document["layers"]} == {4}
    assert all(layer["op"] - layer["ip"] == 2 for layer in document["layers"])
    for layer in document["layers"]:
        assert len(layer["shapes"]) == 1
        group = layer["shapes"][0]
        assert group["ty"] == "gr"
        assert group["it"][-1]["ty"] == "tr"
        assert {shape["ty"] for shape in group["it"][:-1]} <= {"sh", "fl"}
    assert len(first) < 65536


def test_tgs_shapes_use_bodymovin_tg_schema_accepted_by_telegram():
    image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    ImageDraw.Draw(image).ellipse((128, 128, 384, 384), fill=BLUE)

    document = json.loads(gzip.decompress(build_tgs_bytes("demo", [image])))
    group = document["layers"][0]["shapes"][0]
    paths = [item for item in group["it"] if item["ty"] == "sh"]
    fill = next(item for item in group["it"] if item["ty"] == "fl")

    assert document["v"] == "5.5.2"
    assert set(group) == {"ty", "it", "nm", "bm", "hd"}
    assert all(
        set(path) == {"ind", "ty", "ks", "nm", "hd"}
        and path["ind"] == index
        and path["nm"] == f"Path {index + 1}"
        and path["hd"] is False
        for index, path in enumerate(paths)
    )
    assert set(fill) == {"ty", "c", "o", "r", "bm", "nm", "hd"}
    assert fill["r"] == 1
    assert fill["bm"] == 0
    assert fill["nm"] == "Fill 1"
    assert fill["hd"] is False


def test_tgs_preserves_rlottie_type_discriminator_before_shape_payload():
    image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    ImageDraw.Draw(image).ellipse((128, 128, 384, 384), fill=BLUE)

    document = json.loads(gzip.decompress(build_tgs_bytes("demo", [image])))
    group = document["layers"][0]["shapes"][0]
    path = next(item for item in group["it"] if item["ty"] == "sh")
    fill = next(item for item in group["it"] if item["ty"] == "fl")
    transform = group["it"][-1]

    assert list(group)[:2] == ["ty", "it"]
    assert list(path)[:3] == ["ind", "ty", "ks"]
    assert list(fill)[:2] == ["ty", "c"]
    assert list(transform)[0] == "ty"


def test_ira_tgs_contains_brand_blue_heart_and_paper_letters():
    frames = render_high_resolution(SPECS["27-ira-heart"])
    document = json.loads(gzip.decompress(build_tgs_bytes("27-ira-heart", frames)))
    colors = {
        tuple(round(channel * 255) for channel in shape["c"]["k"][:3])
        for layer in document["layers"]
        for group in layer["shapes"]
        for shape in group["it"]
        if shape["ty"] == "fl"
    }

    assert BLUE[:3] in colors
    assert PAPER[:3] in colors
    assert TAUPE[:3] not in colors
    assert colors <= ALLOWED_EXPORTED_COLORS
    assert (255, 255, 255) not in colors
