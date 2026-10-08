"""Build the static Signal workshop.

Signal is deliberately a small, client-only product. This builder has one
job: combine the authored workshop sources with the local Fondy mascot, fonts
and favicon, then write a clean ``site/public`` directory. It never reads a
pack export, reaches outside this repository, or talks to the network.
"""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent

BRAND_ASSETS = PROJECT_ROOT / "brand-kit" / "assets"
BRAND_MASCOT = BRAND_ASSETS / "mascot"
BRAND_FAVICONS = BRAND_ASSETS / "favicons"
BRAND_FONTS = PROJECT_ROOT / "brand-kit" / "fonts"

WORKSHOP_FILES = {
    "html": ROOT / "sections" / "workshop.html",
    "css": ROOT / "sections" / "workshop.css",
    "js": ROOT / "sections" / "workshop.js",
    "state": ROOT / "lib" / "workshop-state.js",
}


def require_file(path: Path, label: str | None = None) -> None:
    if not path.is_file():
        raise SystemExit(f"Missing build dependency: {label or path}")


def require_dir(path: Path, label: str | None = None) -> None:
    if not path.is_dir():
        raise SystemExit(f"Missing build dependency: {label or path}")


def read_text(path: Path) -> str:
    require_file(path)
    return path.read_text(encoding="utf-8")


def copy_file(source: Path, destination: Path, label: str | None = None) -> None:
    """Copy one deliberate runtime asset instead of importing a whole archive."""

    require_file(source, label)
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination / source.name)


def prepare_assets() -> Path:
    """Create a clean runtime asset tree from local brand sources only."""

    require_dir(BRAND_MASCOT, "brand-kit/assets/mascot")
    require_dir(BRAND_FAVICONS, "brand-kit/assets/favicons")
    require_dir(BRAND_FONTS, "brand-kit/fonts")

    assets = ROOT / "assets"
    if assets.exists():
        shutil.rmtree(assets)
    assets.mkdir(parents=True)

    copy_file(BRAND_MASCOT / "fondy-greeting-color-light.svg", assets / "mascot")
    copy_file(BRAND_FAVICONS / "favicon.svg", assets / "favicons")
    for filename in ("dela-gothic-one.woff2", "onest-variable.woff2", "dela-gothic-one-OFL.txt", "onest-variable-OFL.txt"):
        copy_file(BRAND_FONTS / filename, assets / "fonts")
    return assets


def page(title: str, description: str, content: str) -> str:
    """Wrap the authored Signal fragment in a portable HTML document."""

    return f'''<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#2457FF">
  <meta name="description" content="{description}">
  <title>{title}</title>
  <link rel="icon" href="assets/favicons/favicon.svg" type="image/svg+xml">
  <link rel="preload" href="assets/fonts/dela-gothic-one.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="assets/fonts/onest-variable.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="assets/site.css">
  <script defer src="assets/site.js"></script>
</head>
<body>{content}</body>
</html>
'''


def main() -> None:
    for path in WORKSHOP_FILES.values():
        require_file(path)
    require_file(ROOT / "base.css")

    assets = prepare_assets()
    styles = read_text(ROOT / "base.css") + "\n" + read_text(WORKSHOP_FILES["css"])
    # The pure state helper must load before the browser runtime.
    scripts = read_text(WORKSHOP_FILES["state"]) + "\n" + read_text(WORKSHOP_FILES["js"])
    (assets / "site.css").write_text(styles, encoding="utf-8")
    (assets / "site.js").write_text(scripts, encoding="utf-8")

    landing = page(
        "Signal · маленькая мастерская жестов",
        "Signal — маленькая браузерная мастерская Фонди: собери жест, дай ему паузу и сохрани открытку.",
        read_text(WORKSHOP_FILES["html"]),
    )
    (ROOT / "index.html").write_text(landing, encoding="utf-8")

    output = ROOT / "public"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    shutil.copytree(assets, output / "assets")
    (output / "index.html").write_text(landing, encoding="utf-8")

    print(f"Built Signal workshop in {output}.")


if __name__ == "__main__":
    main()
