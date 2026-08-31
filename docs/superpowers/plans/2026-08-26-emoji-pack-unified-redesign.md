# Unified Emoji Pack Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the selected animations, enforce the approved four-color language, physically renumber all 27 emoji, and regenerate a validated Telegram release package.

**Architecture:** Keep `FrameMotionSpec` and the existing frame/TGS/WebM pipeline. Express each animation through semantic state functions and focused layer builders, add one shared geometry helper only for the related like/dislike hands, and preserve every approved animation outside the explicitly scoped palette changes. Perform the renumbering last through a tested collision-safe migration utility, then rebuild every generated artifact from renamed canonical sources.

**Tech Stack:** Python 3.10+, Pillow, NumPy, scikit-image, pytest, bundled ffmpeg/libvpx-vp9, Lottie/TGS gzip JSON.

**Repository note:** This project has no `.git` directory. Where the standard workflow calls for a commit, create and verify a `SHA256SUMS` checkpoint instead; do not initialize Git unless the user separately requests it.

---

### Task 1: Lock the Four-Color Contract and Agent Guidance

**Files:**
- Modify: `AGENTS.md`
- Modify: `04-editable-project/frame_motions/common.py`
- Modify: `04-editable-project/tgs_core/vectorize.py`
- Modify: `04-editable-project/validate_tgs.py`
- Modify: `04-editable-project/tests/test_brand_palette.py`
- Modify: `04-editable-project/tests/test_tgs_export.py`

- [ ] **Step 1: Add a failing authored-palette regression test**

Add this contract to `tests/test_brand_palette.py`:

```python
from pathlib import Path
import re


def test_authored_sources_contain_no_forbidden_color_literals():
    root = Path(__file__).resolve().parents[1] / "frame_motions"
    forbidden = re.compile(
        r"\(\s*(?:255\s*,\s*255\s*,\s*255|"
        r"91\s*,\s*139\s*,\s*196|112\s*,\s*151\s*,\s*194)\s*,"
    )
    violations = []
    for path in sorted(root.glob("*.py")):
        for line_number, line in enumerate(path.read_text().splitlines(), start=1):
            if forbidden.search(line):
                violations.append((path.name, line_number, line.strip()))
    assert violations == []
```

- [ ] **Step 2: Run the test and verify the existing pure-white literals fail**

Run: `cd 04-editable-project && python3 -m pytest tests/test_brand_palette.py::test_authored_sources_contain_no_forbidden_color_literals -q`

Expected: FAIL listing pure white in `m01_heart.py`, `m04_star.py`, `m07_lightning.py`, `m09_idea.py`, `m11_eye.py`, `m13_laugh.py`, `m25_explosion_cloud.py`, and `m10_bulb_spark.py`.

- [ ] **Step 3: Replace white literals and restrict exporter/validator palettes**

Import `PAPER` where needed and replace every visible pure-white RGBA tuple with `PAPER` or `(*PAPER[:3], computed_alpha)`. Change both TGS palette declarations to exactly:

```python
PALETTE = (BLUE[:3], TAUPE[:3], PAPER[:3], INK[:3])
ALLOWED_COLORS = {BLUE[:3], TAUPE[:3], PAPER[:3], INK[:3]}
```

Add to `AGENTS.md` the four exact hex values, their approved roles from the design spec, the prohibition on all other RGB values, and the semantic motion grammar: anticipation, meaningful action, material response, and retraction without global fade or generic scale/pulse.

- [ ] **Step 4: Add a TGS test that rejects pure white**

Extend the palette assertion in `tests/test_tgs_export.py` so the expected fill colors are exactly:

```python
allowed = {
    (46, 58, 77),
    (196, 193, 180),
    (242, 240, 233),
    (13, 13, 13),
}
assert exported_colors <= allowed
assert (255, 255, 255) not in exported_colors
```

- [ ] **Step 5: Verify palette tests and the full existing suite**

Run: `python3 -m pytest tests/test_brand_palette.py tests/test_tgs_export.py -q`

Expected: PASS.

Run: `python3 -m pytest -q`

Expected: all tests pass after updating any old white-specific test vocabulary to “paper,” with no animation timing changes.

- [ ] **Step 6: Record a checksum checkpoint**

Run from the package root: `shasum -a 256 AGENTS.md 04-editable-project/frame_motions/*.py 04-editable-project/tgs_core/*.py 04-editable-project/tests/*.py > docs/superpowers/plans/checkpoint-01-palette.sha256`

