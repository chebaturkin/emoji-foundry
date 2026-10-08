from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build.py"


def test_build_declares_utf8_and_portable_source_paths():
    source = BUILD.read_text(encoding="utf-8")
    assert "encoding=\"utf-8\"" in source or "encoding='utf-8'" in source
    assert "brand-kit/assets/mascot" in source
    assert "brand-kit/assets/favicons" in source
    assert "brand-kit/fonts" in source
    assert "PACK_ROOT" not in source
    assert "assets/hearts" not in source
    assert "01-ready-to-upload" not in source
    assert "02-static-png" not in source
    assert "03-previews" not in source
    assert "04-editable-project" not in source
    assert "href=\"/assets/" not in source
    assert "src=\"/assets/" not in source


def test_build_reports_missing_sources_before_writing_public_output():
    source = BUILD.read_text(encoding="utf-8")
    assert "Missing build dependency" in source
    assert "def main(" in source
