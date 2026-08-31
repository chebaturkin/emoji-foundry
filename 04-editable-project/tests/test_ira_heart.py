import numpy as np

from motion_core.render import render_motion


def alpha_sum(image):
    return int(np.asarray(image.getchannel("A"), dtype=np.uint64).sum())


def test_ira_letters_draw_left_to_right_before_heart_closes():
    from frame_motions.m27_ira_heart import ira_heart_state

    early = ira_heart_state(7)
    embrace = ira_heart_state(21)
    closed = ira_heart_state(29)
    retracting = ira_heart_state(36)
    assert early["letters"][0] > early["letters"][1] > early["letters"][2]
    assert embrace["letters"][2] > early["letters"][2]
    assert embrace["heart_top"] > 0 and embrace["heart_bottom"] > 0
    assert closed["closure"] > embrace["closure"]
    assert retracting["letters"][0] > retracting["letters"][1] > retracting["letters"][2]


def test_ira_letters_are_paper_without_blue_or_beige_understroke():
    from frame_motions.m27_ira_heart import static_layers

    letter_layers = [layer for layer in static_layers(400) if layer.name.startswith("letter_")]
    assert len(letter_layers) == 3
    assert all(layer.name.endswith("_paper") for layer in letter_layers)

    for layer in letter_layers:
        image = np.asarray(layer.image)
        solid = image[:, :, 3] > 32
        colors = image[:, :, :3].astype(np.int16)
        brand = np.max(np.abs(colors - np.array((46, 58, 77))), axis=2) < 20
        beige = np.max(np.abs(colors - np.array((196, 193, 180))), axis=2) < 20
        paper = np.max(np.abs(colors - np.array((242, 240, 233))), axis=2) < 20
        assert int(np.count_nonzero(brand & solid)) == 0
        assert int(np.count_nonzero(beige & solid)) == 0
        assert int(np.count_nonzero(paper & solid)) > 100


def test_ira_lettering_is_large_and_open_enough_for_emoji_scale():
    from frame_motions.m27_ira_heart import static_layers

    alpha = np.maximum.reduce([
        np.asarray(layer.image.getchannel("A"))
        for layer in static_layers(400)
        if layer.name.startswith("letter_")
    ])
    ys, xs = np.where(alpha > 32)
    width = int(xs.max() - xs.min() + 1)
    height = int(ys.max() - ys.min() + 1)
    density = int(np.count_nonzero(alpha > 32)) / (width * height)
    assert width >= 225
    assert density <= 0.38


def test_ira_paper_strokes_have_the_same_weight_as_the_pack_material():
    from frame_motions.m27_ira_heart import static_layers

    letter_alpha = [
        np.asarray(layer.image.getchannel("A"))
        for layer in static_layers(400)
        if layer.name.startswith("letter_")
    ]
    assert sum(int(np.count_nonzero(alpha > 32)) for alpha in letter_alpha) <= 7200


def test_ira_heart_outline_has_the_pack_weight_without_fattening_the_letters():
    from frame_motions.m27_ira_heart import static_layers

    heart_alpha = [
        np.asarray(layer.image.getchannel("A"))
        for layer in static_layers(400)
        if layer.name.startswith("heart_")
    ]
    assert sum(int(np.count_nonzero(alpha > 32)) for alpha in heart_alpha) >= 9000


def test_clean_static_ira_has_no_closure_accents():
    from frame_motions.m27_ira_heart import draw_static_frame, static_layers

    image = draw_static_frame(400)
    assert image.getchannel("A").getbbox() is not None
    assert "closure_accents" not in {layer.name for layer in static_layers(400)}


def test_ira_heart_native_contract_and_brand_color():
    from frame_motions.m27_ira_heart import SPEC

    frames = render_motion(SPEC)
    assert SPEC.duration_frames == 42
    assert len(frames) == 42
    assert alpha_sum(frames[0]) == 0
    assert alpha_sum(frames[-1]) == 0
    middle = np.asarray(frames[28])
    brand = np.max(
        np.abs(middle[:, :, :3].astype(np.int16) - np.array((46, 58, 77))),
        axis=2,
    ) < 20
    assert int(np.count_nonzero(brand)) >= 180


def test_ira_heart_stays_inside_telegram_safe_area():
    from frame_motions.m27_ira_heart import SPEC

    for index, image in enumerate(render_motion(SPEC)):
        alpha = np.asarray(image.getchannel("A"))
        ys, xs = np.where(alpha >= 24)
        if len(xs):
            assert xs.min() >= 8 and xs.max() < 92, index
            assert ys.min() >= 8 and ys.max() < 92, index