Expected: a non-empty checkpoint file covering guidance, authored motion code, TGS code, and tests.

### Task 2: Redesign the Face Family

**Files:**
- Modify: `04-editable-project/frame_motions/m12_smile.py`
- Modify: `04-editable-project/frame_motions/m14_sad.py`
- Modify: `04-editable-project/frame_motions/m15_surprise.py`
- Modify: `04-editable-project/tests/test_batch1_unique.py`
- Modify: `04-editable-project/tests/test_batch2_unique.py`
- Modify: `04-editable-project/tests/test_build.py`

- [ ] **Step 1: Replace old line-fragment tests with failing face-family contracts**

Add focused assertions using public state and layer functions:

```python
def test_smile_face_forms_before_cheeks_lift_and_wink():
    from frame_motions.m12_smile import smile_state
    forming = smile_state(9, 400)
    smiling = smile_state(24, 400)
    assert forming["face"] > forming["wink"]
    assert smiling["cheek_lift"] > forming["cheek_lift"]
    assert smiling["wink"] > forming["wink"]


def test_sad_face_settles_before_weighted_tear_falls():
    from frame_motions.m14_sad import sad_state
    concern = sad_state(18, 400)
    falling = sad_state(31, 400)
    assert concern["face"] > concern["tear_fall"]
    assert falling["face_drop"] > concern["face_drop"]
    assert falling["tear_fall"] > concern["tear_fall"]


def test_surprise_is_a_face_without_external_shock_rays():
    from frame_motions.m15_surprise import surprise_layers, surprise_state
    opening = surprise_state(20, 400)
    assert opening["mouth_open"] > opening["eyes_wide"]
    assert opening["recoil"] > 0
    assert "shock_wave" not in {layer.name for layer in surprise_layers(20, 400)}
```

- [ ] **Step 2: Run the three tests and verify API/behavior failures**

Run each new test directly with `python3 -m pytest <file>::<test_name> -q`.

Expected: FAIL because the old sparse-line APIs and shock layer do not satisfy the new face-family contract.

- [ ] **Step 3: Implement shared visual construction inside each focused module**

Use the approved `m13_laugh.py` proportions without importing its private functions. Each module must expose a state function with the exact keys used above and layers named `blue_depth`, `paper_face`, `blue_outline`, `ink_features`, plus a semantic accent such as `blue_tear`. Construct the face from a jittered closed contour, fill it with `PAPER`, draw delayed `BLUE` depth, and use `INK` only for facial features.

Set all three specs to:

```python
SPEC = FrameMotionSpec(
    "<existing-stem>",
    draw_frame,
    duration_frames=48,
    tags=("soft", "tactile"),
)
```

For smile, remove the floating smile/eye-only composition and spark. For sad, remove fragmented line exit and keep one falling blue tear. For surprise, remove external rays and drive mouth, eyes, and contour recoil locally.

- [ ] **Step 4: Update mixed-duration and native-contract tests**

In `tests/test_build.py`, `tests/test_batch1_unique.py`, and `tests/test_batch2_unique.py`, update only `07`, `09`, and `10` expectations from 42 to 48 frames. Replace hard-coded sample frames with proportional indices `(7, 16, 26, 36, 46)` for these specs and keep the original expectations for unaffected stems.

- [ ] **Step 5: Verify face tests and render contracts**

Run: `python3 -m pytest tests/test_batch1_unique.py tests/test_batch2_unique.py tests/test_motions.py tests/test_build.py -q`

Expected: PASS; all three specs have blank authored endpoints, unique motion signatures, and content inside the 8-pixel safe area.

- [ ] **Step 6: Build and validate the face group**

Run for `12-smile`, `14-sad`, and `15-surprise`:

```bash
python3 build_all.py --only <stem> --preview --encode
python3 validate_animated.py --only <stem>
python3 build_tgs.py --only <stem>
python3 validate_tgs.py --only <stem>
```

Expected: all three WebM and TGS files pass and remain under Telegram limits.

- [ ] **Step 7: Create dark/light QA sheets and pause for user approval**

Extend `build_batch_qa.py` with a `faces-redesign` selection containing the three stems, render representative frames at 20%, 45%, 65%, and 85% of each timeline on both backgrounds, and save `previews/qa-faces-redesign-dark.png` and `previews/qa-faces-redesign-light.png` plus `previews/contact-sheet-faces-redesign.gif`.

