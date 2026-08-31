# Static outlier emoji implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redraw the four rejected static emoji as compact PAPER silhouettes with readable BLUE depth, and create a review board for approval at 100 × 100 px.

**Architecture:** The canonical source remains one `frame_motions/mXX_name.py` module per emoji. `20`, `22`, and `27` already use their approved runtime frame as the static source; switch `21` to the same vector-static path. Preserve the other emoji, historical master PNGs, and all generated release directories until the approved release pass.

**Tech Stack:** Python 3.10+, Pillow, NumPy, pytest, the existing `frame_core` compositing utilities and `pack.py review` board generator.

---

### Task 1: Lock the four visual contracts with regression tests

**Files:**
- Modify: `04-editable-project/tests/test_tactile_symbols.py`
- Modify: `04-editable-project/tests/test_ira_heart.py`
- Modify: `04-editable-project/tests/test_export_final_package.py`

- [ ] **Step 1: Write failing static-material tests**

Add tests that inspect actual RGBA layers, not implementation helpers:

```python
def test_check_has_a_paper_face_and_substantial_blue_depth():
    from frame_motions.m20_check import check_layers

    layers = {layer.name: layer.image for layer in check_layers(24, 400)}
    paper_alpha = np.asarray(layers["paper_check"].getchannel("A")) > 32
    blue_alpha = np.asarray(layers["blue_depth"].getchannel("A")) > 32
    assert int(paper_alpha.sum()) > 9_000
    assert int(blue_alpha.sum()) > int(paper_alpha.sum() * 1.35)
```

```python
def test_cross_is_a_filled_paper_x_with_no_ring_or_rays():
    from frame_motions.m21_cross import cross_layers

    layers = {layer.name: layer.image for layer in cross_layers(20, 400)}
    assert set(layers) == {"blue_depth", "paper_cross"}
    assert np.asarray(layers["paper_cross"].getchannel("A")).sum() > 1_500_000
```

```python
def test_favorite_is_a_paper_bookmark_over_blue_depth_without_inset_line():
    from frame_motions.m22_favorite import favorite_layers

    layers = {layer.name: layer.image for layer in favorite_layers(29, 400)}
    assert set(layers) == {"blue_depth", "paper_bookmark"}
    assert np.asarray(layers["paper_bookmark"].getchannel("A")).sum() > 2_000_000
```

Update the existing IRA tests to require a PAPER-only wordmark wider than 240 px at 400 px, with a heavier filled area than the old hairline lettering, and to require a separate BLUE heart layer.

- [ ] **Step 2: Run only the new tests to verify RED**

Run: `cd 04-editable-project && python3 -m pytest -q tests/test_tactile_symbols.py tests/test_ira_heart.py tests/test_export_final_package.py`

Expected: failures caused by the old thin check rim, old cross ring/rays, favorite inset, and old IRA lettering geometry.

- [ ] **Step 3: Commit the failing tests**

```bash
git add 04-editable-project/tests/test_tactile_symbols.py \
        04-editable-project/tests/test_ira_heart.py \
        04-editable-project/tests/test_export_final_package.py
git commit -m "test: define cohesive static emoji material"
```

### Task 2: Rebuild the paper-and-depth geometry in canonical frame modules

**Files:**
- Modify: `04-editable-project/frame_motions/m20_check.py`
- Modify: `04-editable-project/frame_motions/m21_cross.py`
- Modify: `04-editable-project/frame_motions/m22_favorite.py`
- Modify: `04-editable-project/frame_motions/m27_ira_heart.py`
- Modify: `04-editable-project/pack_registry.py`

- [ ] **Step 1: Implement the minimal layer changes**

In `m20_check.py`, replace the low-opacity lagging shadow and narrow outer line with a single fully opaque `blue_depth` check carrier displaced lower/right and a visibly narrower `paper_check` face. Keep the existing path and meaningful drawing motion.

In `m21_cross.py`, replace the two independent thin strokes, impact rays, and ring treatment with two broad under/overlapping PAPER diagonals over one BLUE depth silhouette. Return exactly `blue_depth` and `paper_cross` from `cross_layers`; animate the two diagonals arriving, but make their settled frame a single X read.

In `m22_favorite.py`, make the bookmark polygon PAPER and place the same silhouette, offset lower/right, in BLUE. Remove `inset_path` and `draw_pressure_stroke` from this module; keep only the lower notch and the existing downward material reveal.

In `m27_ira_heart.py`, replace the hand-drawn narrow letter paths with three geometric PAPER glyph constructions that share a consistent heavy stem. Keep letters PAPER-only and draw a compact independent BLUE heart as its own layer. Preserve the left-to-right letter reveal and the 42-frame timing.

Change the `21-cross` `PackEntry` to `static_source="vector_static_renderer"`, so review and export use the redesigned vector frame rather than `masters/21-cross.png`.

- [ ] **Step 2: Run the contract tests to verify GREEN**

Run: `cd 04-editable-project && python3 -m pytest -q tests/test_tactile_symbols.py tests/test_ira_heart.py tests/test_export_final_package.py`

Expected: PASS. If any threshold is not met, change the geometry, never weaken a requirement solely to pass it.

- [ ] **Step 3: Commit the canonical geometry**

```bash
git add 04-editable-project/frame_motions/m20_check.py \
        04-editable-project/frame_motions/m21_cross.py \
        04-editable-project/frame_motions/m22_favorite.py \
        04-editable-project/frame_motions/m27_ira_heart.py \
        04-editable-project/pack_registry.py
git commit -m "feat: unify four static emoji materials"
```

### Task 3: Generate and inspect the approval artifacts

**Files:**
- Generate only: `04-editable-project/previews/review/current/static-100-{dark,light}-20-check-21-cross-22-favorite-27-ira-heart.png`
- Generate only: `04-editable-project/previews/review/current/keyframes-20-check-21-cross-22-favorite-27-ira-heart.png`

- [ ] **Step 1: Build the four review boards**

Run: `cd 04-editable-project && python3 pack.py review --only 20-check,21-cross,22-favorite,27-ira-heart`

Expected: one dark static board, one light static board, and one keyframe board in `previews/review/current`.

- [ ] **Step 2: Inspect at true emoji scale**

Open both static boards. Confirm: check and cross are as heavy as exclamation; favorite reads as a paper bookmark; `ИРА` is readable without an outline; all four work on both backgrounds. Open the keyframe board to confirm no blank selected frames.

- [ ] **Step 3: Report the review boards and wait for visual approval**

Do not update release PNG/WebM/TGS folders or `SHA256SUMS` in this task. The user must approve the static forms before animation and release work begin.

### Task 4: Run the focused non-mutating verification suite

**Files:**
- No source changes.

- [ ] **Step 1: Run focused static and motion validation**

Run:

```bash
cd 04-editable-project
python3 validate_animated.py --only 20-check,21-cross,22-favorite,27-ira-heart
python3 -m pytest -q
```

Expected: both commands pass. If an existing test fails because `21-cross` is now vector-static, update only the expectation that describes the former master-static behavior.

- [ ] **Step 2: Record verification results in the handoff only after user approval**

Do not alter `CURRENT_STATE.md`, release assets, or checksums until the visual direction has user approval. A later release task will rebuild TGS/WebM, run both validators, synchronize the release directories, and refresh `SHA256SUMS`.
