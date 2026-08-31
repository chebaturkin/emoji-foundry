# Chebaturkin Animated Telegram Emoji

Готовый набор из 27 анимированных эмодзи для Telegram с прозрачным фоном в двух форматах: основной векторный TGS и резервный WebM.

## Текущий статус

Все 27 эмодзи переведены на тактильный покадровый движок. У каждого символа собственная механика появления, акцента и сворачивания.

Исходная утвержденная пилотная пятерка:

- `07-lightning`
- `13-laugh`
- `03-heart-open`
- `25-explosion-cloud`
- `10-bulb-spark`

Первая партия из семи новых сценариев:

- `01-heart`
- `04-star`
- `06-spark`
- `09-idea`
- `11-eye`
- `12-smile`
- `14-sad`

Длительности итогового пака:

- 17 новых динамичных сценариев: 42 кадра при 30 FPS, цикл 1,4 секунды
- `01-heart`, `04-star`, `06-spark`, `09-idea` и `11-eye`: 48 кадров при 30 FPS, цикл 1,6 секунды
- пилотные `07-lightning`, `13-laugh`, `03-heart-open`, `25-explosion-cloud` и `10-bulb-spark`: 60 кадров при 30 FPS, цикл 2,0 секунды

Сценарии собираются вручную нарисованными линиями с меняющимся нажимом, локальной деформацией формы, независимыми слоями глубины, движущейся синей тенью и направленными бликами. Простая общая пульсация и одинаковое покачивание не используются.

Фирменный синий пака: `#2E3A4D`, RGB `(46, 58, 77)`. Голубые акценты вне фирменной палитры не используются в зарегистрированных сценариях. Персональный `27-ira-heart` рисует слово `ИРА` только бумажным `#F2F0E9`, без синей обводки, а две половины сердца остаются синими.

## Требования к окружению

- Python 3.10 или новее
- пакеты Python `Pillow` и `numpy`
- пакет Python `scikit-image` для векторизации TGS
- пакет `pytest` для запуска тестов
- исполняемый `tools/ffmpeg` с поддержкой VP9 через `libvpx-vp9` и прозрачности

В live-проекте `tools/ffmpeg` является Mach-O binary для macOS arm64. На другой платформе или архитектуре его нужно заменить совместимой сборкой ffmpeg по тому же пути и выдать файлу право на исполнение.

Каталог `masters` содержит 26 утверждённых статичных PNG и исторические исходники для сценариев с растровой основой. `pack_registry.py` явно определяет источник статики каждого emoji: исходный master сохраняется, пока он остаётся утверждённой композицией; изменённые векторные emoji рендерятся из канонического кадра `frame_motions`. Векторный `27-ira-heart` не требует master-файла.

## Что загружать

Для максимальной четкости загружай файлы из `tgs_upload`. Это векторные TGS:

- холст 512 x 512 px
- 60 FPS
- только shape layers без растровых изображений
- официальный верхнеуровневый маркер `tgs: 1`
- совместимые с `rlottie` shape groups с обязательным group transform
- видимый первый кадр для миниатюры Telegram
- не больше 64 KiB
- масштабируются Telegram без пикселизации 100 x 100 video emoji

Папка `upload` содержит резервные WebM. Они нужны, если конкретный workflow требует video-format. Каждый WebM:

- WebM с кодеком VP9 и прозрачностью
- VP9 сначала кодируется в lossless-режиме; только если файл превышает официальный лимит 256 KiB, encoder использует минимально необходимый CRF
- 100 x 100 px
- 30 FPS
- 17 новых динамичных сценариев: 1,4 секунды, 42 кадра
- `01-heart`, `04-star`, `06-spark`, `09-idea` и `11-eye`: 1,6 секунды, 48 кадров
- пилотная пятерка: 2,0 секунды, 60 кадров
- без звука
- не превышает 256 KiB, то есть 262144 bytes
- первый кадр содержит видимую форму для корректной миниатюры Telegram

Загружай `tgs_upload` как animated custom emoji pack. WebM из `upload` являются запасным video custom emoji pack.

## Предпросмотр