Expected: do not begin Task 3 until the user approves the face group.

### Task 3: Replace Raster-Sliced Hands with Articulated Geometry

**Files:**
- Create: `04-editable-project/frame_motions/hand_geometry.py`
- Modify: `04-editable-project/frame_motions/m16_like.py`
- Modify: `04-editable-project/frame_motions/m17_dislike.py`
- Modify: `04-editable-project/tests/test_batch2_unique.py`
- Modify: `04-editable-project/tests/test_project_paths.py`

- [ ] **Step 1: Add failing geometry and motion tests**

```python
def test_like_and_dislike_use_continuous_authored_hand_geometry():
    from frame_motions.m16_like import hand_layers as like_layers
    from frame_motions.m17_dislike import hand_layers as dislike_layers
    for layers in (like_layers(25, 400), dislike_layers(25, 400)):
        names = {layer.name for layer in layers}
        assert names == {"blue_depth", "paper_hand", "blue_outline", "ink_creases"}


def test_like_thumb_unfolds_after_wrist_turns_without_spark():
    from frame_motions.m16_like import like_state
    entering = like_state(10, 400)
    confirming = like_state(29, 400)
    assert entering["wrist_turn"] > entering["thumb_extension"]
    assert confirming["thumb_extension"] > entering["thumb_extension"]
    assert "spark" not in confirming


def test_dislike_thumb_drops_with_cuff_lag():
    from frame_motions.m17_dislike import dislike_state
    dropping = dislike_state(24, 400)
    settling = dislike_state(31, 400)
    assert dropping["thumb_drop"] > dropping["cuff_follow"]
    assert settling["cuff_follow"] > dropping["cuff_follow"]
```

- [ ] **Step 2: Verify the old sliced-master implementation fails**

Run: `python3 -m pytest tests/test_batch2_unique.py -k 'continuous_authored_hand_geometry or thumb_unfolds or thumb_drops' -q`

Expected: FAIL because `hand_layers` and the new state keys do not exist.

- [ ] **Step 3: Implement `hand_geometry.py`**

Define immutable authored control points at a 100-unit coordinate scale and expose:

```python
@dataclass(frozen=True)
class HandPose:
    silhouette: np.ndarray
    thumb_joint: np.ndarray
    crease_paths: Sequence[np.ndarray]


def hand_pose(
    direction: Literal["up", "down"],
    progress: float,
    size: int,
) -> HandPose:
    if direction not in {"up", "down"}:
        raise ValueError(f"unknown hand direction: {direction}")
    progress = float(np.clip(progress, 0.0, 1.0))
    relaxed, final, relaxed_joint, final_joint, creases = HAND_CONTROLS[direction]
    silhouette = morph_points(relaxed, final, progress, count=96) * size / 100.0
    thumb_joint = (
        relaxed_joint + (final_joint - relaxed_joint) * progress
    ) * size / 100.0
    scaled_creases = tuple(path * size / 100.0 for path in creases)
    return HandPose(silhouette, thumb_joint, scaled_creases)
```

The returned silhouette must be one closed path containing cuff, wrist, palm, grouped fingers, and thumb. Interpolate authored relaxed and final control points with `smooth`, resample compatible paths before interpolation, and keep all coordinates within 10–90 at the 100-unit scale.

- [ ] **Step 4: Rewrite like/dislike rendering without `master_image`, `masked_part`, or rectangular masks**

Both modules render `BLUE` delayed depth, a `PAPER` polygon, a pressure-sensitive `BLUE` outline, and sparse `INK` crease strokes. Like enters from below, turns the wrist, and extends the thumb. Dislike follows a distinct downward trajectory, drops its thumb with weight, and delays cuff response. Set both durations to 48 frames and expose `hand_layers(frame, size)`.

- [ ] **Step 5: Assert the modules no longer depend on masters**

Extend `test_project_paths.py`:

```python
def test_authored_hands_do_not_slice_raster_masters():
    for name in ("m16_like.py", "m17_dislike.py"):
        source = (PROJECT_ROOT / "frame_motions" / name).read_text()
        assert "master_image" not in source
        assert "masked_part" not in source
```

- [ ] **Step 6: Run focused tests, build both stems, and pause for approval**

Run focused tests, the full suite, the four build/validation commands for both stems, and create `qa-hands-redesign-dark.png`, `qa-hands-redesign-light.png`, and `contact-sheet-hands-redesign.gif`.

