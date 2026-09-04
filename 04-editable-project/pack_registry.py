"""Canonical metadata and selection rules for the heart-only emoji pack."""

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
    PackEntry("01-heart", "Сердце", "Чернильные капли формируют заполненное сердце и дают асимметричный удар.", ("hearts",), 28),
    PackEntry("02-heart-double", "Двойное сердце", "Внутреннее сердце передаёт импульс внешнему.", ("hearts",), 25),
    PackEntry("03-heart-open", "Рисованное сердце", "Открытое сердце плавно рисуется от руки.", ("hearts",), 40),
    PackEntry("27-ira-heart", "ИРА в сердце", "Слово ИРА рисуется бумажным штрихом без обводки, а две синие линии собирают сердце.", ("hearts", "personal"), 28, "vector_static_renderer"),
)

ENTRY_BY_STEM = {entry.stem: entry for entry in PACK_ENTRIES}


def select_stems(selection: str, specs: Mapping[str, object]) -> tuple[str, ...]:
    """Resolve the heart collection or a comma-separated stem list."""
    if selection == "all":
        return tuple(specs)
    grouped = tuple(entry.stem for entry in PACK_ENTRIES if selection in entry.groups)
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
