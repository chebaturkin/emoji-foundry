import numpy as np


def test_lightning_middle_bends_before_tail():
    from frame_motions.m07_lightning import lightning_geometry

    neutral = lightning_geometry(24, 400)
    discharge = lightning_geometry(31, 400)
    middle_motion = np.linalg.norm(discharge[3] - neutral[3])
    tail_motion = np.linalg.norm(discharge[-2] - neutral[-2])
    assert middle_motion > max(0.1, tail_motion * 1.5)


def test_lightning_has_no_side_branches_on_the_final_bolt():
    from frame_motions.m07_lightning import lightning_layers

    assert "branches" not in {layer.name for layer in lightning_layers(32, 100)}


def test_bulb_shadow_lags_at_peak_light():
    from frame_motions.m10_bulb_spark import bulb_state

    before = bulb_state(30, 400)
    peak = bulb_state(38, 400)
    assert peak["glass_flex"] > before["glass_flex"]
    assert peak["light"] > before["light"]


def test_bulb_exists_before_internal_light_blooms():
    from frame_motions.m10_bulb_spark import bulb_state

    ready = bulb_state(14, 400)
    lit = bulb_state(38, 400)
    assert ready["glass"] > ready["light"]
    assert lit["light"] > ready["light"]
    assert lit["base_click"] > 0


def test_lightning_and_bulb_do_not_globally_fade_at_exit():
    from frame_motions.m07_lightning import SPEC as lightning
    from frame_motions.m10_bulb_spark import SPEC as bulb

    for spec in (lightning, bulb):
        alpha = np.asarray(spec.draw_frame(54, 400).getchannel("A"))
        assert alpha.max() == 255