Expected: no task beyond Task 3 proceeds until the user confirms the hands look anatomical and alive.

### Task 4: Apply the Approved Check and Lightning Corrections

**Files:**
- Modify: `04-editable-project/frame_motions/m07_lightning.py`
- Modify: `04-editable-project/frame_motions/m20_check.py`
- Modify: `04-editable-project/tests/test_tactile_symbols.py`
- Modify: `04-editable-project/tests/test_batch2_unique.py`

- [ ] **Step 1: Add failing layer/color tests**

```python
def test_lightning_has_no_lateral_branch_layer():
    from frame_motions.m07_lightning import lightning_layers
    assert "branches" not in {layer.name for layer in lightning_layers(31, 400)}


def test_check_foreground_is_paper_with_blue_depth():
    from frame_motions.common import BLUE, PAPER
    from frame_motions.m20_check import check_layers
    layers = {layer.name: np.asarray(layer.image) for layer in check_layers(24, 400)}
    assert has_visible_color(layers["confident_check"], PAPER[:3])
    assert not has_visible_color(layers["confident_check"], BLUE[:3])
    assert has_visible_color(layers["lagging_shadow"], BLUE[:3])
```

Define `has_visible_color` in the test as an exact RGB comparison restricted to alpha greater than 32.

- [ ] **Step 2: Run and observe failures**

Expected: lightning test fails because `branches` exists; check test fails because the foreground is blue.

- [ ] **Step 3: Remove the branch layer and recolor only the check foreground**

Delete branch geometry, timing, and the `branches` depth layer from `m07_lightning.py`. Keep charge, bend, echo, fill, outline, and 60-frame duration unchanged. In `m20_check.py`, render `_stroke` with `PAPER`; retain `_shadow` in `BLUE` and the current 42-frame timing.

- [ ] **Step 4: Verify and rebuild both stems**

Run the focused tests, full suite, build commands, and validators for `07-lightning` and `20-check`.

Expected: both pass; visual inspection confirms no side branches and a readable paper check on both preview backgrounds.

### Task 5: Redesign the Three Energy Motions

**Files:**
- Modify: `04-editable-project/frame_motions/m24_explosion_ray.py`
- Modify: `04-editable-project/frame_motions/m26_explosion_ring.py`
- Modify: `04-editable-project/frame_motions/m05_star_four.py`
- Modify: `04-editable-project/tests/test_batch3_unique.py`
- Modify: `04-editable-project/tests/test_build.py`

- [ ] **Step 1: Write failing semantic-state tests**

```python
def test_explosion_ray_deforms_core_locally_as_rays_fire():
    from frame_motions.m24_explosion_ray import explosion_ray_state
    burst = explosion_ray_state(28)
    assert len(set(round(value, 3) for value in burst["ray_progress"])) >= 4
    assert len(set(round(value, 3) for value in burst["core_impulses"])) >= 3
    assert "core_scale" not in burst


def test_explosion_ring_closes_from_two_opposing_arcs_before_expanding():
    from frame_motions.m26_explosion_ring import explosion_ring_state
    closing = explosion_ring_state(20)
    expanding = explosion_ring_state(32)
    assert closing["clockwise_arc"] > 0
    assert closing["counterclockwise_arc"] > 0
    assert expanding["radius"] > closing["radius"]
    assert "outer_scale" not in expanding


def test_four_point_star_is_one_centered_material_without_fragment_offsets():
    from frame_motions.m05_star_four import star_four_state
    opening = star_four_state(22)
    assert opening["top"] > opening["left"]
    assert opening["left"] >= opening["bottom"]
    assert "fragment_offsets" not in opening
```

- [ ] **Step 2: Verify failures against the old scale/fragment implementations**

Run the new tests individually. Expected: FAIL on missing keys and the continued presence of `core_scale` or master-image scaling.

- [ ] **Step 3: Implement semantic path animation and remove master transforms**

`m21`: author an irregular closed core path, use eight ray paths with distinct delays/pressures, deform the nearest core control points when a ray fires, and retract rays in staggered order.

`m23`: author inner and outer ring paths, reveal two outer arcs in opposite directions from the impact point, expand radius through path coordinates, apply one decaying sinusoidal irregularity, and retract to the center.

`m25`: author one closed four-ray silhouette, interpolate individual tip radii from the center in top/right-left/bottom sequence, deform only tips for settle, and keep the moving paper glint clipped to visible star material.

