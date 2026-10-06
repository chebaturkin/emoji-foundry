# Fondy Workshop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the service portfolio landing with a polished static Fondy workshop containing four accessible interactions, local hash sharing and browser image export.

**Architecture:** Keep the existing no-build-runtime approach. `site/build.py` assembles a focused workshop page from `site/sections/workshop.html`, `workshop.css` and `workshop.js`, copies stable heart media from the release folders, and writes a base-aware `site/public` bundle. The browser app owns one validated state machine, while each scene renders into its own panel and shares common status, motion, hash and export helpers.

**Tech Stack:** HTML, CSS, vanilla browser JavaScript, SVG/Canvas export, Python static assembly and Playwright-based `site/verify.py`; no npm dependency, server API or model provider.

---

### Task 1: Add focused workshop source structure

**Files:**
- Create: `site/sections/workshop.html`
- Create: `site/sections/workshop.css`
- Create: `site/sections/workshop.js`
- Modify: `site/build.py`

- [ ] **Step 1: Define the page contract in markup**

  Add a skip link, a header with a base-aware home link, a hero containing the labelled Fondy mascot, four scene navigation buttons, four `<section>` panels with stable IDs, one shared action bar, one `role="status" aria-live="polite"` node, and a footer with GitHub/author links. Every scene must include native buttons for its actions before drag enhancement is added.

- [ ] **Step 2: Add the visual system**

  Move the workshop into `site/sections/workshop.css` with the existing Dela/Onest fonts and palette. Add the motion tokens from the design spec, 44px controls, visible focus, mobile-first layout at 320px, scene cards, drop target states, envelope, pause progress and rhythm pads. Put hover-only transforms inside `@media (hover:hover) and (pointer:fine)` and keep reduced-motion rules in one final media block.

- [ ] **Step 3: Add the runtime entry point**

  Make `workshop.js` an IIFE or module-free browser script loaded after the page. Export no globals other than a guarded `window.__fondyWorkshop` debug object in development; production behavior must be driven by `data-*` hooks.

- [ ] **Step 4: Assemble only the workshop bundle**

  Change `build.py` so the landing page concatenates `base.css` plus `workshop.css` and `workshop.js` only. Keep old sections/cases as source archive and continue generating archive case pages separately if their current checks require them, but do not attach old service copy or case CSS to the workshop landing.

- [ ] **Step 5: Build and inspect the generated output**

  Run `python3 site/build.py`. Confirm `site/index.html`, `site/public/index.html`, `site/assets/site.css` and `site/assets/site.js` are generated and contain workshop hooks. Run `git diff --check`.

### Task 2: Implement validated state, hash sharing and common controls

**Files:**
- Modify: `site/sections/workshop.js`
- Modify: `site/sections/workshop.html`

- [ ] **Step 1: Add the state model and schema**

  Use a versioned state object with exact defaults:

  ```js
  const DEFAULT_STATE = { version: 1, mode: 'signal', signal: [], note: '', noteHeart: '01-heart', rhythm: [] };
  ```

  Validate modes against `['signal', 'letter', 'pause', 'rhythm']`, hearts against the four canonical names, signal length at most 4, note at most 120 Unicode code points, and rhythm length at most 32 values from `1..4`. Unknown fields are ignored.

- [ ] **Step 2: Implement hash encode/decode**

  Encode the validated JSON as URL-safe base64 in `#v1=<payload>`. Decode on first paint and on `hashchange`. On malformed/oversized data, use defaults and announce `ссылка устарела или повреждена`; never throw or write a transient pointer position into the hash. Use `history.replaceState` for internal state changes so Back is not polluted.

- [ ] **Step 3: Implement common scene controls**

  Add `reset`, `repeat`, `copy link`, `save PNG`, and mode navigation. Keep focus on the activating control. `copy link` uses `navigator.clipboard.writeText` and a textarea fallback; success and failure update the shared status node. `save PNG` calls the export helper and reports fallback errors in the same status node.

- [ ] **Step 4: Render and persist**

  Render from state rather than mutating only visual fragments. `renderState()` updates active navigation, scene visibility, button pressed state, result card and mascot reaction. Call it after every committed action and after hash decode.

### Task 3: Implement the four interactions

**Files:**
- Modify: `site/sections/workshop.html`
- Modify: `site/sections/workshop.js`
- Modify: `site/sections/workshop.css`

- [ ] **Step 1: Signal composer**

  Add four heart buttons with `aria-describedby` instructions and an `Добавить в сцену` keyboard path. Click/Enter/Space and drag must call the same `commitSignalHeart()` function. Pointer drag starts only after 8px movement or a 120ms hold, uses pointer capture, clamps to the stage, cancels on Escape/pointercancel/lostpointercapture, and suppresses the synthetic click after a successful touch drag. After four choices, play a 560ms reaction and enable save/share.

- [ ] **Step 2: Letter envelope**

  Add a labelled `<textarea maxlength="120">`, four heart choices and a submit button. Keep the input usable while the envelope animates. On submit, render the note into an SVG-safe text block with escaped content, animate tilt/fold by transform only, update state and announce completion. The note must be present in the hash only after the user submits, not on every keystroke.

