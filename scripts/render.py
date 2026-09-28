#!/usr/bin/env python3
"""Draw every card on the profile as SVG, in light and dark.

Text is converted to outlines at build time, so the cards render identically
everywhere GitHub serves them — no webfont request, no fallback stack.

Everything the cards are drawn in comes from scripts/tokens.py: Im Design System
(design.imswarnil.com) resolved to values an SVG can hold. Geist, Geist Mono and
one phrase of Geist Pixel, the system's near-monochrome grey ramp, one orange
rationed across the page — and its twelve columns, drawn. Every full-width card
shares one grid at one width, so the hairlines run unbroken down the README the
way they run down every page of the docs. No colour and no size below is typed
by hand.

    python3 scripts/render.py                     # everything except the stats card
    python3 scripts/render.py --stats             # stats too (needs GH_TOKEN)
    gh api graphql -f query=... | python3 scripts/render.py --stats --from-json -
"""
import argparse, base64, datetime, json, os, ssl, sys, urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from textpath import path, measure
from icons import ICONS
import content as C
import tokens as T

SANS, SANS_MED, SANS_SEMI = T.SANS, T.SANS_MED, T.SANS_SEMI
MONO, MONO_MED = T.MONO, T.MONO_MED
SZ = T.SIZE
W = 1200
GUTTER = 18 * T.SPACE  # 72px — the page margin every card shares
THEME_NAMES = ("dark", "light")

# The twelve columns every full-width card is measured in. `col(n)` is the left
# edge of column n (0-based); `span(n)` the width of n columns and the n-1 gaps
# between them — what `data-span` gives a block on the docs site.
GAP = T.GRID_GAP
COL = (W - 2 * GUTTER - (T.COLUMNS - 1) * GAP) / T.COLUMNS


def col(n):
    return GUTTER + n * (COL + GAP)


def span(n):
    return n * COL + (n - 1) * GAP


# ── helpers ──────────────────────────────────────────────────────────────────
def svg(w, h, bg, label, parts):
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h:.0f}" width="{w}" '
        f'height="{h:.0f}" role="img" aria-label="{escape(label)}">',
        f'<rect width="{w}" height="{h:.0f}" fill="{bg}"/>', *parts, '</svg>'])


def wrap(text_, font, size, max_w, tracking=0.0):
    lines, cur = [], ""
    for word in text_.split():
        trial = f"{cur} {word}".strip()
        if cur and measure(trial, font, size, tracking) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def text(s, font, size, x, y, fill, em=0.0):
    """A run of type. `em` is CSS letter-spacing, in em, as the system states it."""
    return f'<path d="{path(s, font, size, x, y, T.track(size, em))}" fill="{fill}"/>'


def chip(s, x, y, t, h=7 * T.SPACE, size=SZ["xs"], fill=None):
    """im-badge im-badge-pill: a fill from the surface ramp, no border, ink on it."""
    w = measure(s, MONO_MED, size) + 26
    return [f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" '
            f'fill="{fill or t["surface_2"]}"/>',
            text(s, MONO_MED, size, x + 13, y + h / 2 + 4.5, t["ink"])], w


def caption(s, x, y, fill, size=SZ["xs"], font=MONO_MED):
    """im-caption — mono, 12px, 500, 0.08em, and quiet. Every label on the page."""
    return text(s, font, size, x, y, fill, T.CAPTION_TRACKING)


def caption_w(s, size=SZ["xs"], font=MONO_MED):
    return measure(s, font, size, T.track(size, T.CAPTION_TRACKING))


def guides(h, t):
    """im-guides — the twelve columns, drawn behind everything.

    One hairline down the middle of each of the eleven gutters and one at each
    outer edge to close the frame; never two per column, which drew the columns
    as boxes. Every full-width card calls this at the same x, so stacked in the
    README the lines read as one grid running the length of the page.
    """
    xs = [GUTTER, W - GUTTER] + [col(i) - GAP / 2 for i in range(1, T.COLUMNS)]
    return "".join(f'<rect x="{x - 0.5:.2f}" y="0" width="1" height="{h:.0f}" '
                   f'fill="{t["guide"]}"/>' for x in xs)


def ground(x, y, w, h, t):
    """Words sit ON the grid, not under it: running text gets a canvas ground so
    the lines show in the gutters and the margins, never through a sentence."""
    return f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{t["canvas"]}"/>'


