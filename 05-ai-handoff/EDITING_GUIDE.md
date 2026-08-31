# Editing Guide

## Главные пути

- сценарии: `frame_motions/mXX_name.py`
- реестр: `frame_motions/registry.py`
- прозрачные кадры: `frames/<stem>`
- готовые WebM: `upload/<stem>.webm`
- готовые TGS: `tgs_upload/<stem>.tgs`
- TGS exporter: `tgs_core`, `build_tgs.py`, `validate_tgs.py`
- individual GIF: `previews/individual/<stem>.gif`
- `pack_registry.py`: канонический порядок, группы, названия, summary и статичный кадр каждого emoji
- `masters/<stem>.png`: утверждённая статичная графика для emoji, у которых `pack_registry.py` выбрал источник `master`

## Изменить один эмодзи

```bash
python3 -m pytest tests/<target-test>.py -q
python3 pack.py build --only <stem>
python3 pack.py review --only <stem>
```

Несколько emoji передаются через запятую: `--only 20-check,22-favorite`.

## Полная проверка

```bash
python3 -m pytest -q
python3 validate_animated.py
python3 validate_tgs.py
```

## Пересобрать и синхронизировать итоговую папку

Для нового независимого пакета используй staging-export:

```bash
python3 export_final_package.py --destination /absolute/new/path
```

Для обновления текущих release-папок после полной проверки используй одну безопасную команду:

```bash
python3 pack.py release
```

Она собирает весь pack, запускает валидаторы и тесты, создаёт staging-export, заменяет только генерируемые release-папки и обновляет `SHA256SUMS`.
