import ast
import importlib
from pathlib import Path

from PIL import ImageColor

from frame_motions.common import BLUE


APPROVED_RGB = {
    (46, 58, 77),
    (196, 193, 180),
    (242, 240, 233),
    (13, 13, 13),
}
COLOR_KEYWORDS = {"color", "fill", "outline"}
COLOR_POSITIONAL_ARGUMENTS = {
    "new": {2},
    "ellipse": {1, 2},
    "polygon": {1, 2},
    "rectangle": {1, 2},
    "line": {1, 2},
    "draw_pressure_stroke": {2},
    "draw_brush_stroke": {2},
    "_pressure_stroke": {2},
    "_stroke": {3},
    "fill_polygon": {2},
    "draw_closed_shape": {2, 3},
    "_filled_polygon": {1},
    "_polygon_layer": {1},
    "_clipped_disc": {3},
    "_letter_image": {3},
    "_letter_layer": {4},
}
COLOR_NAME_PARTS = {
    "ACCENT",
    "BACKGROUND",
    "BLACK",
    "BLUE",
    "COLOR",
    "COLOUR",
    "ECHO",
    "FILL",
    "FOREGROUND",
    "GLINT",
    "INK",
    "PAPER",
    "SHADOW",
    "TAUPE",
    "TEAR",
    "WHITE",
}


def _rgba_literal(node):
    if isinstance(node, (ast.Tuple, ast.List)) and len(node.elts) in {3, 4}:
        channels = []
        for element in node.elts:
            if not isinstance(element, ast.Constant) or type(element.value) is not int:
                return None
            channels.append(element.value)
        if not all(0 <= channel <= 255 for channel in channels):
            return None
        return tuple(channels + [255]) if len(channels) == 3 else tuple(channels)

    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        try:
            return ImageColor.getcolor(node.value, "RGBA")
        except ValueError:
            return None

    return None


def _assigned_names(node):
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    return [target.id for target in targets if isinstance(target, ast.Name)]


def _is_color_name(name):
    return bool(set(name.upper().split("_")) & COLOR_NAME_PARTS)


def _call_name(call):
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def authored_color_violations(source, filename):
    tree = ast.parse(source, filename=filename)
    candidates = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            color = _rgba_literal(node.value)
            if color is not None and any(_is_color_name(name) for name in _assigned_names(node)):
                candidates[(node.value.lineno, node.value.col_offset)] = color
        elif isinstance(node, ast.Call):
            for keyword in node.keywords:
                color = _rgba_literal(keyword.value)
                if keyword.arg in COLOR_KEYWORDS and color is not None:
                    candidates[(keyword.value.lineno, keyword.value.col_offset)] = color
            for index in COLOR_POSITIONAL_ARGUMENTS.get(_call_name(node), set()):
                if index >= len(node.args):
                    continue
                color = _rgba_literal(node.args[index])
                if color is not None:
                    candidates[(node.args[index].lineno, node.args[index].col_offset)] = color
    return [
        (filename, line_number, color)
        for (line_number, _), color in sorted(candidates.items())
        if color[3] != 0 and color[:3] not in APPROVED_RGB
    ]


CONSTANTS = {
    "frame_motions.m06_spark": "SHADOW_BLUE",
    "frame_motions.m07_lightning": "ECHO_BLUE",
    "frame_motions.m09_idea": "SHADOW_BLUE",
    "frame_motions.m11_eye": "SHADOW_BLUE",
    "frame_motions.m03_heart_open": "SHADOW_BLUE",
}


def test_all_authored_blue_accents_use_brand_rgb():
    for module_name, constant_name in CONSTANTS.items():
        color = getattr(importlib.import_module(module_name), constant_name)
        assert color[:3] == BLUE[:3], (module_name, color)


def test_explosion_cloud_colored_lobes_use_only_brand_palette():
    from frame_motions.common import PAPER, TAUPE
    from frame_motions.m25_explosion_cloud import LOBE_CONFIG

    allowed = {BLUE[:3], PAPER[:3], TAUPE[:3]}
    for name, config in LOBE_CONFIG.items():
        assert config[-1][:3] in allowed, (name, config[-1])


def test_palette_audit_rejects_arbitrary_fifth_visible_color():
    source = """
def draw(drawer):
    drawer.ellipse((10, 20, 30, 40), fill=(1, 2, 3, 255))
"""

    assert authored_color_violations(source, "fixture.py") == [
        ("fixture.py", 3, (1, 2, 3, 255))
    ]


def test_palette_audit_rejects_list_rgb_hex_and_named_color_literals():
    source = '''
def draw(drawer):
    drawer.ellipse((10, 20, 30, 40), fill=[1, 2, 3, 255])
    drawer.ellipse((10, 20, 30, 40), fill=(1, 2, 3))
    drawer.ellipse((10, 20, 30, 40), fill="#010203")
    drawer.ellipse((10, 20, 30, 40), fill="red")
'''

    assert authored_color_violations(source, "fixture.py") == [
        ("fixture.py", 3, (1, 2, 3, 255)),
        ("fixture.py", 4, (1, 2, 3, 255)),
        ("fixture.py", 5, (1, 2, 3, 255)),
        ("fixture.py", 6, (255, 0, 0, 255)),
    ]


def test_palette_audit_ignores_transparency_geometry_comments_and_docstrings():
    source = '''
"""Geometry example: (255, 255, 255, 255)."""
# A comment mentioning fill=(255, 255, 255, 255) is not authored color.
BOUNDS = (255, 255, 255, 255)

def canvas(Image):
    return Image.new("RGBA", (100, 100), (0, 0, 0, 0))
'''

    assert authored_color_violations(source, "fixture.py") == []


def test_authored_sources_contain_no_forbidden_color_literals():
    root = Path(__file__).resolve().parents[1] / "frame_motions"
    violations = []
    for path in sorted(root.glob("*.py")):
        violations.extend(authored_color_violations(path.read_text(), path.name))
    assert violations == []