Remove `master_image`, `masked_part`, and `transform_image` imports from all three modules. Set all three specs to 48 frames.

- [ ] **Step 4: Update duration contracts without changing unaffected stems**

Split the batch-3 duration test into a per-stem mapping and assert exactly:

```python
EXPECTED = {
    "23-launch": 42,
    "02-heart-double": 42,
    "08-lightning-round": 42,
    "24-explosion-ray": 48,
    "26-explosion-ring": 48,
    "05-star-four": 48,
    "22-favorite": 42,
}
```

Task 6 changes the `23-launch` and `22-favorite` entries from 42 to 48 after those implementations are complete.

- [ ] **Step 5: Verify, build, and pause for visual approval**

Run focused tests, full suite, per-stem builds and validators, then create dark/light QA sheets and `contact-sheet-energy-redesign.gif` for `04`, `21`, `23`, and `25`.

Expected: the user approves the group before Task 6 starts.

### Task 6: Redesign Rocket, Bulb, Bookmark, and IRA Lettering

**Files:**
- Modify: `04-editable-project/frame_motions/m23_launch.py`
- Modify: `04-editable-project/frame_motions/m10_bulb_spark.py`
- Modify: `04-editable-project/frame_motions/m22_favorite.py`
- Modify: `04-editable-project/frame_motions/m27_ira_heart.py`
- Modify: `04-editable-project/tests/test_batch3_unique.py`
- Modify: `04-editable-project/tests/test_tactile_symbols.py`
- Modify: `04-editable-project/tests/test_ira_heart.py`
- Modify: `04-editable-project/tests/test_export_final_package.py`

- [ ] **Step 1: Write failing story-motion contracts**

```python
def test_launch_moves_one_coherent_rocket_after_flame_ignition():
    from frame_motions.m23_launch import launch_layers, launch_state
    ignition = launch_state(20, 400)
    flight = launch_state(34, 400)
    assert ignition["flame"] > ignition["flight"]
    assert flight["rocket_y"] < ignition["rocket_y"]
    assert {layer.name for layer in launch_layers(24, 400)} == {
        "trail", "rocket", "flame"
    }


def test_bulb_exists_before_internal_light_blooms():
    from frame_motions.m10_bulb_spark import bulb_state
    ready = bulb_state(14, 400)
    lit = bulb_state(38, 400)
    assert ready["glass"] > ready["light"]
    assert lit["light"] > ready["light"]
    assert lit["base_click"] > 0


def test_favorite_is_a_solid_blue_ribbon_without_confirmation_mark():
    from frame_motions.m22_favorite import favorite_layers
    names = {layer.name for layer in favorite_layers(29, 400)}
    assert names == {"bookmark"}


def test_ira_letters_are_paper_without_blue_or_beige_understroke():
    from frame_motions.m27_ira_heart import static_layers
    letters = [layer for layer in static_layers(400) if layer.name.startswith("letter_")]
    assert all(layer.name.endswith("_paper") for layer in letters)
    # Exact visible RGB values are asserted against PAPER[:3].
```

- [ ] **Step 2: Verify all new tests fail for the intended old behavior**

Expected: old rocket exposes separate wing/body layers, bulb lacks `bulb_state`, bookmark exposes outline/fold/confirm layers, and IRA layers end in `_beige`.

- [ ] **Step 3: Implement the four approved changes**

`m17`: composite the complete master silhouette into one `rocket` layer, animate only whole-object position/very small alignment rotation, and render a separately authored paper/beige flame whose changing length precedes upward flight. Remove rectangular part masks. Set 48 frames.

`m24`: expose `bulb_state(frame, size)` with `glass`, `spark`, `light`, `glass_flex`, and `base_click`; retain a coherent glass contour before ignition, grow radial paper light from the internal four-point spark, deform the glass locally, and keep 60 frames.

`m26`: render one solid `BLUE` bookmark silhouette whose height unfolds downward and whose bottom-notch control points converge into the final V. Remove paper fill, double stroke, and confirmation mark. Set 48 frames.

`m27`: replace `TAUPE` with `PAPER` for all animated/static letter strokes and rename `letter_*_beige` layers to `letter_*_paper`; keep all timing and heart geometry unchanged.

- [ ] **Step 4: Update static-export IRA assertions**

In `test_export_final_package.py`, replace the beige pixel assertion with exact paper-color detection and assert there are no visible beige pixels inside the letter bounding region.

