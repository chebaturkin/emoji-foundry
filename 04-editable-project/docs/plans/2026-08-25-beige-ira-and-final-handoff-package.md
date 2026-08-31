# Beige Ira and Final Handoff Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the approved beige-over-blue lettering to `27-ira-heart` and export one self-contained Desktop folder with animated files, static files, editable sources and an AI handoff.

**Architecture:** Extend only the letter layers of the existing vector animation and expose a clean static renderer. Add one exporter that validates the live project, derives static assets, copies an explicit source inventory, generates machine-readable metadata and hashes the result. The exporter refuses an existing destination and never deletes user files.

**Tech Stack:** Python 3, Pillow 12.1.0, NumPy 2.4.2, pytest 9.0.2, JSON, hashlib, shutil, bundled ffmpeg/libvpx.

**Repository note:** The project is not a Git repository. Focused RED/GREEN verification replaces commits, and the final exported package includes SHA-256 checksums.

---

### Task 1: Add the beige delayed letter stroke

**Files:**
- Modify: `frame_motions/m27_ira_heart.py`
- Modify: `tests/test_ira_heart.py`

- [ ] **Step 1: Write failing behavior and palette tests**

Add tests that require `beige_letters` to lag the blue letters and require both palette colors in the formed frame:

```python
def test_beige_letter_strokes_lag_blue_by_one_frame():
    from frame_motions.m27_ira_heart import ira_heart_state

    drawing = ira_heart_state(7)
    assert drawing["letters"][0] > drawing["beige_letters"][0]
    assert drawing["letters"][1] > drawing["beige_letters"][1]


def test_formed_ira_uses_brand_blue_and_beige():
    from frame_motions.m27_ira_heart import SPEC

    image = np.asarray(render_motion(SPEC)[29])[:, :, :3].astype(np.int16)
    brand = np.max(np.abs(image - np.array((46, 58, 77))), axis=2) < 20
    beige = np.max(np.abs(image - np.array((196, 193, 180))), axis=2) < 20
    assert int(np.count_nonzero(brand)) >= 150
    assert int(np.count_nonzero(beige)) >= 20
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
python3 -m pytest tests/test_ira_heart.py -q
```

Expected: FAIL because `beige_letters` and beige output do not exist.

- [ ] **Step 3: Implement the delayed beige layers**

Add `TAUPE` support to `_stroke`, add these state tracks, and composite one thinner beige layer above each blue letter:

```python
"beige_letters": (
    smooth(phase(frame, 2, 10)) * (1 - smooth(phase(frame, 36, 40))),
    smooth(phase(frame, 6, 14)) * (1 - smooth(phase(frame, 34, 39))),
    smooth(phase(frame, 10, 18)) * (1 - smooth(phase(frame, 32, 38))),
),
```

The blue letter uses width `.041`; the beige overlay uses width `.022`. Heart layers and closure accents remain `BLUE`.

- [ ] **Step 4: Add a clean static renderer**

Expose:

```python
def draw_static_frame(size):
    return compose_depth(
        _static_letter_layers(size)
        + [
            DepthLayer("heart_top", _stroke(_heart_paths(size, 0)[0], size, 1, .043, 2731), 20),
            DepthLayer("heart_bottom", _stroke(_heart_paths(size, 0)[1], size, 1, .043, 2737), 21),
        ]
    )
```

`_static_letter_layers` renders every blue stroke at progress `1`, then every beige stroke at progress `1`, without closure accents.

- [ ] **Step 5: Run the focused tests and rebuild `27`**

Run:

```bash
python3 -m pytest tests/test_ira_heart.py -q
python3 build_all.py --only 27-ira-heart --preview --encode
python3 validate_animated.py --only 27-ira-heart
```

Expected: tests PASS and validator reports one valid WebM.

### Task 2: Add exporter behavior tests

**Files:**
- Create: `tests/test_export_final_package.py`
- Create later: `export_final_package.py`

- [ ] **Step 1: Write failing tests for inventory and safety**

```python
from pathlib import Path

import pytest


def test_manifest_has_27_unique_complete_entries():
    from export_final_package import build_manifest

    manifest = build_manifest()
    assert len(manifest["emoji"]) == 27
    assert len({item["stem"] for item in manifest["emoji"]}) == 27
    ira = manifest["emoji"][-1]
    assert ira["stem"] == "27-ira-heart"
    assert ira["static_source"] == "vector_static_renderer"
    assert ira["master"] is None


def test_export_refuses_existing_destination(tmp_path: Path):
    from export_final_package import export_package

    destination = tmp_path / "existing"
    destination.mkdir()
    with pytest.raises(FileExistsError, match="already exists"):
        export_package(destination)


def test_expected_layout_is_explicit():
    from export_final_package import EXPECTED_DIRECTORIES

    assert "01-ready-to-upload/animated-webm" in EXPECTED_DIRECTORIES
    assert "02-static-png/100x100" in EXPECTED_DIRECTORIES
    assert "04-editable-project/frame_motions" in EXPECTED_DIRECTORIES
    assert "05-ai-handoff" in EXPECTED_DIRECTORIES
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
python3 -m pytest tests/test_export_final_package.py -q
```

Expected: three failures because `export_final_package` does not exist.

### Task 3: Implement the self-contained exporter

