# Fondy workshop site

The public product is a static Russian-language workshop centred on Fondy and
the four released heart emoji. Keep it runnable from any subpath: authored
HTML, CSS, JavaScript and build output must use relative asset URLs.

## Source boundaries

- `sections/workshop.*` and `lib/workshop-state.js` are the workshop source.
- `base.css` owns shared typography and visual tokens.
- `brand-kit/assets` and `brand-kit/fonts` are the source for site media.
- The four heart files come from the canonical release folders in the sibling
  `Чебутуркин Emoji` project. Set `EMOJI_PACK_ROOT` when the sibling uses a
  different path. Do not hand-edit generated heart files.
- `assets/` and `public/` are build results. Regenerate them with
  `python3 site/build.py` instead of editing generated files.

## Behaviour

The workshop stays client-only. State is encoded in the URL hash; it must not
require a server, user account, external API, or analytics script. Every
button needs a useful action, and motion needs a reduced-motion path. Preserve
keyboard operation and visible focus when changing scenes or controls.

## Required checks

```sh
python3 site/build.py
python3 -m pytest -q site/tests
node --test site/tests/test_workshop_state.mjs site/tests/test_workshop_contract.mjs
```

If the source heart pack changes, follow the release and validation commands
in `../Чебутуркин Emoji/AGENTS.md` before rebuilding this site.
