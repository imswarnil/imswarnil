# Vendored fonts

Committed so the SVG build is reproducible and offline — the render step turns text into
outlines, which needs the actual font files, not a webfont link.

Geist and Geist Mono are the faces [Frame & Signal](https://design.imswarnil.com) is set in
(`--im-font-sans`, `--im-font-mono`). The cards use the same ones, so the profile and the
system it is drawn in are the same page in the same voice.

| File | Family | Weight | Licence |
|---|---|---|---|
| `Geist-Regular.ttf` | Geist | 400 | SIL Open Font Licence 1.1 |
| `Geist-Medium.ttf` | Geist | 500 | SIL Open Font Licence 1.1 |
| `Geist-SemiBold.ttf` | Geist | 600 | SIL Open Font Licence 1.1 |
| `GeistMono-Regular.ttf` | Geist Mono | 400 | SIL Open Font Licence 1.1 |
| `GeistMono-Medium.ttf` | Geist Mono | 500 | SIL Open Font Licence 1.1 |

`Geist-OFL.txt` is the licence, copied unmodified from upstream.

## Why static weights

Upstream ships one variable file per family with a `wght` axis. A glyph that has been
converted to a `<path>` has no axis left to vary, and an SVG cannot synthesise a weight the
way a browser can, so each weight the cards use is instanced once and committed:

```
python3 -c "
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
for src, fam, ws in (('Geist-Variable.woff2', 'Geist', ((400,'Regular'),(500,'Medium'),(600,'SemiBold'))),
                     ('GeistMono-Variable.woff2', 'GeistMono', ((400,'Regular'),(500,'Medium')))):
    for wght, name in ws:
        f = instancer.instantiateVariableFont(TTFont(src), {'wght': wght}, updateFontNames=True)
        f.flavor = None
        f.save(f'{fam}-{name}.ttf')
"
```

Nothing is subset and nothing else is modified. Re-run it against a newer Geist release to
update them.
