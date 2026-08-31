# Участие в Emoji Foundry

Emoji Foundry — приватный проект, который ведёт владелец. Любые изменения вносятся только с его явного одобрения.

## Перед началом работы

1. Прочитай `AGENTS.md`.
2. Прочитай `05-ai-handoff/CURRENT_STATE.md`, `STYLE_SYSTEM.md` и `emoji-manifest.json`.
3. Считай `04-editable-project/frame_motions` каноническим источником; не редактируй сгенерированные release-файлы вручную.
4. Меняй только запрошенный emoji и его целевые тесты.

## Обязательный порядок работы

```bash
cd 04-editable-project
python3 pack.py build --only <stem>
python3 pack.py review --only <stem>
python3 -m pytest -q
python3 validate_animated.py
python3 validate_tgs.py
```

Используй `python3 pack.py release`, только когда весь пак готов к синхронизации. Команда сначала собирает release во временную папку, затем заменяет сгенерированные release-папки и обновляет `SHA256SUMS`.

## Границы дизайна

- Используй в видимой графике только BLUE, TAUPE, PAPER и INK.
- Сравнивай читаемость в сгенерированных boards 100 × 100, а не только в 400 × 400.
- Не меняй персональный контент, например `27-ira-heart`, если он прямо не входит в задачу.
- Не добавляй лицензию и не делай репозиторий публичным без одобрения владельца.
