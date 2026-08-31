# Unified Emoji Pack Redesign Design

## Goal

Improve the selected Chebaturkin Telegram emoji animations, enforce one visual language across all 27 items, and physically renumber every project artifact into a coherent final pack order.

## Scope

The redesign changes animation behavior for these current stems:

- `07-lightning`
- `12-smile`
- `14-sad`
- `15-surprise`
- `16-like`
- `17-dislike`
- `23-launch`
- `24-explosion-ray`
- `26-explosion-ring`
- `10-bulb-spark`
- `05-star-four`
- `22-favorite`

The following current stems receive constrained color-only changes:

- `01-heart`, `04-star`, `07-lightning`, `09-idea`, `11-eye`, `13-laugh`, `25-explosion-cloud`, and `10-bulb-spark`: replace pure-white glints or surfaces with paper `#F2F0E9`.
- `20-check`: change the foreground stroke from blue to paper while retaining the delayed blue depth layer.
- `27-ira-heart`: change the letters from beige to paper while retaining the blue heart and existing animation.

All other approved animation mechanics and silhouettes remain unchanged.

## Visual Language

The approved references are the current `01-heart`, `04-star`, `09-idea`, `11-eye`, `13-laugh`, `02-heart-double`, `03-heart-open`, `08-lightning-round`, and `25-explosion-cloud`.

Only these four colors may appear in authored or exported visible material:

- Brand blue `#2E3A4D`: principal colored silhouettes, contour depth, moving shadows, and deliberate accents.
- Taupe beige `#C4C1B4`: warm secondary material, restrained dimensional details, and selected tactile accents.
- Paper `#F2F0E9`: principal light material, light foreground strokes, highlights, and the `ИРА` lettering.
- Ink `#0D0D0D`: sparse high-contrast facial features, interior articulation, and details necessary for readability.

Pure white, the former blues `#5B8BC4` and `#7097C2`, interpolated decorative colors, and any other visible RGB values are forbidden. Alpha variation of the four approved colors is allowed.

Every symbol must read as a coherent physical object at Telegram custom emoji size. Animation is driven by the semantic behavior of the object rather than global scaling, generic pulsing, arbitrary fragments, rectangular reveals, or glitch motion. The shared motion grammar is anticipation, meaningful action, brief material response, and natural retraction. Exit motion uses reverse movement, directional erasure, or material retraction rather than a global opacity fade.

## Animation Designs

### Faces

`12-smile`, `14-sad`, and `15-surprise` become a visual family with `13-laugh`: a coherent paper face, tactile blue outline and depth, ink facial features, and local cheek and contour deformation. Each uses 48 source frames at 30 FPS.

- `12-smile`: the face is drawn as one object, the eyes appear, the mouth lifts the cheeks, and one eye closes into a natural wink. The floating line composition and decorative spark are removed.
- `14-sad`: the face settles downward, the brows converge, the mouth bends into a sad arc, and one blue tear gains weight and slides down the cheek. Fragmented line disintegration is removed.
- `15-surprise`: the face appears first, the mouth opens, the eyes widen with a short delay, and the contour gives one restrained elastic recoil. External shock rays are removed while the meaning remains clearly “surprise.”

### Hands and Check

`16-like` and `17-dislike` use shared authored hand geometry: a continuous palm, readable wrist and cuff, four grouped fingers, and an articulated thumb. Raster slicing into rectangular regions is removed. Both use 48 source frames at 30 FPS.

- `16-like`: the wrist enters from below, the palm turns slightly toward the viewer, and the thumb unfolds upward through its joint before settling. The confirmation spark is removed.
- `17-dislike`: the palm enters with more weight, the wrist turns downward, the thumb drops with inertia, and the cuff follows one or two frames later. It is related to, but not a mirrored copy of, the like gesture.
- Both hands use paper fill, blue contour and depth, and only sparse ink creases required to explain articulation.
- `20-check` retains its current 42-frame draw and tip-whip behavior. Its main stroke becomes paper and its delayed depth remains blue.

### Energy Symbols

- `07-lightning`: retain the approved 60-frame build, fill, charge, bend, and retraction. Remove both lateral branches. Convert the glint to paper.
- `24-explosion-ray`: a compressed irregular core accumulates tension and emits eight rays in a staggered wave. Each ray has distinct timing, length, and pressure. Core edges deform locally in response to the impulses rather than scaling as one image. Use 48 source frames.
- `26-explosion-ring`: a compact center impact starts two arcs that travel in opposing directions and close the outer wave. The ring expands asymmetrically, gives one restrained oscillation, and retracts toward the center. Scaling of the complete master image is removed. Use 48 source frames.
- `05-star-four`: the star grows continuously from one center. The leading vertical ray extends first, the horizontal pair follows, and the lower ray catches up. Tips flex locally and a paper highlight travels only over visible material. Rays retract sequentially into the center. Fragment assembly is removed. Use 48 source frames.

