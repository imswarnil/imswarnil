"""Frame & Signal, resolved to values an SVG can use.

design.imswarnil.com is CSS: custom properties, `oklch()`, `color-mix()`. An SVG
served through GitHub's image proxy gets none of that — no cascade, no
`prefers-color-scheme`, no relative colour. So the system is resolved here, once,
and every card reads it from this file. The rule the profile is built on holds:
tokens are the source of truth, and nothing below is a colour someone picked by
eye to look close.

Three steps, in the order the system defines them:

  PRIMITIVES  the grey ramp, as `oklch(L 0 0)` — the L values are verbatim from
              the system's `foundation/tokens/primitives.css`, converted to sRGB
              here by the CSS Color 4 formula.
  SEMANTIC    canvas / surface / line / ink / body / muted / faint, mapped onto
              the ramp exactly as `foundation/tokens/semantic.css` maps them,
              light and dark.
  BRAND       one accent. Near-monochrome is the point: a single hue, rationed,
              so that when it appears it means something.

`--im-line` is a `color-mix()` with `transparent`. SVG has no compositing model
worth trusting through a proxy, so it is flattened over its own canvas here —
the same pixel a browser would paint, minus the maths at view time.
"""

# ── primitives: oklch(L 0 0) → sRGB ──────────────────────────────────────────
# Chroma is 0, so a and b are 0, so l' = m' = s' = L and every linear channel is
# L³. That collapses the full Oklab → sRGB matrix to one line.
def _grey(lightness):
    linear = lightness ** 3
    c = 12.92 * linear if linear <= 0.0031308 else 1.055 * linear ** (1 / 2.4) - 0.055
    v = round(max(0.0, min(1.0, c)) * 255)
    return f"#{v:02x}{v:02x}{v:02x}"


# primitives.css, verbatim.
GRAY = {n: _grey(l) for n, l in (
    (50, 0.985), (100, 0.97), (200, 0.922), (300, 0.87), (400, 0.708),
    (500, 0.556), (600, 0.439), (700, 0.371), (800, 0.269), (900, 0.205),
    (950, 0.145))}
WHITE = "#ffffff"


def _over(fg, alpha, bg):
    """Flatten `color-mix(in oklab, fg α%, transparent)` onto an opaque bg.

    Both ends of the mix are neutral, so oklab and sRGB agree on the hue and the
    only thing that survives is the alpha — a straight source-over composite.
    """
    fr, fg_, fb = (int(fg[1:][i:i + 2], 16) for i in (0, 2, 4))
    br, bg_, bb = (int(bg[1:][i:i + 2], 16) for i in (0, 2, 4))
    mix = lambda a, b_: round(alpha * a + (1 - alpha) * b_)
    return f"#{mix(fr, br):02x}{mix(fg_, bg_):02x}{mix(fb, bb):02x}"


# ── brand ────────────────────────────────────────────────────────────────────
# The system's own accent — the vermilion the docs site wears. One colour, on one
# thing at a time: the record light, the current row, the first number.
ACCENT = "#f04e2e"
ON_ACCENT = "#ffffff"


# ── semantic ─────────────────────────────────────────────────────────────────
def _theme(canvas, surface, surface_2, surface_3, ink, body, muted, faint,
           line_from, line_alpha):
    return dict(
        canvas=canvas, surface=surface, surface_2=surface_2, surface_3=surface_3,
        ink=ink, body=body, muted=muted, faint=faint,
        line=_over(line_from, line_alpha, canvas),
        accent=ACCENT, on_accent=ON_ACCENT)


THEMES = {
    "light": _theme(
        canvas=WHITE, surface=GRAY[100], surface_2=GRAY[200], surface_3=GRAY[300],
        ink=GRAY[950], body=GRAY[600], muted=GRAY[500], faint=GRAY[400],
        line_from=GRAY[500], line_alpha=0.24),
    "dark": _theme(
        canvas=GRAY[950], surface=GRAY[900], surface_2=GRAY[800], surface_3=GRAY[700],
        ink=WHITE, body=GRAY[400], muted=GRAY[500], faint=GRAY[600],
        line_from=GRAY[400], line_alpha=0.26),
}

# ── type ─────────────────────────────────────────────────────────────────────
# Geist and Geist Mono are the system's faces. Weights are separate files because
# the render outlines glyphs: there is no synthesis to fall back on, and no
# variable axis survives a <path>.
from pathlib import Path  # noqa: E402

_F = Path(__file__).resolve().parent.parent / "fonts"
SANS = str(_F / "Geist-Regular.ttf")
SANS_MED = str(_F / "Geist-Medium.ttf")
SANS_SEMI = str(_F / "Geist-SemiBold.ttf")
MONO = str(_F / "GeistMono-Regular.ttf")
MONO_MED = str(_F / "GeistMono-Medium.ttf")

# primitives.css, in px at a 16px root. `display` is the top of its clamp.
SIZE = dict(xs=12, sm=14, base=16, lg=18, h6=14, h5=16, h4=18, h3=20, h2=24,
            h1=30, display=60, figure=44)

# Tracking is em in CSS and px in a path, so it is multiplied at the call site.
TIGHT, TIGHTER, WIDE = -0.02, -0.035, 0.04
CAPTION_TRACKING = 0.08  # .im-caption, layout/page.css

RADIUS = dict(xs=4, sm=6, md=8, lg=12, xl=16, full=999)
SPACE = 4  # --im-space: 0.25rem. Every gap on these cards is a multiple.


def track(size, em):
    """CSS letter-spacing in em → the per-glyph advance textpath wants, in px."""
    return size * em
