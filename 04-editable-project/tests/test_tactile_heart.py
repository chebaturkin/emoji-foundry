import numpy as np


def alpha_sum(image):
    return int(np.asarray(image.getchannel("A"), dtype=np.uint64).sum())


def test_heart_shadow_arrives_before_main_ink():
    from frame_motions.m03_heart_open import heart_layers

    layers = {layer.name: layer.image for layer in heart_layers(5, 400)}
    assert alpha_sum(layers["shadow"]) > alpha_sum(layers["outline"])


def test_heart_lobes_move_more_than_anchored_tail():
    from frame_motions.m03_heart_open import heart_geometry

    before = heart_geometry(36, 400)
    after = heart_geometry(41, 400)
    tail_motion = np.linalg.norm(after[0] - before[0])
    lobe_motion = np.linalg.norm(after[70] - before[70])
    assert lobe_motion > max(0.1, tail_motion * 1.8)


def test_heart_retracts_spatially_instead_of_fading():
    from frame_motions.m03_heart_open import SPEC

    frame_52 = SPEC.draw_frame(52, 400)
    frame_56 = SPEC.draw_frame(56, 400)
    assert np.asarray(frame_52.getchannel("A")).max() == 255
    assert np.asarray(frame_56.getchannel("A")).max() == 255
    assert alpha_sum(frame_56) < alpha_sum(frame_52)
