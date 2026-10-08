"""Build the static Fondy workshop bundle.

The build has no network inputs. It copies the small set of brand assets used
by the workshop, takes the four released heart files from the canonical pack
directories, and writes a self-contained ``site/public`` tree. Existing
fictional case studies are kept as an optional archive when their source files
are present; the workshop itself never depends on that archive.
"""

from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
PACK_ROOT = PROJECT_ROOT

# Keep these paths explicit: they are the source of truth for generated assets
# in a clean clone. The workshop only copies released media; it never edits the
# canonical heart sources.
BRAND_ASSET_ROOT = PROJECT_ROOT / "brand-kit/assets"
BRAND_MASCOT = PROJECT_ROOT / "brand-kit/assets/mascot"
BRAND_LOGOS = PROJECT_ROOT / "brand-kit/assets/logos"
BRAND_FONTS = PROJECT_ROOT / "brand-kit/fonts"

WORKSHOP_FILES = {
    "html": ROOT / "sections/workshop.html",
    "css": ROOT / "sections/workshop.css",
    "js": ROOT / "sections/workshop.js",
    "state": ROOT / "lib/workshop-state.js",
}
HEARTS = ("01-heart", "02-heart-double", "03-heart-open", "27-ira-heart")

ARCHIVE_ORDER = ("hero", "everyday", "examples", "process", "contact")
CASES = {
    "kroshka": (
        "Крошка — стикерпак пекарни",
        "Стикеры с характером пекарни: демонстрационный проект Emoji Foundry.",
    ),
    "listva": (
        "Листва — эмодзи растительной мастерской",
        "Авторский набор ботанических эмодзи: демонстрационный проект Emoji Foundry.",
    ),
    "hod": (
        "Ход — персонаж веломастерской",
        "Персонаж и состояния ремонта: демонстрационный проект Emoji Foundry.",
    ),
}


def read_text(path: Path) -> str:
    """Read authored text as UTF-8, with a useful build error."""

    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SystemExit(f"Missing build dependency: {path}") from exc


def require_file(path: Path, label: str | None = None) -> None:
    if not path.is_file():
        raise SystemExit(f"Missing build dependency: {label or path}")


def require_dir(path: Path, label: str | None = None) -> None:
    if not path.is_dir():
        raise SystemExit(f"Missing build dependency: {label or path}")


def copy_files(source: Path, destination: Path, *, suffixes: tuple[str, ...] | None = None) -> None:
    """Copy files from a source directory without deleting generated siblings."""

    require_dir(source)
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        if item.is_file() and (suffixes is None or item.suffix.lower() in suffixes):
            shutil.copy2(item, destination / item.name)


def prepare_assets() -> None:
    """Populate ``site/assets`` from brand-kit and canonical release outputs."""

    require_dir(BRAND_ASSET_ROOT, "brand-kit/assets")
    require_dir(BRAND_MASCOT, "brand-kit/assets/mascot")
    require_dir(BRAND_FONTS, "brand-kit/fonts")

    assets = ROOT / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    # Copy complete brand groups so visual variants remain available without a
    # runtime dependency on brand-kit. Generated case/hearts siblings survive.
    for group in ("favicons", "logos", "mascot", "stickers", "icons"):
        source = BRAND_ASSET_ROOT / group
        if source.is_dir():
            copy_files(source, assets / group)
    copy_files(BRAND_FONTS, assets / "fonts", suffixes=(".woff2", ".txt"))

    heart_sources = {
        ".webm": PACK_ROOT / "01-ready-to-upload/animated-webm",
        ".gif": PACK_ROOT / "03-previews/individual-gif",
        ".png": PACK_ROOT / "02-static-png/100x100",
    }
    heart_dest = assets / "hearts"
    heart_dest.mkdir(parents=True, exist_ok=True)
    if all(source_dir.is_dir() for source_dir in heart_sources.values()):
        for suffix, source_dir in heart_sources.items():
            for heart in HEARTS:
                source = source_dir / f"{heart}{suffix}"
                require_file(source)
                shutil.copy2(source, heart_dest / source.name)
    else:
        # Keep a local preview usable if generated release folders were removed
        # in a source-review worktree. A clean clone uses the canonical media.
        require_file(heart_dest / "01-heart.png", "site/assets/hearts/01-heart.png")


