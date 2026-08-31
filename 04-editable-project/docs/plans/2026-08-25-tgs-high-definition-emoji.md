# High-definition TGS Emoji Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a crisp 27-file TGS custom emoji pack while retaining uploadable WebM fallbacks below 64 KiB.

**Architecture:** Render every registered `FrameMotionSpec` at 400 x 400, mount it into the established safe area, vectorize approved color regions into simplified closed paths, then write deterministic 512 x 512 Lottie JSON compressed as TGS. Validate structure, duration, palette and file size independently of the exporter.

**Tech Stack:** Python 3, Pillow, NumPy, scikit-image contours, gzip, JSON, pytest, VP9 fallback WebM.

---

### Task 1: TGS vector core

**Files:**
- Create: `tgs_core/vectorize.py`
- Create: `tgs_core/build.py`
- Test: `tests/test_tgs_export.py`

- [ ] Write failing tests for 512 x 512 source rendering, palette-only contour extraction, deterministic gzip and 60 FPS Lottie metadata.
- [ ] Run `python3 -m pytest -q tests/test_tgs_export.py` and confirm missing-module failures.
- [ ] Implement high-resolution rendering, contour simplification and shape-only Lottie serialization.
- [ ] Run the focused tests and confirm they pass.

### Task 2: Builder and validator

**Files:**
- Create: `build_tgs.py`
- Create: `validate_tgs.py`
- Modify: `requirements.txt`
- Test: `tests/test_tgs_validation.py`

- [ ] Write failing CLI and validation tests for selection, inventory, dimensions, FPS, duration, unsupported layers and 65536-byte limit.
- [ ] Implement `--only` selection compatible with the existing registry and deterministic outputs in `tgs_upload`.
- [ ] Implement validation without requiring Telegram or Adobe software.
- [ ] Add `scikit-image==0.26.0` to reproducible dependencies.

### Task 3: Pilot quality and size

**Files:**
- Generate: `tgs_upload/13-laugh.tgs`
- Generate: `tgs_upload/02-heart-double.tgs`
- Generate: `tgs_upload/03-heart-open.tgs`
- Generate: `tgs_upload/25-explosion-cloud.tgs`
- Generate: `tgs_upload/26-explosion-ring.tgs`

- [ ] Build the five stems that exposed the WebM size failure.
- [ ] Validate them with `validate_tgs.py` and python-lottie `tgs_check.py`.
- [ ] Render representative frames to PNG or SVG and compare silhouettes, colors and readability against source frames.
- [ ] Tune only contour tolerance and minimum visible area until every file is valid and visually faithful.

### Task 4: Full pack and WebM fallback

**Files:**
- Modify: `motion_core/encode.py`
- Modify: `tests/test_encoding.py`
- Generate: `tgs_upload/*.tgs`
- Generate: `upload/*.webm`

- [ ] Restore the practical WebM maximum to 64 KiB and keep best-quality adaptive fallback.
- [ ] Build all 27 TGS and all 27 uploadable WebM fallbacks.
- [ ] Run full tests, `validate_tgs.py` and `validate_animated.py`.

### Task 5: Final handoff

**Files:**
- Modify: `export_final_package.py`
- Modify: `README.md`
- Update: final package outputs and `SHA256SUMS`

- [ ] Add `animated-tgs` as the primary upload directory and document WebM as fallback.
- [ ] Copy TGS, WebM, previews, source code and tests into the final Desktop folder.
- [ ] Verify inventories, checksums and reproducibility from `04-editable-project`.
