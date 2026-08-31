import gzip
import json
from pathlib import Path

from build_tgs import build_selection, select_stems
from validate_tgs import validate_pack, validate_tgs


def test_tgs_builder_reuses_pack_selection_contract():
    assert select_stems("27-ira-heart") == ["27-ira-heart"]
    assert len(select_stems("all")) == 27
    assert set(select_stems("13-laugh,26-explosion-ring")) == {
        "13-laugh",
        "26-explosion-ring",
    }


def test_builder_creates_uploadable_vector_tgs(tmp_path: Path):
    outputs = build_selection("27-ira-heart", tmp_path)

    assert list(outputs) == ["27-ira-heart"]
    output = tmp_path / "27-ira-heart.tgs"
    assert output.is_file() and output.stat().st_size <= 65536
    assert validate_tgs(output, expected_source_frames=42) == []


def test_tgs_first_frame_has_visible_shape_for_telegram_thumbnail(tmp_path: Path):
    build_selection("27-ira-heart", tmp_path)
    document = json.loads(gzip.decompress((tmp_path / "27-ira-heart.tgs").read_bytes()))

    assert any(layer["ip"] <= 0 < layer["op"] for layer in document["layers"])


def test_validator_requires_telegram_tgs_marker(tmp_path: Path):
    document = {
        "v": "5.5.2",
        "fr": 60,
        "ip": 0,
        "op": 84,
        "w": 512,
        "h": 512,
        "assets": [],
        "layers": [{"ty": 4, "ip": 0, "op": 84, "shapes": []}],
    }
    path = tmp_path / "missing-marker.tgs"
    path.write_bytes(gzip.compress(json.dumps(document).encode(), mtime=0))

    issues = validate_tgs(path, expected_source_frames=42)

    assert "top-level tgs marker must equal 1" in issues


def test_validator_rejects_non_vector_or_wrong_canvas(tmp_path: Path):
    document = {
        "v": "5.7.4",
        "fr": 60,
        "ip": 0,
        "op": 84,
        "w": 100,
        "h": 100,
        "assets": [{"id": "image"}],
        "layers": [{"ty": 2, "ip": 0, "op": 84, "shapes": []}],
    }
    path = tmp_path / "invalid.tgs"
    path.write_bytes(gzip.compress(json.dumps(document).encode(), mtime=0))

    issues = validate_tgs(path, expected_source_frames=42)

    assert any("512x512" in issue for issue in issues)
    assert any("assets" in issue for issue in issues)
    assert any("shape layer" in issue for issue in issues)


def test_validator_reports_exact_forbidden_fill_color(tmp_path: Path):
    document = {
        "tgs": 1,
        "v": "5.5.2",
        "fr": 60,
        "ip": 0,
        "op": 84,
        "w": 512,
        "h": 512,
        "assets": [],
        "layers": [
            {
                "ty": 4,
                "nm": "forbidden-fill",
                "ip": 0,
                "op": 84,
                "shapes": [
                    {
                        "ty": "gr",
                        "it": [
                            {
                                "ty": "fl",
                                "c": {
                                    "a": 0,
                                    "k": [1 / 255, 2 / 255, 3 / 255, 1],
                                },
                            },
                            {"ty": "tr"},
                        ],
                    }
                ],
            }
        ],
    }
    path = tmp_path / "forbidden-fill.tgs"
    path.write_bytes(gzip.compress(json.dumps(document).encode(), mtime=0))

    issues = validate_tgs(path, expected_source_frames=42)

    assert issues == ["layer forbidden-fill uses color (1, 2, 3)"]


def test_pack_validator_rejects_missing_inventory(tmp_path: Path):
    report = validate_pack(tmp_path, stems=["27-ira-heart"])

    assert report == {"27-ira-heart": ["missing TGS"]}
