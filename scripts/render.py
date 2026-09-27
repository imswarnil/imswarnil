#!/usr/bin/env python3
"""Draw every card on the profile as SVG, in light and dark.

Text is converted to outlines at build time, so the cards render identically
everywhere GitHub serves them — no webfont request, no fallback stack.

Everything the cards are drawn in comes from scripts/tokens.py: Frame & Signal
(design.imswarnil.com) resolved to values an SVG can hold. Geist and Geist Mono,
the system's near-monochrome grey ramp, and one orange rationed across the
page. No colour and no size below is typed by hand.

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


def chip(s, x, y, t, h=7 * T.SPACE, size=SZ["xs"]):
    """im-badge, pill variant: a fill from the surface ramp, no border, ink on it."""
    w = measure(s, MONO_MED, size) + 26
    return [f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" '
            f'fill="{t["surface_2"]}"/>',
            text(s, MONO_MED, size, x + 13, y + h / 2 + 4.5, t["ink"])], w


def caption(s, x, y, fill, size=SZ["xs"], font=MONO_MED):
    """im-caption — mono, 12px, 500, 0.08em, and quiet. Every label on the page."""
    return text(s, font, size, x, y, fill, T.CAPTION_TRACKING)


def caption_w(s, size=SZ["xs"], font=MONO_MED):
    return measure(s, font, size, T.track(size, T.CAPTION_TRACKING))


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


# The pattern families a card falls back to, cycled so neighbours differ.
PATTERNS = (bg_grid, bg_diamond, bg_lines, bg_dots)


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
def button(s, x, y, t, primary=False, h=44):
    """im-btn-lg. Primary is the accent; the second is im-btn-ink."""
    size = SZ["sm"]
    label = f"{s}  →"
    w = measure(label, SANS_MED, size) + 48
    bg, fg = (t["accent"], t["on_accent"]) if primary else (t["ink"], t["canvas"])
    return [f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" '
            f'rx="{T.RADIUS["md"]}" fill="{bg}"/>',
            text(label, SANS_MED, size, x + 24, y + h / 2 + 5, fg)], w


def hero(t):
    """The home hero: drafting paper, a numbered eyebrow, the headline with one
    phrase in the pixel face, a lede, and a cluster of two buttons."""
    H, L, R = 440, GUTTER, W - GUTTER
    o = [bg_grid(W, H, t), outline(0, 0, W, H, t, r=T.RADIUS["2xl"])]

    o += eyebrow("00", C.ROLE, L, 66, t)[0]
    o.append(caption(C.PLACE, R - caption_w(C.PLACE), 66, t["muted"]))

    o.append(text(C.NAME, SANS_SEMI, SZ["display"], L, 148, t["ink"], T.TIGHTER))

    head, pix, size = C.TAGLINE_HEAD, C.TAGLINE_PIXEL, 30
    o.append(text(head, SANS_MED, size, L, 196, t["body"], T.TIGHT))
    hw = measure(head, SANS_MED, size, T.track(size, T.TIGHT))
    o.append(text(pix, T.PIXEL, size, L + hw + 12, 196, t["accent"]))

    y = 246
    for line in wrap(C.LEDE, SANS, SZ["lg"], 760):
        o.append(text(line, SANS, SZ["lg"], L, y, t["body"]))
        y += round(SZ["lg"] * T.LEADING["lg"])

    by = y + 16
    x = L
    for (label, _url), primary in ((C.CTA_PRIMARY, True), (C.CTA_SECOND, False)):
        parts, bw = button(label, x, by, t, primary)
        o += parts
        x += bw + 3 * T.SPACE

    cx = R
    for c in reversed(C.CHIPS):
        parts, cw = chip(c, 0, 0, t)
        cx -= cw
        parts, _ = chip(c, cx, by + 8, t)
        o += parts
        cx -= 2 * T.SPACE

    return svg(W, H, t["canvas"], f"{C.NAME} — {C.TAGLINE}", o)


# ── stat band ────────────────────────────────────────────────────────────────
def band(t):
    """Four outline cards with a figure apiece — the row the docs home page puts
    directly under its hero. Every number is counted from content.py."""
    # The cards are their own image, stacked straight under the hero's, so the
    # gap between the two bands has to live inside this one — nothing in a README
    # puts space between two <img>. It is --im-grid-gap, the same gap as between
    # the cards themselves.
    gap = 6 * T.SPACE
    TOP = gap
    H, L, R = 132 + TOP, GUTTER, W - GUTTER
    cw = (R - L - 3 * gap) / 4
    figures = [(str(len(C.BUILDING)), "BUILDING"),
               (str(len(C.LIVE)), "LIVE"),
               (str(sum(len(items) for _g, items in C.SKILLS)), "SKILLS"),
               (str(len(C.ROLES)), "COMPANIES")]
    o = []
    for i, (value, label) in enumerate(figures):
        x = L + i * (cw + gap)
        o.append(outline(x, TOP, cw, H - TOP, t))
        o.append(text(value, SANS_SEMI, SZ["figure"], x + 28, TOP + 76, t["accent"] if i == 0
                      else t["ink"], T.TIGHTER))
        o.append(caption(label, x + 28, TOP + 104, t["muted"]))
    return svg(W, H, t["canvas"], "By the numbers", o)


# ── section head ─────────────────────────────────────────────────────────────
def section_head(index, title, cta, t):
    """home-head — the numbered caption, a hairline across, and a CTA on the right."""
    H, L, R = 56, GUTTER, W - GUTTER
    o = eyebrow(index, title, L, 22, t)[0]
    left = L + caption_w(index) + 14 + caption_w(title) + 24
    o.append(rule(left, R - (caption_w(cta) + 24 if cta else 0), 18, t["line"]))
    if cta:
        o.append(caption(cta, R - caption_w(cta) - 16, 22, t["ink"]))
        o.append(text("→", MONO_MED, SZ["xs"], R - 12, 22, t["accent"]))
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
    L, R, LABEL_W = GUTTER, W - GUTTER, 200
    GAP, ROW = 2 * T.SPACE, 9 * T.SPACE
    body, y = [], 58
    for i, (group, items) in enumerate(C.SKILLS):
        if i:
            y += 14
            body.append(rule(L, R, y - 24, t["line"]))
        top, x = y, L + LABEL_W
        for item in items:
            parts, cw = chip(item, x, y, t)
            if x + cw > R:
                x, y = L + LABEL_W, y + ROW
                parts, cw = chip(item, x, y, t)
            body += parts
            x += cw + GAP
        body.append(caption(group, L, top + 19, t["accent"] if i == 0 else t["muted"]))
        y += ROW
    return svg(W, y + 18, t["canvas"], "Skills",
               [caption("SKILLS", L, 32, t["muted"])] + body)


# ── experience ───────────────────────────────────────────────────────────────
def experience_card(t):
    L, R = GUTTER, W - GUTTER
    o = [caption("EXPERIENCE  ·  GO-TO-MARKET ENGINEERING", L, 34, t["muted"])]

    y = 68
    for line in wrap(C.SUMMARY, SANS, SZ["base"], R - L):
        o.append(text(line, SANS, SZ["base"], L, y, t["body"]))
        y += 26  # --im-leading-base, 1.6
    y += 12
    o.append(rule(L, R, y, t["line"]))
    y += 34

    for years, role, company, place, current in C.ROLES:
        o.append(caption(years, L, y, t["accent"] if current else t["muted"]))
        o.append(text(role, SANS_SEMI, SZ["h4"], L + 150, y, t["ink"], T.TIGHT))
        rw = measure(role, SANS_SEMI, SZ["h4"], T.track(SZ["h4"], T.TIGHT))
        o.append(text("· " + company, SANS, SZ["h4"], L + 150 + rw + 10, y, t["body"]))
        o.append(caption(place, R - caption_w(place), y, t["muted"]))
        y += 10 * T.SPACE

    y += 4
    o.append(rule(L, R, y, t["line"]))
    y += 34
    o.append(caption("SELECTED WORK", L, y, t["muted"]))
    y += 26

    for item in C.HIGHLIGHTS:
        o.append(f'<rect x="{L}" y="{y - 9}" width="10" height="2" fill="{t["accent"]}"/>')
        for line in wrap(item, SANS, SZ["sm"], R - L - 26):
            o.append(text(line, SANS, SZ["sm"], L + 26, y, t["body"]))
            y += 21  # --im-leading-sm, 1.5
        y += 10

    y += 4
    o.append(rule(L, R, y, t["line"]))
    y += 30
    o.append(caption(C.EDUCATION, L, y, t["muted"]))

    return svg(W, y + 30, t["canvas"], "Experience", o)


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
    H, L, R = 300, GUTTER, W - GUTTER
    o = [caption(f'SNAPSHOT  ·  {data["stamped"]}', L, 44, t["muted"])]
    tail = "GITHUB.COM/IMSWARNIL"
    o.append(caption(tail, R - caption_w(tail), 44, t["muted"]))
    o.append(rule(L, R, 60, t["line"]))

    col = (R - L) / 4
    for i, (value, lab) in enumerate(data["stats"]):
        x = L + i * col
        o.append(text(value, SANS_SEMI, SZ["figure"], x, 124,
                      t["accent"] if i == 0 else t["ink"], T.TIGHTER))
        o.append(caption(lab, x + 2, 152, t["muted"]))

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
        o.append(f'<circle cx="{x + 4:.1f}" cy="{by + 44}" r="4" fill="{color}"/>')
        o.append(text(lab, MONO, SZ["xs"], x + 16, by + 48.5, t["body"]))
        x += measure(lab, MONO, SZ["xs"]) + 42

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
