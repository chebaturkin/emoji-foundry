# Telegram Emoji Ira Heart and Brand Blue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the animated `27-ira-heart` emoji and replace every light-blue accent in seven existing animations with the brand blue `#2E3A4D`.

**Architecture:** Keep the new emoji isolated in one `FrameMotionSpec` module with vector paths for each Cyrillic letter and the two heart gestures. Reuse the existing brush, path, depth and render primitives. Change only color constants in the seven existing modules, then rebuild exactly eight affected WebM files before the final pack validation.

**Tech Stack:** Python 3, Pillow, NumPy, pytest, libvpx VP9 through the bundled ffmpeg.

**Repository note:** This project is not a Git repository. Commit steps are replaced by focused verification after each task and one checksummed source checkpoint after the final full pass.

---

### Task 1: Lock the brand palette with a regression test

**Files:**
- Create: `tests/test_brand_palette.py`
- Modify: `frame_motions/m06_spark.py`
- Modify: `frame_motions/m07_lightning.py`
- Modify: `frame_motions/m09_idea.py`
- Modify: `frame_motions/m11_eye.py`
- Modify: `frame_motions/m14_sad.py`
- Modify: `frame_motions/m20_check.py`
- Modify: `frame_motions/m03_heart_open.py`

- [ ] **Step 1: Write the failing palette test**

```python
import importlib

from frame_motions.common import BLUE


CONSTANTS = {
    "frame_motions.m06_spark": "SHADOW_BLUE",
    "frame_motions.m07_lightning": "ECHO_BLUE",
    "frame_motions.m09_idea": "SHADOW_BLUE",
    "frame_motions.m11_eye": "SHADOW_BLUE",
    "frame_motions.m14_sad": "TEAR_BLUE",
    "frame_motions.m20_check": "ACCENT_BLUE",
    "frame_motions.m03_heart_open": "SHADOW_BLUE",
}


def test_all_authored_blue_accents_use_brand_rgb():
    for module_name, constant_name in CONSTANTS.items():
        color = getattr(importlib.import_module(module_name), constant_name)
        assert color[:3] == BLUE[:3], (module_name, color)
```

- [ ] **Step 2: Run the test and verify the expected failure**

Run:

```bash
python3 -m pytest tests/test_brand_palette.py -q
```

Expected: FAIL because the seven constants still use RGB `(91, 139, 196)`.

- [ ] **Step 3: Replace only the RGB values**

For each listed constant, preserve its existing alpha and replace the RGB tuple with `(46, 58, 77)`. Examples:

```python
SHADOW_BLUE = (46, 58, 77, 158)
ECHO_BLUE = (46, 58, 77, 164)
TEAR_BLUE = (46, 58, 77, 255)
ACCENT_BLUE = (46, 58, 77, 255)
```

- [ ] **Step 4: Run the palette test**

Run:

```bash
python3 -m pytest tests/test_brand_palette.py -q
```

Expected: PASS.

### Task 2: Define the behavior contract for `27-ira-heart`

**Files:**
- Create: `tests/test_ira_heart.py`
- Create later in Task 3: `frame_motions/m27_ira_heart.py`

- [ ] **Step 1: Write failing tests for timing, rendering and safe area**

```python
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
```

- [ ] **Step 2: Run the new test file and verify RED**

Run:

```bash
python3 -m pytest tests/test_ira_heart.py -q
```

Expected: three failures because `frame_motions.m27_ira_heart` does not exist.

### Task 3: Implement the vector letters and two-part heart

**Files:**
- Create: `frame_motions/m27_ira_heart.py`
- Test: `tests/test_ira_heart.py`

- [ ] **Step 1: Implement the authored state timeline**

The module must expose this state shape:

```python
def ira_heart_state(frame):
    return {
        "letters": (
            smooth(phase(frame, 1, 9)) * (1 - smooth(phase(frame, 37, 41))),
            smooth(phase(frame, 5, 13)) * (1 - smooth(phase(frame, 35, 40))),
            smooth(phase(frame, 9, 17)) * (1 - smooth(phase(frame, 33, 39))),
        ),
        "heart_top": smooth(phase(frame, 14, 25)) * (1 - smooth(phase(frame, 33, 40))),
        "heart_bottom": smooth(phase(frame, 16, 27)) * (1 - smooth(phase(frame, 32, 39))),
        "closure": math.sin(math.pi * phase(frame, 25, 33)),
    }
```

- [ ] **Step 2: Implement vector paths without a font dependency**

Use `cubic_points` and short NumPy polylines in a 100-unit coordinate system:

```python
def _letter_paths(size):
    unit = size / 100.0
    return (
        (
            np.array(((33, 42), (33, 61))) * unit,
            np.array(((33, 61), (43, 42))) * unit,
            np.array(((43, 42), (43, 61))) * unit,
        ),
        (
            np.array(((47, 61), (47, 42))) * unit,
            cubic_points((47*unit, 42*unit), (59*unit, 39*unit), (59*unit, 52*unit), (47*unit, 51*unit), 20),
        ),
        (
            np.array(((58, 61), (65, 42), (72, 61))) * unit,
            np.array(((61, 53), (69, 53))) * unit,
        ),
    )


def _heart_paths(size, closure):
    unit = size / 100.0
    top = np.vstack((
        cubic_points((18*unit, 46*unit), (13*unit, 27*unit), (34*unit, 18*unit), (48*unit, 37*unit), 28),
        cubic_points((48*unit, 37*unit), (62*unit, 16*unit), (88*unit, 26*unit), (82*unit, 48*unit), 32)[1:],
    ))
    bottom = cubic_points(
        (21*unit, 62*unit),
        ((31-closure)*unit, 73*unit),
        ((42+closure)*unit, 79*unit),
        (50*unit, 84*unit),
        24,
    )
    bottom = np.vstack((
        bottom,
        cubic_points((50*unit, 84*unit), ((61-closure)*unit, 77*unit), ((73+closure)*unit, 69*unit), (80*unit, 58*unit), 24)[1:],
    ))
    return top, bottom
```

