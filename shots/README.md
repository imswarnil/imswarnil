# Project screenshots

Drop `<slug>.png` in here and that project's card uses it as its picture. The slug is
the first field of the project's row in [`scripts/content.py`](../scripts/content.py) —
`namaste.png`, `fands.png`, `crma.png` and so on. Nothing else to wire up: re-run
`python3 scripts/render.py` and the card picks it up.

With no file here the card falls back to the system's own no-image treatment — the
surface, a pattern from the utilities, and the title's initial — which is what
`im-thumb` does for a post with no feature image. That is a real state, not a
placeholder to be embarrassed about, so the page is finished either way.

## What to put in

The picture band is **2:1** (`--im-card-ratio`), drawn at 578×289, so a 1156×578 PNG
is the useful size — twice up, for the same reason any asset is. Anything else is
cropped to fill from the centre.

## Why PNGs and not a live capture

The card is an SVG and GitHub serves it through an image proxy, which will not fetch
anything: no webfont, no stylesheet, no external image. So the picture has to travel
inside the file, base64-encoded, and `scripts/render.py` inlines it at build time.
That also means a screenshot is not free — roughly a third more bytes than the PNG
itself, on top of a card that is currently ~50KB. Keep them compressed.
