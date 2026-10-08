# Signal site

The public product is a static Russian-language workshop centred on the Fondy
mascot. Keep it runnable from any subpath: authored HTML, CSS, JavaScript and
build output must use relative asset URLs.

## Source boundaries

- `sections/workshop.*` and `lib/workshop-state.js` are the product source;
- `base.css` owns shared typography and visual tokens;
- `brand-kit/assets/mascot`, `brand-kit/assets/favicons` and `brand-kit/fonts`
  are the only brand media copied into runtime output;
- `assets/`, `index.html` and `public/` are generated output. Regenerate them
  with `python3 site/build.py` instead of editing them manually.

## Behaviour

The workshop stays client-only. State is encoded in the URL hash and never
requires a server, user account, external API or analytics script. Every
button needs a useful action, and motion needs a reduced-motion path. Preserve
keyboard operation and visible focus when changing scenes or controls.

## Required checks

```bash
python3 site/build.py
python3 -m pytest -q site/tests
node --test site/tests/test_workshop_state.mjs site/tests/test_workshop_contract.mjs
```
