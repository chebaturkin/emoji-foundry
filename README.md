# Emoji Foundry

<p align="center">
  <img src="03-previews/review/current/static-100-dark.png" alt="Emoji Foundry — 27 Telegram custom emoji" width="720">
</p>

**Emoji Foundry** is a private creative workspace for designing, animating, validating, and packaging a cohesive Telegram custom emoji pack. It currently contains 27 hand-drawn paper-like emoji with a strict four-colour visual system and vector-first Telegram delivery.

This repository is intentionally private. It is the source of truth for the current pack, not a public generator or a licensed asset library.

## What is inside

- 27 animated custom emoji in **TGS** — the primary Telegram upload format.
- VP9-with-alpha **WebM** fallbacks.
- Static PNG exports at 100 × 100 and editable 400 × 400.
- A Python animation system with tactile, frame-based motion.
- Validators for Telegram dimensions, duration, safe area, palette, alpha, TGS structure, and file size.
- Current 100 × 100 review boards on light and dark backgrounds.

## The visual system

Visible emoji artwork uses only these four colours:

| Role | Name | Hex |
| --- | --- | --- |
| Primary silhouette, contour, depth | BLUE | `#2E3A4D` |
| Warm secondary material | TAUPE | `#C4C1B4` |
| Paper, highlights, light lettering | PAPER | `#F2F0E9` |
| Rare high-contrast internal detail | INK | `#0D0D0D` |

Every animation follows the same physical rhythm: anticipation → meaningful action → short material reaction → natural return. Global pulse/fade animation, glitches, rectangular reveals, and arbitrary fragments are not part of the pack language.

The active visual decisions are documented in [CURRENT_STATE.md](05-ai-handoff/CURRENT_STATE.md) and [STYLE_SYSTEM.md](05-ai-handoff/STYLE_SYSTEM.md).

## Repository map

```text
01-ready-to-upload/    Final TGS and WebM files for Telegram
02-static-png/         Static PNG exports
03-previews/           Review boards and preview GIFs
04-editable-project/   Python sources, motion modules, tests, and build tools
05-ai-handoff/         Current rules and machine-readable pack manifest
```

The canonical animation modules are in `04-editable-project/frame_motions`. Files in release directories, `frames`, `upload`, `tgs_upload`, and `previews` are generated outputs.

## Quick start

Requirements:

- Python 3.10+
- Dependencies from `04-editable-project/requirements.txt`
- `04-editable-project/tools/ffmpeg` with `libvpx-vp9` support; the bundled file targets macOS arm64.

```bash
cd 04-editable-project
python3 -m pip install -r requirements.txt

# Rebuild and validate one or more emoji.
python3 pack.py build --only 20-check,22-favorite

# Generate actual 100 × 100 review boards.
python3 pack.py review --only 20-check,22-favorite

# Rebuild the full pack, run the quality gate, stage the release, synchronise
# release folders, and update SHA-256 checksums.
python3 pack.py release
```

## Quality gate

Before any handoff or Telegram upload, run:

```bash
cd 04-editable-project
python3 -m pytest -q
python3 validate_animated.py
python3 validate_tgs.py
```

The current review artefacts live in `03-previews/review/current/`. Judge line weight and readability at 100 × 100 first; the editable 400 × 400 renders are supporting material only.

## Editing an emoji

1. Read [AGENTS.md](AGENTS.md), then the documents in `05-ai-handoff/`.
2. Locate the target stem in `04-editable-project/pack_registry.py` and its `frame_motions/mXX_name.py` module.
3. Add a narrow regression test and observe it fail before changing animation behaviour.
4. Run `python3 pack.py build --only <stem>` and `python3 pack.py review --only <stem>`.
5. Run the full quality gate before release.

`20-check`, `22-favorite`, and `27-ira-heart` render their release statics from canonical vector frames. Other approved static compositions remain explicitly sourced from their master PNG; the selection is recorded in `pack_registry.py` and the manifest.

## Current status

- 27/27 TGS files
- 27/27 WebM files
- 27/27 static PNG files
- 232 automated tests
- SHA-256 manifest for the complete local release package

## Ownership and contributions

This is a private repository. No licence is granted for the code, visual assets, name, or personal marks. Do not redistribute, reuse, or publish its contents without the repository owner’s written permission.

For future collaboration rules, see [CONTRIBUTING.md](CONTRIBUTING.md). Security reports are described in [SECURITY.md](SECURITY.md).
