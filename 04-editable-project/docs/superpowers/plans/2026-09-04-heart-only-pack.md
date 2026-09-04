# Heart-only Pack Implementation Plan

**Goal:** Reduce the package to three heart emoji and the personal `ИРА` heart.

1. Add a failing four-stem contract for both runtime and export registries.
2. Remove excluded emoji modules and generated assets, while preserving shared tooling.
3. Update registry, manifest, handoff documents, commands, and tests to expect four entries.
4. Rebuild the retained assets, validate TGS/WebM, regenerate checksums, and run the full suite.
