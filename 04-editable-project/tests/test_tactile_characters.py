import numpy as np


def test_laugh_cheeks_move_before_tongue():
    from frame_motions.m13_laugh import face_geometry

    neutral = face_geometry(20, 400)
    opening = face_geometry(28, 400)
    cheek_motion = abs(opening["cheek_y"] - neutral["cheek_y"])
    tongue_motion = abs(opening["tongue_y"] - neutral["tongue_y"])
    assert cheek_motion > tongue_motion


def test_explosion_back_lobes_precede_front_lobes():
    from frame_motions.m25_explosion_cloud import lobe_timeline

    timeline = lobe_timeline()
    assert max(timeline[name][0] for name in ("back_left", "back_right")) < min(
        timeline[name][0] for name in ("front_left", "front_right")
    )


def test_laugh_and_explosion_keep_solid_ink_during_exit():
    from frame_motions.m13_laugh import SPEC as laugh
    from frame_motions.m25_explosion_cloud import SPEC as explosion

    for spec in (laugh, explosion):
        alpha = np.asarray(spec.draw_frame(54, 400).getchannel("A"))
        assert alpha.max() == 255
