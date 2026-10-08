# Работа над Emoji Foundry

Emoji Foundry содержит бренд-кит и Fondy workshop. Авторский Telegram-пак
находится в отдельном проекте `../Чебутуркин Emoji` и имеет собственные
инструкции в его `AGENTS.md`.

После изменения исходников Foundry пересоберите сайт и запустите проверки:

```bash
python3 site/build.py
python3 -m pytest -q site/tests
node --test site/tests/test_workshop_state.mjs site/tests/test_workshop_contract.mjs
```

Не правьте `site/assets` и `site/public` вручную. Если изменился авторский
пак, сначала выполните его release и валидаторы, затем пересоберите workshop.
