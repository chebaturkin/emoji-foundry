import numpy as np

from motion_core.render import render_motion


def test_surprise_redesign_state_and_layers_remove_shock_rays():
    from frame_motions.m15_surprise import SPEC, surprise_layers, surprise_state

    assert SPEC.duration_frames == 48
    early = surprise_state(10, 100)
    delayed = surprise_state(18, 100)
    assert {"mouth_open", "eyes_wide", "recoil"} <= early.keys()
    assert early["mouth_open"] > early["eyes_wide"]
    assert delayed["eyes_wide"] > early["eyes_wide"]
    names = {layer.name for layer in surprise_layers(24, 100)}
    assert "shock_wave" not in names
    assert {"blue_depth", "paper_face", "blue_outline", "ink_features", "recoil"} <= names


def test_surprise_redesign_has_blank_authored_endpoints():
    from frame_motions.m15_surprise import SPEC

    frames = render_motion(SPEC)
    assert len(frames) == 48
    assert int(np.asarray(frames[0].getchannel("A"), dtype=np.uint64).sum()) == 0
    assert int(np.asarray(frames[-1].getchannel("A"), dtype=np.uint64).sum()) == 0


def test_surprise_mouth_is_organic_and_continuous_during_opening():
    from frame_motions.m15_surprise import surprise_layers

    masks = []
    for frame in (10, 20, 30):
        layers = {layer.name: layer.image for layer in surprise_layers(frame, 100)}
        assert "mouth_open" in layers
        mask = np.asarray(layers["mouth_open"].getchannel("A")) > 0
        ys, xs = np.where(mask)
        assert len(xs) > 20
        assert np.any(mask[ys.min() + 1, xs.min() + 1 : xs.max()])
        assert not mask[ys.min(), xs.min()]
        assert not mask[ys.min(), xs.max()]
        masks.append(mask)
    assert all(mask.sum() > 0 for mask in masks)


STEMS = (
    "15-surprise", "16-like", "17-dislike", "18-question",
    "19-exclamation", "20-check", "21-cross",
)


def alpha_sum(image):
    return int(np.asarray(image.getchannel("A"), dtype=np.uint64).sum())


def test_surprise_mouth_leads_eyes_and_recoil_follows():
    from frame_motions.m15_surprise import surprise_state

    early = surprise_state(10, 100)
    accent = surprise_state(25, 100)
    assert early["mouth_open"] > early["eyes_wide"]
    assert accent["recoil"] > 0


def test_like_builds_from_cuff_to_thumb_then_confirms():
    from frame_motions.m16_like import like_state

    entering = like_state(10, 400)
    confirming = like_state(29, 400)
    assert entering["wrist_turn"] > entering["thumb_extension"]
    assert confirming["thumb_extension"] > entering["thumb_extension"]
    assert "spark" not in confirming


def test_like_and_dislike_use_continuous_authored_hand_geometry():
    from frame_motions.m16_like import hand_layers as like_layers
    from frame_motions.m17_dislike import hand_layers as dislike_layers

    for layers in (like_layers(25, 400), dislike_layers(25, 400)):
        assert {layer.name for layer in layers} == {
            "blue_depth", "paper_hand", "blue_outline", "ink_creases"
        }


def test_dislike_has_weighted_downward_thumb_and_lagging_cuff():
    from frame_motions.m17_dislike import dislike_state

    dropping = dislike_state(24, 400)
    settling = dislike_state(31, 400)
    assert dropping["thumb_drop"] > dropping["cuff_follow"]
    assert settling["cuff_follow"] > dropping["cuff_follow"]


def test_dislike_final_pose_has_a_readable_downward_thumb_silhouette():
    from frame_motions.hand_geometry import hand_pose

    pose = hand_pose("down", 1.0, 100)
    right_side = pose.silhouette[pose.silhouette[:, 0] > 78]
    assert right_side[:, 1].max() >= 75


def test_dislike_settled_palm_is_continuous_geometry():
    from frame_motions.m17_dislike import SPEC

    image = np.asarray(render_motion(SPEC)[24])[:, :, :3].astype(np.int16)
    central_row = image[47, 35:75]
    paper_like = np.max(
        np.abs(central_row - np.array((242, 240, 233), dtype=np.int16)), axis=1
    ) < 25
    assert float(paper_like.mean()) > 0.1


def test_question_dot_arrives_before_wrapping_curve():
    from frame_motions.m18_question import question_state

    early = question_state(6, 400)
    formed = question_state(20, 400)
    assert early["dot"] > early["curve"]
    assert formed["curve"] > early["curve"]
    assert formed["dot_y"] > early["dot_y"]


