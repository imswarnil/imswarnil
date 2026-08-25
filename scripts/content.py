"""Everything the cards say, in one place. Edit here, re-run scripts/render.py."""

NAME    = "SWARNIL SINGHAI"
TAGLINE = "I slap keyboard & talk to camera"
ROLE    = "SALESFORCE  ·  GTM ENGINEERING  ·  7 YEARS"
PLACE   = "BUDAPEST  ·  HUNGARY"
CHIPS   = ["Engineer", "YouTuber", "Creator", "Trailblazer"]

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
    ("WEB", ["JavaScript", "TypeScript", "Vue", "Next.js", "Handlebars", "Tailwind",
             "Sass", "Design Tokens"]),
    ("PLATFORM", ["Ghost", "Jekyll", "Supabase", "Postgres", "Vercel", "Cloudflare",
                  "GitHub Pages", "Git"]),
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
    ("nsds", "NS Design System",
     "One token set feeding both halves of it, Handlebars and React reading one source.",
     "Tokens · React", "building", "https://github.com/imswarnil/NSDS-Design-System"),
    ("ghosttheme", "Swarnil Ghost Theme",
     "A premium Ghost theme for independent creators, on a two-axis token architecture.",
     "Ghost 6 · gscan clean", "building", "https://github.com/imswarnil/Swarnil-Ghost-Theme"),
    ("sponsor", "Be My Sponsor",
     "Single-tenant ad platform — advertisers buy placements on the blog, videos and repos.",
     "Next.js · Supabase", "building", "https://github.com/imswarnil"),
    ("onboarding", "Invite-Only Onboarding",
     "A gated onboarding flow, built as a self-contained portal.",
     "HTML", "building", "https://github.com/imswarnil/Invite-Only-Onboarding-Portal"),
]

LIVE = [
    ("hub", "imswarnil.com",
     "The main desk — writing, videos, courses, projects and travel.",
     "Ghost 6 · self-hosted", "live", "https://imswarnil.com"),
    ("fands", "Frame & Signal",
     "Token-first, dependency-free CSS. Near-monochrome, so one colour can mean something.",
     "CSS · 144 doc pages", "live", "https://design.imswarnil.com"),
    ("crma", "CRM Analytics Academy",
     "A full CRMA curriculum — data prep, SAQL, dashboards, Einstein Discovery. Free forever.",
     "Vue · open source", "live", "https://crmanalytics.imswarnil.com"),
    ("trailblazer", "Trailblazer",
     "A Jekyll theme for Salesforce developers — lesson player, printable resume, cert wall.",
     "SCSS · MIT", "live", "https://trailblazer.imswarnil.com"),
    ("index", "The index",
     "A bento grid of everything. No CMS, no post pages. Linktree, built properly.",
     "Jekyll", "live", "https://imswarnil.github.io"),
    ("jobs", "Job Seekers Guide",
     "Notes and tooling for people job-hunting in the Salesforce ecosystem.",
     "Vue", "live", "https://jobseekers.imswarnil.com"),
    ("psk", "Passport Seva Kendra",
     "A public-service workflow, modelled properly on the platform.",
     "Apex", "live", "https://salesforce.imswarnil.com"),
    ("noai", "No AI Content",
     "A badge and a position, for people who still write it themselves.",
     "TypeScript", "live", "https://github.com/imswarnil/No-AI-Content"),
]