def rec_dot(cx, cy, t, r=5):
    """The recording light — the dot at the top right of the logo's last letter.
    A ring and a light, drawn once per page; it means *on air*, never *active*."""
    return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 1.9:.1f}" fill="{t["accent_tint"]}"/>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{t["accent"]}"/>')


def rule(x1, x2, y, fill):
    return f'<rect x="{x1}" y="{y}" width="{x2 - x1}" height="1" fill="{fill}"/>'


def outline(x, y, w, h, t, r=None):
    """im-card-outline — transparent, one hairline. The docs home page is built
    almost entirely out of these; a filled card is the exception there, not the rule."""
    r = T.RADIUS["xl"] if r is None else r
    return (f'<rect x="{x + 0.5}" y="{y + 0.5}" width="{w - 1}" height="{h - 1}" rx="{r}" '
            f'fill="none" stroke="{t["line"]}"/>')


def bg_grid(w, h, t, pitch=40, x=0, y=0, pid="grid", ink=None):
    """im-bg-grid — drafting paper, at the utility's own 2.5rem pitch."""
    return (f'<defs><pattern id="{pid}" width="{pitch}" height="{pitch}" '
            f'patternUnits="userSpaceOnUse" patternTransform="translate(-1 -1)">'
            f'<path d="M{pitch} 0 L0 0 0 {pitch}" fill="none" stroke="{ink or t["line"]}" '
            f'stroke-width="1"/></pattern></defs>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{pid})"/>')


def bg_lines(w, h, t, x=0, y=0, pitch=8, pid="hatch", ink=None):
    """im-bg-lines — a 135° hatch, the filler the docs put beside a split section."""
    return (f'<defs><pattern id="{pid}" width="{pitch}" height="{pitch}" '
            f'patternUnits="userSpaceOnUse" patternTransform="rotate(135)">'
            f'<line x1="0" y1="0" x2="0" y2="{pitch}" stroke="{ink or t["line"]}" '
            f'stroke-width="1"/></pattern></defs>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{pid})"/>')


def bg_diamond(w, h, t, x=0, y=0, pitch=16, pid="dia", ink=None):
    """im-bg-diamond — hatching both ways, a diamond lattice."""
    return (f'<defs><pattern id="{pid}" width="{pitch}" height="{pitch}" '
            f'patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<line x1="0" y1="0" x2="0" y2="{pitch}" stroke="{ink or t["line"]}" stroke-width="1"/>'
            f'<line x1="0" y1="0" x2="{pitch}" y2="0" stroke="{ink or t["line"]}" stroke-width="1"/>'
            f'</pattern></defs>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{pid})"/>')


def bg_dots(w, h, t, x=0, y=0, pitch=16, pid="dots", ink=None):
    """im-bg-dots — the marks family."""
    return (f'<defs><pattern id="{pid}" width="{pitch}" height="{pitch}" '
            f'patternUnits="userSpaceOnUse">'
            f'<circle cx="1.5" cy="1.5" r="1.5" fill="{ink or t["line"]}"/></pattern></defs>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{pid})"/>')


def bg_columns(w, h, t, x=0, y=0, pitch=24, pid="cols", ink=None):
    """im-bg-columns — upright hairlines, the grid's own gesture at thumbnail size."""
    return (f'<defs><pattern id="{pid}" width="{pitch}" height="{pitch}" '
            f'patternUnits="userSpaceOnUse">'
            f'<rect x="{pitch / 2}" y="0" width="1" height="{pitch}" fill="{ink or t["line"]}"/>'
            f'</pattern></defs>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{pid})"/>')


# The pattern families a card falls back to, cycled so neighbours differ.
PATTERNS = (bg_columns, bg_grid, bg_diamond, bg_lines, bg_dots)


def shot(slug):
    """A real screenshot for this project, if one has been put in shots/.

    An SVG served through GitHub's image proxy can fetch nothing, so the picture
    has to travel inside the file — base64, not an href to the png. Drop
    shots/<slug>.png in and the card uses it; leave it out and the media falls
    back to the system's own no-image treatment.
    """
    f = ROOT / "shots" / f"{slug}.png"
    return base64.b64encode(f.read_bytes()).decode() if f.exists() else None


