# Signal — editorial workshop redesign

## Goal

Make the Signal workshop feel like a small, authored Fondy studio rather than a
generic collection of rounded interface cards. Keep all four existing scenes,
local-only state, keyboard access, reduced-motion behavior, and export actions.
Rewrite the visible and dynamic copy so every label tells the reader what they
can do or what just happened.

## Visual direction

The interface becomes an editorial workbench built on the existing paper,
cobalt, orange, ink, and Fondy assets:

- replace the repeated pill/card treatment with thin ruled lines, offset panels,
  small registration marks, and a stronger vertical rhythm;
- give the hero a two-column magazine composition with an oversized title,
  handwritten-feeling annotation, and a framed Fondy illustration instead of a
  circular blue badge;
- turn the scene navigation into a numbered index with active ink underline and
  compact descriptions, so the four choices read as a table of contents;
- make each scene's main interactive area a distinct work surface: a cobalt
  signal board, a dark pause sheet, an orange letter desk, and a blue rhythm
  strip, with less decoration and clearer controls;
- keep motion to purposeful state changes and preserve a no-motion path under
  `prefers-reduced-motion`.

The design stays responsive at the current breakpoints and uses only the local
fonts and mascot already in the repository.

## Copy direction

Use the established informal `ты` voice, lower-case authored headings where it
fits, and concrete action/result language. Remove symmetrical poetic lists,
vague personification, and labels that repeat the heading without adding
information.

Key changes:

- header note: `интерактивная мастерская Фонди`;
- hero lede: `здесь можно собрать последовательность, сделать паузу, написать записку или сыграть ритм. Фонди реагирует на действия.`;
- instruction: `нажимай и перетаскивай знаки, чтобы собрать сигнал`;
- mascot caption: `Фонди реагирует на твои действия.`;
- status: `добавь первый знак`;
- scene indices: `01 · знаки`, `02 · пауза`, `03 · записка`, `04 · ритм`;
- signal description: `выбери до четырёх знаков и расставь их в своём порядке`;
- pause description: `пройди четыре шага: нажми, удержи, отпусти и останься`;
- letter description: `напиши до 120 знаков и выбери знак для открытки`;
- rhythm description: `нажимай кнопки или клавиши 1–4 — ритм запишется`;
- remove poetic token subtitles and use one concrete palette instruction;
- action labels name their object (`сбросить сцену`, `повторить сигнал` etc.);
- privacy note: `данные остаются в браузере. аккаунт не нужен`;
- footer: `Signal — интерактивная мастерская Фонди`.

Dynamic status messages and export strings follow the same rule. In particular,
the product never claims that it sends or shares a note; it only creates a
local postcard or a copyable URL.

## Implementation scope

Modify only authored product sources:

- `site/sections/workshop.html` for structure and copy;
- `site/sections/workshop.css` for the visual system and responsive states;
- `site/sections/workshop.js` for dynamic copy and action labels;
- `docs/superpowers/specs/2026-10-09-signal-editorial-redesign-design.md` and
  the implementation plan for documentation.

Do not edit generated `site/index.html`, `site/assets`, or `site/public` by
hand. The state codec and export data model remain unchanged.

## Accessibility and verification

Keep tab/tabpanel semantics, visible focus, drag-and-click parity, keyboard
shortcuts, and status announcements. Every new visual animation must have a
reduced-motion override. After implementation run the repository's build,
Python tests, Node tests, and `site/verify.py` at the existing viewport set.
