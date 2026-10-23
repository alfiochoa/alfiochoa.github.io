#!/usr/bin/env python3
"""Static site generator for alfiochoa.github.io (standard library + Pillow only).

  python3 build.py           # write index.html, projects/*/index.html, 404.html, sitemap.xml, robots.txt
  python3 build.py --check   # CI: generated files must equal the committed ones, every local link/asset must exist,
                             # and the pages must make no third-party requests

All copy lives in content.py. Output is deterministic (no dates), so --check is a plain comparison.
"""
import html, json, re, sys, tempfile
from pathlib import Path
from PIL import Image
import content as C

ROOT = Path(__file__).resolve().parent
SITE = C.SITE
H = lambda s: html.escape(s, quote=True)

ICONS = {
    "bolt": "M13 3 L5 13.5 H11 L10 21 L19 10 H13 Z",
    "chat": "M4 5.5 H20 V16 H12 L7.5 20 V16 H4 Z",
    "db": "M4 6.5 C4 4.5 8 3.5 12 3.5 S20 4.5 20 6.5 V17.5 C20 19.5 16 20.5 12 20.5 S4 19.5 4 17.5 Z M4 12 C4 14 8 15 12 15 S20 14 20 12 M4 6.5 C4 8.5 8 9.5 12 9.5 S20 8.5 20 6.5",
    "merge": "M6 4 V9 C6 12 9 12 12 12 M18 4 V9 C18 12 15 12 12 12 V20 M9.5 17 L12 20 L14.5 17",
    "clock": "M12 3.5 A8.5 8.5 0 1 0 12 20.5 A8.5 8.5 0 1 0 12 3.5 M12 7.5 V12 L15 14",
    "code": "M8 7 L3.5 12 L8 17 M16 7 L20.5 12 L16 17 M13.5 5 L10.5 19",
    "shield": "M12 3 L19 6 V12 C19 16.5 15.5 19.5 12 21 C8.5 19.5 5 16.5 5 12 V6 Z M9 12 L11.2 14.2 L15.2 9.8",
    "replay": "M4.5 12 A7.5 7.5 0 1 0 7 6.5 M4.5 4 V8.5 H9",
    "bell": "M6 17 V11 A6 6 0 0 1 18 11 V17 L19.5 18.5 H4.5 Z M10 21 H14",
    "check": "M5 12.5 L10 17.5 L19 6.5",
    "arrow": "M5 12 H19 M13 6 L19 12 L13 18",
    "external": "M14 4 H20 V10 M20 4 L11 13 M18 14 V19 H5 V6 H10",
    "github": "M12 3.5 C7.3 3.5 3.5 7.3 3.5 12 C3.5 15.8 6 18.9 9.4 20 C9.8 20.1 10 19.8 10 19.5 V18 C7.7 18.5 7.2 16.9 7.2 16.9 C6.8 15.9 6.3 15.7 6.3 15.7 C5.5 15.2 6.4 15.2 6.4 15.2 C7.2 15.3 7.7 16 7.7 16 C8.4 17.3 9.6 16.9 10 16.7 C10.1 16.2 10.3 15.8 10.5 15.6 C8.7 15.4 6.8 14.7 6.8 11.6 C6.8 10.7 7.1 10 7.7 9.4 C7.6 9.2 7.3 8.4 7.7 7.3 C7.7 7.3 8.4 7.1 10 8.2 C10.7 8 11.3 7.9 12 7.9 C12.7 7.9 13.3 8 14 8.2 C15.6 7.1 16.3 7.3 16.3 7.3 C16.7 8.4 16.4 9.2 16.3 9.4 C16.9 10 17.2 10.7 17.2 11.6 C17.2 14.7 15.3 15.4 13.5 15.6 C13.8 15.9 14 16.3 14 17 V19.5 C14 19.8 14.2 20.1 14.6 20 C18 18.9 20.5 15.8 20.5 12 C20.5 7.3 16.7 3.5 12 3.5 Z",
    "sun": "M12 8 A4 4 0 1 0 12 16 A4 4 0 1 0 12 8 M12 2.5 V5 M12 19 V21.5 M2.5 12 H5 M19 12 H21.5 M5.3 5.3 L7 7 M17 17 L18.7 18.7 M5.3 18.7 L7 17 M17 7 L18.7 5.3",
    "moon": "M20 14.5 A8.5 8.5 0 1 1 9.5 4 A7 7 0 0 0 20 14.5 Z",
    "menu": "M4 7 H20 M4 12 H20 M4 17 H20",
    "play": "M8 5.5 L19 12 L8 18.5 Z",
}


