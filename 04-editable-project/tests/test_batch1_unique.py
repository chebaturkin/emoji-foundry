import numpy as np
from PIL import Image, ImageChops

from frame_motions.m01_heart import draw_frame as draw_m01
from frame_motions.m04_star import draw_frame as draw_m02
from frame_motions.m06_spark import draw_frame as draw_m03
from frame_motions.m09_idea import draw_frame as draw_m05
from frame_motions.m11_eye import draw_frame as draw_m06
from motion_core.render import render_motion


BATCH1_DRAW_FRAMES = (
    draw_m01,
    draw_m02,
    draw_m03,
    draw_m05,
    draw_m06,
)


def alpha_sum(image):
    return int(np.asarray(image.getchannel("A"), dtype=np.uint64).sum())


def union_alpha(layers, names):
    selected = [layer.image.getchannel("A") for layer in layers if layer.name in names]
    assert selected
    result = selected[0]
    for alpha in selected[1:]:
        result = ImageChops.lighter(result, alpha)
    return result


def maximum_identical_nonblank_run(frames):
    maximum = 1
    current = 1
    for previous, current_frame in zip(frames, frames[1:]):
        identical = np.array_equal(
            np.asarray(previous),
            np.asarray(current_frame),
        )
        if identical and current_frame.getchannel("A").getbbox() is not None:
            current += 1
            maximum = max(maximum, current)
        else:
            current = 1
    return maximum


def test_redesigned_faces_never_hold_blank_endpoints():
    from frame_motions.m12_smile import SPEC as smile
    from frame_motions.m14_sad import SPEC as sad
    for spec in (smile, sad):
        frames = render_motion(spec)
        assert frames[0].getchannel("A").getbbox() is None, spec.stem
        assert frames[-1].getchannel("A").getbbox() is None, spec.stem


def test_faces_redesign_uses_coherent_layers_and_state_contracts():
    from frame_motions.m12_smile import SPEC as smile, smile_layers, smile_state
    from frame_motions.m14_sad import SPEC as sad, sad_layers, sad_state

    assert smile.duration_frames == 48
    assert sad.duration_frames == 48
    assert {layer.name for layer in smile_layers(24, 100)} == {
        "blue_depth", "paper_face", "blue_outline", "ink_features", "cheek_lift"
    }
    assert {layer.name for layer in sad_layers(24, 100)} == {
        "blue_depth", "paper_face", "blue_outline", "ink_features", "tear_fall", "face_drop"
    }
    assert {"face", "wink", "cheek_lift"} <= smile_state(24, 100).keys()
    assert {"face", "tear_fall", "face_drop"} <= sad_state(24, 100).keys()


def test_faces_redesign_has_blank_authored_endpoints():
    from frame_motions.m12_smile import SPEC as smile
    from frame_motions.m14_sad import SPEC as sad

    for spec in (smile, sad):
        frames = render_motion(spec)
        assert len(frames) == 48
        assert sum(frames[0].getchannel("A").getdata()) == 0
        assert sum(frames[-1].getchannel("A").getdata()) == 0


def test_batch1_specs_keep_solid_late_ink_and_blank_endpoints():
    for draw_frame in BATCH1_DRAW_FRAMES:
        assert alpha_sum(draw_frame(0, 400)) == 0
        assert np.asarray(draw_frame(54, 400).getchannel("A")).max() == 255
        assert alpha_sum(draw_frame(59, 400)) == 0


def test_heart_drops_converge_before_material_impact():
    from frame_motions.m01_heart import heart_state

    early = heart_state(8, 400)
    joined = heart_state(22, 400)
    assert early["drop_distance"] > joined["drop_distance"] * 2
    assert joined["body_scale"] > early["body_scale"]


def test_star_tips_unfold_clockwise():
    from frame_motions.m04_star import tip_timeline

    starts = [tip_timeline()[index][0] for index in range(5)]
    assert starts == sorted(starts)
    assert len(set(starts)) == 5


