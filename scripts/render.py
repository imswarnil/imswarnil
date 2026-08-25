#!/usr/bin/env python3
"""Draw every card on the profile as SVG, in light and dark.

Text is converted to outlines at build time, so the cards render identically
everywhere GitHub serves them — no webfont request, no fallback stack.

Palette and type are Frame & Signal (design.imswarnil.com): a near-monochrome ink
ramp with vermilion rationed as the record light.

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

FONTS  = ROOT / "fonts"
SG_BOLD = str(FONTS / "SpaceGrotesk-Bold.ttf")
SG_MED  = str(FONTS / "SpaceGrotesk-Medium.ttf")
MONO    = str(FONTS / "IBMPlexMono-Regular.ttf")
MONO_M  = str(FONTS / "IBMPlexMono-Medium.ttf")

SIGNAL = "#f04e2e"
THEMES = {
    "dark":  dict(bg="#08080c", frame="#272734", rule="#1c1c26", name="#f8f8fa",
                  tag="#a5a5b2", micro="#76768a", tick="#3c3c4e", body="#a5a5b2",
                  chip="#101017", chipline="#272734", chiptext="#a5a5b2",
                  tile="#0d0d13", tileline="#22222e", track="#191922"),
    "light": dict(bg="#fcfcfd", frame="#d3d3db", rule="#e5e5ea", name="#101017",
                  tag="#55556a", micro="#76768a", tick="#d3d3db", body="#3c3c4e",
                  chip="#f8f8fa", chipline="#e5e5ea", chiptext="#55556a",
                  tile="#ffffff", tileline="#e5e5ea", track="#f1f1f4"),
}
W = 1200
THEME_NAMES = ("dark", "light")


# ── helpers ──────────────────────────────────────────────────────────────────
def svg(w, h, bg, label, parts):
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h:.0f}" width="{w}" '
        f'height="{h:.0f}" role="img" aria-label="{escape(label)}">',
        f'<rect width="{w}" height="{h:.0f}" fill="{bg}"/>', *parts, '</svg>'])


def wrap(text, font, size, max_w, tracking=0.0):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and measure(trial, font, size, tracking) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def chip(text, x, y, t, h=28, size=12.5):
    w = measure(text, MONO, size, 0.2) + 26
    return [f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h/2}" '
            f'fill="{t["chip"]}" stroke="{t["chipline"]}"/>',
            f'<path d="{path(text, MONO, size, x+13, y+h/2+4.5, 0.2)}" '
            f'fill="{t["chiptext"]}"/>'], w


def label(text, x, y, fill, size=11, tracking=3.0, font=MONO):
    return f'<path d="{path(text, font, size, x, y, tracking)}" fill="{fill}"/>'


def rule(x1, x2, y, fill):
    return f'<rect x="{x1}" y="{y}" width="{x2-x1}" height="1" fill="{fill}"/>'


# ── banner ───────────────────────────────────────────────────────────────────
def banner(t):
    H = 340
    o, M = [], 26
    for x, y, dx, dy in ((M, M, 1, 1), (W-M, M, -1, 1), (M, H-M, 1, -1), (W-M, H-M, -1, -1)):
        o.append(f'<path d="M{x} {y+dy*26} L{x} {y} L{x+dx*26} {y}" fill="none" '
                 f'stroke="{t["frame"]}" stroke-width="2" stroke-linecap="square"/>')

    rx, ry = 74, 84
    o.append(f'<circle cx="{rx}" cy="{ry}" r="11" fill="{SIGNAL}" opacity="0.14"/>')
    o.append(f'<circle cx="{rx}" cy="{ry}" r="5" fill="{SIGNAL}"/>')
    o.append(label(C.ROLE, rx+22, ry+4.5, t["micro"], 12, 3.2, MONO_M))
    pw = measure(C.PLACE, MONO, 12, 3.2)
    o.append(label(C.PLACE, W-74-pw, ry+4.5, t["micro"], 12, 3.2))

    o.append(f'<path d="{path(C.NAME, SG_BOLD, 68, 72, 186, -0.5)}" fill="{t["name"]}"/>')
    o.append(f'<path d="{path(C.TAGLINE, SG_MED, 24, 74, 228)}" fill="{t["tag"]}"/>')
    o.append(f'<path d="{path(".", SG_MED, 24, 74+measure(C.TAGLINE, SG_MED, 24), 228)}" '
             f'fill="{SIGNAL}"/>')

    x, y = 72, 262
    for c in C.CHIPS:
        parts, cw = chip(c, x, y, t)
        o += parts
        x += cw + 8

    for i in range(9):
        o.append(f'<rect x="{W-74-i*13:.0f}" y="{y+6}" width="3" height="14" rx="1.5" '
                 f'fill="{SIGNAL if i == 3 else t["tick"]}"/>')

    return svg(W, H, t["bg"], f"{C.NAME} — {C.TAGLINE}", o)


# ── social pills ─────────────────────────────────────────────────────────────
def social_pill(icon, handle, primary, t):
    H, SZ, PAD = 34, 15, 15
    tw = measure(handle, MONO, 12.5, 0.2)
    w = PAD + SZ + 9 + tw + PAD
    fg = "#ffffff" if primary else t["chiptext"]
    return svg(round(w), H, t["bg"], handle, [
        f'<rect x="0.5" y="0.5" width="{w-1:.1f}" height="{H-1}" rx="{(H-1)/2}" '
        f'fill="{SIGNAL if primary else t["chip"]}" '
        f'stroke="{SIGNAL if primary else t["chipline"]}"/>',
        f'<g transform="translate({PAD} {(H-SZ)/2}) scale({SZ/24})">'
        f'<path d="{ICONS[icon]}" fill="{fg}"/></g>',
        f'<path d="{path(handle, MONO, 12.5, PAD+SZ+9, H/2+4.5, 0.2)}" fill="{fg}"/>'])


# ── skills ───────────────────────────────────────────────────────────────────
def skills_card(t):
    L, R, LABEL_W, CH, GAP, ROW = 72, W-72, 168, 28, 8, 36
    body, y = [], 58
    for i, (group, items) in enumerate(C.SKILLS):
        if i:
            y += 14
            body.append(rule(L, R, y-24, t["rule"]))
        top, x = y, L + LABEL_W
        for item in items:
            parts, cw = chip(item, x, y, t)
            if x + cw > R:
                x, y = L + LABEL_W, y + ROW
                parts, cw = chip(item, x, y, t)
            body += parts
            x += cw + GAP
        body.append(label(group, L, top+18.5, SIGNAL if i == 0 else t["micro"], 11, 3, MONO_M))
        y += ROW
    return svg(W, y+18, t["bg"], "Skills",
               [label("SKILLS", L, 32, t["micro"])] + body)


# ── experience ───────────────────────────────────────────────────────────────
def experience_card(t):
    L, R = 72, W-72
    o = [label("EXPERIENCE  ·  GO-TO-MARKET ENGINEERING", L, 34, t["micro"])]

    y = 68
    for line in wrap(C.SUMMARY, SG_MED, 16, R-L):
        o.append(f'<path d="{path(line, SG_MED, 16, L, y)}" fill="{t["tag"]}"/>')
        y += 25
    y += 12
    o.append(rule(L, R, y, t["rule"]))
    y += 34

    for years, role, company, place, current in C.ROLES:
        o.append(label(years, L, y, SIGNAL if current else t["micro"], 12, 1.6, MONO_M))
        rw = measure(role, SG_BOLD, 17)
        o.append(f'<path d="{path(role, SG_BOLD, 17, L+150, y)}" fill="{t["name"]}"/>')
        o.append(f'<path d="{path("· " + company, SG_MED, 17, L+150+rw+10, y)}" '
                 f'fill="{t["tag"]}"/>')
        pw = measure(place, MONO, 11, 1.6)
        o.append(label(place, R-pw, y, t["micro"], 11, 1.6))
        y += 40

    y += 4
    o.append(rule(L, R, y, t["rule"]))
    y += 34
    o.append(label("SELECTED WORK", L, y, t["micro"]))
    y += 26

    for item in C.HIGHLIGHTS:
        o.append(f'<rect x="{L}" y="{y-9}" width="10" height="2" fill="{SIGNAL}"/>')
        for line in wrap(item, SG_MED, 14.5, R-L-26):
            o.append(f'<path d="{path(line, SG_MED, 14.5, L+26, y)}" fill="{t["body"]}"/>')
            y += 22
        y += 10

    y += 4
    o.append(rule(L, R, y, t["rule"]))
    y += 30
    o.append(label(C.EDUCATION, L, y, t["micro"], 12, 1.4, MONO_M))

    return svg(W, y+30, t["bg"], "Experience", o)


# ── project tiles ────────────────────────────────────────────────────────────
def project_tile(title, blurb, stack, status, t):
    TW, TH, P = 580, 190, 28
    building = status == "building"
    o = [f'<rect x="0.5" y="0.5" width="{TW-1}" height="{TH-1}" rx="14" '
         f'fill="{t["tile"]}" stroke="{t["tileline"]}"/>',
         f'<circle cx="{P+4}" cy="34" r="4" fill="{SIGNAL if building else t["tick"]}"/>',
         label(status.upper(), P+17, 38, SIGNAL if building else t["micro"], 10, 2.6, MONO_M),
         f'<path d="M{TW-P-13} 40 L{TW-P} 27 M{TW-P-8} 27 H{TW-P} V35" fill="none" '
         f'stroke="{t["tick"]}" stroke-width="1.6" stroke-linecap="square"/>',
         f'<path d="{path(title, SG_BOLD, 23, P, 84, -0.3)}" fill="{t["name"]}"/>']

    y = 114
    for line in wrap(blurb, SG_MED, 14, TW-2*P)[:2]:
        o.append(f'<path d="{path(line, SG_MED, 14, P, y)}" fill="{t["tag"]}"/>')
        y += 21
    o.append(label(stack, P, TH-28, t["micro"], 11.5, 0.8))
    return svg(TW, TH, t["bg"], f"{title} — {blurb}", o)


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
            langs.setdefault(n, [0, e["node"]["color"] or "#76768a"])
            langs[n][0] += e["size"]
    total = sum(v[0] for v in langs.values()) or 1
    cc = u["contributionsCollection"]
    return dict(
        stats=[(f'{cc["contributionCalendar"]["totalContributions"]:,}', "CONTRIBUTIONS · 1Y"),
               (f'{cc["totalCommitContributions"]:,}', "COMMITS · 1Y"),
               (str(u["repositories"]["totalCount"]), "PUBLIC REPOS"),
               (str(u["followers"]["totalCount"]), "FOLLOWERS")],
        langs=[(n, v[0]/total*100, v[1])
               for n, v in sorted(langs.items(), key=lambda kv: -kv[1][0])[:6]],
        stamped=datetime.datetime.now(datetime.timezone.utc).strftime("%d %b %Y").upper())


def stats_card(t, data):
    H, L, R = 300, 72, W-72
    o = [label(f'SNAPSHOT  ·  {data["stamped"]}', L, 44, t["micro"])]
    tail = "GITHUB.COM/IMSWARNIL"
    o.append(label(tail, R-measure(tail, MONO, 11, 3), 44, t["micro"]))
    o.append(rule(L, R, 60, t["rule"]))

    col = (R-L)/4
    for i, (value, lab) in enumerate(data["stats"]):
        x = L + i*col
        o.append(f'<path d="{path(value, SG_BOLD, 46, x, 124, -0.5)}" '
                 f'fill="{SIGNAL if i == 0 else t["name"]}"/>')
        o.append(label(lab, x+2, 150, t["micro"], 11, 2.4))

    o.append(label("LANGUAGES BY VOLUME", L, 202, t["micro"]))
    by, bh = 216, 10
    o.append(f'<clipPath id="bar"><rect x="{L}" y="{by}" width="{R-L}" height="{bh}" '
             f'rx="{bh/2}"/></clipPath>')
    o.append(f'<rect x="{L}" y="{by}" width="{R-L}" height="{bh}" rx="{bh/2}" '
             f'fill="{t["track"]}"/><g clip-path="url(#bar)">')
    x = float(L)
    for _, pct, color in data["langs"]:
        w = (R-L)*pct/100
        o.append(f'<rect x="{x:.2f}" y="{by}" width="{w:.2f}" height="{bh}" fill="{color}"/>')
        x += w
    o.append('</g>')

    x = float(L)
    for name, pct, color in data["langs"]:
        lab = f"{name}  {pct:.0f}%"
        o.append(f'<circle cx="{x+4:.1f}" cy="{by+44}" r="4" fill="{color}"/>')
        o.append(f'<path d="{path(lab, MONO, 12, x+16, by+48.5, 0.2)}" fill="{t["chiptext"]}"/>')
        x += measure(lab, MONO, 12, 0.2) + 42

    return svg(W, H, t["bg"], "GitHub activity for imswarnil", o)


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
        t = THEMES[theme]
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
            write(f"stats-{theme}.svg", stats_card(THEMES[theme], data))

    print(f"wrote {written} svg files to {out}")


if __name__ == "__main__":
    main()
