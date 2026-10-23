# alfiochoa.github.io

Portfolio site of Alfredo Ochoa (AI automation and data integration): https://alfiochoa.github.io/

A static site: plain HTML, one CSS file and about 60 lines of JavaScript. No framework, no build service, no cookies,
no analytics and no third-party requests (the Inter typeface is self-hosted, under the SIL Open Font License).
It is hosted on GitHub Pages, so it never sleeps and costs nothing.

## What is here

| Path | What |
|---|---|
| `content.py` | All copy: projects, services, stats, limits. Every number comes from the project READMEs. |
| `build.py` | Generates `index.html`, `projects/<slug>/index.html`, `404.html`, `sitemap.xml`, `robots.txt` from `content.py`. |
| `assets/` | `site.css`, `site.js`, favicon, social preview image, fonts. |
| `media/` | Web versions of the project videos (silent, 720p), the intro and showreel, posters and screenshots. |
| `tools/make_media.py` | Rebuilds `media/` from the local 1080p motion-graphics sources (not stored here). |
| `tools/og.py` | Renders `assets/og.png`. |

## Edit and publish

```bash
python3 build.py          # regenerate the pages after editing content.py
python3 build.py --check  # what CI runs: output up to date, local links resolve, no third-party requests
python3 -m http.server    # preview at http://localhost:8000
git add -A && git commit -m "..." && git push   # GitHub Pages deploys from main
```

To show an Upwork, Fiverr or LinkedIn button in the contact section, put the profile URL in `SITE["links"]` in `content.py`
and rebuild. A button only appears for a non-empty URL.

## Honesty rules for the copy

All twelve projects are demos on synthetic or public data and are not client work. No client names, reviews or results appear
on the site. The market-data demos are reference or delayed data and not investment advice. Add a number only if it is in the
project's README.

Requires Python 3.10+ and Pillow (`pip install pillow`) for `build.py`.