def test_spark_axes_and_rays_have_distinct_starts():
    from frame_motions.m06_spark import spark_timeline

    timeline = spark_timeline()
    assert timeline["vertical"][0] < timeline["horizontal"][0]
    ray_starts = [
        value[0] for key, value in timeline.items() if key.startswith("ray_")
    ]
    assert timeline["horizontal"][0] < min(ray_starts)
    assert len(set(ray_starts)) == 4


def test_idea_filament_precedes_glass_and_base():
    from frame_motions.m09_idea import idea_state

    early = idea_state(10, 400)
    assert early["filament"] > early["glass"]
    assert early["glass"] > early["base"]


def test_idea_layers_consume_idea_state_as_the_build_clock(monkeypatch):
    import frame_motions.m09_idea as idea

    def zero_state(frame, size):
        return {"filament": 0.0, "glass": 0.0, "base": 0.0, "rays": 0.0}

    monkeypatch.setattr(idea, "idea_state", zero_state)
    build_layers = {
        "glass_shadow",
        "glass_light",
        "filament",
        "glass_far",
        "base",
        "glass_near",
        "rays",
    }
    for layer in idea.idea_layers(36, 400):
        if layer.name in build_layers:
            assert alpha_sum(layer.image) == 0


def test_spark_shadow_is_complete_two_frame_lagged_body_mask():
    from frame_motions.m06_spark import spark_layers

    frame = 54
    body_names = {"vertical", "horizontal", *(f"ray_{index}" for index in range(4))}
    shadow_names = {
        "vertical_shadow",
        "horizontal_shadow",
        *(f"ray_{index}_shadow" for index in range(4)),
    }
    lagged_body = union_alpha(spark_layers(frame - 2, 400), body_names)
    expected = ImageChops.offset(lagged_body, 8, 12)
    actual = union_alpha(spark_layers(frame, 400), shadow_names)
    assert np.array_equal(np.asarray(actual) > 0, np.asarray(expected) > 0)


def test_idea_shadow_is_complete_two_frame_lagged_glass_mask():
    from frame_motions.m09_idea import idea_layers

    frame = 54
    lagged_glass = union_alpha(
        idea_layers(frame - 2, 400), {"glass_near", "glass_far"}
    )
    expected = ImageChops.offset(lagged_glass, 8, 12)
    actual = union_alpha(idea_layers(frame, 400), {"glass_shadow"})
    assert np.array_equal(np.asarray(actual) > 0, np.asarray(expected) > 0)


def test_new_batch1_specs_keep_solid_late_ink_and_blank_endpoints():
    from frame_motions.m06_spark import draw_frame as draw_spark
    from frame_motions.m09_idea import draw_frame as draw_idea

    for draw_frame in (draw_spark, draw_idea):
        assert alpha_sum(draw_frame(0, 400)) == 0
        assert np.asarray(draw_frame(54, 400).getchannel("A")).max() == 255
        assert alpha_sum(draw_frame(59, 400)) == 0


def test_spark_tactile_intersection_is_detail_not_shadow():
    from frame_motions.m06_spark import spark_layers

    names = {layer.name for layer in spark_layers(36, 400)}
    assert "intersection_detail" in names
    assert "intersection_shadow" not in names


def test_star_glint_stays_on_visible_material():
    from frame_motions.m04_star import star_layers

    for frame in (32, 34, 36, 38, 40, 41):
        layers = star_layers(frame, 400)
        material = next(
            layer.image.getchannel("A")
            for layer in layers
            if layer.name == "paper_core"
        )
        for layer in layers:
            if layer.name.startswith("tip_") and not layer.name.endswith("_shadow"):
                material = ImageChops.lighter(material, layer.image.getchannel("A"))
        glint = next(
            layer.image.getchannel("A")
            for layer in layers
            if layer.name == "travelling_glint"
        )
        glint_pixels = np.asarray(glint) > 0
        material_pixels = np.asarray(material) > 0
        assert glint_pixels.any()
        assert (glint_pixels & material_pixels).sum() >= glint_pixels.sum() * 0.95