def icon(name, cls=""):
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="{ICONS[name]}"/></svg>'


def project_by_slug(slug):
    return next(p for p in C.PROJECTS if p["slug"] == slug)


def img_size(path):
    with Image.open(ROOT / path) as im:
        return im.size


# ---------------------------------------------------------------- shared chrome
THEME_INIT = ("<script>(function(){try{var t=localStorage.getItem('theme');if(t==='light'||t==='dark')"
              "document.documentElement.setAttribute('data-theme',t)}catch(e){}document.documentElement.className+=' js'})()</script>")


def head(title, desc, path, og_image, jsonld, og_type="website"):
    url = SITE["url"].rstrip("/") + path
    og = SITE["url"].rstrip("/") + og_image
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False, separators=(",", ":"))}</script>' if jsonld else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{H(title)}</title>
<meta name="description" content="{H(desc)}">
<link rel="canonical" href="{url}">
<meta name="color-scheme" content="dark light">
<meta name="theme-color" content="#0b1020" media="(prefers-color-scheme: dark)">
<meta name="theme-color" content="#f5f7fc" media="(prefers-color-scheme: light)">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{H(SITE['name'])}">
<meta property="og:title" content="{H(title)}">
<meta property="og:description" content="{H(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/assets/fonts/inter-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/site.css">
{THEME_INIT}
{ld}
</head>
"""


BRAND_MARK = ('<svg viewBox="0 0 34 34" aria-hidden="true"><rect width="34" height="34" rx="9" style="fill:var(--card);stroke:var(--line-2)"/>'
              '<path d="M9 23 L17 11 L25 23" fill="none" style="stroke:var(--line-2)" stroke-width="1.6"/>'
              '<circle cx="9" cy="23" r="3.2" fill="#4f8cff"/><circle cx="17" cy="11" r="3.2" fill="#3ddc97"/><circle cx="25" cy="23" r="3.2" fill="#ffb454"/></svg>')

NAV = [("Work", "/#work"), ("Services", "/#services"), ("Approach", "/#approach"), ("About", "/#about")]


def header():
    links = "".join(f'<a href="{h}">{t}</a>' for t, h in NAV)
    mlinks = "".join(f'<a href="{h}">{t}</a>' for t, h in NAV + [("Contact", "/#contact")])
    return f"""<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
<div class="wrap bar">
<a class="brand" href="/" aria-label="{H(SITE['name'])}, home">{BRAND_MARK}<span>{H(SITE['name'])}</span></a>
<nav class="nav" aria-label="Main">{links}<a class="btn btn-primary nav-cta" href="/#contact">Contact</a></nav>
<div class="bar-right">
<button class="icon-btn" id="theme-toggle" type="button" aria-label="Switch colour theme">{icon('moon', 'icon-moon')}{icon('sun', 'icon-sun')}</button>
<details class="menu"><summary class="icon-btn" aria-label="Open menu">{icon('menu')}</summary><div class="menu-list">{mlinks}</div></details>
</div>
</div>
</header>
"""


def footer():
    gh = SITE["links"]["github"]
    li = f'<a href="{SITE["links"]["linkedin"]}">LinkedIn</a>' if SITE["links"].get("linkedin") else ""
    return f"""<footer>
<div class="wrap cols">
<div>
<p><strong>{H(SITE['name'])}</strong> &middot; AI automation and data integration &middot; &copy; {C.YEAR}</p>
<p>All projects are demos on synthetic or public data and are not client work. The finance and market-data demos use reference or delayed data, are not investment advice and have no trading features. Not affiliated with, endorsed by or sponsored by any data provider.</p>
<p>This site is static: no cookies, no analytics, no third-party requests. Typeface: Inter, under the SIL Open Font License.</p>
</div>
<div class="links">{li}<a href="{gh}">GitHub</a><a href="{C.REPO}">Source of this site</a><a href="#top">Back to top</a></div>
</div>
</footer>
<script src="/assets/site.js" defer></script>
</body>
</html>
"""


# ---------------------------------------------------------------- home
def flow_svg():
    def node(x, y, label, ic, cls="", icls=""):
        return (f'<g class="node {cls}"><rect x="{x}" y="{y}" width="104" height="64" rx="14"/>'
                f'<g transform="translate({x + 52 - 10} {y + 9}) scale(.84)"><path class="ico {icls}" d="{ICONS[ic]}"/></g>'
                f'<text x="{x + 52}" y="{y + 52}">{label}</text></g>')
    return f"""<svg class="flow-svg" viewBox="0 0 534 270" role="img" aria-label="Schematic: a record flows from a webhook through validation and a step. When the step fails, the record is retried and an alert is raised instead of the record disappearing.">
