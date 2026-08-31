from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_current_state_records_the_active_pack_rules():
    current_state = (ROOT / "05-ai-handoff" / "CURRENT_STATE.md").read_text(
        encoding="utf-8"
    )
    for heading in (
        "## Канонический порядок",
        "## Текущие исключения",
        "## Проверка перед передачей",
    ):
        assert heading in current_state
    assert "27-ira-heart" in current_state
    assert "#F2F0E9" in current_state


def test_style_system_defines_references_and_review_scale():
    style_system = (ROOT / "05-ai-handoff" / "STYLE_SYSTEM.md").read_text(
        encoding="utf-8"
    )
    for heading in (
        "## Линия и материал",
        "## Эталонные emoji",
        "## Правило review",
    ):
        assert heading in style_system
    assert "19-exclamation" in style_system
    assert "100 × 100" in style_system