- [ ] **Step 5: Verify, build, and pause for visual approval**

Run focused tests, full suite, build/validate all four stems, and create dark/light QA sheets plus `contact-sheet-story-redesign.gif`.

Expected: the user approves the last redesign group before any physical renaming.

### Task 7: Add and Test Collision-Safe Physical Renumbering

**Files:**
- Create: `04-editable-project/renumber_pack.py`
- Create: `04-editable-project/tests/test_renumber_pack.py`
- Modify after migration: every numbered file and textual reference covered by the mapping below

- [ ] **Step 1: Write the exact mapping and failing inventory test**

Define this immutable mapping in `renumber_pack.py`:

```python
OLD_TO_NEW = {
    "01-heart": "01-heart",
    "02-heart-double": "02-heart-double",
    "03-heart-open": "03-heart-open",
    "04-star": "04-star",
    "05-star-four": "05-star-four",
    "06-spark": "06-spark",
    "07-lightning": "07-lightning",
    "08-lightning-round": "08-lightning-round",
    "09-idea": "09-idea",
    "10-bulb-spark": "10-bulb-spark",
    "11-eye": "11-eye",
    "12-smile": "12-smile",
    "13-laugh": "13-laugh",
    "14-sad": "14-sad",
    "15-surprise": "15-surprise",
    "16-like": "16-like",
    "17-dislike": "17-dislike",
    "18-question": "18-question",
    "19-exclamation": "19-exclamation",
    "20-check": "20-check",
    "21-cross": "21-cross",
    "22-favorite": "22-favorite",
    "23-launch": "23-launch",
    "24-explosion-ray": "24-explosion-ray",
    "25-explosion-cloud": "25-explosion-cloud",
    "26-explosion-ring": "26-explosion-ring",
    "27-ira-heart": "27-ira-heart",
}
```

Test that keys and values are unique, numbers are exactly 1–27, `ira-heart` is last, and a dry run over a temporary fixture reports no collisions.

- [ ] **Step 2: Implement two-phase rename planning**

Expose these three fully implemented functions (the type signatures are the compatibility contract used by the tests):

```python
def build_moves(package_root: Path) -> list[tuple[Path, Path]]:
    """Return validated source/destination pairs inside package_root."""


def apply_moves(moves: list[tuple[Path, Path]]) -> None:
    """Apply a collision-free stage-then-final rename transaction."""


def rewrite_text_references(package_root: Path) -> None:
    """Rewrite stems and numbered module imports simultaneously."""
```

`build_moves` covers numbered artifacts in both release and editable trees, including `masters`, `frames`, `upload`, `tgs_upload`, `previews/individual`, static PNG directories, release TGS/WebM/GIF directories, and numbered modules in both `frame_motions` and legacy `motions`. Module destinations use `m<new-number>_<slug_with_underscores>.py`.

`apply_moves` first moves every source to a unique sibling name prefixed `.renumber-stage-`, validates that all staged files exist, then moves staged paths to final destinations. It refuses missing sources, duplicate destinations, existing unrelated destinations, package roots without `AGENTS.md`, and a second application.

`rewrite_text_references` uses simultaneous replacement tokens rather than sequential string replacement so `02-heart-double` cannot be accidentally rewritten twice. It rewrites whitelisted UTF-8 files (`.py`, `.md`, `.json`) and updates module import paths separately from stem strings.

- [ ] **Step 3: Test the migration on a copied temporary package**

Copy the package to `tmp_path`, run the migration there, import `motions.registry`, and assert:

```python
assert list(SPECS) == list(OLD_TO_NEW.values())
assert len(SPECS) == 27
assert all(spec.stem == stem for stem, spec in SPECS.items())
assert not any(old in all_text for old in OLD_TO_NEW if old != OLD_TO_NEW[old])
```

Also assert 26 renamed masters, 27 renamed module files, and exact final inventories in generated directories.

- [ ] **Step 4: Update metadata order before applying to the real package**

Reorder `DISPLAY_NAMES` and `ANIMATION_SUMMARIES` in `export_final_package.py` to match `OLD_TO_NEW.values()`. Rewrite summaries for redesigned animations using the approved design language. Update `BATCH1_STEMS`, `BATCH2_STEMS`, `BATCH3_STEMS`, category group expectations, registry imports, tests, README examples, and handoff references.

- [ ] **Step 5: Run dry-run and archive the exact move manifest**