- [ ] **Step 3: Pause sequence**

  Add four explicit step buttons. A pointer press starts the current step, release commits it, and a visible progress indicator updates. Provide `пропустить шаг` and `начать заново` so the scene remains usable with reduced motion and keyboard. Do not use mandatory audio or a timer that traps the user.

- [ ] **Step 4: Rhythm pad**

  Add four 44px+ buttons, keyboard shortcuts `1–4` and Space for the focused pad, and an eight-bar visual timeline. Ignore shortcuts while focus is in input/textarea/select/contenteditable. Each committed beat adds a value up to 32 entries, pulses the pad for 160ms and updates the result card. No audio is required.

- [ ] **Step 5: Mascot reactions**

  Add one pointer proximity loop capped to one `requestAnimationFrame`, clamped to ±6px/5°, only for fine pointers and no reduced motion. Add an IntersectionObserver and `visibilitychange` pause for the 7–9s idle loop. Add short state classes for signal, letter, pause and rhythm; keep decorative duplicate images empty-alt.

### Task 4: Add static asset copying and export helpers

**Files:**
- Modify: `site/build.py`
- Modify: `site/sections/workshop.js`
- Create: `site/assets/hearts/.gitkeep` (only if the source directory needs to be tracked)

- [ ] **Step 1: Copy release media during build**

  Copy `01-ready-to-upload/animated-webm`, `03-previews/individual-gif` and `02-static-png/100x100` into `site/public/assets/hearts` with the canonical four names. If any source is missing, stop with the exact missing path; never reference `../` at runtime. Add poster PNGs for video where present.

- [ ] **Step 2: Implement card SVG generation**

  Create a deterministic SVG string containing the current mode, selected heart media, note/rhythm summary and accessible title. Escape XML text and restrict note output to the validated 120 code points.

- [ ] **Step 3: Implement PNG/SVG download fallback**

  Await `document.fonts.ready`, load the SVG through a same-origin Blob URL, call `img.decode()` and draw to a fixed 1200×900 canvas. Use `canvas.toBlob`; if it returns null, download the SVG Blob instead. Revoke every temporary object URL in `finally`.

### Task 5: Rewrite product copy and repository guidance

**Files:**
- Modify: `site/sections/workshop.html`
- Modify: `site/README.md`
- Modify: `site/AGENTS.md`
- Modify: `README.md`
- Modify: `CONTRIBUTING.md`
- Modify: `SECURITY.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/WEB_PRODUCT.md`

- [ ] **Step 1: Replace public page copy**

  Use the approved short Russian copy: `скажи это жестом`, `собрать сигнал`, `дать паузу`, `упаковать записку`, `сыграть ритм`, `сохранить PNG`, `скопировать ссылку`. Remove service pricing, fictional client claims, Telegram sales CTA and promises.

- [ ] **Step 2: Rewrite README files**

  Explain the four scenes, static/no-API constraint, local launch with `python3 -m http.server 8000 --directory site`, hash sharing, PNG fallback, source layout and verification commands. State that the Telegram pack sources and workshop are separate and that no secrets or personal data are required.

- [ ] **Step 3: Mark legacy documents accurately**

  Mark `docs/WEB_PRODUCT.md` as historical AI-editor planning and update project instructions so contributors do not restore the old portfolio landing. Keep old cases as archive/source.

### Task 6: Extend automated and browser verification

**Files:**
- Modify: `site/verify.py`
- Create: `site/tests/test_workshop_state.mjs`
- Modify: `.gitignore` (only if generated verification artifacts need exclusion)

- [ ] **Step 1: Add pure state tests**

  Test defaults, valid round-trip, malformed hash fallback, unknown-field stripping, Unicode note length, signal/rhythm caps and state changes not including pointer coordinates. Run with `node --test site/tests/test_workshop_state.mjs`.

- [ ] **Step 2: Update browser checks**

  Serve the generated `site/public`, open at `/` and a `/emoji/`-style base path fixture, then assert four scene buttons, no broken media, no console errors, 320/390/768/1024/1440 no horizontal overflow, keyboard activation, hash restore, copy fallback, export fallback and reduced-motion behavior. Keep case archive checks separate from landing checks.

- [ ] **Step 3: Run the full verification set**

  Run `python3 site/build.py`, `python3 site/verify.py`, `node --test site/tests/test_workshop_state.mjs`, and `git diff --check`. Fix failures before moving to visual QA.

### Task 7: Visual QA and integration review

**Files:**
- Modify any source files needed after QA; regenerate `site/public` through `python3 site/build.py`.

- [ ] **Step 1: Inspect mobile first**

  Capture 320px and 390px screenshots, then 768px and 1440px. Check hero balance, active scene transition, card export appearance, focus ring and no clipping.

- [ ] **Step 2: Inspect motion and reduced motion**

  Verify idle pauses offscreen, pointer motion uses one frame, drag does not hijack scroll, reaction settles within 620ms, and reduced motion presents all content without autoplay.

- [ ] **Step 3: Review diff and generated files**

  Confirm no canonical emoji source, release artifact or unrelated worktree change was edited. Confirm generated outputs came only from the build command and run the final verification commands again.

- [ ] **Step 4: Commit implementation in focused commits**

  Commit source/runtime, docs/copy, and QA/generated output separately after each group passes its checks. Do not stage unrelated pre-existing changes.
