import numpy as np
from PIL import Image

from frame_core.composite import finalize_frame, phase
from frame_core.models import FrameMotionSpec


def alpha_sum(image):
    return int(np.asarray(image.getchannel("A"), dtype=np.uint64).sum())


def test_frame_motion_spec_defaults_to_42_supersampled_frames():
    def draw(frame: int, size: int) -> Image.Image:
        return Image.new("RGBA", (size, size), (0, 0, 0, 0))

    spec = FrameMotionSpec("demo", draw)
    assert spec.duration_frames == 42
    assert spec.fps == 30
    assert spec.supersample == 4
    assert spec.draw_frame(10, 400).size == (400, 400)


def test_phase_has_locked_endpoints():
    assert phase(5, 10, 20) == 0.0
    assert phase(10, 10, 20) == 0.0
    assert phase(15, 10, 20) == 0.5
    assert phase(20, 10, 20) == 1.0
    assert phase(30, 10, 20) == 1.0


def test_finalize_frame_returns_clean_100px_rgba():
    source = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    source.putpixel((200, 200), (46, 58, 77, 255))
    result = finalize_frame(source)
    assert result.mode == "RGBA"
    assert result.size == (100, 100)
    assert result.getpixel((0, 0)) == (0, 0, 0, 0)


def test_finalize_frame_applies_a_fixed_safe_inset():
    source = Image.new("RGBA", (400, 400), (46, 58, 77, 255))
    result = finalize_frame(source)
    alpha = np.asarray(result.getchannel("A"))
    bbox = Image.fromarray((alpha >= 24).astype(np.uint8) * 255, "L").getbbox()
    assert bbox is not None
    assert bbox[0] >= 8 and bbox[1] >= 8
    assert bbox[2] <= 92 and bbox[3] <= 92


def test_heart_19_draws_contour_then_fill_then_holds():
    from frame_motions.m03_heart_open import SPEC as heart

    frames = [heart.draw_frame(index, 400) for index in (0, 10, 24, 36, 48, 59)]
    alpha = [alpha_sum(frame) for frame in frames]
    assert alpha[0] < alpha[1] < alpha[2] < alpha[3]
    assert alpha[4] > alpha[2]
    assert alpha[5] == 0


def test_heart_19_fill_has_an_organic_front():
    from frame_motions.m03_heart_open import _fill_layer, heart_path

    alpha = np.asarray(_fill_layer(heart_path(400), 32, 400).getchannel("A"))
    front = []
    for x in range(40, 360):
        visible = np.where(alpha[:, x] >= 128)[0]
        if len(visible):
            front.append(int(visible.min()))
    assert len(set(front)) >= 8
    assert np.std(front) >= 4.0


def test_lightning_builds_before_discharge():
    from frame_motions.m07_lightning import SPEC as lightning

    alpha = [alpha_sum(lightning.draw_frame(index, 400)) for index in (0, 10, 22, 34, 52)]
    assert alpha[0] < alpha[1] < alpha[2]
    assert alpha[3] >= alpha[2] * 0.8
    assert alpha[4] > 0


def test_bulb_draws_glass_before_inner_star():
    from frame_motions.m10_bulb_spark import SPEC as bulb

    early = np.asarray(bulb.draw_frame(12, 400))
    lit = np.asarray(bulb.draw_frame(34, 400))
    center = np.s_[120:280, 120:280, 3]
    assert lit[center].sum() > early[center].sum() * 1.25


def test_laugh_changes_actual_mouth_pixels():
    from frame_motions.m13_laugh import SPEC as laugh

    closed = np.asarray(laugh.draw_frame(14, 400))
    open_mouth = np.asarray(laugh.draw_frame(30, 400))
    mouth = np.s_[190:330, 90:310, :]
    assert np.mean(np.abs(open_mouth[mouth].astype(int) - closed[mouth].astype(int))) > 12


def test_laugh_starts_from_a_clean_empty_frame():
    from frame_motions.m13_laugh import SPEC as laugh

    assert alpha_sum(laugh.draw_frame(0, 400)) == 0


def test_cloud_lobes_appear_in_sequence():
    from frame_motions.m25_explosion_cloud import SPEC as cloud

    sums = [alpha_sum(cloud.draw_frame(index, 400)) for index in (4, 10, 16, 24, 38)]
    assert sums[0] < sums[1] < sums[2] < sums[3]
    assert sums[4] >= sums[3] * 0.85


def test_cloud_final_shape_has_no_internal_lobe_seams():
    from frame_motions.common import BLUE
    from frame_motions.m25_explosion_cloud import SPEC as cloud

    image = np.asarray(cloud.draw_frame(48, 400))
    center = image[110:290, 110:290]
    distance = np.linalg.norm(center[:, :, :3].astype(float) - np.array(BLUE[:3]), axis=2)
    internal_blue = ((distance < 12) & (center[:, :, 3] > 200)).sum()
    assert internal_blue < 5000


def test_all_pilot_motions_have_a_clean_loop():
    from frame_motions.m07_lightning import SPEC as lightning
    from frame_motions.m13_laugh import SPEC as laugh
    from frame_motions.m03_heart_open import SPEC as heart
    from frame_motions.m25_explosion_cloud import SPEC as cloud
    from frame_motions.m10_bulb_spark import SPEC as bulb

    for spec in (lightning, laugh, heart, cloud, bulb):
        start = np.asarray(spec.draw_frame(0, 400), dtype=np.int16)
        end = np.asarray(spec.draw_frame(59, 400), dtype=np.int16)
        assert np.mean(np.abs(end - start)) < 0.1, spec.stem
