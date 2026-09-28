"""Everything the cards say, in one place. Edit here, re-run scripts/render.py."""

NAME    = "SWARNIL SINGHAI"
TAGLINE = "I slap keyboard & talk to camera"
ROLE    = "SALESFORCE  ·  GTM ENGINEERING  ·  7 YEARS"
PLACE   = "BUDAPEST  ·  HUNGARY"
CHIPS   = ["Engineer", "YouTuber", "Creator", "Trailblazer"]

# The hero sets the last phrase of the tagline in Geist Pixel, the way the h1 on
# design.imswarnil.com does: one phrase, once. TAGLINE_HEAD + TAGLINE_PIXEL must
# reassemble into TAGLINE.
TAGLINE_HEAD  = "I slap keyboard &"
TAGLINE_PIXEL = "talk to camera."

# One paragraph under the headline. readme.py prints the same text as prose, so
# the card and the page cannot drift.
LEDE = ("Salesforce engineer, seven years deep in go-to-market: pipeline, funnel, CPQ, "
        "forecasting and product-usage data turned into dashboards people actually open. "
        "Off the clock I build one corner of the internet end to end: the site, the theme "
        "it runs on, the design system under the theme, and the courses on top.")

# The hero's right-hand card, the way the docs home puts art beside its copy.
NOW = ("Salesforce Engineer", "Education First", "Budapest, Hungary")

# The plain-text block under the pills. readme.py prints it verbatim.
NOW_LINES = [
    ("now",    "Salesforce Engineer @ Education First · Budapest, Hungary"),
    ("before", "Twilio · Cognizant · Accenture — GTM analytics, CRM Analytics, CPQ"),
    ("making", "Im Design System, CreatorKit, an OBS plugin, a Salesforce teaching platform"),
    ("rule",   "tokens are the source of truth; nothing ships with a dependency it didn't need"),
]

# The two the hero leads with; the full set stays in SOCIAL below.
CTA_PRIMARY = ("imswarnil.com", "https://imswarnil.com")
CTA_SECOND  = ("the index", "https://imswarnil.github.io")

# ── the bands of the page ────────────────────────────────────────────────────
# index, slug, title, CTA. Numbered because every band on design.imswarnil.com is;
# readme.py draws the head and the heading from this one list.
SECTIONS = [
    ("01", "building",   "CURRENTLY BUILDING", "github.com/imswarnil"),
    ("02", "live",       "LIVE",               "imswarnil.com"),
    ("03", "experience", "EXPERIENCE",         "in/imswarnil"),
    ("04", "skills",     "SKILLS",             ""),
    ("05", "numbers",    "THE NUMBERS",        ""),
]

# ── social ───────────────────────────────────────────────────────────────────
# slug, icon key, handle, url. Add a line, get a linked pill.
SOCIAL = [
    ("site",   "ghost",     "imswarnil.com",  "https://imswarnil.com",         True),
    ("x",      "x",         "@imswarnil",     "https://x.com/imswarnil",       False),
    ("github", "github",    "imswarnil",      "https://github.com/imswarnil",  False),
    ("linkedin",  "linkedin",  "in/imswarnil",   "https://www.linkedin.com/in/imswarnil/", False),
    ("instagram", "instagram", "@imswarnil",     "https://instagram.com/imswarnil", False),
    ("facebook",  "facebook",  "hashtag_swarnil", "https://facebook.com/hashtag_swarnil", False),
    ("email",  "mail",      "email",          "mailto:swarnilsinghaicse@gmail.com", False),
    ("index",  "grid",      "the index",      "https://imswarnil.github.io",   False),
]

# ── skills, GTM first ────────────────────────────────────────────────────────
SKILLS = [
    ("GTM", ["Quote-to-Cash", "CPQ", "Pipeline Management", "Forecasting",
             "Funnel Analytics", "Lead Velocity", "Cross-Sell", "Product Usage",
             "Sales Operations", "Revenue Ops", "AE Productivity", "Adoption"]),
    ("SALESFORCE", ["CRM Analytics", "SAQL", "Einstein Discovery", "Apex",
                    "Sales Cloud", "Service Cloud", "Data Modelling",
                    "Data Preparation", "Recipes & Dataflows", "Bindings",
                    "Automation", "Salesforce Admin"]),
    ("DATA", ["SQL", "Snowflake", "JSON", "Qlik Sense migration", "KPI Definition",
              "Dashboard Design", "Python"]),
    ("WEB", ["JavaScript", "TypeScript", "React", "Vue", "Next.js", "Handlebars",
             "Tailwind 4", "Sass", "Design Tokens", "C"]),
    ("PLATFORM", ["Ghost", "Jekyll", "Supabase", "Postgres", "Neon", "Vercel",
                  "Cloudflare Workers", "GitHub Pages", "OBS Studio", "Git"]),
]