def rewrite_case_paths(value: str) -> str:
    """Make case fragments work from ``public/cases`` on any host path."""

    # Case fragments predate the portable workshop and use root-absolute URLs.
    value = re.sub(r"([\"'`])(/assets/)", r"\1../assets/", value)
    value = re.sub(r"([\"'`])(/cases/)", r"\1../cases/", value)
    value = re.sub(r"url\((/assets/)", r"url(../assets/", value)
    return value


def archive_available() -> bool:
    """Return whether all optional case sources are present."""

    required_files = []
    required_dirs = []
    for name in ARCHIVE_ORDER:
        required_files.extend((ROOT / "sections" / f"{name}.html", ROOT / "sections" / f"{name}.css"))
    for name in CASES:
        required_files.extend(
            (
                ROOT / "cases" / f"{name}.html",
                ROOT / "cases" / f"{name}-preview.html",
                ROOT / "cases" / f"{name}.css",
            )
        )
        required_dirs.append(ROOT / "assets/cases" / name)
    required_files.extend((ROOT / "refinements.css", ROOT / "ui.css", ROOT / "ui.js"))
    return all(path.is_file() for path in required_files) and all(path.is_dir() for path in required_dirs)


def build_archive_assets() -> None:
    """Create downloadable SVG archives for optional case studies."""

    notes = {
        "kroshka": "Крошка: 3 позы печенья, 6 фразовых стикеров, 4 предметных эмодзи и этикетка.",
        "listva": "Листва: 3 позы улитки Тиши, 9 ботанических эмодзи и этикетка.",
        "hod": "Ход: 3 позы механика Звена, 10 знаков, логотип и его компактная версия.",
    }
    for name in CASES:
        folder = ROOT / "assets/cases" / name
        require_dir(folder, f"site/assets/cases/{name}")
        svg_files = sorted(folder.glob("*.svg"))
        if not svg_files:
            raise SystemExit(f"Missing build dependency: SVG sources for {name}")
        archive_path = folder / f"{name}-svg.zip"
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for source in svg_files:
                archive.write(source, arcname=f"{name}/{source.name}")
            archive.writestr(
                f"{name}/README.txt",
                notes[name]
                + "\n\nАвторский демонстрационный проект Emoji Foundry. Клиент вымышленный. "
                + "Материалы созданы как примеры и редактируемые исходники; это не готовый Telegram TGS-пак.\n"
                + "https://chebaturkin.com\n",
            )


def page(title: str, description: str, content: str, *, case: bool = False, workshop: bool = False) -> str:
    """Wrap a fragment with paths relative to its output directory."""

    prefix = "../" if case else ""
    stylesheet = "site.css" if workshop else "archive.css"
    script = "site.js" if workshop else "archive.js"
    if workshop:
        return f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#2457FF"><title>{title}</title><meta name="description" content="{description}">
<link rel="icon" href="assets/favicons/favicon.svg" type="image/svg+xml">
<link rel="preload" href="assets/fonts/dela-gothic-one.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="assets/fonts/onest-variable.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="assets/{stylesheet}"><script defer src="assets/{script}"></script>
</head><body>{content}</body></html>'''
    nav = (
        f'<a class="case-return" href="{prefix}#examples">← все проекты</a>'
        if case
        else '<a class="page-nav-link" href="#examples">примеры</a><a class="page-nav-link" href="#process">как начинаем</a>'
    )
    return f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · Emoji Foundry</title><meta name="description" content="{description}">
<link rel="icon" href="{prefix}assets/favicons/favicon.svg" type="image/svg+xml">
<link rel="preload" href="{prefix}assets/fonts/dela-gothic-one.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{prefix}assets/fonts/onest-variable.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{prefix}assets/{stylesheet}"><script defer src="{prefix}assets/{script}"></script>
</head><body{' class="case-shell"' if case else ''}><a class="page-skip" href="#main">К содержимому</a>
<header class="page-header"><a class="page-logo" href="{prefix}" aria-label="Emoji Foundry — начало"><img src="{prefix}assets/logos/primary-horizontal-color-light.svg" alt="Emoji Foundry" width="1112" height="246"></a><nav class="page-nav" aria-label="Навигация">{nav}</nav></header>
<main id="main">{content}</main>
<footer class="page-footer"><p>Emoji Foundry — авторская графика Тимофея Чебатуркина</p><a href="https://chebaturkin.com" target="_blank" rel="noopener noreferrer">chebaturkin.com ↗</a><span>2026</span></footer></body></html>'''


