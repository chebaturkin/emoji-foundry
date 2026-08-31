# START HERE

Это полный переносимый пакет из 27 Telegram emoji.

1. Сначала прочитай корневой `AGENTS.md`, затем `CURRENT_STATE.md` и `STYLE_SYSTEM.md`.
2. Для максимальной четкости загружай TGS из `01-ready-to-upload/animated-tgs`.
3. Если нужен video-format, резервные WebM находятся в `01-ready-to-upload/animated-webm`.
4. Статичные прозрачные PNG находятся в `02-static-png/100x100`.
5. Для точечного редактирования открой `04-editable-project`.
6. Описание каждого символа, его статичного кадра и всех путей находится в `emoji-manifest.json`.

Ничего внутри `01-ready-to-upload` редактировать вручную не нужно. TGS и WebM пересобираются из source module соответствующего stem.

Для текущего review используй `04-editable-project/previews/review/current`: там есть статичные 100 × 100 boards на светлом и тёмном фоне, а также boards ключевых кадров.
