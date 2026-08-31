import numpy as np

from motion_core.render import render_motion


STEMS = (
    "23-launch",
    "02-heart-double",
    "08-lightning-round",
    "24-explosion-ray",
    "26-explosion-ring",
    "05-star-four",
    "22-favorite",
)


def alpha_sum(image):
    return int(np.asarray(image.getchannel("A"), dtype=np.uint64).sum())


def test_launch_enters_before_flame_and_then_accelerates():
    from frame_motions.m23_launch import launch_state

    early = launch_state(7, 400)
    ignition = launch_state(23, 400)
    flight = launch_state(29, 400)
    assert early["entry"] > early["flame"]
    assert ignition["flame"] > early["flame"]
    assert ignition["flight"] > 0
    assert flight["rocket_y"] < ignition["rocket_y"]


def test_launch_moves_one_coherent_rocket_after_flame_ignition():
    from frame_motions.m23_launch import launch_layers, launch_state

    ignition = launch_state(20, 400)
    flight = launch_state(34, 400)
    assert ignition["flame"] > ignition["flight"]
    assert flight["rocket_y"] < ignition["rocket_y"]
    assert {layer.name for layer in launch_layers(24, 400)} == {
        "trail", "rocket", "flame"
    }


def test_double_heart_passes_impulse_from_inner_to_outer():
    from frame_motions.m02_heart_double import heart_double_state

    inner_hit = heart_double_state(19)
    outer_hit = heart_double_state(25)
    assert inner_hit["inner"] > inner_hit["outer"]
    assert inner_hit["inner_beat"] > inner_hit["outer_beat"]
    assert outer_hit["outer_beat"] > inner_hit["outer_beat"]


def test_round_lightning_charges_ring_before_bolt_and_moves_residue():
    from frame_motions.m08_lightning_round import lightning_round_state

    charge = lightning_round_state(10)
    strike = lightning_round_state(21)
    residue = lightning_round_state(28)
    assert charge["ring"] > charge["bolt"]
    assert strike["bolt"] > charge["bolt"]
    assert residue["charge_angle"] > strike["charge_angle"]


def test_explosion_rays_fire_with_independent_timing_and_pressure():
    from frame_motions.m24_explosion_ray import explosion_ray_state

    compressed = explosion_ray_state(8)
    burst = explosion_ray_state(20)
    assert max(compressed["core_impulses"]) < max(burst["core_impulses"])
    assert len(set(round(value, 3) for value in burst["ray_progress"])) >= 4
    assert len(set(round(value, 3) for value in burst["pressures"])) >= 3


def test_explosion_ray_deforms_core_locally_as_rays_fire():
    from frame_motions.m24_explosion_ray import explosion_ray_state

    burst = explosion_ray_state(28)
    assert len(set(round(value, 3) for value in burst["ray_progress"])) >= 4
    assert len(set(round(value, 3) for value in burst["core_impulses"])) >= 3
    assert "core_scale" not in burst


def test_explosion_ring_propagates_from_inner_hit_to_irregular_outer_wave():
    from frame_motions.m26_explosion_ring import explosion_ring_state

    inner_hit = explosion_ring_state(12)
    outer_hit = explosion_ring_state(22)
    assert inner_hit["clockwise_arc"] > inner_hit["counterclockwise_arc"]
    assert outer_hit["counterclockwise_arc"] > inner_hit["counterclockwise_arc"]
    assert outer_hit["irregularity"] > 0


def test_explosion_ring_closes_from_two_opposing_arcs_before_expanding():
    from frame_motions.m26_explosion_ring import explosion_ring_state

    closing = explosion_ring_state(20)
    expanding = explosion_ring_state(32)
    assert closing["clockwise_arc"] > 0
    assert closing["counterclockwise_arc"] > 0
    assert expanding["radius"] > closing["radius"]
    assert "outer_scale" not in expanding


def test_four_point_star_opens_rays_in_sequence_with_one_leading_glint():
    from frame_motions.m05_star_four import star_four_state

    opening = star_four_state(13)
    accent = star_four_state(23)
    assert len(set(round(value, 3) for value in opening["rays"])) >= 3
    assert max(accent["glints"]) > 0
    assert sum(value > 0 for value in accent["glints"]) == 1


def test_four_point_star_is_one_centered_material_without_fragment_offsets():
    from frame_motions.m05_star_four import star_four_state

    opening = star_four_state(22)
    assert opening["top"] > opening["left"]
    assert opening["left"] >= opening["bottom"]
    assert "fragment_offsets" not in opening