<path class="wire" d="M124 82 H150"/><path class="wire" d="M254 82 H280"/><path class="wire" d="M384 82 H410"/>
<path class="wire dash" d="M332 114 V190"/><path class="wire amber" d="M384 222 H410"/>
{node(20, 50, "Webhook", "bolt")}{node(150, 50, "Validate", "shield", icls="m")}{node(280, 50, "Step", "code", "on")}{node(410, 50, "Done", "check", icls="m")}
{node(280, 190, "Retry", "replay", "on", "a")}{node(410, 190, "Alert", "bell", "alert", "a")}
<circle class="packet" r="5" cx="0" cy="0"/><circle class="packet p2" r="5" cx="0" cy="0"/><circle class="packet p3" r="5" cx="0" cy="0"/>
<circle class="packet amber" r="5.5" cx="0" cy="0"/>
</svg>"""


def card(p):
    slug = p["slug"]
    stat_v, stat_l = p["stats"][0]
    flag = '<span class="badge flag">Flagship</span>' if p.get("flagship") else ""
    live = p["live"]
    return f"""<article class="card reveal{' flagship' if p.get('flagship') else ''}{' featured' if p.get('featured') else ''}" data-cat="{H(p['category'])}">
<a class="card-media" href="/projects/{slug}/" tabindex="-1" aria-hidden="true"><img src="/media/poster/{slug}.jpg" width="1280" height="720" loading="lazy" alt=""></a>
<div class="card-body">
<div class="badges">{flag}<span class="badge cat">{H(p['category'])}</span><span class="badge">{H(p['data_short'])}</span></div>
<h3><a href="/projects/{slug}/">{H(p['title'])}</a></h3>
<p>{H(p['short'])}</p>
<p class="keystat"><b>{H(stat_v)}</b> {H(stat_l)}</p>
<div class="card-links"><a href="{live[0]}">{H(live[1])}</a><a href="{p['code']}">Code on GitHub</a></div>
</div>
</article>"""


def contact_buttons():
    L, out = SITE["links"], []
    if L.get("upwork"): out.append(f'<a class="btn btn-primary" href="{L["upwork"]}">Hire me on Upwork</a>')
    if L.get("fiverr"): out.append(f'<a class="btn btn-primary" href="{L["fiverr"]}">See my Fiverr gigs</a>')
    if L.get("linkedin"): out.append(f'<a class="btn {"btn-ghost" if out else "btn-primary"}" href="{L["linkedin"]}">{"Message me on LinkedIn" if not out else "LinkedIn"}</a>')
    out.append(f'<a class="btn btn-ghost" href="{L["github"]}">{icon("github")}All the code on GitHub</a>')
    return "".join(out)


def index_page():
    ld = {"@context": "https://schema.org", "@type": "Person", "name": SITE["name"], "url": SITE["url"],
          "jobTitle": "AI automation and data integration freelancer", "knowsLanguage": ["es", "en"],
          "knowsAbout": ["n8n", "Workflow automation", "Python", "Data integration", "ETL", "PostgreSQL", "LLM tool calling", "Data reconciliation"],
          "sameAs": [u for u in SITE["links"].values() if u]}
    parts = [head(SITE["title"], SITE["description"], "/", "/assets/og.png", ld), '<body id="top">', header(), '<main id="main">']
    meta = "".join(f"<li>{H(m)}</li>" for m in SITE["meta"])
    parts.append(f"""<section class="hero" aria-labelledby="h1"><div class="wrap hero-grid">
