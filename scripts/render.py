#!/usr/bin/env python3
"""Render the profile banner and the stats card as SVG, in light and dark.

Text is converted to outlines, so the cards look the same everywhere GitHub serves
them — no webfont request, no fallback stack, no camo surprises.

Palette and type are Frame & Signal (design.imswarnil.com): a near-monochrome ink
ramp, with vermilion rationed as the record light.

    python3 scripts/render.py                     # banner only, no network
    python3 scripts/render.py --stats             # refresh the stats card (needs GH_TOKEN)
    gh api graphql -f query=... | python3 scripts/render.py --stats --from-json -
"""
import argparse, datetime, json, os, ssl, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from textpath import path, measure
from xml.sax.saxutils import escape

FONTS = ROOT / "fonts"
SG_BOLD = str(FONTS / "SpaceGrotesk-Bold.ttf")
SG_MED  = str(FONTS / "SpaceGrotesk-Medium.ttf")
MONO    = str(FONTS / "IBMPlexMono-Regular.ttf")
MONO_M  = str(FONTS / "IBMPlexMono-Medium.ttf")

SIGNAL = "#f04e2e"
THEMES = {
    "dark":  dict(bg="#08080c", frame="#272734", rule="#1c1c26", name="#f8f8fa",
                  tag="#a5a5b2", micro="#76768a", tick="#3c3c4e",
                  chip="#101017", chipline="#272734", chiptext="#a5a5b2", track="#191922"),
    "light": dict(bg="#fcfcfd", frame="#d3d3db", rule="#e5e5ea", name="#101017",
                  tag="#55556a", micro="#76768a", tick="#d3d3db",
                  chip="#f8f8fa", chipline="#e5e5ea", chiptext="#55556a", track="#f1f1f4"),
}

# ── content ──────────────────────────────────────────────────────────────────
NAME    = "SWARNIL SINGHAI"
TAGLINE = "I slap keyboard & talk to camera"
ROLE    = "SALESFORCE ENGINEER  ·  7 YEARS"
PLACE   = "BUDAPEST  ·  HUNGARY"
CHIPS   = ["Engineer", "YouTuber", "Creator", "Trailblazer"]

SKILLS = [
    ("SALESFORCE", ["Salesforce", "CRM Analytics", "SAQL", "Apex", "Sales Cloud",
                    "Service Cloud", "CPQ", "Data Modelling", "Data Preparation",
                    "Einstein Discovery", "Automation"]),
    ("WEB",        ["JavaScript", "TypeScript", "Vue", "Next.js", "Python", "HTML",
                    "CSS", "Sass", "Tailwind", "Handlebars"]),
    ("PLATFORM",   ["Ghost", "Jekyll", "Supabase", "Postgres", "Vercel", "Cloudflare",
                    "GitHub Pages", "Git"]),
]

W = 1200


def bracket(x, y, dx, dy, c, arm=26, sw=2):
    return (f'<path d="M{x} {y+dy*arm} L{x} {y} L{x+dx*arm} {y}" fill="none" '
            f'stroke="{c}" stroke-width="{sw}" stroke-linecap="square"/>')


