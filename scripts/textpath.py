"""Convert a text run into an SVG <path> using fontTools. Text becomes geometry,
so the banner renders identically on every machine GitHub serves it to."""
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform

_cache = {}

def _load(path):
    if path not in _cache:
        f = TTFont(path)
        _cache[path] = (f, f.getGlyphSet(), f["cmap"].getBestCmap(),
                        f["hmtx"], f["head"].unitsPerEm)
    return _cache[path]

def measure(text, font_path, size, tracking=0.0):
    _, _, cmap, hmtx, upem = _load(font_path)
    scale = size / upem
    w = 0.0
    for ch in text:
        g = cmap.get(ord(ch))
        if g is None:
            continue
        w += hmtx[g][0] * scale + tracking
    return w - (tracking if text else 0)

def path(text, font_path, size, x=0.0, y=0.0, tracking=0.0):
    """y is the baseline. Returns an SVG path 'd' string."""
    _, glyphset, cmap, hmtx, upem = _load(font_path)
    scale = size / upem
    pen = SVGPathPen(glyphset, ntos=lambda v: f"{v:.2f}")
    cursor = x
    for ch in text:
        g = cmap.get(ord(ch))
        if g is None:
            continue
        tp = TransformPen(pen, Transform(scale, 0, 0, -scale, cursor, y))
        glyphset[g].draw(tp)
        cursor += hmtx[g][0] * scale + tracking
    return pen.getCommands()