- `previews/contact-sheet-pilot.gif` показывает новую эталонную пятерку
- `previews/qa-tactile-dark.png` показывает ключевые кадры на темном фоне
- `previews/qa-tactile-light.png` показывает ключевые кадры на светлом фоне
- `previews/tactile-pilot-review.mp4` показывает два синхронных цикла новой пятерки
- `previews/contact-sheet-batch1-42.gif` и `previews/contact-sheet-batch1-48.gif` показывают первую партию без изменения темпа отдельных сценариев
- `previews/contact-sheet-batch2.gif` показывает сценарии `10-16`
- `previews/contact-sheet-batch3.gif` показывает сценарии `17`, `18`, `20`, `21`, `23`, `25` и `26`
- `previews/individual/27-ira-heart.gif` показывает персональный эмодзи `ИРА` с сердцем
- `previews/qa-batch1-dark.png` показывает ключевые кадры первой партии на темном фоне
- `previews/qa-batch1-light.png` показывает ключевые кадры первой партии на светлом фоне
- `previews/contact-sheet-all-42.gif`, `previews/contact-sheet-all-48.gif` и `previews/contact-sheet-all-60.gif` показывают текущий пак целиком, разделенный по длительности
- смешанные группы `soft`, `impact` и `story` используют тот же шаблон `previews/contact-sheet-<group>-<frames>.gif`
- однородные выборки сохраняют прежние имена без суффикса длительности, например `previews/contact-sheet-pilot.gif`
- `previews/individual` содержит отдельный GIF для каждого эмодзи на темном фоне
- `frames` содержит исходные прозрачные PNG-кадры 100 x 100 px
- `previews/review/current` содержит актуальные 100 × 100 статичные boards на светлом/тёмном фоне и keyframe boards для review

GIF-файлы предназначены только для просмотра. В Telegram сначала используй TGS из `tgs_upload`.

## Пересборка и проверка

Полная чистая пересборка всех кадров, individual GIF, WebM и TGS:

```bash
python3 build_all.py --only all --preview --encode
python3 build_tgs.py --only all
python3 validate_animated.py
python3 validate_tgs.py
python3 -m pytest -q
```

Пересборка двух последних партий:

```bash
python3 build_all.py --only batch2 --preview --encode
python3 build_all.py --only batch3 --preview --encode
python3 build_preview.py --only all --individual
```

`build_preview.py` не рендерит кадры и не кодирует WebM. Флаг `--individual` пересобирает individual GIF из уже существующих PNG с точным количеством кадров спецификации. Без флага команда строит contact sheets. Для всех поддерживаемых выборок:

```bash
for preview_group in all pilot batch1 batch2 batch3 soft impact story; do
    python3 build_preview.py --only "$preview_group"
done
```

Для проверки только новой пятерки:

```bash
python3 build_all.py --only pilot --preview --encode
python3 build_tactile_qa.py
python3 validate_animated.py --only pilot
```

Для полной сборки и проверки первой партии:

```bash
python3 build_all.py --only batch1 --preview --encode
python3 build_batch_qa.py
python3 validate_animated.py --only batch1
```

Валидатор берет ожидаемое количество кадров из спецификации каждого сценария. Поэтому он корректно проверяет набор с циклами по 42, 48 и 60 кадров. Contact sheets никогда не строят общий LCM-цикл для разных длительностей. Смешанная выборка разбивается на отдельные GIF с исходным темпом 30 FPS.

Все используемые сценарии находятся в `frame_motions`. Каждый символ можно корректировать независимо.

## Короткие команды

```bash
# собрать и проверить один или несколько emoji
python3 pack.py build --only 20-check,22-favorite

# получить review в настоящем размере emoji
python3 pack.py review --only 20-check,22-favorite

# выполнить полный build, тесты, staging-export, sync release и SHA-256
python3 pack.py release
```

Текущие визуальные правила находятся выше корневого README: сначала читай `../05-ai-handoff/CURRENT_STATE.md` и `../05-ai-handoff/STYLE_SYSTEM.md`. Старые документы в `docs/design` и `docs/plans` — исторические.