**Files:**
- Create: `export_final_package.py`
- Create: `requirements.txt`
- Create: `docs/design/`
- Create: `docs/plans/`
- Test: `tests/test_export_final_package.py`

- [ ] **Step 1: Define explicit package inventories**

The exporter defines `ROOT`, `DEFAULT_DESTINATION`, `EXPECTED_DIRECTORIES`, the ordered 27 display names and animation summaries, plus the source directories:

```python
SOURCE_DIRECTORIES = (
    "frame_core", "frame_motions", "motion_core", "motions",
    "masters", "frames", "upload", "previews", "tests", "tools", "docs",
)

SOURCE_FILES = (
    "README.md", "build_all.py", "build_batch_qa.py", "build_preview.py",
    "build_tactile_qa.py", "validate_animated.py", "export_final_package.py",
    "pytest.ini", "requirements.txt",
)
```

- [ ] **Step 2: Implement project validation and manifest generation**

`validate_source_project` verifies 27 registry stems, exact 27 WebM names, one complete frame directory and one individual GIF per spec, 26 masters, tools/ffmpeg and every declared source path. `build_manifest` derives durations and tags from `SPECS`; items `01-26` use `static_source: master`, while `27` uses `vector_static_renderer`.

- [ ] **Step 3: Implement static exports**

For stems `01-26`, open each master as RGBA and export LANCZOS versions at 400 and 100 px. For `27`, call `draw_static_frame(400)` for the editable PNG and `finalize_frame(draw_static_frame(400))` for the 100 px PNG. Confirm every 100 px image has RGBA mode, transparent corners and visible alpha inside the 8 px safe area.

- [ ] **Step 4: Implement file copying and generated handoff files**

Use `shutil.copy2` and `shutil.copytree` with an ignore rule for `__pycache__`, `.pytest_cache`, `.DS_Store` and `*.pyc`. Generate `START_HERE.md`, `AI_EDITING_PROMPT.md`, `EDITING_GUIDE.md`, `PALETTE.md`, `PACKAGE_MANIFEST.md` and formatted UTF-8 `emoji-manifest.json` from constant templates and actual inventories.

- [ ] **Step 5: Implement previews and checksums**

Copy individual GIF and contact sheets. Generate `static-contact-light.png` and `static-contact-dark.png` from the 27 exported 100 px PNG files. Hash every package file except `SHA256SUMS` with SHA-256 and write sorted relative paths.

- [ ] **Step 6: Add the command-line entry point**

```python
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args()
    export_package(args.destination)
    print(args.destination)
```

- [ ] **Step 7: Add pinned requirements and local documentation copies**

`requirements.txt` contains:

```text
Pillow==12.1.0
numpy==2.4.2
pytest==9.0.2
```

Copy the approved emoji design specs into `docs/design` and implementation plans into `docs/plans` so the exported project has no dependency on the Obsidian path.

- [ ] **Step 8: Run exporter tests**

Run:

```bash
python3 -m pytest tests/test_export_final_package.py -q
```

Expected: PASS.

### Task 4: Export and inspect the final Desktop folder

**Files:**
- Create: `/Users/timofeychebaturkin/Desktop/chebaturkin-telegram-emoji-final/`

- [ ] **Step 1: Confirm the target does not exist**

Run:

```bash
test ! -e /Users/timofeychebaturkin/Desktop/chebaturkin-telegram-emoji-final
```

Expected: exit code `0`.

- [ ] **Step 2: Run the exporter once**

Run:

```bash
python3 export_final_package.py
```

Expected: prints the absolute final folder path and creates no files outside that folder.

- [ ] **Step 3: Verify package counts and checksums**

Run:

```bash
find /Users/timofeychebaturkin/Desktop/chebaturkin-telegram-emoji-final/01-ready-to-upload/animated-webm -name '*.webm' | wc -l
find /Users/timofeychebaturkin/Desktop/chebaturkin-telegram-emoji-final/02-static-png/100x100 -name '*.png' | wc -l
find /Users/timofeychebaturkin/Desktop/chebaturkin-telegram-emoji-final/02-static-png/editable-400x400 -name '*.png' | wc -l
shasum -a 256 -c SHA256SUMS
```

Expected: counts `27`, `27`, `27`; every checksum reports `OK`.

- [ ] **Step 4: Visually inspect both static contact sheets and the new GIF**

Open `static-contact-light.png`, `static-contact-dark.png` and `individual-gif/27-ira-heart.gif`. Confirm that all silhouettes are centered, the static backgrounds remain transparent, and the beige `ИРА` is readable over the blue base.

### Task 5: Run the full release gate

**Files:**
- Verify live project and exported project.

- [ ] **Step 1: Run the live full test suite and validator**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider -q
PYTHONDONTWRITEBYTECODE=1 python3 validate_animated.py
```

Expected: zero failures and `PASS: 27 animated emoji`.

- [ ] **Step 2: Run tests and validator from the copied editable project**

Run from `04-editable-project`:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider -q
PYTHONDONTWRITEBYTECODE=1 python3 validate_animated.py
```

Expected: the same zero-failure result, proving that the package is portable and self-contained.

- [ ] **Step 3: Re-run package checksums**

Run:

```bash
shasum -a 256 -c SHA256SUMS
```

Expected: every file reports `OK` after all read-only verification.