# ── experience ───────────────────────────────────────────────────────────────
SUMMARY = ("Seven years turning raw pipeline, funnel, CPQ, product-usage and service data "
           "into decision-ready dashboards — used daily across the full go-to-market "
           "motion, from top-of-funnel through post-sale expansion.")

ROLES = [
    ("2026 —",    "Salesforce Engineer",         "Education First", "Budapest, Hungary", True),
    ("2022 – 26", "Salesforce GTM Engineer",     "Twilio",          "Bangalore, India",  False),
    ("2021 – 22", "CRM Analytics Consultant",    "Cognizant",       "Bangalore, India",  False),
    ("2018 – 21", "Salesforce Engineer",         "Accenture",       "Bangalore, India",  False),
]

HIGHLIGHTS = [
    "Owned GTM analytics for Twilio's Sales Operations team — the single CRM Analytics "
    "point of contact for AEs, Sales leadership, CPQ, product-usage and service data.",
    "Shipped Unified CPQ Insights — configuration and pricing in one view, prioritised "
    "and adopted team-wide.",
    "Built lead and funnel-velocity dashboards that exposed staged drop-off and stalled "
    "deals, and forecast/pipeline dashboards that replaced manual prep before forecast calls.",
    "Migrated Qlik Sense reporting to CRM Analytics at Education First without breaking "
    "continuity for Sales, Marketing and Customer Service.",
]

EDUCATION = "B.E. Computer Science  ·  LNCT Group of Colleges (RGPV), Bhopal  ·  2013 – 2017"

# ── projects ─────────────────────────────────────────────────────────────────
# slug, title, blurb, stack, status, url
BUILDING = [
    ("namaste", "Namaste Salesforce",
     "A Salesforce teaching platform — Ghost theme out front, Next.js LMS behind it.",
     "Handlebars · Next.js", "building", "https://github.com/imswarnil/Namaste-Salesforce"),
    ("creatorkit", "CreatorKit",
     "A React and Tailwind UI kit for people who publish. One recipe, two renderers.",
     "React · Tailwind · Turborepo", "building", "https://github.com/imswarnil/CreatorKit"),
    ("scratchpad", "Scratchpad",
     "A dev portfolio theme. One design, every stack: Jekyll now, then Astro, Hugo, Next.",
     "Jekyll · MIT", "building", "https://github.com/imswarnil/scratchpad-theme"),
    ("sponsor", "Be My Sponsor",
     "Brands buy placements, readers become members. Everything disclosed and priced openly.",
     "Next.js · Supabase", "building", "https://github.com/imswarnil/Sponsor-Me-Platform"),
]

LIVE = [
    ("hub", "imswarnil.com",
     "The main desk: writing, videos, courses, projects and travel. Self-hosted Ghost.",
     "Ghost 6 · Im Design System", "live", "https://imswarnil.com"),
    ("im", "Im Design System",
     "Tailwind 4 for Ghost themes, laid out on a twelve-column grid you can see.",
     "Tailwind 4 · Ghost 6 · Geist", "live", "https://design.imswarnil.com"),
    ("obs", "Swarnil Broadcast Kit",
     "A native OBS Studio plugin. Twenty sources, six filters and a 22-scene show.",
     "C · libobs · MIT", "live", "https://obs.imswarnil.com"),
    ("crma", "CRM Analytics Academy",
     "A full CRMA curriculum: data prep, SAQL, dashboards, Einstein Discovery. Free forever.",
     "Vue · open source", "live", "https://crmanalytics.imswarnil.com"),
    ("trailblazer", "Trailblazer",
     "A Jekyll theme for Salesforce developers: lesson player, printable resume, cert wall.",
     "SCSS · MIT", "live", "https://trailblazer.imswarnil.com"),
    ("icons", "Swarnil Icons",
     "61 icons on a 24 grid, drawn from scratch. No dependencies.",
     "SVG · MIT", "live", "https://icons.imswarnil.com"),
    ("index", "The index",
     "A bento of everything, every card live: YouTube, GitHub, Ghost, a guestbook.",
     "Next.js · Cloudflare Workers", "live", "https://imswarnil.github.io"),
    ("jobs", "Job Seekers Guide",
     "Notes and tooling for people job-hunting in the Salesforce ecosystem.",
     "Vue", "live", "https://jobseekers.imswarnil.com"),
    ("psk", "Passport Seva Kendra",
     "A public-service workflow, modelled properly on the platform.",
     "Apex", "live", "https://salesforce.imswarnil.com"),
    ("noai", "No AI Content",
     "A badge and a position, for people who still write it themselves.",
     "TypeScript · Vercel", "live", "https://nac.imswarnil.com"),
]
