"""Collision-safe physical renumbering for the 27-emoji package."""

from __future__ import annotations

import argparse
from pathlib import Path


OLD_TO_NEW = {
    "01-heart": "01-heart",
    "18-heart-double": "02-heart-double",
    "19-heart-open": "03-heart-open",
    "02-star": "04-star",
    "25-star-four": "05-star-four",
    "03-spark": "06-spark",
    "04-lightning": "07-lightning",
    "20-lightning-round": "08-lightning-round",
    "05-idea": "09-idea",
    "24-bulb-spark": "10-bulb-spark",
    "06-eye": "11-eye",
    "07-smile": "12-smile",
    "08-laugh": "13-laugh",
    "09-sad": "14-sad",
    "10-surprise": "15-surprise",
    "11-like": "16-like",
    "12-dislike": "17-dislike",
    "13-question": "18-question",
    "14-exclamation": "19-exclamation",
    "15-check": "20-check",
    "16-cross": "21-cross",
    "26-favorite": "22-favorite",
    "17-launch": "23-launch",
    "21-explosion-ray": "24-explosion-ray",
    "22-explosion-cloud": "25-explosion-cloud",
    "23-explosion-ring": "26-explosion-ring",
    "27-ira-heart": "27-ira-heart",
}

IGNORED_PARTS = {"__pycache__", ".pytest_cache", ".superpowers", ".git"}
TEXT_SUFFIXES = {".py", ".md", ".json"}


def _module_name(stem: str) -> str:
    number, slug = stem.split("-", 1)
    return f"m{number}_{slug.replace('-', '_')}"


MODULE_TO_MODULE = {
    _module_name(old): _module_name(new)
    for old, new in OLD_TO_NEW.items()
    if old != new
}


def _renamed_basename(name: str) -> str:
    suffix = Path(name).suffix
    stem = name[:-len(suffix)] if suffix else name
    if stem in MODULE_TO_MODULE:
        return MODULE_TO_MODULE[stem] + suffix
    for old, new in sorted(OLD_TO_NEW.items(), key=lambda item: -len(item[0])):
        if old != new and old in name:
            return name.replace(old, new)
    return name


def _ignored(path: Path, root: Path) -> bool:
    return any(part in IGNORED_PARTS for part in path.relative_to(root).parts)


def build_moves(package_root: Path) -> list[tuple[Path, Path]]:
    """Return validated source/destination pairs inside package_root."""
    root = package_root.resolve()
    if not (root / "AGENTS.md").is_file():
        raise ValueError(f"not an emoji package root: {root}")
    staged = [path for path in root.rglob(".renumber-stage-*") if not _ignored(path, root)]
    if staged:
        raise ValueError(f"unfinished renumber staging exists: {staged[0]}")

    raw = []
    for source in sorted(root.rglob("*"), key=lambda path: len(path.parts), reverse=True):
        if _ignored(source, root):
            continue
        renamed = _renamed_basename(source.name)
        if renamed != source.name:
            raw.append((source, source.with_name(renamed)))

    moved_directories = {source for source, _ in raw if source.is_dir()}
    moves = [
        (source, destination)
        for source, destination in raw
        if not any(parent in moved_directories for parent in source.parents)
    ]
    if not moves:
        raise ValueError("package is already renumbered or has no numbered assets")

    sources = {source for source, _ in moves}
    destinations = [destination for _, destination in moves]
    if len(set(destinations)) != len(destinations):
        raise ValueError("duplicate renumber destination")
    for source, destination in moves:
        if not source.exists():
            raise FileNotFoundError(source)
        try:
            destination.relative_to(root)
        except ValueError as error:
            raise ValueError(f"destination escapes package root: {destination}") from error
        if destination.exists() and destination not in sources:
            raise FileExistsError(destination)
    return sorted(moves, key=lambda pair: str(pair[0]))


def apply_moves(moves: list[tuple[Path, Path]]) -> None:
    """Apply a collision-free stage-then-final rename transaction."""
    if not moves:
        raise ValueError("no moves to apply")
    staged = []
    for index, (source, destination) in enumerate(moves):
        stage = source.with_name(f".renumber-stage-{index:04d}-{source.name}")
        if stage.exists():
            raise FileExistsError(stage)
        source.rename(stage)
        staged.append((stage, destination))
    if not all(stage.exists() for stage, _ in staged):
        raise RuntimeError("renumber staging transaction is incomplete")
    for stage, destination in staged:
        destination.parent.mkdir(parents=True, exist_ok=True)
        stage.rename(destination)


def _simultaneous_replace(text: str, replacements: dict[str, str], prefix: str) -> str:
    placeholders = {}
    for index, old in enumerate(sorted(replacements, key=len, reverse=True)):
        placeholder = f"__{prefix}_{index:03d}__"
        if placeholder in text:
            raise ValueError(f"replacement placeholder already present: {placeholder}")
        if old in text:
            text = text.replace(old, placeholder)
            placeholders[placeholder] = replacements[old]
    for placeholder, new in placeholders.items():
        text = text.replace(placeholder, new)
    return text


def rewrite_text_references(package_root: Path) -> None:
    """Rewrite stems and numbered module imports simultaneously."""
    root = package_root.resolve()
    excluded = {root / "04-editable-project" / "renumber_pack.py"}
    stem_replacements = {old: new for old, new in OLD_TO_NEW.items() if old != new}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES or _ignored(path, root):
            continue
        if path in excluded or path.name == "test_renumber_pack.py":
            continue
        original = path.read_text(encoding="utf-8")
        updated = _simultaneous_replace(original, MODULE_TO_MODULE, "MODULE_RENUMBER")
        updated = _simultaneous_replace(updated, stem_replacements, "STEM_RENUMBER")
        if updated != original:
            path.write_text(updated, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    moves = build_moves(args.root)
    for source, destination in moves:
        print(f"{source.relative_to(args.root.resolve())} -> {destination.relative_to(args.root.resolve())}")
    if args.apply:
        apply_moves(moves)
        rewrite_text_references(args.root)


if __name__ == "__main__":
    main()
