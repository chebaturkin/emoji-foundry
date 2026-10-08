# Работа над Signal

Signal — маленький статический продукт. Правки интерфейса делаются в
`site/sections`, чистая логика состояния — в `site/lib`, а исходные медиа
Фонди и шрифты лежат в `brand-kit`.

Перед отправкой изменений пересоберите сайт и запустите проверки:

```bash
python3 site/build.py
python3 -m pytest -q site/tests
node --test site/tests/test_workshop_state.mjs site/tests/test_workshop_contract.mjs
```

Для проверки в браузере запустите `python3 site/serve.py --port 8799`, затем
`python3 site/verify.py`.

Не редактируйте `site/assets`, `site/index.html` и `site/public` вручную:
это результаты сборки. Сохраняйте относительные пути, доступность клавиатурой
и поведение при `prefers-reduced-motion: reduce`. Не добавляйте секреты,
сетевые зависимости или трекинг.
