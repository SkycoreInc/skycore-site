"""
SkyCore — Sitemap updater utility.
Called by generate_blog.py and generate_howto.py after each new post.
Reads both posts.js manifests and regenerates sitemap.xml from scratch.
"""

import re
from datetime import date

SITE_ROOT = "https://skycoresolutions.com"
SITEMAP_PATH = "sitemap.xml"
BLOG_POSTS_JS = "blog/posts.js"
HOWTO_POSTS_JS = "how-to/posts.js"


def parse_posts_js(path: str) -> list[dict]:
    """Extract slug + date entries from a posts.js manifest."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return []

    entries = []
    # Match each object block between { ... }
    for block in re.findall(r'\{[^{}]+\}', content, re.DOTALL):
        slug  = re.search(r'slug\s*:\s*["\']([^"\']+)["\']', block)
        ddate = re.search(r'date\s*:\s*["\']([^"\']+)["\']', block)
        if slug and ddate:
            entries.append({"slug": slug.group(1), "date": ddate.group(1)})
    return entries


def build_url(loc: str, lastmod: str, changefreq: str, priority: str) -> str:
    return (
        f"  <url>\n"
        f"    <loc>{loc}</loc>\n"
        f"    <lastmod>{lastmod}</lastmod>\n"
        f"    <changefreq>{changefreq}</changefreq>\n"
        f"    <priority>{priority}</priority>\n"
        f"  </url>"
    )


def regenerate():
    today = date.today().isoformat()

    # ── Static core pages ─────────────────────────────────────────────────────
    urls = [
        build_url(f"{SITE_ROOT}/",              today,  "weekly",  "1.0"),
        build_url(f"{SITE_ROOT}/services.html", today,  "monthly", "0.9"),
        build_url(f"{SITE_ROOT}/about.html",    today,  "monthly", "0.8"),
        build_url(f"{SITE_ROOT}/contact.html",  today,  "monthly", "0.8"),
    ]

    # ── Blog hub ──────────────────────────────────────────────────────────────
    urls.append(build_url(f"{SITE_ROOT}/blog/", today, "daily", "0.9"))

    # ── Blog posts (deduplicated by slug, keep newest date) ───────────────────
    blog_posts = parse_posts_js(BLOG_POSTS_JS)
    seen_slugs: dict[str, str] = {}
    for p in blog_posts:
        slug, d = p["slug"], p["date"]
        if slug not in seen_slugs or d > seen_slugs[slug]:
            seen_slugs[slug] = d
    for slug, d in seen_slugs.items():
        urls.append(build_url(
            f"{SITE_ROOT}/blog/{slug}.html", d, "monthly", "0.7"
        ))

    # ── How-To hub ────────────────────────────────────────────────────────────
    urls.append(build_url(f"{SITE_ROOT}/how-to/", today, "daily", "0.9"))

    # ── How-To articles ───────────────────────────────────────────────────────
    howto_posts = parse_posts_js(HOWTO_POSTS_JS)
    seen_howto: dict[str, str] = {}
    for p in howto_posts:
        slug, d = p["slug"], p["date"]
        if slug not in seen_howto or d > seen_howto[slug]:
            seen_howto[slug] = d
    for slug, d in seen_howto.items():
        urls.append(build_url(
            f"{SITE_ROOT}/how-to/{slug}.html", d, "monthly", "0.8"
        ))

    # ── Write sitemap.xml ─────────────────────────────────────────────────────
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n\n'
        + "\n".join(urls)
        + "\n\n</urlset>\n"
    )
    with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
        f.write(xml)

    total = len(seen_slugs) + len(seen_howto) + 5  # posts + core pages
    print(f"sitemap.xml updated -- {total} URLs written OK")


if __name__ == "__main__":
    regenerate()