def media(x, y, w, h, title, slug, t, idx):
    """im-card-media, on --im-surface-2, at a ratio set the way --im-card-ratio
    sets one. With no screenshot this is im-thumb's treatment: the surface, a
    pattern from the utilities, and the title's initial set large and quiet —
    what the system already does for a post with no feature image.
    """
    clip = f"m{slug}"
    o = [f'<defs><clipPath id="{clip}"><rect x="{x}" y="{y}" width="{w}" height="{h}" '
         f'rx="1"/></clipPath></defs>',
         f'<g clip-path="url(#{clip})">',
         f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{t["surface_2"]}"/>']
    png = shot(slug)
    if png:
        o.append(f'<image x="{x}" y="{y}" width="{w}" height="{h}" '
                 f'preserveAspectRatio="xMidYMid slice" '
                 f'href="data:image/png;base64,{png}"/>')
    else:
        o.append(PATTERNS[idx % len(PATTERNS)](w, h, t, x=x, y=y, pid=f"p{slug}",
                                               ink=t["surface_3"]))
        initial, size = title[0].upper(), h * 0.4
        iw = measure(initial, SANS_SEMI, size)
        o.append(text(initial, SANS_SEMI, size, x + (w - iw) / 2,
                      y + h / 2 + size * 0.36, t["faint"], T.TIGHTER))
    o.append("</g>")
    return o


def badge(s, x, y, t, accent=False):
    """im-badge. Accent for the one thing that is live work; outline for the rest."""
    h, size = 22, SZ["xs"]
    w = measure(s, MONO_MED, size) + 20
    if accent:
        box = (f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" '
               f'rx="{T.RADIUS["sm"]}" fill="{t["accent_tint"]}"/>')
        fg = t["accent"]
    else:
        box = outline(x, y, w, h, t, r=T.RADIUS["sm"])
        fg = t["muted"]
    return [box, text(s, MONO_MED, size, x + 10, y + h / 2 + 4.3, fg)], w


def eyebrow(index, label, x, y, t):
    """im-caption with data-index — the number in the accent, then the label.

    This is the thing that makes a page on design.imswarnil.com recognisable as
    one: every band is numbered, and the number is the only accent in the row.
    """
    o = [caption(index, x, y, t["accent"])]
    return o + [caption(label, x + caption_w(index) + 14, y, t["muted"])], None


def arrow(x, y, t, size=11):
    """The ↗ the docs put on a card that leaves the page."""
    return (f'<path d="M{x} {y + size} L{x + size} {y} M{x + size - 8} {y} H{x + size} '
            f'V{y + 8}" fill="none" stroke="{t["faint"]}" stroke-width="1.6" '
            f'stroke-linecap="square"/>')


# ── hero ─────────────────────────────────────────────────────────────────────
def button(s_, x, y, t, primary=False, h=44):
    """im-btn im-btn-lg — a pill (`--im-btn-radius: var(--im-radius-full)`).
    Primary is the accent; the second is the plain im-btn on --im-surface, which
    is how the docs home pairs them."""
    size = SZ["sm"]
    label = f"{s_}  →"
    w = measure(label, SANS_MED, size) + 44
    bg, fg = (t["accent"], t["on_accent"]) if primary else (t["surface"], t["ink"])
    return [f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" '
            f'rx="{h / 2}" fill="{bg}"/>',
            text(label, SANS_MED, size, x + 22, y + h / 2 + 5, fg)], w


def now_card(x, y, w, t):
    """home-hero-art: an im-card on --im-surface, four columns wide. It covers the
    lines, as anything with a ground does. What it holds is the one fact a reader
    wants first — where he is now — and the four hats as pill badges."""
    P = 6 * T.SPACE
    role, company, place = C.NOW
    rows, cx, cy = [], x + P, 0
    for c in C.CHIPS:
        _, cw = chip(c, 0, 0, t)
        if cx + cw > x + w - P:
            cx, cy = x + P, cy + 9 * T.SPACE
        rows.append((c, cx, cy))
        cx += cw + 2 * T.SPACE
    h = 172 + cy + 7 * T.SPACE + P
    o = [f'<rect x="{x:.2f}" y="{y}" width="{w:.2f}" height="{h}" rx="{T.RADIUS["xl"]}" '
         f'fill="{t["surface"]}"/>']
    o.append(caption("NOW", x + P, y + P + 12, t["muted"]))
    tail = "ON AIR"
    o.append(caption(tail, x + w - P - caption_w(tail), y + P + 12, t["muted"]))
    o.append(rec_dot(x + w - P - caption_w(tail) - 14, y + P + 8, t, r=3.5))
    o.append(text(role, SANS_SEMI, SZ["h3"], x + P, y + P + 58, t["ink"], T.TIGHT))
    o.append(text(company, SANS, SZ["base"], x + P, y + P + 84, t["body"]))
    o.append(caption(place.upper(), x + P, y + P + 110, t["muted"]))
    o.append(rule(x + P, x + w - P, y + P + 130, t["line"]))
    for c, cx, cy in rows:
        o += chip(c, cx, y + P + 148 + cy, t, fill=t["canvas"])[0]
    return o, h


def hero(t):
    """The home hero, on the grid: a numbered eyebrow, the name at display size
    with the recording light on its last letter, the tagline with one phrase in
    Geist Pixel, a lede held to seven columns, a pill cluster — and on the right,
    four columns of art, the way the docs home sets `home-hero-art`."""
    H = 452
    o = [guides(H, t)]

    o.append(ground(col(0), 48, caption_w("00") + 14 + caption_w(C.ROLE) + 8, 22, t))
    o += eyebrow("00", C.ROLE, col(0), 64, t)[0]

    size = SZ["display"]
    nw = measure(C.NAME, SANS_SEMI, size, T.track(size, T.TIGHTER))
    o.append(ground(col(0), 96, nw + 30, 66, t))
    o.append(text(C.NAME, SANS_SEMI, size, col(0), 148, t["ink"], T.TIGHTER))
    o.append(rec_dot(col(0) + nw + 12, 108, t, r=6))

    head, pix, ts = C.TAGLINE_HEAD, C.TAGLINE_PIXEL, 30
    hw = measure(head, SANS_MED, ts, T.track(ts, T.TIGHT))
    pw = measure(pix, T.PIXEL, ts)
    o.append(ground(col(0), 170, hw + 12 + pw + 8, 40, t))
    o.append(text(head, SANS_MED, ts, col(0), 200, t["body"], T.TIGHT))
    o.append(text(pix, T.PIXEL, ts, col(0) + hw + 12, 200, t["accent"]))

    lines = wrap(C.LEDE, SANS, SZ["lg"], span(7))
    lead = round(SZ["lg"] * T.LEADING["lg"])
    o.append(ground(col(0), 228, span(7), lead * len(lines) + 8, t))
    y = 252
    for line in lines:
        o.append(text(line, SANS, SZ["lg"], col(0), y, t["body"]))
        y += lead

    by, x = y + 14, col(0)
    for (label, _url), primary in ((C.CTA_PRIMARY, True), (C.CTA_SECOND, False)):
        parts, bw = button(label, x, by, t, primary)
        o += parts
        x += bw + 3 * T.SPACE

    card, ch = now_card(col(8), 186, span(4), t)
    o += card
    return svg(W, max(H, 186 + ch + 40), t["canvas"], f"{C.NAME} — {C.TAGLINE}", o)


# ── stat band ────────────────────────────────────────────────────────────────
def band(t):
    """Four outline cards with a figure apiece — the row the docs home page puts
    directly under its hero, three columns each (`im-grid-span-3`). Every number
    is counted from content.py."""
    H = 156
    o = [guides(H, t)]
    figures = [(str(len(C.BUILDING)), "BUILDING NOW"),
               (str(len(C.LIVE)), "LIVE"),
               (str(sum(len(items) for _g, items in C.SKILLS)), "SKILLS"),
               (str(len(C.ROLES)), "COMPANIES")]
    for i, (value, label) in enumerate(figures):
        x = col(3 * i)
        o.append(outline(x, 12, span(3), H - 24, t))
        o.append(text(value, SANS_SEMI, SZ["figure"], x + 28, 88, t["accent"] if i == 0
                      else t["ink"], T.TIGHTER))
        o.append(caption(label, x + 28, 116, t["muted"]))
    return svg(W, H, t["canvas"], "By the numbers", o)


# ── section head ─────────────────────────────────────────────────────────────
def section_head(index, title, cta, t):
    """home-head — the numbered caption, a hairline across, a CTA on the right.
    The caption sits on the grid; only the words get a ground."""
    H, L, R = 64, col(0), col(12) - GAP
    o = [guides(H, t)]
    lw = caption_w(index) + 14 + caption_w(title)
    o.append(ground(L, 16, lw + 16, 22, t))
    o += eyebrow(index, title, L, 32, t)[0]
    left = L + lw + 24
    right = R - (caption_w(cta) + 40 if cta else 0)
    o.append(rule(left, right, 27, t["line"]))
    if cta:
        cx = R - caption_w(cta) - 16
        o.append(ground(cx - 8, 16, R - cx + 8, 22, t))
        o.append(caption(cta, cx, 32, t["ink"]))
        o.append(text("→", MONO_MED, SZ["xs"], R - 12, 32, t["accent"]))
    return svg(W, H, t["canvas"], title, o)


# ── social pills ─────────────────────────────────────────────────────────────
def social_pill(icon, handle, primary, t):
    H, ICON, PAD = 34, 15, 15
    tw = measure(handle, MONO_MED, SZ["xs"])
    w = PAD + ICON + 9 + tw + PAD
    fg = t["on_accent"] if primary else t["ink"]
    return svg(round(w), H, t["canvas"], handle, [
        f'<rect width="{w:.1f}" height="{H}" rx="{H / 2}" '
        f'fill="{t["accent"] if primary else t["surface_2"]}"/>',
        f'<g transform="translate({PAD} {(H - ICON) / 2}) scale({ICON / 24})">'
        f'<path d="{ICONS[icon]}" fill="{fg}"/></g>',
        text(handle, MONO_MED, SZ["xs"], PAD + ICON + 9, H / 2 + 4.5, fg)])


# ── skills ───────────────────────────────────────────────────────────────────
def skills_card(t):
    """Label in columns one and two, chips from column three to the edge. Every
    chip has a ground, so it covers the lines it sits across."""
    L, R, X0 = col(0), col(12) - GAP, col(2)
    GAP_, ROW = 2 * T.SPACE, 9 * T.SPACE
    body, y = [], 36
    for i, (group, items) in enumerate(C.SKILLS):
        if i:
            y += 14
            body.append(rule(L, R, y - 24, t["line"]))
        top, x = y, X0
        for item in items:
            parts, cw = chip(item, x, y, t)
            if x + cw > R:
                x, y = X0, y + ROW
                parts, cw = chip(item, x, y, t)
            body += parts
            x += cw + GAP_
        body.append(ground(L, top + 4, caption_w(group) + 8, 20, t))
        body.append(caption(group, L, top + 19, t["accent"] if i == 0 else t["muted"]))
        y += ROW
    H = y + 18
    return svg(W, H, t["canvas"], "Skills", [guides(H, t)] + body)


# ── experience ───────────────────────────────────────────────────────────────
def experience_card(t):
    """The CV on the grid: years in columns one and two, the role from column
    three, the place flush to the last line. The summary and the selected work
    are running text, held to eight columns and given a ground."""
    L, R = col(0), col(12) - GAP
    body, o = [], []

    y = 30
    lines = wrap(C.SUMMARY, SANS, SZ["lg"], span(8))
    lead = round(SZ["lg"] * T.LEADING["lg"])
    o.append(ground(L, y - 22, span(8), lead * len(lines) + 12, t))
    for line in lines:
        o.append(text(line, SANS, SZ["lg"], L, y, t["body"]))
        y += lead
    y += 12
    o.append(rule(L, R, y, t["line"]))
    y += 40

    for years, role, company, place, current in C.ROLES:
        rw = measure(role, SANS_SEMI, SZ["h4"], T.track(SZ["h4"], T.TIGHT))
        cw = measure("· " + company, SANS, SZ["h4"])
        o.append(ground(L, y - 20, caption_w(years) + 8, 28, t))
        o.append(ground(col(2) - 4, y - 20, rw + cw + 22, 28, t))
        o.append(ground(R - caption_w(place) - 8, y - 20, caption_w(place) + 8, 28, t))
        o.append(caption(years, L, y, t["accent"] if current else t["muted"]))
        o.append(text(role, SANS_SEMI, SZ["h4"], col(2), y, t["ink"], T.TIGHT))
        o.append(text("· " + company, SANS, SZ["h4"], col(2) + rw + 10, y, t["body"]))
        o.append(caption(place, R - caption_w(place), y, t["muted"]))
        y += 11 * T.SPACE

    o.append(rule(L, R, y - 10, t["line"]))
    y += 30
    o.append(ground(L, y - 16, caption_w("SELECTED WORK") + 8, 22, t))
    o.append(caption("SELECTED WORK", L, y, t["muted"]))

    for item in C.HIGHLIGHTS:
        lines = wrap(item, SANS, SZ["sm"], span(8) - 26)
        top = y + 10
        o.append(ground(col(2) - 4, top, span(8) + 4, len(lines) * 21 + 14, t))
        yy = top + 24
        o.append(f'<rect x="{col(2)}" y="{yy - 9}" width="10" height="2" fill="{t["accent"]}"/>')
        for line in lines:
            o.append(text(line, SANS, SZ["sm"], col(2) + 26, yy, t["body"]))
            yy += 21  # --im-leading-sm, 1.5
        y = yy - 6

    y += 18
    o.append(rule(L, R, y, t["line"]))
    y += 34
    o.append(ground(L, y - 16, caption_w(C.EDUCATION) + 8, 22, t))
    o.append(caption(C.EDUCATION, L, y, t["muted"]))
    H = y + 30
    return svg(W, H, t["canvas"], "Experience", [guides(H, t)] + o)


# ── project tiles ────────────────────────────────────────────────────────────
def project_tile(title, blurb, stack, status, t, slug="x", idx=0):
    """im-card with media: the picture band, a badge over it, then the body.

    The media is the point of the card here — a project is a thing you look at.
    With no screenshot yet it is the system's no-image treatment rather than a
    blank box, and dropping shots/<slug>.png in swaps a real one straight into
    the same slot without touching this function.
    """
    TW, P = 580, 7 * T.SPACE
    MH = round(TW / 2)              # --im-card-ratio: 2 / 1
    TH = MH + 176
    o = [outline(0, 0, TW, TH, t)]
    o += media(1, 1, TW - 2, MH, title, slug, t, idx)
    o.append(rule(0, TW, MH + 1, t["line"]))
    o += badge(status.upper(), P, MH - 34, t, accent=(status == "building"))[0]

    y = MH + 60
    o.append(text(title, SANS_SEMI, SZ["h2"], P, y, t["ink"], T.TIGHT))
    o.append(arrow(TW - P - 12, y - 22, t))
    y += 32
    for line in wrap(blurb, SANS, SZ["sm"], TW - 2 * P)[:2]:
        o.append(text(line, SANS, SZ["sm"], P, y, t["body"]))
        y += round(SZ["sm"] * T.LEADING["sm"])
    o.append(rule(P, TW - P, TH - 46, t["line"]))
    o.append(text(stack, MONO, SZ["xs"], P, TH - 24, t["muted"], T.WIDE))
    return svg(TW, TH, t["canvas"], f"{title} — {blurb}", o)


# ── stats ────────────────────────────────────────────────────────────────────
QUERY = """
{ user(login: "imswarnil") {
    followers { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false) {
      totalCount
      nodes { languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
        edges { size node { name color } } } } }
    contributionsCollection {
      totalCommitContributions
      contributionCalendar { totalContributions } } } }
"""


def _ctx():
    """python.org builds on macOS ship without a CA bundle; CI has one."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def fetch(from_json=None):
    if from_json:
        raw = sys.stdin.read() if from_json == "-" else Path(from_json).read_text()
        return shape(json.loads(raw))
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("set GH_TOKEN (or GITHUB_TOKEN) to refresh the stats card")
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=json.dumps({"query": QUERY}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "imswarnil-profile"})
    with urllib.request.urlopen(req, timeout=30, context=_ctx()) as r:
        return shape(json.load(r))


def shape(payload):
    if "errors" in payload:
        sys.exit(f"graphql: {payload['errors']}")
    u = payload["data"]["user"]
    langs = {}
    for repo in u["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            n = e["node"]["name"]
            langs.setdefault(n, [0, e["node"]["color"] or T.GRAY[500]])
            langs[n][0] += e["size"]
    total = sum(v[0] for v in langs.values()) or 1
    cc = u["contributionsCollection"]
    return dict(
        stats=[(f'{cc["contributionCalendar"]["totalContributions"]:,}', "CONTRIBUTIONS · 1Y"),
               (f'{cc["totalCommitContributions"]:,}', "COMMITS · 1Y"),
               (str(u["repositories"]["totalCount"]), "PUBLIC REPOS"),
               (str(u["followers"]["totalCount"]), "FOLLOWERS")],
        langs=[(n, v[0] / total * 100, v[1])
               for n, v in sorted(langs.items(), key=lambda kv: -kv[1][0])[:6]],
        stamped=datetime.datetime.now(datetime.timezone.utc).strftime("%d %b %Y").upper())


def stats_card(t, data):
    """Four figures, three columns each, and the language bar across all twelve."""
    H, L, R = 300, col(0), col(12) - GAP
    o = [guides(H, t)]
    head = f'SNAPSHOT  ·  {data["stamped"]}'
    tail = "GITHUB.COM/IMSWARNIL"
    o.append(ground(L, 28, caption_w(head) + 8, 22, t))
    o.append(ground(R - caption_w(tail) - 8, 28, caption_w(tail) + 8, 22, t))
    o.append(caption(head, L, 44, t["muted"]))
    o.append(caption(tail, R - caption_w(tail), 44, t["muted"]))
    o.append(rule(L, R, 60, t["line"]))

    for i, (value, lab) in enumerate(data["stats"]):
        x = col(3 * i)
        vw = measure(value, SANS_SEMI, SZ["figure"], T.track(SZ["figure"], T.TIGHTER))
        o.append(ground(x, 84, max(vw, caption_w(lab)) + 12, 76, t))
        o.append(text(value, SANS_SEMI, SZ["figure"], x, 124,
                      t["accent"] if i == 0 else t["ink"], T.TIGHTER))
        o.append(caption(lab, x + 2, 152, t["muted"]))

    o.append(ground(L, 186, caption_w("LANGUAGES BY VOLUME") + 8, 22, t))
    o.append(caption("LANGUAGES BY VOLUME", L, 202, t["muted"]))
    by, bh = 216, 10
    o.append(f'<clipPath id="bar"><rect x="{L}" y="{by}" width="{R - L}" height="{bh}" '
             f'rx="{bh / 2}"/></clipPath>')
    o.append(f'<rect x="{L}" y="{by}" width="{R - L}" height="{bh}" rx="{bh / 2}" '
             f'fill="{t["surface_2"]}"/><g clip-path="url(#bar)">')
    x = float(L)
    for _, pct, color in data["langs"]:
        w = (R - L) * pct / 100
        o.append(f'<rect x="{x:.2f}" y="{by}" width="{w:.2f}" height="{bh}" fill="{color}"/>')
        x += w
    o.append('</g>')

    x = float(L)
    for name, pct, color in data["langs"]:
        lab = f"{name}  {pct:.0f}%"
        lw = measure(lab, MONO, SZ["xs"])
        o.append(ground(x - 4, by + 32, lw + 28, 24, t))
        o.append(f'<circle cx="{x + 4:.1f}" cy="{by + 44}" r="4" fill="{color}"/>')
        o.append(text(lab, MONO, SZ["xs"], x + 16, by + 48.5, t["body"]))
        x += lw + 42

    return svg(W, H, t["canvas"], "GitHub activity for imswarnil", o)


# ── build ────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true", help="also refresh the stats card")
    ap.add_argument("--from-json", metavar="PATH",
                    help="read the GraphQL response from a file, or '-' for stdin")
    args = ap.parse_args()

    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    written = 0

    def write(name, body):
        nonlocal written
        (out / name).write_text(body)
        written += 1

    for theme in THEME_NAMES:
        t = T.THEMES[theme]
        write(f"header-{theme}.svg", hero(t))
        write(f"band-{theme}.svg", band(t))
        for index, slug, title, cta in C.SECTIONS:
            write(f"head-{slug}-{theme}.svg", section_head(index, title, cta, t))
        write(f"skills-{theme}.svg", skills_card(t))
        write(f"experience-{theme}.svg", experience_card(t))
        for slug, icon, handle, _url, primary in C.SOCIAL:
            write(f"social-{slug}-{theme}.svg", social_pill(icon, handle, primary, t))
        for i, (slug, title, blurb, stack, status, _url) in enumerate(C.BUILDING + C.LIVE):
            write(f"proj-{slug}-{theme}.svg",
                  project_tile(title, blurb, stack, status, t, slug, i))

    if args.stats:
        data = fetch(args.from_json)
        for theme in THEME_NAMES:
            write(f"stats-{theme}.svg", stats_card(T.THEMES[theme], data))

    print(f"wrote {written} svg files to {out}")


if __name__ == "__main__":
    main()
