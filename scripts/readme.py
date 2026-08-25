#!/usr/bin/env python3
"""Write README.md from scripts/content.py, so the page and the cards never drift.

Add a project to content.py, run scripts/render.py then this, and the tile, the link
and the grid cell all appear together.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import content as C


def picture(base, alt, width=None):
    w = f' width="{width}"' if width else ""
    return (f'<picture>'
            f'<source media="(prefers-color-scheme: dark)" srcset="assets/{base}-dark.svg">'
            f'<source media="(prefers-color-scheme: light)" srcset="assets/{base}-light.svg">'
            f'<img alt="{alt}" src="assets/{base}-light.svg"{w}>'
            f'</picture>')


def grid(projects):
    """Two columns of linked tiles. A table keeps the pair side by side on GitHub."""
    rows = []
    for i in range(0, len(projects), 2):
        cells = []
        for slug, title, blurb, _stack, _status, url in projects[i:i+2]:
            alt = f"{title} — {blurb}"
            cells.append(f'    <td width="50%">\n'
                         f'      <a href="{url}">{picture(f"proj-{slug}", alt, "100%")}</a>\n'
                         f'    </td>')
        if len(cells) == 1:
            cells.append('    <td width="50%"></td>')
        rows.append("  <tr>\n" + "\n".join(cells) + "\n  </tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def social():
    pills = [f'  <a href="{url}">{picture(f"social-{slug}", handle)}</a>'
             for slug, _icon, handle, url, _primary in C.SOCIAL]
    return "<p align=\"center\">\n" + "\n".join(pills) + "\n</p>"


def main():
    md = f"""<div align="center">
  <a href="https://imswarnil.com">{picture("header", f"{C.NAME} — {C.TAGLINE}", "100%")}</a>
</div>

{social()}

Salesforce engineer, seven years deep in go-to-market: pipeline, funnel, CPQ, forecasting
and product-usage data turned into dashboards people actually open. Off the clock I build
one corner of the internet end to end — the site, the theme it runs on, the design system
under the theme, and the courses on top.

```
now      Salesforce Engineer @ Education First · Budapest, Hungary
before   Twilio · Cognizant · Accenture — GTM analytics, CRM Analytics, CPQ
making   a Salesforce teaching platform, two design systems, a paid Ghost theme
rule     tokens are the source of truth; nothing ships with a dependency it didn't need
```

## Currently building

{grid(C.BUILDING)}

## Live

{grid(C.LIVE)}

## Experience

<div align="center">{picture("experience", "Experience — go-to-market engineering", "100%")}</div>

## Skills

<div align="center">{picture("skills", "Skills — GTM, Salesforce, data, web, platform", "100%")}</div>

## The numbers

<div align="center">{picture("stats", "GitHub activity for imswarnil", "100%")}</div>

<sub>Not a third-party widget. <a href="scripts/render.py"><code>scripts/render.py</code></a>
draws every card on this page from the GitHub API in
<a href="https://design.imswarnil.com">Frame &amp; Signal</a>, converting the type to
outlines so it renders the same everywhere. Same rule as the rest: no dependency it
didn't need.</sub>

## Sponsor

The Salesforce material — [CRM Analytics Academy](https://crmanalytics.imswarnil.com),
[Trailblazer](https://trailblazer.imswarnil.com),
[Job Seekers Guide](https://jobseekers.imswarnil.com) — is free and stays free.
If it saved you a week, you can pay for a week of it.

[![Sponsor](https://img.shields.io/badge/Sponsor-f04e2e?style=flat-square&logo=githubsponsors&logoColor=white)](https://github.com/sponsors/imswarnil)

---

<div align="center">
  <sub>
    <a href="https://imswarnil.com">imswarnil.com</a> ·
    <a href="https://imswarnil.github.io">the index</a> ·
    <a href="https://design.imswarnil.com">Frame &amp; Signal</a> ·
    <a href="https://x.com/imswarnil">@imswarnil</a>
  </sub>
</div>
"""
    (ROOT / "README.md").write_text(md)
    print("wrote README.md")


if __name__ == "__main__":
    main()
