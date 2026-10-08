# Signal

This repository contains the Signal browser workshop and the local visual
sources it needs. Signal is a static, client-only product centred on the Fondy
mascot; it has no backend, account system, analytics or external API.

Workshop sources live in `site/sections` and `site/lib`. Brand sources used by
the runtime live in `brand-kit/assets/mascot`, `brand-kit/assets/favicons` and
`brand-kit/fonts`. Generated files in `site/assets`, `site/index.html` and
`site/public` are build output and must only be updated through the build.

After a source change, run:

```bash
python3 site/build.py
python3 -m pytest -q site/tests
node --test site/tests/test_workshop_state.mjs site/tests/test_workshop_contract.mjs
```

Do not reintroduce external pack exports or source folders into this
repository. Keep asset references relative so the generated page works from a
subpath, and preserve keyboard access plus a reduced-motion path for every
interactive scene.