# ── banner ───────────────────────────────────────────────────────────────────
def banner(theme):
    t, H = THEMES[theme], 340
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
         f'height="{H}" role="img" aria-label="{escape(NAME)} — {escape(TAGLINE)}">',
         f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/>']

    M = 26
    for x, y, dx, dy in ((M, M, 1, 1), (W-M, M, -1, 1), (M, H-M, 1, -1), (W-M, H-M, -1, -1)):
        o.append(bracket(x, y, dx, dy, t["frame"]))

    rx, ry = 74, 84
    o.append(f'<circle cx="{rx}" cy="{ry}" r="11" fill="{SIGNAL}" opacity="0.14"/>')
    o.append(f'<circle cx="{rx}" cy="{ry}" r="5" fill="{SIGNAL}"/>')
    o.append(f'<path d="{path(ROLE, MONO_M, 12, rx+22, ry+4.5, 3.2)}" fill="{t["micro"]}"/>')

    pw = measure(PLACE, MONO, 12, 3.2)
    o.append(f'<path d="{path(PLACE, MONO, 12, W-74-pw, ry+4.5, 3.2)}" fill="{t["micro"]}"/>')

    o.append(f'<path d="{path(NAME, SG_BOLD, 68, 72, 186, -0.5)}" fill="{t["name"]}"/>')

    o.append(f'<path d="{path(TAGLINE, SG_MED, 24, 74, 228)}" fill="{t["tag"]}"/>')
    tw = measure(TAGLINE, SG_MED, 24)
    o.append(f'<path d="{path(".", SG_MED, 24, 74+tw, 228)}" fill="{SIGNAL}"/>')

    cx, cy = 72, 262
    for c in CHIPS:
        cw = measure(c, MONO, 12.5, 0.2) + 26
        o.append(f'<rect x="{cx:.1f}" y="{cy}" width="{cw:.1f}" height="26" rx="13" '
                 f'fill="{t["chip"]}" stroke="{t["chipline"]}"/>')
        o.append(f'<path d="{path(c, MONO, 12.5, cx+13, cy+17.5, 0.2)}" fill="{t["chiptext"]}"/>')
        cx += cw + 8

    bx = W - 74
    for i in range(9):
        o.append(f'<rect x="{bx-i*13:.0f}" y="{cy+6}" width="3" height="14" rx="1.5" '
                 f'fill="{SIGNAL if i == 3 else t["tick"]}"/>')

    o.append('</svg>')
    return "\n".join(o)


# ── stats ────────────────────────────────────────────────────────────────────
QUERY = """
{ user(login: "imswarnil") {
    followers { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false) {
      totalCount
      nodes { languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
        edges { size node { name color } } } }
    }
    contributionsCollection {
      totalCommitContributions
      contributionCalendar { totalContributions } } } }
"""


def _ssl_context():
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
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "imswarnil-profile"})
    with urllib.request.urlopen(req, timeout=30, context=_ssl_context()) as r:
        payload = json.load(r)
    return shape(payload)


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
    top = sorted(langs.items(), key=lambda kv: -kv[1][0])[:6]

    return dict(
        stats=[
            (f'{u["contributionsCollection"]["contributionCalendar"]["totalContributions"]:,}',
             "CONTRIBUTIONS · 1Y"),
            (f'{u["contributionsCollection"]["totalCommitContributions"]:,}', "COMMITS · 1Y"),
            (str(u["repositories"]["totalCount"]), "PUBLIC REPOS"),
            (str(u["followers"]["totalCount"]), "FOLLOWERS"),
        ],
        langs=[(n, v[0] / total * 100, v[1]) for n, v in top],
        stamped=datetime.datetime.now(datetime.timezone.utc).strftime("%d %b %Y").upper(),
    )


