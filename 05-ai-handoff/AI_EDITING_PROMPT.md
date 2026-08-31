# Prompt for another AI

Ты работаешь с полным исходным проектом Telegram emoji pack из 27 символов.

Сначала прочитай корневой `AGENTS.md`, затем `05-ai-handoff/START_HERE.md`, `05-ai-handoff/CURRENT_STATE.md`, `05-ai-handoff/STYLE_SYSTEM.md`, `05-ai-handoff/emoji-manifest.json`, `05-ai-handoff/PALETTE.md` и `05-ai-handoff/EDITING_GUIDE.md`.

Правила работы:

- меняй только тот stem, который явно указал пользователь
- не изменяй остальные TGS, WebM, кадры или исходники
- перед изменением поведения создай узкий regression test и проверь, что он падает
- для TGS сохрани 512 x 512 px, 60 FPS, только shape layers и размер не больше 65536 байт
- каждый TGS shape group должен завершаться group transform, а первый кадр должен содержать видимую форму для миниатюры Telegram
- никогда не используй `sort_keys=True` для TGS JSON: в `rlottie` ключ `ty` должен идти до `it`, `ks`, `c` и другой полезной нагрузки, иначе Telegram может принять файл, но показать пустой emoji
- для резервного WebM сохрани 100 x 100 px, 30 FPS, VP9, отсутствие аудио, safe area 8 px, видимый первый кадр и размер не больше 262144 байт
- во всех видимых emoji используй только четыре цвета: #2E3A4D, #C4C1B4, #F2F0E9 и #0D0D0D; допустимы варианты этих цветов с прозрачностью
- не используй голубые вне палитры, включая прежние #5B8BC4 и #7097C2
- сначала пересобери один stem командой `python3 build_all.py --only <stem> --preview --encode`
- затем запусти `python3 validate_animated.py --only <stem>`
- пересобери векторный файл командой `python3 build_tgs.py --only <stem>`
- проверь его командой `python3 validate_tgs.py --only <stem>`
- после визуальной проверки запусти полный `python3 -m pytest -q` и `python3 validate_animated.py`
- для визуальной проверки сначала сгенерируй `python3 pack.py review --only <stem>` и оцени PNG в 100 × 100, а не только увеличенный PNG
- не удаляй пользовательские файлы и не перезаписывай итоговую папку без явного разрешения

В ответе укажи измененный source module, готовые TGS и WebM и результаты тестов.