### Story Symbols

- `23-launch`: the rocket enters as one coherent object from below and aligns vertically. A paper-and-beige flame ignites, changes length and silhouette, then provides the impulse for a smooth upward flight. The body follows the thrust with restrained lag and stabilizes. Part-by-part assembly is removed. Use 48 source frames.
- `10-bulb-spark`: unlike `09-idea`, the bulb is not assembled from separate components. Its coherent blue glass contour is present first, the internal four-point element ignites, paper light expands from the center to the glass, the glass flexes locally, and the base reacts as if to a switch click. Retain 60 source frames.
- `22-favorite`: use a solid brand-blue bookmark without paper fill, double outline, or interior confirmation mark. The dense ribbon unrolls downward from the top, its lower V notch forms through a soft fold, and the material settles once. Use 48 source frames.
- `27-ira-heart`: retain the current 42-frame motion and blue heart. Render all three letters in paper instead of beige, including the static export. Rename internal layer identifiers and tests so they describe paper lettering.

## Final Physical Order

All numbered stems, source module filenames, `SPEC.stem` values, masters, generated frame directories, TGS, WebM, GIF previews, registries, tests, documentation references, manifest entries, and checksums are physically renamed to this order:

1. `heart`
2. `heart-double`
3. `heart-open`
4. `star`
5. `star-four`
6. `spark`
7. `lightning`
8. `lightning-round`
9. `idea`
10. `bulb-spark`
11. `eye`
12. `smile`
13. `laugh`
14. `sad`
15. `surprise`
16. `like`
17. `dislike`
18. `question`
19. `exclamation`
20. `check`
21. `cross`
22. `favorite`
23. `launch`
24. `explosion-ray`
25. `explosion-cloud`
26. `explosion-ring`
27. `ira-heart`

Renaming occurs only after the redesigned animations have passed visual review under their current stems. It uses collision-free temporary names before assigning final numbered names. `27-ira-heart` remains the final personal signature of the pack.

## Workflow and Review Gates

1. Add the four-color and motion-language rules to the root `AGENTS.md`.
2. Enforce the four-color rule in authored frames, TGS vectorization, validation, and regression tests.
3. Redesign and review the faces group.
4. Redesign and review the hands and check group.
5. Redesign and review the energy group.
6. Redesign and review the story group.
7. For each group, build source frames, individual GIFs, WebM, TGS, and a contact sheet. Review keyframes on both the dark preview background and the paper background.
8. After visual approval of every group, perform the physical renumbering and regenerate every derived artifact.
9. Update `emoji-manifest.json`, handoff documentation, and `SHA256SUMS` only after the final build is complete.

## Testing and Validation

Each behavior change begins with a narrow regression test that fails against the existing motion for the intended reason. Tests must assert semantic state or layer behavior rather than fragile whole-image equality.

Per-stem validation uses:

```bash
python3 build_all.py --only <stem> --preview --encode
python3 validate_animated.py --only <stem>
python3 build_tgs.py --only <stem>
python3 validate_tgs.py --only <stem>
```

Each thematic review gate includes its focused tests and the complete test suite. Final release validation uses:

```bash
python3 validate_animated.py
python3 validate_tgs.py
python3 -m pytest -q
shasum -a 256 -c SHA256SUMS
```

TGS files retain Telegram’s required 512×512 canvas, 60 FPS timeline, shape-only layers, `tgs: 1`, Bodymovin 5.5.2, rlottie-safe key order, visible first frame, and 65,536-byte maximum. WebM files retain 100×100 VP9 with alpha, 30 FPS, no audio, visible first frame, safe area, duration derived from the source frame count, and 262,144-byte maximum.

If one TGS exceeds or approaches its size budget, only that stem receives progressively simplified vector contours. Quality settings for other emoji remain unchanged.

## Completion Criteria

The redesign is complete when all 27 items use only the four approved colors, all selected animations match the approved mechanics, every thematic group has received visual approval, the complete project uses the new physical numbering without stale old-number artifacts, all generated release files pass both validators, all tests pass, and every entry in `SHA256SUMS` verifies.