def test_exclamation_bar_hits_and_squashes_dot():
    from frame_motions.m19_exclamation import exclamation_state

    falling = exclamation_state(8, 400)
    impact = exclamation_state(20, 400)
    assert impact["bar_y"] > falling["bar_y"]
    assert impact["dot_squash"] < falling["dot_squash"]
    assert impact["recoil"] > 0


def test_check_reveal_precedes_tip_whip_and_shadow_catches_up():
    from frame_motions.m20_check import check_state

    early = check_state(8)
    accent = check_state(22)
    assert early["reveal"] > early["whip"]
    assert accent["whip"] > early["whip"]
    assert accent["shadow_reveal"] <= accent["reveal"]


def test_paper_check_remains_readable_on_dark_telegram_background():
    from PIL import Image
    from frame_motions.m20_check import SPEC

    icon = render_motion(SPEC)[24]
    background = Image.new("RGBA", (100, 100), (23, 34, 45, 255))
    background.alpha_composite(icon)
    pixels = np.asarray(background)[:, :, :3].astype(np.int16)
    separation = np.max(
        np.abs(pixels - np.array((23, 34, 45), dtype=np.int16)), axis=2
    )
    assert int(np.count_nonzero(separation > 50)) >= 20
    icon_pixels = np.asarray(icon)[:, :, :3].astype(np.int16)
    accent_like = np.max(
        np.abs(icon_pixels - np.array((242, 240, 233), dtype=np.int16)), axis=2
    ) < 20
    assert int(np.count_nonzero(accent_like)) >= 20


def test_check_has_a_paper_face_with_a_separate_blue_outline():
    from frame_motions.common import BLUE, PAPER
    from frame_motions.m20_check import check_layers

    layers = {layer.name: np.asarray(layer.image) for layer in check_layers(24, 400)}
    assert {"lagging_shadow", "blue_outline", "paper_check"} == set(layers)
    for name, color in (("blue_outline", BLUE), ("paper_check", PAPER)):
        image = layers[name]
        assert np.any(np.all(image[:, :, :3] == color[:3], axis=2) & (image[:, :, 3] > 32))


def test_check_uses_the_pack_weight_for_outline_and_paper_stroke():
    from frame_motions.m20_check import check_layers

    layers = {layer.name: np.asarray(layer.image.getchannel("A")) for layer in check_layers(24, 400)}
    assert int(np.count_nonzero(layers["blue_outline"] > 32)) >= 13000
    assert int(np.count_nonzero(layers["paper_check"] > 32)) >= 7500


def test_cross_strokes_converge_then_release_impact():
    from frame_motions.m21_cross import cross_state

    early = cross_state(6, 400)
    hit = cross_state(19, 400)
    assert hit["distance"] < early["distance"]
    assert hit["impact"] > early["impact"]
    assert hit["stroke_a"] > 0 and hit["stroke_b"] > 0


def test_batch2_native_contract_and_distinct_motion_signatures():
    from frame_motions.m15_surprise import SPEC as m10
    from frame_motions.m16_like import SPEC as m11
    from frame_motions.m17_dislike import SPEC as m12
    from frame_motions.m18_question import SPEC as m13
    from frame_motions.m19_exclamation import SPEC as m14
    from frame_motions.m20_check import SPEC as m15
    from frame_motions.m21_cross import SPEC as m16

    specs = (m10, m11, m12, m13, m14, m15, m16)
    signatures = set()
    for spec in specs:
        expected = 48 if spec.stem in {"15-surprise", "16-like", "17-dislike"} else 42
        assert spec.duration_frames == expected
        frames = render_motion(spec)
        assert len(frames) == expected
        assert alpha_sum(frames[0]) == 0
        assert alpha_sum(frames[-1]) == 0
        sample_indices = tuple(round(f * (expected - 1)) for f in (0.2, 0.45, 0.65, 0.85))
        signature = tuple(alpha_sum(frames[index]) // 1000 for index in sample_indices)
        signatures.add(signature)
    assert len(signatures) == len(specs)


def test_batch2_final_frames_stay_inside_telegram_safe_area():
    from frame_motions.m15_surprise import SPEC as m10
    from frame_motions.m16_like import SPEC as m11
    from frame_motions.m17_dislike import SPEC as m12
    from frame_motions.m18_question import SPEC as m13
    from frame_motions.m19_exclamation import SPEC as m14
    from frame_motions.m20_check import SPEC as m15
    from frame_motions.m21_cross import SPEC as m16

    for spec in (m10, m11, m12, m13, m14, m15, m16):
        for index, image in enumerate(render_motion(spec)):
            alpha = np.asarray(image.getchannel("A"))
            ys, xs = np.where(alpha >= 24)
            if len(xs):
                assert xs.min() >= 8 and xs.max() < 92, (spec.stem, index)
                assert ys.min() >= 8 and ys.max() < 92, (spec.stem, index)
