# Agent Handoff and Operability Design

## Goal

Make the emoji pack safe and quick for the next agent to understand, edit, review, and release without relying on stale documents or manual synchronisation.

## Decisions

1. `04-editable-project/pack_registry.py` becomes the source of truth for display metadata, pack order, groups, static-frame selection, and visual role notes. Build, validation, export, and the JSON handoff manifest consume it.
2. `04-editable-project/pack.py` supplies three explicit workflows: `build`, `review`, and `release`. A selection accepts one or more comma-separated stems everywhere.
3. Release is staged, validated, then synchronised into the five generated release directories. It regenerates SHA-256 checksums only after a successful full gate.
4. `03-previews/review/current` is the sole current review location. It contains 100 px light/dark review boards plus a keyframe board for the selected emoji. Historical contact sheets remain untouched in `03-previews/contact-sheets`.
5. `05-ai-handoff/CURRENT_STATE.md` records current non-negotiable decisions; `STYLE_SYSTEM.md` defines visual roles and line-weight references. Historical design/planning documents remain historical and are labelled as such rather than deleted.
6. Every emoji declares an explicit static source in the registry. Existing approved masters remain the static source unless the emoji is marked `vector_static_renderer`; a vector source also declares its canonical frame. This prevents silent drift without replacing an approved composed icon with an intermediate animation pose.

## Non-goals

- No redesign of unrelated emoji or changes to the four-colour palette.
- No deletion of existing historical previews or source art.
- No automatic upload to Telegram.

## Acceptance criteria

- A new agent can read `AGENTS.md`, `CURRENT_STATE.md`, and `STYLE_SYSTEM.md` to find the active visual rules.
- One command builds, validates, exports, synchronises, and hashes a release safely.
- A one-stem change produces a 100 px dark/light preview without creating ad-hoc files.
- Registry, manifest, release inventory, and static exports are covered by tests.