def main() -> None:
    for path in WORKSHOP_FILES.values():
        require_file(path)
    require_file(ROOT / "base.css")

    prepare_assets()
    workshop_html = read_text(WORKSHOP_FILES["html"])
    workshop_styles = read_text(ROOT / "base.css") + "\n" + read_text(WORKSHOP_FILES["css"])
    # The pure state helper must load before the runtime in the generated file.
    workshop_scripts = read_text(WORKSHOP_FILES["state"]) + "\n" + read_text(WORKSHOP_FILES["js"])

    archive = archive_available()
    if archive:
        build_archive_assets()
        archive_styles = read_text(ROOT / "base.css") + "\n" + "\n".join(
            read_text(ROOT / "sections" / f"{name}.css") for name in ARCHIVE_ORDER
        )
        archive_styles += "\n" + read_text(ROOT / "refinements.css") + "\n" + read_text(ROOT / "ui.css")
        archive_styles += "\n" + "\n".join(read_text(ROOT / "cases" / f"{name}.css") for name in CASES)
        archive_scripts = read_text(ROOT / "ui.js") + "\n" + "\n".join(
            read_text(ROOT / "cases" / f"{name}.js")
            for name in CASES
            if (ROOT / "cases" / f"{name}.js").is_file()
        )
        archive_styles = rewrite_case_paths(archive_styles)
        archive_scripts = rewrite_case_paths(archive_scripts)
    else:
        archive_styles = archive_scripts = ""

    assets = ROOT / "assets"
    (assets / "site.css").write_text(workshop_styles, encoding="utf-8")
    (assets / "site.js").write_text(workshop_scripts, encoding="utf-8")
    if archive:
        (assets / "archive.css").write_text(archive_styles, encoding="utf-8")
        (assets / "archive.js").write_text(archive_scripts, encoding="utf-8")
    else:
        # Avoid carrying stale archive bundles into a workshop-only build.
        for stale in (assets / "archive.css", assets / "archive.js"):
            stale.unlink(missing_ok=True)

    landing = page(
        "скажи это жестом · Emoji Foundry",
        "Маленькая статическая мастерская Фонди: собери сигнал, упакуй записку и сыграй ритм из четырёх сердечных жестов.",
        workshop_html,
        workshop=True,
    )
    (ROOT / "index.html").write_text(landing, encoding="utf-8")

    out = ROOT / "public"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copytree(assets, out / "assets")
    (out / "index.html").write_text(landing, encoding="utf-8")

    if archive:
        cases_out = out / "cases"
        cases_out.mkdir()
        ending = '''<section class="case-bottom"><div><h2>а что можно сделать для вас?</h2><p>Пришлите ссылку на свой проект и пару строк о задаче. Обсудим, какая графика пригодится вам.</p></div><a class="fk-cut" href="https://t.me/chebaturkin" target="_blank" rel="noopener noreferrer">обсудить задачу <span aria-hidden="true">↗</span></a></section>'''
        for name, (title, description) in CASES.items():
            content = rewrite_case_paths(read_text(ROOT / "cases" / f"{name}.html")) + ending
            (cases_out / f"{name}.html").write_text(page(title, description, content, case=True), encoding="utf-8")

    status = " + optional case archive" if archive else ""
    print(f"Built Fondy workshop in {out}{status}.")


if __name__ == "__main__":
    main()
