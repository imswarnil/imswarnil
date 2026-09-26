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
import argparse, datetime, json, os, ssl, sys, urllib.request
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


# ── banner ───────────────────────────────────────────────────────────────────
def banner(t):
    H = 340
    o, M = [], 26
    for x, y, dx, dy in ((M, M, 1, 1), (W - M, M, -1, 1),
                         (M, H - M, 1, -1), (W - M, H - M, -1, -1)):
        o.append(f'<path d="M{x} {y + dy * 26} L{x} {y} L{x + dx * 26} {y}" fill="none" '
                 f'stroke="{t["surface_3"]}" stroke-width="2" stroke-linecap="square"/>')

    rx, ry = 74, 84
    o.append(f'<circle cx="{rx}" cy="{ry}" r="11" fill="{t["accent"]}" opacity="0.14"/>')
    o.append(f'<circle cx="{rx}" cy="{ry}" r="5" fill="{t["accent"]}"/>')
    o.append(caption(C.ROLE, rx + 22, ry + 4.5, t["muted"]))
    o.append(caption(C.PLACE, W - 74 - caption_w(C.PLACE), ry + 4.5, t["muted"]))

    o.append(text(C.NAME, SANS_SEMI, SZ["display"], 72, 190, t["ink"], T.TIGHTER))
    o.append(text(C.TAGLINE, SANS_MED, SZ["h2"], 74, 232, t["body"], T.TIGHT))
    tw = measure(C.TAGLINE, SANS_MED, SZ["h2"], T.track(SZ["h2"], T.TIGHT))
    o.append(text(".", SANS_MED, SZ["h2"], 74 + tw, 232, t["accent"]))

    x, y = 72, 264
    for c in C.CHIPS:
        parts, cw = chip(c, x, y, t)
        o += parts
        x += cw + 2 * T.SPACE

    for i in range(9):
        o.append(f'<rect x="{W - 74 - i * 13:.0f}" y="{y + 6}" width="3" height="14" rx="1.5" '
                 f'fill="{t["accent"] if i == 3 else t["surface_3"]}"/>')

    return svg(W, H, t["canvas"], f"{C.NAME} — {C.TAGLINE}", o)


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
def project_tile(title, blurb, stack, status, t):
    TW, TH, P = 580, 190, 7 * T.SPACE
    building = status == "building"
    o = [f'<rect x="0.5" y="0.5" width="{TW - 1}" height="{TH - 1}" rx="{T.RADIUS["xl"]}" '
         f'fill="{t["surface"]}" stroke="{t["line"]}"/>',
         f'<circle cx="{P + 4}" cy="34" r="4" '
         f'fill="{t["accent"] if building else t["surface_3"]}"/>',
         caption(status.upper(), P + 17, 38, t["accent"] if building else t["muted"]),
         f'<path d="M{TW - P - 13} 40 L{TW - P} 27 M{TW - P - 8} 27 H{TW - P} V35" fill="none" '
         f'stroke="{t["faint"]}" stroke-width="1.6" stroke-linecap="square"/>',
         text(title, SANS_SEMI, SZ["h2"], P, 88, t["ink"], T.TIGHT)]

    y = 120
    for line in wrap(blurb, SANS, SZ["sm"], TW - 2 * P)[:2]:
        o.append(text(line, SANS, SZ["sm"], P, y, t["body"]))
        y += 21
    o.append(text(stack, MONO, SZ["xs"], P, TH - 28, t["muted"], T.WIDE))
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
        write(f"header-{theme}.svg", banner(t))
        write(f"skills-{theme}.svg", skills_card(t))
        write(f"experience-{theme}.svg", experience_card(t))
        for slug, icon, handle, _url, primary in C.SOCIAL:
            write(f"social-{slug}-{theme}.svg", social_pill(icon, handle, primary, t))
        for slug, title, blurb, stack, status, _url in C.BUILDING + C.LIVE:
            write(f"proj-{slug}-{theme}.svg", project_tile(title, blurb, stack, status, t))

    if args.stats:
        data = fetch(args.from_json)
        for theme in THEME_NAMES:
            write(f"stats-{theme}.svg", stats_card(T.THEMES[theme], data))

    print(f"wrote {written} svg files to {out}")


if __name__ == "__main__":
    main()