def test_heart_shadow_retraction_uses_two_frame_lag():
    from frame_motions.m01_heart import _heart_geometry, heart_layers

    frame = 54
    expected = _heart_geometry(frame - 2, 400)
    shadow = next(
        layer.image
        for layer in heart_layers(frame, 400)
        if layer.name == "material_shadow"
    )
    assert abs(shadow.getbbox()[2] - shadow.getbbox()[0] - np.ptp(expected[:, 0])) <= 2


def test_star_core_shadow_retraction_uses_two_frame_lag():
    from frame_motions.m04_star import _core_geometry, star_layers

    frame = 56
    expected = _core_geometry(frame - 2, 400)
    shadow = next(
        layer.image
        for layer in star_layers(frame, 400)
        if layer.name == "core_shadow"
    )
    assert abs(shadow.getbbox()[2] - shadow.getbbox()[0] - np.ptp(expected[:, 0])) <= 2


def test_all_star_tip_shadows_use_complete_two_frame_lag():
    from frame_core.composite import phase, smooth
    from frame_motions.m04_star import (
        SHADOW_BLUE,
        _filled_polygon,
        _tip_geometry,
        star_layers,
    )

    frame = 56
    shadow_frame = frame - 2
    shadow_remain = 1.0 - smooth(phase(shadow_frame, 53, 59))
    shadow_offset = np.array((2.3, 3.0)) * 4 * shadow_remain
    layers = {layer.name: layer.image for layer in star_layers(frame, 400)}

    for index in range(5):
        geometry = _tip_geometry(shadow_frame, index, 400)
        expected = _filled_polygon(geometry + shadow_offset, SHADOW_BLUE, 400)
        assert np.array_equal(
            np.asarray(layers[f"tip_{index}_shadow"].getchannel("A")),
            np.asarray(expected.getchannel("A")),
        )


def test_eye_searches_then_focuses():
    from frame_motions.m11_eye import eye_state

    left = eye_state(22, 400)
    right = eye_state(28, 400)
    focus = eye_state(36, 400)
    assert left["pupil_x"] < 0 < right["pupil_x"]
    assert focus["iris_scale"] < right["iris_scale"]


def _smile_layer_images(frame, size=400):
    from frame_motions.m12_smile import smile_layers

    return {layer.name: layer.image for layer in smile_layers(frame, size)}


def _pixel_coverage(image):
    return int((np.asarray(image.getchannel("A")) > 0).sum())


def test_smile_is_a_48_frame_face_motion_with_coherent_layers():
    from frame_motions.m12_smile import SPEC, draw_frame, smile_state
    assert SPEC.draw_frame is draw_frame
    assert SPEC.duration_frames == 48
    frames = render_motion(SPEC)
    assert len(frames) == 48
    assert alpha_sum(frames[0]) == 0 and alpha_sum(frames[-1]) == 0
    assert smile_state(4, 100)["face"] > 0
    assert smile_state(4, 100)["cheek_lift"] == 0
    assert smile_state(27, 100)["wink"] > 0


def test_smile_family_layers_are_named_and_palette_safe():
    from frame_motions.m12_smile import smile_layers
    images = _smile_layer_images(24, 100)
    assert list(images) == ["blue_depth", "paper_face", "blue_outline", "ink_features", "cheek_lift"]
    allowed = {(46, 58, 77), (196, 193, 180), (242, 240, 233), (13, 13, 13), (0, 0, 0)}
    for image in images.values():
        colors = {tuple(color) for color in np.asarray(image)[:, :, :3].reshape(-1, 3)}
        assert colors <= allowed


def _sad_layer_images(frame, size=400):
    from frame_motions.m14_sad import sad_layers

    return {layer.name: layer.image for layer in sad_layers(frame, size)}


def _connected_components(image):
    pixels = np.asarray(image.getchannel("A")) > 0
    remaining = set(zip(*np.where(pixels)))
    components = []
    while remaining:
        stack = [remaining.pop()]
        component = []
        while stack:
            y, x = stack.pop()
            component.append((y, x))
            for neighbor in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def _solid_component_count(image, minimum_pixels=20):
    return sum(
        len(component) >= minimum_pixels
        for component in _connected_components(image)
    )


