"""Canonical human-facing metadata and selection rules for the emoji pack."""

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class PackEntry:
    stem: str
    display_name: str
    animation_summary: str
    groups: tuple[str, ...]
    static_frame: int
    static_source: str = "master"


PACK_ENTRIES = (
    PackEntry("01-heart", "Сердце", "Чернильные капли формируют заполненное сердце и дают асимметричный удар.", ("batch1",), 28),
    PackEntry("02-heart-double", "Двойное сердце", "Внутреннее сердце передает импульс внешнему.", ("batch3",), 25),
    PackEntry("03-heart-open", "Рисованное сердце", "Открытое сердце плавно рисуется от руки.", ("pilot",), 40),
    PackEntry("04-star", "Звезда", "Пять лучей раскрываются по очереди и складываются к центру.", ("batch1",), 20),
    PackEntry("05-star-four", "Четырехлучевая звезда", "Единая четырехлучевая звезда раскрывает концы по очереди и мягко оседает.", ("batch3",), 31),
    PackEntry("06-spark", "Искра", "Пересекающиеся мазки запускают четыре неодновременных луча.", ("batch1",), 29),
    PackEntry("07-lightning", "Молния", "Молния собирается импульсом без боковых отростков и оставляет короткое эхо.", ("pilot",), 30),
    PackEntry("08-lightning-round", "Молния в круге", "Круг заряжается, затем молния пробивает центр.", ("batch3",), 24),
    PackEntry("09-idea", "Идея", "Филамент, стекло и цоколь собираются независимыми слоями.", ("batch1",), 29),
    PackEntry("10-bulb-spark", "Лампочка", "Цельная лампа появляется до внутренней искры, после чего свет раздвигает стекло.", ("pilot",), 39),
    PackEntry("11-eye", "Глаз", "Веки открываются, зрачок ищет цель и фокусируется.", ("batch1",), 15),
    PackEntry("12-smile", "Улыбка", "Улыбка поднимает щеки, глаза и контур догоняют мимику.", ("batch1",), 14),
    PackEntry("13-laugh", "Смех", "Смеющееся лицо оживает тактильной мимикой.", ("pilot",), 33),
    PackEntry("14-sad", "Грусть", "Лицо оседает, рот прогибается и падает тяжелая слеза.", ("batch1",), 39),
    PackEntry("15-surprise", "Удивление", "Рот раскрывается первым, затем локально реагируют глаза и контур лица.", ("batch2",), 27),
    PackEntry("16-like", "Лайк", "Цельная бумажная рука входит от манжеты, поворачивается и поднимает палец.", ("batch2",), 38),
    PackEntry("17-dislike", "Дизлайк", "Цельная бумажная рука опускает большой палец с запаздывающей манжетой.", ("batch2",), 12),
    PackEntry("18-question", "Вопрос", "Точка падает первой, вопросительный штрих оборачивается вокруг.", ("batch2",), 28),
    PackEntry("19-exclamation", "Восклицание", "Тяжелый штрих падает на точку и получает упругую отдачу.", ("batch2",), 11),
    PackEntry("20-check", "Галочка", "Бумажная галочка рисуется одним уверенным мазком над синей глубиной.", ("batch2",), 24, "vector_static_renderer"),
    PackEntry("21-cross", "Крестик", "Два мазка сталкиваются в центре и расходятся обратно.", ("batch2",), 20),
    PackEntry("22-favorite", "Избранное", "Синяя закладка разворачивается вниз и формирует нижний вырез.", ("batch3",), 29, "vector_static_renderer"),
    PackEntry("23-launch", "Ракета", "Цельная ракета зажигает бумажное пламя и только затем плавно летит вверх.", ("batch3",), 26),
    PackEntry("24-explosion-ray", "Взрыв лучами", "Локально деформируемое ядро выпускает бумажные лучи с разными задержками.", ("batch3",), 26),
    PackEntry("25-explosion-cloud", "Облако взрыва", "Облачный взрыв раскрывается слоями и сворачивается.", ("pilot",), 20),
    PackEntry("26-explosion-ring", "Кольцо взрыва", "Две встречные дуги замыкаются и расширяются в неровное материальное кольцо.", ("batch3",), 34),
    PackEntry("27-ira-heart", "ИРА в сердце", "Слово ИРА рисуется бумажным штрихом без обводки, две синие линии собирают сердце.", ("personal",), 28, "vector_static_renderer"),
)

ENTRY_BY_STEM = {entry.stem: entry for entry in PACK_ENTRIES}


def select_stems(selection: str, specs: Mapping[str, object]) -> tuple[str, ...]:
    """Resolve pack groups, visual tags, or a comma-separated stem list."""
    if selection == "all":
        return tuple(specs)
    grouped = tuple(
        entry.stem for entry in PACK_ENTRIES if selection in entry.groups
    )
    if grouped:
        return grouped
    tagged = tuple(
        stem for stem, spec in specs.items() if selection in getattr(spec, "tags")
    )
    if tagged:
        return tagged
    stems = tuple(item.strip() for item in selection.split(",") if item.strip())
    unknown = tuple(stem for stem in stems if stem not in specs)
    if unknown or not stems:
        raise ValueError(f"unknown selection: {','.join(unknown) or selection}")
    return stems


def review_frames(entry: PackEntry, duration_frames: int) -> tuple[int, int, int]:
    """Return early, approved-static, and late frames for compact review."""
    early = max(1, duration_frames // 4)
    late = min(duration_frames - 2, max(entry.static_frame + 1, duration_frames * 3 // 4))
    return early, entry.static_frame, late