- [ ] **Step 3: Render every stroke only in `BLUE`**

Create a local helper that reveals each path and calls `draw_pressure_stroke` with `BLUE`, variable pressure and no paper overlay. Compose letters, upper heart, lower heart and two tiny closure accents as independent `DepthLayer` objects. Return a blank canvas for frames `0` and `41`.

Register the specification in the module:

```python
SPEC = FrameMotionSpec(
    "27-ira-heart",
    draw_frame,
    duration_frames=42,
    tags=("soft", "tactile"),
)
```

- [ ] **Step 4: Run the focused behavior tests**

Run:

```bash
python3 -m pytest tests/test_ira_heart.py -q
```

Expected: PASS.

### Task 4: Register the 27th emoji and update pack invariants

**Files:**
- Modify: `frame_motions/registry.py`
- Modify: `tests/test_motions.py`
- Modify: `tests/test_build.py`
- Modify: `tests/test_project_paths.py`

- [ ] **Step 1: Add failing registry expectations**

Append `27-ira-heart` to `EXPECTED` in `tests/test_motions.py`, rename the registry test to `test_registry_has_27_unique_specs`, update the unique count from 26 to 27, update `select_specs("all")` and `len(SPECS)` expectations in `tests/test_build.py`, and append `27-ira-heart` to the expected `soft` group and the 42-frame group. In `tests/test_project_paths.py`, change the master inventory expectation to the first 26 stems because the new vector-only scenario has no master PNG dependency.

- [ ] **Step 2: Run the focused registry tests and verify RED**

Run:

```bash
python3 -m pytest tests/test_motions.py::test_registry_has_27_unique_specs tests/test_build.py::test_select_specs_supports_groups_and_single_stem tests/test_build.py::test_registry_replaces_all_legacy_specs tests/test_build.py::test_group_specs_by_duration_preserves_duration_and_registry_order tests/test_project_paths.py::test_project_contains_exact_master_for_every_registered_stem -q
```

Expected: FAIL because the registry still has 26 specs.

- [ ] **Step 3: Register the new spec**

Add:

```python
from frame_motions.m27_ira_heart import SPEC as ira_heart
```

Append `ira_heart` after `favorite` in the `FRAME_SPECS` tuple.

- [ ] **Step 4: Run registry and build tests**

Run:

```bash
python3 -m pytest tests/test_motions.py tests/test_build.py -q
```

Expected: PASS.

### Task 5: Build and validate exactly eight changed WebM files

**Files:**
- Generate: `upload/27-ira-heart.webm`
- Regenerate: `upload/06-spark.webm`
- Regenerate: `upload/07-lightning.webm`
- Regenerate: `upload/09-idea.webm`
- Regenerate: `upload/11-eye.webm`
- Regenerate: `upload/14-sad.webm`
- Regenerate: `upload/20-check.webm`
- Regenerate: `upload/03-heart-open.webm`
- Generate: `previews/individual/27-ira-heart.gif`

- [ ] **Step 1: Build the eight affected outputs**

Run:

```bash
for emoji_stem in 06-spark 07-lightning 09-idea 11-eye 14-sad 20-check 03-heart-open 27-ira-heart; do
    python3 build_all.py --only "$emoji_stem" --preview --encode
done
```

Expected: eight `built <stem>` lines and no encoder error.

- [ ] **Step 2: Validate the eight affected outputs**

Run:

```bash
python3 validate_animated.py --only 06-spark,07-lightning,09-idea,11-eye,14-sad,20-check,03-heart-open,27-ira-heart
```

Expected: `PASS: 8 animated emoji` and largest WebM not above 65536 bytes.

- [ ] **Step 3: Inspect the real animation**

Open `previews/individual/27-ira-heart.gif` and key frames `10`, `21`, `29` on dark and light backgrounds. Confirm that `ИРА` is readable, the two heart gestures remain separate, and no content crosses the 8 px safe margin.

### Task 6: Update documentation, run the full gate and save one checkpoint

**Files:**
- Modify: `README.md`
- Create: `checkpoints/full-pack/ira-heart-brand-blue-source/`

- [ ] **Step 1: Update release documentation**

Change the pack count from 26 to 27, state that 17 scenarios use 42 frames, list `27-ira-heart` under the soft group, and document the new brand palette rule `#2E3A4D`.

- [ ] **Step 2: Rebuild current all-pack previews from saved frames**

Run:

```bash
python3 build_preview.py --only all
python3 build_preview.py --only all --individual
```

- [ ] **Step 3: Run the fresh full verification gate**

Run:

```bash
python3 -m pytest -q
python3 validate_animated.py
```

Expected: zero failed tests and `PASS: 27 animated emoji`.

- [ ] **Step 4: Save one recoverable source checkpoint**

Create `checkpoints/full-pack/ira-heart-brand-blue-source`, copy the source packages, tests, masters and build scripts while excluding `__pycache__`, add a `CHECKPOINT.md` recording the fresh test count and validator result, generate `SHA256SUMS`, and verify it with:

```bash
shasum -a 256 -c SHA256SUMS
```

Expected: every checkpoint file reports `OK`.
