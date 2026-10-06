"""Assemble the static Fondy workshop and archive case studies. No network inputs."""
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parent
WORKSHOP_FILES = {
    'html': ROOT / 'sections/workshop.html',
    'css': ROOT / 'sections/workshop.css',
    'js': ROOT / 'sections/workshop.js',
}
ARCHIVE_ORDER = ['hero', 'everyday', 'examples', 'process', 'contact']
CASES = {
    'kroshka': ('Крошка — стикерпак пекарни', 'Стикеры с характером пекарни: демонстрационный проект Emoji Foundry.'),
    'listva': ('Листва — эмодзи растительной мастерской', 'Авторский набор ботанических эмодзи: демонстрационный проект Emoji Foundry.'),
    'hod': ('Ход — персонаж веломастерской', 'Персонаж и состояния ремонта: демонстрационный проект Emoji Foundry.'),
}
HEARTS = ('01-heart', '02-heart-double', '03-heart-open', '27-ira-heart')

for label, source in WORKSHOP_FILES.items():
    if not source.is_file():
        raise SystemExit(f'Missing workshop source: {source}')
for name in CASES:
    for suffix in ['.html', '.css', '-preview.html']:
        if not (ROOT / 'cases' / (name + suffix)).is_file():
            raise SystemExit('Missing case source: ' + name + suffix)

workshop_html = WORKSHOP_FILES['html'].read_text()
workshop_styles = (ROOT / 'base.css').read_text() + '\n' + WORKSHOP_FILES['css'].read_text()
workshop_scripts = WORKSHOP_FILES['js'].read_text()

# Keep the former portfolio and case pages buildable as an archive bundle. They are
# deliberately kept out of the workshop landing bundle.
archive_sections = '\n'.join((ROOT / 'sections' / f'{name}.html').read_text() for name in ARCHIVE_ORDER)
archive_previews = '\n'.join((ROOT / 'cases' / f'{name}-preview.html').read_text() for name in CASES)
archive_sections = archive_sections.replace('<!-- CASE_PREVIEWS -->', archive_previews)
archive_styles = (ROOT / 'base.css').read_text() + '\n' + '\n'.join((ROOT / 'sections' / f'{name}.css').read_text() for name in ARCHIVE_ORDER)
archive_styles += '\n' + (ROOT / 'refinements.css').read_text() + '\n' + (ROOT / 'ui.css').read_text()
archive_styles += '\n' + '\n'.join((ROOT / 'cases' / f'{name}.css').read_text() for name in CASES)
archive_scripts = (ROOT / 'ui.js').read_text() + '\n'
archive_scripts += '\n'.join((ROOT / 'cases' / f'{name}.js').read_text() for name in CASES if (ROOT / 'cases' / f'{name}.js').exists())

# The public examples include their editable source packs.
pack_notes = {
    'kroshka': 'Крошка: 3 позы печенья, 6 фразовых стикеров, 4 предметных эмодзи и этикетка. Вишнёвый #6D202E, абрикосовый #F3B18B, кремовый #FFF4DD.',
    'listva': 'Листва: 3 позы улитки Тиши, 9 ботанических эмодзи и этикетка. Лесной зелёный, сливочная бумага и сирень. Палитра сохранена в SVG.',
    'hod': 'Ход: 3 позы механика Звена, 10 знаков, логотип и его компактная версия. Графит #1C201B, бумага #F1F0E5, лайм #D5F74A.',
}
for name in CASES:
    folder = ROOT / 'assets/cases' / name
    with zipfile.ZipFile(folder / (name + '-svg.zip'), 'w', zipfile.ZIP_DEFLATED) as archive:
        for source in sorted(folder.glob('*.svg')):
            archive.write(source, arcname=name + '/' + source.name)
        archive.writestr(name + '/README.txt', pack_notes[name] + '\n\nАвторский демонстрационный проект Emoji Foundry. Клиент вымышленный. Материалы созданы как примеры и редактируемые исходники; это не готовый Telegram TGS-пак. SVG подходят для веба и дальнейшей подготовки под площадку.\nНадписи используют текстовые элементы; для точного воспроизведения учитывайте указанные в SVG шрифты или переводите текст в кривые в векторном редакторе.\nhttps://chebaturkin.com\n')

