# Chebaturkin Telegram Emoji Pack

## Назначение

Это самостоятельный проект авторского набора из 27 Telegram custom emoji. Основной результат: векторные анимированные TGS с прозрачным фоном. Также сохранены статичные PNG, превью GIF и резервные WebM.

Перед работой прочитай этот файл, затем `05-ai-handoff/CURRENT_STATE.md`, `05-ai-handoff/STYLE_SYSTEM.md` и `05-ai-handoff/emoji-manifest.json`. Подробности по палитре и путям находятся в `05-ai-handoff`.

## Структура

- `01-ready-to-upload/animated-tgs`: итоговые TGS для анимированного emoji pack
- `01-ready-to-upload/animated-webm`: резервный video-формат
- `02-static-png`: статичные версии 100 x 100 и редактируемые PNG 400 x 400
- `03-previews`: individual GIF и contact sheets, только для просмотра
- `04-editable-project`: Python-исходники, тесты, кадры и сборщики
- `05-ai-handoff`: манифест 27 emoji, палитра и краткие инструкции
- `SHA256SUMS`: контрольные суммы всего пакета

Канонические исходники анимаций находятся в `04-editable-project/frame_motions`. Не редактируй вручную файлы в `01-ready-to-upload`, `frames`, `upload`, `tgs_upload` или `previews`: это генерируемые результаты.

## Визуальные правила

- во всех видимых авторских и экспортируемых элементах разрешены ровно четыре RGB-цвета; варианты этих цветов с прозрачностью разрешены
- фирменный синий `BLUE`: `#2E3A4D`, RGB `(46, 58, 77)` — основные цветные силуэты, контуры, глубина, тени и акценты
- тёплый серо-бежевый `TAUPE`: `#C4C1B4`, RGB `(196, 193, 180)` — вторичный тёплый материал
- бумажный `PAPER`: `#F2F0E9`, RGB `(242, 240, 233)` — светлый материал, блики, светлые штрихи и буквы `ИРА`
- чернильный `INK`: `#0D0D0D`, RGB `(13, 13, 13)` — редкие высококонтрастные внутренние детали
- чистый белый, старые голубые `#5B8BC4` и `#7097C2`, а также любые другие видимые RGB-значения запрещены
- формы должны читаться в размере custom emoji, без мелких декоративных деталей
- каждый emoji должен читаться как цельный физический объект и следовать смысловой пластике: предвосхищение → смысловое действие → короткая реакция материала → естественное возвращение
- запрещены общая пульсация, глобальные scale/fade вместо смыслового движения, произвольные фрагменты, прямоугольные раскрытия и glitch-эффекты
- `27-ira-heart`: слово `ИРА` только бумажное, без обводки; сердце синее

## Как изменить один emoji

Работай из `04-editable-project`.

1. Найди stem в `frame_motions/registry.py` и модуль `frame_motions/mXX_name.py`.
2. Перед изменением поведения добавь узкий regression test и убедись, что он падает по нужной причине.
3. Меняй только запрошенный stem и связанные с ним тесты.
4. Пересобери и проверь:

```bash
python3 build_all.py --only <stem> --preview --encode
python3 validate_animated.py --only <stem>
python3 build_tgs.py --only <stem>
python3 validate_tgs.py --only <stem>
python3 -m pytest -q
```

5. После визуального подтверждения скопируй готовые файлы:

```bash
cp tgs_upload/<stem>.tgs ../01-ready-to-upload/animated-tgs/
cp upload/<stem>.webm ../01-ready-to-upload/animated-webm/
cp previews/individual/<stem>.gif ../03-previews/individual-gif/
```

Для текущего проекта предпочтительнее использовать `python3 pack.py review --only <stem>` для review и `python3 pack.py release` для безопасной синхронизации всех генерируемых release-файлов.

Для полной пересборки используй `python3 build_tgs.py --only all`, валидаторы и полный pytest. `export_final_package.py` создаёт новый пакет только по несуществующему пути и не предназначен для обновления текущей папки на месте.

## Критические требования TGS

- gzip JSON с расширением `.tgs` и верхнеуровневым `"tgs": 1`
- Bodymovin/Lottie version `5.5.2`
- холст 512 x 512, 60 FPS, цикл не длиннее 3 секунд
- размер не больше 65536 байт
- только векторные shape layers, без изображений, текста, масок, 3D, expressions, effects, merge paths, repeaters и других запрещённых Telegram возможностей
- объект не выходит за холст, первый кадр видимый
- каждый shape group заканчивается transform

### Важно: порядок ключей JSON для Telegram rlottie

Не включай `sort_keys=True` при `json.dumps`. Telegram может принять отсортированный файл, но показать пустой emoji. Парсер `rlottie` читает тип объекта последовательно и должен увидеть дискриминатор `ty` до полезной нагрузки:

- group: `ty` раньше `it`
- path: `ty` раньше `ks` (`ind` может идти перед `ty`)
- fill: `ty` раньше `c`
- transform: `ty` первым
- layer: `ty` раньше `ks` и `shapes`

Регрессия покрыта тестом `test_tgs_preserves_rlottie_type_discriminator_before_shape_payload`. Не ослабляй и не удаляй его. Локальные JSON-проверки сами по себе недостаточны: если бот принимает TGS, но emoji пустой, проверяй рендер через официальный Telegram `rlottie`.

## Требования резервного WebM

- ровно 100 x 100, VP9 с alpha, не больше 30 FPS
- без аудио, не длиннее 3 секунд, размер не больше 262144 байт
- первый кадр видимый

WebM не заменяет основной TGS, если пользователь просит максимально чёткие векторные emoji.

## Окружение и проверка

- Python 3.10+
- зависимости из `04-editable-project/requirements.txt`
- `04-editable-project/tools/ffmpeg` рассчитан на macOS arm64; на другой системе замени бинарник совместимым ffmpeg с `libvpx-vp9`

Финальный quality gate:

```bash
cd 04-editable-project
python3 validate_animated.py
python3 validate_tgs.py
python3 -m pytest -q
```

После изменений обнови `SHA256SUMS`. Не удаляй пользовательские исходники и не меняй остальные emoji без прямого запроса.
