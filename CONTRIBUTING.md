# Contributing to Emoji Foundry

Emoji Foundry is currently a private, owner-led project. Changes are made only with explicit approval from the repository owner.

## Before changing anything

1. Read `AGENTS.md`.
2. Read `05-ai-handoff/CURRENT_STATE.md`, `STYLE_SYSTEM.md`, and `emoji-manifest.json`.
3. Treat `04-editable-project/frame_motions` as canonical source; do not edit generated release files by hand.
4. Change only the requested emoji and its focused tests.

## Required workflow

```bash
cd 04-editable-project
python3 pack.py build --only <stem>
python3 pack.py review --only <stem>
python3 -m pytest -q
python3 validate_animated.py
python3 validate_tgs.py
```

Use `python3 pack.py release` only when the full pack is ready to be synchronised. It stages the release before replacing generated release folders and refreshes `SHA256SUMS` afterward.

## Design boundaries

- Use only BLUE, TAUPE, PAPER, and INK in visible artwork.
- Compare readability in the generated 100 × 100 boards, not only at 400 × 400.
- Preserve personal content such as `27-ira-heart` unless it is explicitly in scope.
- Do not add a licence or make the repository public without owner approval.