fontdest = ROOT / 'assets/fonts'
fontdest.mkdir(exist_ok=True)
for font in (ROOT / 'fonts').iterdir():
    if font.is_file():
        shutil.copy2(font, fontdest / font.name)

# Keep the canonical heart files immutable; the build only copies release media
# into the website asset tree under stable names.
heart_sources = {
    '.webm': ROOT.parent / '01-ready-to-upload/animated-webm',
    '.gif': ROOT.parent / '03-previews/individual-gif',
    '.png': ROOT.parent / '02-static-png/100x100',
}
heart_dest = ROOT / 'assets/hearts'
heart_dest.mkdir(parents=True, exist_ok=True)
for suffix, source_dir in heart_sources.items():
    for heart in HEARTS:
        source = source_dir / f'{heart}{suffix}'
        if not source.is_file():
            raise SystemExit(f'Missing heart source: {source}')
        shutil.copy2(source, heart_dest / source.name)

(ROOT / 'assets/site.css').write_text(workshop_styles)
(ROOT / 'assets/site.js').write_text(workshop_scripts)
(ROOT / 'assets/archive.css').write_text(archive_styles)
(ROOT / 'assets/archive.js').write_text(archive_scripts)


def page(title, description, content, *, case=False, workshop=False):
    if workshop:
        return f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><meta name="description" content="{description}">
<link rel="icon" href="assets/favicons/favicon.svg" type="image/svg+xml">
<link rel="preload" href="assets/fonts/dela-gothic-one.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="assets/fonts/onest-variable.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="assets/site.css"><script defer src="assets/site.js"></script>
</head><body>{content}</body></html>'''
    nav = '<a class="case-return" href="/#examples">← все проекты</a>' if case else '<a class="page-nav-link" href="#examples">примеры</a><a class="page-nav-link" href="#process">как начинаем</a><a class="page-nav-contact" href="https://t.me/chebaturkin" target="_blank" rel="noopener noreferrer">обсудить задачу ↗</a>'
    return f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · Emoji Foundry</title><meta name="description" content="{description}">
<link rel="icon" href="/assets/favicons/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/assets/fonts/dela-gothic-one.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/onest-variable.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/archive.css"><script defer src="/assets/archive.js"></script>
</head><body{' class="case-shell"' if case else ''}><a class="page-skip" href="#main">К содержимому</a>
<header class="page-header"><a class="page-logo" href="/" aria-label="Emoji Foundry — начало"><img src="/assets/logos/primary-horizontal-color-light.svg" alt="Emoji Foundry" width="1112" height="246"></a><nav class="page-nav" aria-label="Навигация">{nav}</nav></header>
<main id="main">{content}</main>
<footer class="page-footer"><p>Emoji Foundry — авторская графика Тимофея Чебатуркина</p><a href="https://chebaturkin.com" target="_blank" rel="noopener noreferrer">chebaturkin.com ↗</a><span>2026</span></footer></body></html>'''

out = ROOT / 'public'
if out.exists():
    shutil.rmtree(out)
out.mkdir()
shutil.copytree(ROOT / 'assets', out / 'assets')
landing = page('скажи это жестом · Emoji Foundry', 'Маленькая статическая мастерская Фонди: собери сигнал, упакуй записку и сыграй ритм из четырёх сердечных жестов.', workshop_html, workshop=True)
(ROOT / 'index.html').write_text(landing)
(out / 'index.html').write_text(landing)
(out / 'cases').mkdir()
ending = '''<section class="case-bottom"><div><h2>а что можно сделать для вас?</h2><p>Пришлите ссылку на свой проект и пару строк о задаче. Обсудим, какая графика пригодится вам.</p></div><a class="fk-cut" href="https://t.me/chebaturkin" target="_blank" rel="noopener noreferrer">обсудить задачу <span aria-hidden="true">↗</span></a></section>'''
for name, (title, description) in CASES.items():
    content = (ROOT / 'cases' / f'{name}.html').read_text() + ending
    (out / 'cases' / f'{name}.html').write_text(page(title, description, content, case=True))
print('Built Fondy workshop landing + three archived case studies in site/public.')
