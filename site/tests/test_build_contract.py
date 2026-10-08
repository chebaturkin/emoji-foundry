from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build.py"


def test_build_declares_utf8_and_portable_source_paths():
    source = BUILD.read_text(encoding="utf-8")
    assert "encoding=\"utf-8\"" in source or "encoding='utf-8'" in source
    assert "brand-kit/assets/mascot" in source
    assert "brand-kit/assets/logos" in source
    assert "brand-kit/fonts" in source
    assert "href=\"/assets/" not in source
    assert "src=\"/assets/" not in source


def test_build_reports_missing_sources_before_writing_public_output():
    source = BUILD.read_text(encoding="utf-8")
    assert "Missing build dependency" in source
    assert "def main(" in source
