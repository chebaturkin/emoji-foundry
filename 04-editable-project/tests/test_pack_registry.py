from pack_registry import PACK_ENTRIES, select_stems
from motions.registry import SPECS


def test_registry_is_the_canonical_order_for_runtime_specs():
    assert tuple(entry.stem for entry in PACK_ENTRIES) == tuple(SPECS)
    assert len(PACK_ENTRIES) == 27
    assert len({entry.display_name for entry in PACK_ENTRIES}) == 27


def test_registry_static_frames_are_visible_runtime_frames():
    for entry in PACK_ENTRIES:
        assert 0 < entry.static_frame < SPECS[entry.stem].duration_frames


def test_registry_resolves_groups_tags_and_comma_selections():
    assert select_stems("batch2", SPECS) == (
        "15-surprise", "16-like", "17-dislike", "18-question",
        "19-exclamation", "20-check", "21-cross",
    )
    assert select_stems("soft", SPECS) == tuple(
        stem for stem, spec in SPECS.items() if "soft" in spec.tags
    )
    assert select_stems("20-check,22-favorite", SPECS) == (
        "20-check", "22-favorite",
    )
