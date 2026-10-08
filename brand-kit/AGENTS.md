# Signal brand sources

This directory contains the local visual sources used by Signal. Fondy is the
mascot; the product palette is Electric Cobalt `#2457FF`, Hot Tangerine
`#FF6B35`, Warm Paper `#FFF4DF` and Near Black `#171717`.

- `assets/mascot` — the Fondy SVG;
- `assets/favicons` — the browser favicon;
- `fonts` — local interface fonts and their licences;

The Signal build copies only these three groups. Preserve transparent SVGs and
the local font files when changing sources. Do not add exported media bundles or
network dependencies here.
