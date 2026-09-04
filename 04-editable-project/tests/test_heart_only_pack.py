EXPECTED_STEMS = (
    "01-heart",
    "02-heart-double",
    "03-heart-open",
    "27-ira-heart",
)


def test_runtime_and_package_registry_contain_only_the_heart_collection():
    from frame_motions.registry import FRAME_SPECS
    from pack_registry import PACK_ENTRIES

    assert tuple(FRAME_SPECS) == EXPECTED_STEMS
    assert tuple(entry.stem for entry in PACK_ENTRIES) == EXPECTED_STEMS


def test_export_manifest_contains_only_the_heart_collection():
    from export_final_package import build_manifest

    manifest = build_manifest()
    assert tuple(item["stem"] for item in manifest["emoji"]) == EXPECTED_STEMS
