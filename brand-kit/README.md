# Signal · исходники визуальной системы

Папка хранит локальные медиа, которые нужны браузерной мастерской Signal:
персонажа Фонди, favicon и два шрифта. Сайт не загружает эти файлы из сети.

## Что используется в Signal

| Путь | Назначение |
| --- | --- |
| `assets/mascot` | SVG персонажа Фонди |
| `assets/favicons` | favicon для браузера |
| `fonts` | Dela Gothic One, Onest и тексты лицензий |

`python3 site/build.py` копирует эти группы в `site/assets` и `site/public/assets`.
Получившиеся файлы не редактируйте вручную.

## Палитра и типографика

- Electric Cobalt `#2457FF`;
- Hot Tangerine `#FF6B35`;
- Warm Paper `#FFF4DF`;
- Near Black `#171717`.

Dela Gothic One используется для крупных заголовков, Onest — для интерфейса.
Лицензии SIL Open Font License лежат рядом с WOFF2-файлами.