def _curve_center_minus_ends(image):
    pixels = np.asarray(image.getchannel("A")) > 0
    _, xx = np.where(pixels)
    left, right = np.quantile(xx, (0.16, 0.84))
    span = right - left
    center = pixels[:, (xx.min() + xx.max()) // 2 - 6:(xx.min() + xx.max()) // 2 + 7]
    ends = np.concatenate(
        (
            np.where(pixels[:, int(left):int(left + span * 0.18)])[0],
            np.where(pixels[:, int(right - span * 0.18):int(right) + 1])[0],
        )
    )
    return float(np.where(center)[0].mean() - ends.mean())


def test_sad_is_a_48_frame_settling_face_with_weighted_tear():
    from frame_motions.m14_sad import SPEC, draw_frame, sad_state
    assert SPEC.draw_frame is draw_frame
    assert SPEC.duration_frames == 48
    frames = render_motion(SPEC)
    assert len(frames) == 48
    assert alpha_sum(frames[0]) == 0 and alpha_sum(frames[-1]) == 0
    assert sad_state(16, 100)["face_drop"] > 0
    assert sad_state(16, 100)["tear_fall"] == 0
    assert sad_state(32, 100)["tear_fall"] > 0


def test_sad_family_keeps_contour_intact_and_tear_slides_down():
    images = _sad_layer_images(32, 100)
    assert list(images) == ["blue_depth", "paper_face", "blue_outline", "ink_features", "tear_fall", "face_drop"]
    tear = images["tear_fall"].getchannel("A").getbbox()
    assert tear is not None and tear[3] > 60
    assert _solid_component_count(images["blue_outline"], minimum_pixels=4) == 1


def _assert_two_frame_shadow_lag(
    layers, frame, material_names, shadow_name, directional=False
):
    lagged_material = union_alpha(layers(frame - 2, 400), material_names)
    expected = ImageChops.offset(lagged_material, 8, 12)
    if directional:
        expected = ImageChops.subtract(expected, lagged_material)
    actual = union_alpha(layers(frame, 400), {shadow_name})
    assert np.array_equal(np.asarray(actual) > 0, np.asarray(expected) > 0)


def test_eye_shadow_keeps_true_two_frame_lag_during_exit():
    from frame_motions.m11_eye import eye_layers

    _assert_two_frame_shadow_lag(
        eye_layers, 56, {"paper_surface"}, "blue_shadow"
    )


def test_eye_material_finishes_before_lagged_shadow():
    from frame_motions.m11_eye import eye_layers

    material = next(
        layer.image for layer in eye_layers(57, 400) if layer.name == "paper_surface"
    )
    shadow = next(
        layer.image for layer in eye_layers(59, 400) if layer.name == "blue_shadow"
    )
    assert alpha_sum(material) == 0
    assert alpha_sum(shadow) == 0


def test_eye_late_shadow_coverage_tapers_to_zero():
    from frame_motions.m11_eye import eye_layers

    coverage = []
    for frame in range(54, 60):
        shadow = next(
            layer.image for layer in eye_layers(frame, 400) if layer.name == "blue_shadow"
        )
        coverage.append(int((np.asarray(shadow.getchannel("A")) > 0).sum()))
    assert coverage == sorted(coverage, reverse=True)
    assert coverage[-2] < 1500
    assert coverage[-1] == 0


def test_new_eye_layer_compositions_are_blank_at_endpoints():
    from frame_motions.m11_eye import eye_layers

    for layer in eye_layers(59, 400):
        assert alpha_sum(layer.image) == 0, layer.name


def test_new_eye_keeps_solid_late_ink_and_blank_endpoints():
    from frame_motions.m11_eye import draw_frame as draw_eye
    from frame_motions.m11_eye import eye_layers

    assert alpha_sum(draw_eye(0, 400)) == 0
    late_ink = union_alpha(eye_layers(54, 400), {"upper_lid", "lower_lid"})
    late_alpha = np.asarray(late_ink)
    assert late_alpha.max() == 255
    assert (late_alpha > 0).sum() > 400
    assert alpha_sum(draw_eye(59, 400)) == 0