def stats_card(theme, data):
    t, H = THEMES[theme], 300
    L, R = 72, W - 72
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
         f'height="{H}" role="img" aria-label="GitHub activity for imswarnil">',
         f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/>']

    head = f'SNAPSHOT  ·  {data["stamped"]}'
    o.append(f'<path d="{path(head, MONO, 11, L, 44, 3)}" fill="{t["micro"]}"/>')
    tail = "GITHUB.COM/IMSWARNIL"
    o.append(f'<path d="{path(tail, MONO, 11, R-measure(tail, MONO, 11, 3), 44, 3)}" '
             f'fill="{t["micro"]}"/>')
    o.append(f'<rect x="{L}" y="60" width="{R-L}" height="1" fill="{t["rule"]}"/>')

    col = (R - L) / 4
    for i, (value, label) in enumerate(data["stats"]):
        x = L + i * col
        fill = SIGNAL if i == 0 else t["name"]
        o.append(f'<path d="{path(value, SG_BOLD, 46, x, 124, -0.5)}" fill="{fill}"/>')
        o.append(f'<path d="{path(label, MONO, 11, x+2, 150, 2.4)}" fill="{t["micro"]}"/>')

    o.append(f'<path d="{path("LANGUAGES BY VOLUME", MONO, 11, L, 202, 3)}" fill="{t["micro"]}"/>')

    bar_y, bar_h = 216, 10
    o.append(f'<clipPath id="bar"><rect x="{L}" y="{bar_y}" width="{R-L}" height="{bar_h}" '
             f'rx="{bar_h/2}"/></clipPath>')
    o.append(f'<rect x="{L}" y="{bar_y}" width="{R-L}" height="{bar_h}" rx="{bar_h/2}" '
             f'fill="{t["track"]}"/>')
    o.append(f'<g clip-path="url(#bar)">')
    x = float(L)
    for _, pct, color in data["langs"]:
        w = (R - L) * pct / 100
        o.append(f'<rect x="{x:.2f}" y="{bar_y}" width="{w:.2f}" height="{bar_h}" fill="{color}"/>')
        x += w
    o.append('</g>')

    x = float(L)
    for name, pct, color in data["langs"]:
        label = f"{name}  {pct:.0f}%"
        o.append(f'<circle cx="{x+4:.1f}" cy="{bar_y+44}" r="4" fill="{color}"/>')
        o.append(f'<path d="{path(label, MONO, 12, x+16, bar_y+48.5, 0.2)}" fill="{t["chiptext"]}"/>')
        x += measure(label, MONO, 12, 0.2) + 42

    o.append('</svg>')
    return "\n".join(o)


# ── skills ───────────────────────────────────────────────────────────────────
def skills_card(theme):
    """Chips wrapped into rows, one labelled group per band."""
    t = THEMES[theme]
    L, R, LABEL_W = 72, W - 72, 158
    CH, GAP, ROW = 28, 8, 36

    body, y = [], 58
    for i, (group, items) in enumerate(SKILLS):
        if i:
            y += 14
            body.append(f'<rect x="{L}" y="{y-24}" width="{R-L}" height="1" fill="{t["rule"]}"/>')

        row_top = y
        x = L + LABEL_W
        for item in items:
            cw = measure(item, MONO, 12.5, 0.2) + 26
            if x + cw > R:                      # wrap
                x, y = L + LABEL_W, y + ROW
            body.append(f'<rect x="{x:.1f}" y="{y}" width="{cw:.1f}" height="{CH}" rx="{CH/2}" '
                        f'fill="{t["chip"]}" stroke="{t["chipline"]}"/>')
            body.append(f'<path d="{path(item, MONO, 12.5, x+13, y+18.5, 0.2)}" '
                        f'fill="{t["chiptext"]}"/>')
            x += cw + GAP

        body.append(f'<path d="{path(group, MONO_M, 11, L, row_top + 18.5, 3)}" '
                    f'fill="{SIGNAL if i == 0 else t["micro"]}"/>')
        y += ROW

    H = y + 18
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
        f'height="{H}" role="img" aria-label="Skills">',
        f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/>',
        f'<path d="{path("SKILLS", MONO, 11, L, 32, 3)}" fill="{t["micro"]}"/>',
        *body, '</svg>'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true", help="also refresh the stats card")
    ap.add_argument("--from-json", metavar="PATH",
                    help="read the GraphQL response from a file, or '-' for stdin")
    args = ap.parse_args()

    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    for theme in ("dark", "light"):
        (out / f"header-{theme}.svg").write_text(banner(theme))
        (out / f"skills-{theme}.svg").write_text(skills_card(theme))
        print("wrote", out / f"header-{theme}.svg", "+ skills")

    if args.stats:
        data = fetch(args.from_json)
        for theme in ("dark", "light"):
            (out / f"stats-{theme}.svg").write_text(stats_card(theme, data))
            print("wrote", out / f"stats-{theme}.svg")


if __name__ == "__main__":
    main()