<div>
<p class="kicker">AI automation &middot; Data integration</p>
<h1 class="display" id="h1">Automations that <em>don&rsquo;t fail quietly.</em></h1>
<p class="lede">{H(SITE['lede'])}</p>
<div class="cta-row"><a class="btn btn-primary" href="{SITE['links'].get('linkedin') or '#contact'}">Contact me on LinkedIn</a><a class="btn btn-ghost" href="#work">See my work</a></div>
<ul class="meta">{meta}</ul>
</div>
<figure class="flow-card">{flow_svg()}<figcaption>Schematic: one record fails at a step, is retried and raises an alert, instead of disappearing.</figcaption></figure>
</div></section>""")
    stats = "".join(f'<div class="stat reveal"><b>{H(v)}</b><span>{H(l)}</span></div>' for v, l in C.STATS)
    parts.append(f'<div class="wrap stats">{stats}</div>')

    vids = ""
    for key in ("intro", "showreel"):
        t, dur, desc = C.MEDIA[key]
        vids += f"""<div class="vcard reveal"><video controls preload="none" playsinline poster="/media/poster/{key}.jpg" aria-label="{H(t)}"><source src="/media/video/{key}.mp4" type="video/mp4"></video>
<div class="vbody"><h3>{H(t)} <span class="badge">{dur}</span></h3><p>{H(desc)}</p></div></div>"""
    parts.append(f"""<section id="watch" aria-labelledby="h-watch"><div class="wrap">
<div class="sec-head"><p class="kicker">Watch</p><h2 id="h-watch">Short on time? Start here.</h2><p>Two short videos: who I am, and what the projects do.</p></div>
<div class="videos">{vids}</div></div></section>""")

    svcs = ""
    for ic, t, d, slug in C.SERVICES:
        pr = project_by_slug(slug)
        svcs += f"""<article class="svc reveal"><div class="ic">{icon(ic)}</div><h3>{H(t)}</h3><p>{H(d)}</p>
<a class="more" href="/projects/{slug}/">Example: {H(pr['title'])}&nbsp;&rarr;</a></article>"""
    parts.append(f"""<section id="services" class="alt" aria-labelledby="h-svc"><div class="wrap">
<div class="sec-head"><p class="kicker">Services</p><h2 id="h-svc">What I build</h2><p>Integration first, AI second, and a test for every claim.</p></div>
<div class="grid-3">{svcs}</div></div></section>""")

    chips = '<button class="chip" type="button" data-filter="all" aria-pressed="true">All</button>' + "".join(
        f'<button class="chip" type="button" data-filter="{H(c)}" aria-pressed="false">{H(c)}</button>' for c in C.CATEGORIES)
    cards = "".join(card(p) for p in C.PROJECTS)
    parts.append(f"""<section id="work" aria-labelledby="h-work"><div class="wrap">
<div class="sec-head"><p class="kicker">Work</p><h2 id="h-work">Twelve demo projects, all open</h2><p>Each one has public code and tests, plus a live demo or a sample report. They run on synthetic or public data, so I can show them in full without exposing anyone&rsquo;s business.</p></div>
<div class="filters" role="group" aria-label="Filter projects">{chips}</div><p class="sr" id="filter-status" role="status" aria-live="polite"></p>
<div class="cards">{cards}</div></div></section>""")

    flow = "".join(f"<li><b>{H(t)}</b><span>{H(d)}</span></li>" for t, d in C.FLOW)
    prin = "".join(f'<div class="principle reveal"><h3>{H(t)}</h3><p>{H(d)}</p></div>' for t, d in C.PRINCIPLES)
    how = "".join(f"<li>{H(x)}</li>" for x in C.HOW_I_WORK)
    parts.append(f"""<section id="approach" class="alt" aria-labelledby="h-app"><div class="wrap">
<div class="sec-head"><p class="kicker">Approach</p><h2 id="h-app">From the problem to a verified result</h2><p>One chain, in this order. Skipping a step is how automations end up failing quietly.</p></div>
<ol class="flow">{flow}</ol><div class="principles">{prin}</div>
<div class="how reveal"><h3>How we would work together</h3><ul>{how}</ul></div></div></section>""")

    hon = "".join(f"<li>{H(x)}</li>" for x in C.HONEST)
    parts.append(f"""<section aria-labelledby="h-hon"><div class="wrap"><div class="honest reveal">
