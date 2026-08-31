# Agent Handoff and Operability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Make the current emoji pack self-describing, consistently buildable, and safely releasable by a future agent.

**Architecture:** A small Python registry owns pack metadata. `pack.py` orchestrates existing builders and the exporter into explicit build/review/release commands. Handoff documents describe the active visual system, while tests protect registry-derived output and review artefacts.

**Tech Stack:** Python 3.10+, Pillow, pytest, existing TGS/WebM tooling.

---

### Task 1: Establish the active handoff source of truth

**Files:**
- Create: `05-ai-handoff/CURRENT_STATE.md`
- Create: `05-ai-handoff/STYLE_SYSTEM.md`
- Modify: `AGENTS.md`
- Modify: `05-ai-handoff/AI_EDITING_PROMPT.md`
- Test: `04-editable-project/tests/test_handoff_docs.py`

- [x] Write failing tests requiring both handoff documents and their mandatory headings.
- [x] Create documents that state pack order, four-colour rules, current special cases, visual-role references, review protocol, and historical-document policy.
- [x] Point root instructions and the AI prompt to the new documents.
- [x] Run `python3 -m pytest tests/test_handoff_docs.py -q`.

### Task 2: Centralize mutable pack metadata

**Files:**
- Create: `04-editable-project/pack_registry.py`
- Modify: `04-editable-project/build_all.py`
- Modify: `04-editable-project/validate_animated.py`
- Modify: `04-editable-project/export_final_package.py`
- Test: `04-editable-project/tests/test_pack_registry.py`

- [x] Write failing tests for canonical pack order, shared groups, and static-frame definitions.
- [x] Define one immutable record per stem with display name, summary, groups, static frame, and review frame.
- [x] Replace duplicated batches and exporter tuples with registry access.
- [x] Make every build selection accept a comma-separated list.
- [x] Run focused registry/build/validation/export tests.

### Task 3: Add deterministic review and release workflows

**Files:**
- Create: `04-editable-project/pack.py`
- Modify: `04-editable-project/export_final_package.py`
- Modify: `04-editable-project/README.md`
- Modify: `05-ai-handoff/EDITING_GUIDE.md`
- Test: `04-editable-project/tests/test_pack_cli.py`

- [x] Write failing tests for selected review boards and staged release synchronisation.
- [x] Implement `pack.py build`, `pack.py review`, and `pack.py release` using existing builders and validators.
- [x] Generate 100 px dark/light static boards and a keyframe board under `03-previews/review/current`.
- [x] Stage release into a temporary directory, validate, sync only generated release folders, then calculate root checksums.
- [x] Run focused command tests.

### Task 4: Align static sources and release docs

**Files:**
- Modify: `04-editable-project/export_final_package.py`
- Modify: `05-ai-handoff/emoji-manifest.json` (generated)
- Modify: `04-editable-project/README.md`
- Modify: `05-ai-handoff/EDITING_GUIDE.md`
- Test: `04-editable-project/tests/test_export_final_package.py`

- [x] Write a failing test requiring every manifest item to declare a vector static frame.
- [x] Export all static PNG from canonical frame renderers; retain masters only as source-art references.
- [x] Correct stale statements about `ИРА`, masters, and batch previews; label old design/planning material as historical.
- [x] Run export and documentation tests.

### Task 5: Rebuild, verify, and publish current artefacts

**Files:**
- Modify: generated release folders and `SHA256SUMS`

- [x] Build all emoji and TGS files.
- [x] Run `python3 -m pytest -q`, `python3 validate_animated.py`, and `python3 validate_tgs.py`.
- [x] Run `python3 pack.py review --only all` and `python3 pack.py release`.
- [x] Verify every `SHA256SUMS` entry with `shasum -a 256 -c SHA256SUMS`.