Run: `python3 renumber_pack.py --root .. --dry-run > ../docs/superpowers/plans/renumber-move-manifest.txt`

Expected: every move has an existing source, every destination is unique, and the manifest contains no path outside the package root.

- [ ] **Step 6: Apply migration once and immediately run import/inventory tests**

Run: `python3 renumber_pack.py --root .. --apply`

Then run: `python3 -m pytest tests/test_renumber_pack.py tests/test_motions.py tests/test_project_paths.py tests/test_export_final_package.py -q`

Expected: PASS with exact new registry order and no stale old-number artifacts.

### Task 8: Rebuild Every Artifact Under Final Names

**Files:**
- Regenerate: `04-editable-project/frames/*`
- Regenerate: `04-editable-project/upload/*.webm`
- Regenerate: `04-editable-project/tgs_upload/*.tgs`
- Regenerate: `04-editable-project/previews/*`
- Regenerate/copy: `01-ready-to-upload/*`, `02-static-png/*`, `03-previews/*`
- Modify: `05-ai-handoff/emoji-manifest.json`
- Modify: `05-ai-handoff/PACKAGE_MANIFEST.md`
- Modify: `05-ai-handoff/START_HERE.md`
- Modify: `05-ai-handoff/EDITING_GUIDE.md`
- Modify: `05-ai-handoff/AI_EDITING_PROMPT.md`
- Modify: `04-editable-project/README.md`

- [ ] **Step 1: Run the complete editable-project build**

```bash
python3 build_all.py --only all --preview --encode
python3 build_tgs.py --only all
python3 build_preview.py --only all --individual
```

Expected: 27 frame directories, 27 WebM, 27 TGS, 27 individual GIFs, and duration-split contact sheets using final stems.

- [ ] **Step 2: Regenerate static assets and manifest into a new temporary export**

Run: `python3 export_final_package.py --destination "$(mktemp -d)/chebaturkin-final"` only after resolving the destination to an explicit newly created child path; do not target the project root or an existing package directory.

Expected: the exporter creates a complete new package and its manifest lists the approved final order.

- [ ] **Step 3: Copy verified derived outputs into the current package**

Copy only after the temporary export passes `validate_source_project`. Replace the current release directories stem-for-stem, verify each target is one of the 27 mapped final names, and report removal of stale old-number generated files. This is a material destructive step and must use the archived move manifest as the target inventory.

- [ ] **Step 4: Update human-readable handoff documents**

Document the four-color-only rule, final numbering, new durations, redesigned summaries, and the same per-stem build/validation workflow. Ensure every old numbered stem absent from `OLD_TO_NEW.values()` is removed from text.

- [ ] **Step 5: Regenerate `SHA256SUMS` only after every file is final**

Generate hashes for the same package inventory as the existing checksum file, sorted by relative path, excluding `.superpowers`, Python caches, pytest caches, and `SHA256SUMS` itself.

Expected: exactly one checksum line per shipped file and no temporary/staging path.

### Task 9: Final Verification and Visual Acceptance

**Files:**
- Verify only; no source changes unless a gate fails

- [ ] **Step 1: Run the full automated quality gate**

```bash
cd 04-editable-project
python3 -m pytest -q
python3 validate_animated.py
python3 validate_tgs.py
cd ..
shasum -a 256 -c SHA256SUMS
```

Expected: all tests pass; 27 animated emoji pass; 27 vector TGS emoji pass; every checksum reports `OK`.

- [ ] **Step 2: Audit exact final inventories and size headroom**

Assert 27 TGS, 27 WebM, 27 static 100×100 PNG, 27 editable 400×400 PNG, 27 individual GIFs, 26 masters, and 27 registered specs. Report the largest TGS and WebM and their remaining Telegram byte headroom.

- [ ] **Step 3: Audit palette and stale-name absence**

Run the authored palette test, inspect all generated visible pixels against the four-color palette with alpha-aware exact or nearest-color rules appropriate to raster antialiasing, and search text/inventories for every retired numbered stem.

Expected: no pure white, old blue, stale numbered artifact, `.renumber-stage-` path, or unexpected fifth palette color.

- [ ] **Step 4: Present final dark/light contact sheets and animated grouped previews**

Show the user final sheets for hearts, stars/electricity, lights, faces, gestures, signs, and launch/explosions, plus the full duration-split contact sheets.

Expected: final completion is claimed only after the user visually accepts the complete reordered pack.