<div><p class="kicker">Read this first</p><h2 id="h-hon">What this portfolio is, and is not</h2><p class="lead">I would rather show you a transparent demo than make claims you cannot check.</p></div>
<ul>{hon}</ul></div></div></section>""")

    about = "".join(f"<p>{H(x)}</p>" for x in C.ABOUT)
    tools = "".join(f'<span class="tag">{H(t)}</span>' for t in C.TOOLS)
    parts.append(f"""<section id="about" class="alt" aria-labelledby="h-about"><div class="wrap about">
<div><p class="kicker">About</p><h2 id="h-about" style="font-size:clamp(1.8rem,3.4vw,2.6rem);margin-bottom:18px">Hi, I&rsquo;m Alfredo.</h2>{about}</div>
<aside class="facts reveal"><dl><div><dt>Experience</dt><dd>8 years in data automation and AI integration</dd></div><div><dt>Languages</dt><dd>Spanish (native), English (native-like)</dd></div>
<div><dt>Availability</dt><dd>About 30 hours a week, on Madrid time (CET/CEST)</dd></div></dl>
<div class="tags">{tools}</div></aside></div></section>""")

    parts.append(f"""<section id="contact" class="contact" aria-labelledby="h-contact"><div class="wrap">
<h2 id="h-contact">Tell me which process costs you the most time.</h2>
<p>If someone on your team exports a file, pastes it into a spreadsheet and checks it by eye, describe it to me. I will tell you plainly whether it can be automated and what it would take.</p>
<div class="cta-row">{contact_buttons()}</div></div></section>""")
    parts += ["</main>", footer()]
    return "\n".join(parts)


# ---------------------------------------------------------------- project pages
def project_page(i):
    p = C.PROJECTS[i]
    slug = p["slug"]
    ld = {"@context": "https://schema.org", "@type": "SoftwareSourceCode", "name": p["title"], "description": p["short"],
          "codeRepository": p["code"], "author": {"@type": "Person", "name": SITE["name"], "url": SITE["url"]}}
    desc = p["short"] + " Demo project by " + SITE["name"] + "."
    parts = [head(f"{p['title']} | {SITE['name']}", desc, f"/projects/{slug}/", f"/media/poster/{slug}.jpg", ld, "article"), '<body id="top">', header(), '<main id="main">']
    flag = '<span class="badge flag">Flagship</span>' if p.get("flagship") else ""
    parts.append(f"""<div class="wrap crumbs"><a href="/#work">Work</a> / {H(p['title'])}</div>
<section class="proj-hero" style="padding-bottom:32px"><div class="wrap">
<div class="badges">{flag}<span class="badge cat">{H(p['category'])}</span><span class="badge">{H(p['data'])}</span><span class="badge">{H(p['ai'])}</span></div>
<h1>{H(p['title'])}</h1><p class="lede">{H(p['short'])}</p>
<div class="cta-row"><a class="btn btn-primary" href="{p['live'][0]}">{H(p['live'][1])}</a><a class="btn btn-ghost" href="{p['code']}">{icon('github')}Code on GitHub</a></div>
<div class="proj-video"><video controls preload="none" playsinline poster="/media/poster/{slug}.jpg" aria-label="Walkthrough of {H(p['title'])}"><source src="/media/video/{slug}.mp4" type="video/mp4"></video></div>
<p class="vnote">A short silent walkthrough. The diagrams are schematic illustrations, labelled as such in the video.</p>
</div></section>""")

    does = "".join(f"<li>{H(x)}</li>" for x in p["does"])
    tiles = "".join(f"<div class='tile'><b>{H(v)}</b><span>{H(l)}</span></div>" for v, l in p["stats"])
    evid = ("<ul>" + "".join(f"<li>{H(x)}</li>" for x in p["evidence"]) + "</ul>") if p["evidence"] else ""
    caps = C.SHOTS.get(slug, [])
    shots = ""
    for n, cap in enumerate(caps, 1):
        w, h = img_size(f"media/img/{slug}-{n}.webp")
        shots += f'<figure><a href="/media/img/{slug}-{n}.webp"><img src="/media/img/{slug}-{n}.webp" width="{w}" height="{h}" loading="lazy" alt="{H(p["title"] + ": " + cap)}"></a><figcaption>{H(cap)}</figcaption></figure>'
    limits = "".join(f"<li>{H(x)}</li>" for x in p["limits"])
    stack = "".join(f'<span class="tag">{H(t)}</span>' for t in p["stack"])
    prev_p, next_p = C.PROJECTS[i - 1], C.PROJECTS[(i + 1) % len(C.PROJECTS)]
    parts.append(f"""<div class="wrap proj-layout">
