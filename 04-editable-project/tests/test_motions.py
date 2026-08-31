import numpy as np

from frame_core.models import FrameMotionSpec
from motion_core.render import render_motion
from motions.registry import SPECS


EXPECTED = [
    "01-heart", "02-heart-double", "03-heart-open", "04-star", "05-star-four",
    "06-spark", "07-lightning", "08-lightning-round", "09-idea",
    "10-bulb-spark", "11-eye", "12-smile", "13-laugh", "14-sad",
    "15-surprise", "16-like", "17-dislike", "18-question", "19-exclamation",
    "20-check", "21-cross", "22-favorite", "23-launch", "24-explosion-ray",
    "25-explosion-cloud", "26-explosion-ring", "27-ira-heart",
]


def test_registry_has_27_unique_specs():
    assert list(SPECS) == EXPECTED
    assert len({id(spec) for spec in SPECS.values()}) == 27


def test_every_motion_moves_and_loops():
    signatures = []
    for stem, spec in SPECS.items():
        frames = render_motion(spec)
        start = np.asarray(frames[0], dtype=np.int16)
        differences = [np.mean(np.abs(np.asarray(frames[index], dtype=np.int16) - start)) for index in (10, 16, 24, 32)]
        assert max(differences) > 0.45, stem
        assert np.mean(np.abs(np.asarray(frames[-1], dtype=np.int16) - start)) < 0.5, stem
        alpha_signature = tuple(np.asarray(frames[index].getchannel("A")).sum() // 1000 for index in (10, 16, 24, 32))
        signatures.append(alpha_signature)
    assert len(set(signatures)) >= 22


def test_redesigned_face_family_uses_48_source_frames_and_distinct_signatures():
    from frame_motions.m12_smile import SPEC as smile
    from frame_motions.m14_sad import SPEC as sad
    from frame_motions.m15_surprise import SPEC as surprise

    specs = (smile, sad, surprise)
    signatures = []
    for spec in specs:
        assert spec.duration_frames == 48
        frames = render_motion(spec)
        indices = tuple(round(f * (spec.duration_frames - 1)) for f in (0.2, 0.45, 0.65, 0.85))
        signatures.append(tuple(np.asarray(frames[i].getchannel("A")).sum() // 1000 for i in indices))
    assert len(set(signatures)) == 3


def test_laugh_keeps_the_drawn_face_intact():
    spec = SPECS["13-laugh"]
    if isinstance(spec, FrameMotionSpec):
        assert callable(spec.draw_frame)
        return
    assert spec.layers == ()
    root = next(track for track in spec.tracks if track.layer == "root")
    assert any(keyframe.sy < 0.94 for keyframe in root.keyframes)
    assert any(keyframe.sy > 1.05 for keyframe in root.keyframes)


def test_open_heart_does_not_split_the_outer_contour():
    spec = SPECS["03-heart-open"]
    if isinstance(spec, FrameMotionSpec):
        assert callable(spec.draw_frame)
        return
    layer_names = {layer.name for layer in spec.layers}
    assert "left" not in layer_names
    assert "right" not in layer_names
    assert "root" in {track.layer for track in spec.tracks}


def test_favorite_folds_as_one_silhouette():
    spec = SPECS["22-favorite"]
    if isinstance(spec, FrameMotionSpec):
        assert callable(spec.draw_frame)
        return
    layer_names = {layer.name for layer in spec.layers}
    assert layer_names == {"dash"}
    root = next(track for track in spec.tracks if track.layer == "root")
    assert any(keyframe.sy < 1 for keyframe in root.keyframes)


def test_impact_silhouettes_do_not_tear_into_regions():
    for stem in ("04-star", "07-lightning", "08-lightning-round", "25-explosion-cloud"):
        spec = SPECS[stem]
        if isinstance(spec, FrameMotionSpec):
            assert callable(spec.draw_frame)
            continue
        assert spec.layers == (), stem
        assert {track.layer for track in spec.tracks} == {"root"}, stem


def test_story_icons_only_extract_isolated_semantic_marks():
    expected = {
        "09-idea": set(),
        "18-question": {"dot"},
        "19-exclamation": {"dot"},
        "10-bulb-spark": set(),
    }
    for stem, allowed in expected.items():
        spec = SPECS[stem]
        if isinstance(spec, FrameMotionSpec):
            assert callable(spec.draw_frame)
            continue
        assert {layer.name for layer in spec.layers} == allowed, stem
        assert "root" in {track.layer for track in spec.tracks}, stem
