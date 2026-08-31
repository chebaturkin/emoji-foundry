# Static cohesion: four outlier emoji

## Goal

Make `20-check`, `21-cross`, `22-favorite`, and `27-ira-heart` read as members of the existing 27-emoji pack at the real Telegram review size of 100 × 100 px. The approved direction is a light PAPER object with a visible BLUE depth layer; it replaces the current thin, symbolic treatment.

## Shared language

- The primary read is always a compact, filled PAPER silhouette.
- BLUE is a deliberate lower/right material depth, not a hairline contour or decorative ring.
- The target visual mass is the `18-question` / `19-exclamation` pair.
- Keep the four sanctioned palette colors only. Never add white.
- Evaluate first at 100 × 100 on dark and light backgrounds; 400 × 400 is only an editing aid.

## Emoji changes

### 20-check

A single wide PAPER check stroke sits over a materially thicker BLUE carrier. The visible BLUE rim must be clearly readable at 100 px, with the perceived mass aligned to `19-exclamation`. No separate shadow effect is required beyond this depth layer.

### 21-cross

Replace the circular arc and thin crossed strokes with one compact, filled PAPER X silhouette over BLUE depth. Remove collision rays and any surrounding ring in the static state. The sign should form a balanced semantic pair with `18-question` and `19-exclamation`.

### 22-favorite

Use a solid PAPER bookmark silhouette over BLUE depth. Retain only the bottom notch needed to identify it as a bookmark. Remove the thin internal PAPER contour and avoid small decorative details.

### 27-ira-heart

Redraw `ИРА` as a compact, wide, geometric PAPER wordmark with a consistent, deliberately heavy stroke width. It must have no outline. Use an independent compact BLUE heart as the supporting mark, with enough separation for both components to read at 100 px.

## Animation follow-through

Static form is the source of truth. Once the static direction is accepted, update the named motion modules so each animation reveals and settles the same physical layers. Do not introduce global scale/fade, glitches, or arbitrary fragments.

## Acceptance checks

1. A contact sheet at 100 × 100 shows no visible style break between these four and their reference emoji.
2. The four artwork files contain only the approved palette and transparency.
3. `20-check` and `21-cross` remain unmistakable at 100 px.
4. `22-favorite` reads as a bookmark, not a flat UI outline.
5. `ИРА` is readable and PAPER-only; its heart is BLUE and separate.
6. Before release, run the repository's static, animated, TGS, WebM, test, and checksum gates required by `AGENTS.md`.