<div class="proj-main">
<h2>The problem</h2><p>{H(p['problem'])}</p>
<h2>What it does</h2><ul>{does}</ul>
<h2>Evidence</h2><div class="tiles">{tiles}</div>{evid}
{('<h2>Screenshots</h2><div class="shots">' + shots + '</div>') if shots else ''}
<h2>Honest limits</h2><ul class="limits">{limits}</ul>
</div>
<aside class="aside">
<div class="panel"><h2>Try it</h2><a class="btn btn-primary" href="{p['live'][0]}">{H(p['live'][1])}</a><a class="btn btn-ghost" href="{p['code']}">{icon('github')}Code on GitHub</a>
<p class="vnote" style="margin:12px 0 0">Free hosting: a demo app can take about 30 seconds to wake on the first visit.</p></div>
<div class="panel"><h2>Built with</h2><div class="tags">{stack}</div></div>
<div class="panel"><h2>Details</h2><dl><div><dt>Data</dt><dd>{H(p['data'])}</dd></div><div><dt>AI</dt><dd>{H(p['ai'])}</dd></div><div><dt>Category</dt><dd>{H(p['category'])}</dd></div></dl></div>
</aside></div>
<div class="wrap"><nav class="pn" aria-label="Other projects"><a href="/projects/{prev_p['slug']}/"><small>&larr; Previous</small>{H(prev_p['title'])}</a><a href="/projects/{next_p['slug']}/"><small>Next &rarr;</small>{H(next_p['title'])}</a></nav></div>""")
    parts += ["</main>", footer()]
    return "\n".join(parts)


def not_found():
    return "\n".join([head("Page not found | " + SITE["name"], "This page does not exist.", "/404.html", "/assets/og.png", None), '<body id="top">', header(),
                      '<main id="main"><section><div class="wrap" style="text-align:center"><p class="kicker">404</p><h1 class="display" style="font-size:clamp(2rem,5vw,3.2rem)">That page is not here.</h1>'
                      '<p class="lede" style="margin-inline:auto">It may have moved. The work is one click away.</p><div class="cta-row" style="justify-content:center"><a class="btn btn-primary" href="/">Back to the portfolio</a></div></div></section></main>',
                      footer()])


def all_files():
    files = {"index.html": index_page(), "404.html": not_found()}
    for i, p in enumerate(C.PROJECTS):
        files[f"projects/{p['slug']}/index.html"] = project_page(i)
    base = SITE["url"].rstrip("/")
    urls = [base + "/"] + [f"{base}/projects/{p['slug']}/" for p in C.PROJECTS]
    files["sitemap.xml"] = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                            + "".join(f"<url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    files["robots.txt"] = f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n"
    return files


# ---------------------------------------------------------------- check
def check(files):
    problems = []
    for name, text in files.items():
        f = ROOT / name
        if not f.exists() or f.read_text() != text:
            problems.append(f"out of date: {name} (run python3 build.py)")
        if not name.endswith(".html"): continue
        if len(text.encode()) > 200_000: problems.append(f"{name} is over 200 KB")
        for m in re.finditer(r'<(\w+)\b[^>]*?\b(?:src|href)="([^"]+)"', text):
            tag, u = m.group(1), m.group(2)
            if u.startswith(("#", "mailto:")): continue
            if u.startswith("http"):
                if tag == "a" or (tag == "link" and 'rel="canonical"' in m.group(0)): continue   # outbound links and the canonical URL are fine
                problems.append(f"{name}: third-party resource <{tag}> {u}")
                continue
            path = u.split("#")[0]
            target = ROOT / path.lstrip("/")
            if path.endswith("/"): target = target / "index.html"
            if not target.exists(): problems.append(f"{name}: missing local file {u}")
    return problems


def main():
    files = all_files()
    if "--check" in sys.argv:
        bad = check(files)
        for b in bad: print("FAIL", b)
        print("site check:", "OK" if not bad else f"{len(bad)} problem(s)", f"({len(files)} generated files)")
        return 1 if bad else 0
    for name, text in files.items():
        f = ROOT / name
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)
    print(f"wrote {len(files)} files")
    bad = check(files)
    for b in bad: print("WARN", b)
    return 0


if __name__ == "__main__":
    sys.exit(main())