def test_four_point_star_never_collapses_into_a_square_mid_motion():
    from frame_motions.m05_star_four import star_four_state, _star_points

    for frame in (21, 44, 46):
        points = _star_points(star_four_state(frame), 100)
        tip_radii = np.linalg.norm(points[::4] - np.array((50, 50)), axis=1)
        inner_radii = np.linalg.norm(points[1::2] - np.array((50, 50)), axis=1)
        assert tip_radii.min() >= inner_radii.max() * 1.45


def test_explosion_ray_uses_paper_rays_with_blue_material_depth():
    from frame_motions.common import BLUE, PAPER
    from frame_motions.m24_explosion_ray import explosion_ray_layers

    layers = {layer.name: np.asarray(layer.image) for layer in explosion_ray_layers(21, 100)}
    ray = layers["ray_0"]
    depth = layers["ray_depth_0"]
    assert np.any(np.all(ray[:, :, :3] == PAPER[:3], axis=2) & (ray[:, :, 3] > 32))
    assert np.any(np.all(depth[:, :, :3] == BLUE[:3], axis=2) & (depth[:, :, 3] > 32))


def test_favorite_unfolds_then_forms_notch_without_confirmation_mark():
    from frame_motions.m22_favorite import favorite_state

    drawing = favorite_state(10)
    folding = favorite_state(21)
    settled = favorite_state(29)
    assert drawing["bookmark"] > drawing["notch"]
    assert folding["notch"] > drawing["notch"]
    assert settled["settle"] > 0


def test_favorite_is_a_solid_blue_ribbon_without_confirmation_mark():
    from frame_motions.m22_favorite import favorite_layers

    assert {layer.name for layer in favorite_layers(29, 400)} == {
        "blue_depth", "blue_bookmark", "paper_inset"
    }


def test_favorite_inset_has_a_readable_paper_line_at_emoji_scale():
    from frame_motions.m22_favorite import favorite_layers

    layers = {layer.name: np.asarray(layer.image.getchannel("A")) for layer in favorite_layers(29, 400)}
    assert int(np.count_nonzero(layers["paper_inset"] > 32)) >= 4200


def test_favorite_blue_outline_remains_readable_on_light_background():
    from frame_motions.m22_favorite import SPEC

    image = np.asarray(render_motion(SPEC)[22])[:, :, :3].astype(np.int16)
    blue_like = np.max(
        np.abs(image - np.array((46, 58, 77), dtype=np.int16)), axis=2
    ) < 20
    assert int(np.count_nonzero(blue_like)) >= 200


def test_batch3_native_contract_and_distinct_motion_signatures():
    from frame_motions.m23_launch import SPEC as m17
    from frame_motions.m02_heart_double import SPEC as m18
    from frame_motions.m08_lightning_round import SPEC as m20
    from frame_motions.m24_explosion_ray import SPEC as m21
    from frame_motions.m26_explosion_ring import SPEC as m23
    from frame_motions.m05_star_four import SPEC as m25
    from frame_motions.m22_favorite import SPEC as m26

    specs = (m17, m18, m20, m21, m23, m25, m26)
    expected_durations = {
        "23-launch": 48,
        "02-heart-double": 42,
        "08-lightning-round": 42,
        "24-explosion-ray": 48,
        "26-explosion-ring": 48,
        "05-star-four": 48,
        "22-favorite": 48,
    }
    signatures = set()
    for spec in specs:
        assert spec.duration_frames == expected_durations[spec.stem]
        frames = render_motion(spec)
        assert len(frames) == spec.duration_frames
        assert alpha_sum(frames[0]) == 0
        assert alpha_sum(frames[-1]) == 0
        sample_indices = tuple(
            round((spec.duration_frames - 1) * fraction)
            for fraction in (.15, .35, .55, .75, .92)
        )
        signature = tuple(
            alpha_sum(frames[index]) // 1000 for index in sample_indices
        )
        signatures.add(signature)
    assert len(signatures) == len(specs)


def test_batch3_frames_stay_inside_telegram_safe_area():
    from frame_motions.m23_launch import SPEC as m17
    from frame_motions.m02_heart_double import SPEC as m18
    from frame_motions.m08_lightning_round import SPEC as m20
    from frame_motions.m24_explosion_ray import SPEC as m21
    from frame_motions.m26_explosion_ring import SPEC as m23
    from frame_motions.m05_star_four import SPEC as m25
    from frame_motions.m22_favorite import SPEC as m26

    for spec in (m17, m18, m20, m21, m23, m25, m26):
        for index, image in enumerate(render_motion(spec)):
            alpha = np.asarray(image.getchannel("A"))
            ys, xs = np.where(alpha >= 24)
            if len(xs):
                assert xs.min() >= 8 and xs.max() < 92, (spec.stem, index)
                assert ys.min() >= 8 and ys.max() < 92, (spec.stem, index)
