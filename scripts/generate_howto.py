"""
SkyCore Solutions — How-To Article Generator
Generates one SEO-optimized, schema-marked how-to article per run.
Picks the next unwritten keyword from the priority list (highest volume first).

Requires env vars:
  GEMINI_API_KEY   — free at aistudio.google.com
  PEXELS_API_KEY   — free at pexels.com/api

Run:
  python scripts/generate_howto.py
"""

import os
import re
import json
import textwrap
import requests
import feedparser
from google import genai
from datetime import date

# ── Config ────────────────────────────────────────────────────────────────────

CLIENT         = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
GEMINI_MODEL   = "gemini-2.5-flash"
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

# Priority keyword list — ordered by opportunity score (volume / competition)
# Generator picks the first one not yet in how-to/posts.js
KEYWORD_QUEUE = [
    {"keyword": "disaster recovery plan for small business",  "category": "IT Strategy",          "volume": 2900},
    {"keyword": "IT disaster recovery guide",                 "category": "IT Strategy",          "volume": 1900},
    {"keyword": "zero trust network access implementation",   "category": "Security Hardening",   "volume": 1600},
    {"keyword": "ransomware protection for small business",   "category": "Security Hardening",   "volume": 1300},
    {"keyword": "GitHub Actions CI CD pipeline setup",        "category": "Infrastructure Revamp","volume": 880},
    {"keyword": "how to set up MFA for your organization",    "category": "Security Hardening",   "volume": 260},
    {"keyword": "how to implement zero trust security",       "category": "Security Hardening",   "volume": 210},
    {"keyword": "PIPEDA compliance IT checklist",             "category": "Security Hardening",   "volume": 170},
    {"keyword": "IT infrastructure modernization guide",      "category": "Infrastructure Revamp","volume": 170},
    {"keyword": "DMARC configuration step by step",          "category": "Security Hardening",   "volume": 140},
    {"keyword": "Office 365 MFA setup guide",                 "category": "Security Hardening",   "volume": 140},
    {"keyword": "Windows Server hardening checklist",         "category": "Security Hardening",   "volume": 110},
    {"keyword": "Azure MFA configuration guide",              "category": "Cloud Migration",      "volume": 90},
    {"keyword": "endpoint protection for small business",     "category": "Security Hardening",   "volume": 90},
    {"keyword": "cloud migration guide for SMB",              "category": "Cloud Migration",      "volume": 70},
    {"keyword": "Exchange to Office 365 migration guide",     "category": "Cloud Migration",      "volume": 70},
    {"keyword": "server hardening checklist",                 "category": "Security Hardening",   "volume": 70},
    {"keyword": "Docker containerization tutorial",           "category": "Infrastructure Revamp","volume": 70},
    {"keyword": "Active Directory tiering best practices",    "category": "Security Hardening",   "volume": 70},
    {"keyword": "how to configure DMARC DKIM SPF",            "category": "Security Hardening",   "volume": 40},
    {"keyword": "on premise to Azure migration guide",        "category": "Cloud Migration",      "volume": 40},
    {"keyword": "Office 365 migration step by step",          "category": "Cloud Migration",      "volume": 30},
    {"keyword": "Azure AD Connect setup guide",               "category": "Cloud Migration",      "volume": 30},
    {"keyword": "CI CD pipeline setup for small teams",       "category": "Infrastructure Revamp","volume": 30},
    {"keyword": "DevOps implementation for small business",   "category": "Infrastructure Revamp","volume": 10},
    {"keyword": "SQL Server to Azure migration guide",        "category": "Cloud Migration",      "volume": 10},
    {"keyword": "Azure backup setup guide",                   "category": "Cloud Migration",      "volume": 10},
    {"keyword": "physical server to Azure VM migration",      "category": "Cloud Migration",      "volume": 10},
    {"keyword": "how to harden Windows Server 2022",          "category": "Security Hardening",   "volume": 10},
    {"keyword": "Azure conditional access setup guide",       "category": "Security Hardening",   "volume": 10},
]

# Fallback Unsplash photos by category
FALLBACK_PHOTOS = {
    "Security Hardening":   "1550751827-4bd374c3f58b",
    "Cloud Migration":      "1451187580459-43490279c0fa",
    "Infrastructure Revamp":"1461749280684-dccba630e2f6",
    "IT Strategy":          "1558494949-ef010cbdcc31",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_written_keywords() -> set:
    """Return set of keywords already written (from how-to/posts.js slugs + titles)."""
    try:
        with open("how-to/posts.js", "r", encoding="utf-8") as f:
            content = f.read()
        return set(re.findall(r'keyword:\s*"([^"]+)"', content))
    except Exception:
        return set()


def get_used_image_urls() -> set:
    """Return all image URLs already in how-to/posts.js."""
    try:
        with open("how-to/posts.js", "r", encoding="utf-8") as f:
            content = f.read()
        return set(re.findall(r'image:\s*"([^"]+)"', content))
    except Exception:
        return set()


def pick_next_keyword() -> dict | None:
    """Return the highest-priority keyword not yet written."""
    written = get_written_keywords()
    for item in KEYWORD_QUEUE:
        if item["keyword"] not in written:
            return item
    return None


def pick_photo_pexels(query: str, used_urls: set) -> tuple[str, str] | tuple[None, None]:
    if not PEXELS_API_KEY:
        return None, None
    queries = [query, query.split()[0] + " technology", "IT technology"]
    for q in queries:
        try:
            resp = requests.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": PEXELS_API_KEY},
                params={"query": q, "per_page": 20, "orientation": "landscape"},
                timeout=10,
            )
            resp.raise_for_status()
            for photo in resp.json().get("photos", []):
                hero  = photo["src"]["original"] + "?auto=compress&cs=tinysrgb&w=1400&fit=crop&h=600"
                thumb = photo["src"]["original"] + "?auto=compress&cs=tinysrgb&w=800&fit=crop&h=450"
                if thumb not in used_urls:
                    print(f"   ✓ Pexels photo #{photo['id']}")
                    return hero, thumb
        except Exception as e:
            print(f"   Pexels error: {e}")
    return None, None


def pick_photo(image_query: str, category: str) -> tuple[str, str]:
    used = get_used_image_urls()
    hero, thumb = pick_photo_pexels(image_query, used)
    if hero:
        return hero, thumb
    # Fallback to Unsplash
    pid   = FALLBACK_PHOTOS.get(category, "1558494949-ef010cbdcc31")
    hero  = f"https://images.unsplash.com/photo-{pid}?w=1400&auto=format&fit=crop&q=80"
    thumb = f"https://images.unsplash.com/photo-{pid}?w=800&auto=format&fit=crop&q=80"
    print(f"   ✓ Unsplash fallback: {pid}")
    return hero, thumb


def generate_article(kw_item: dict) -> dict:
    keyword  = kw_item["keyword"]
    category = kw_item["category"]
    today    = date.today().isoformat()

    prompt = textwrap.dedent(f"""
        You are a senior IT consultant writing for SkyCore Solutions, a global IT consulting firm.
        Services: Cloud Migration (Azure), Security Hardening (NIST/CIS/Zero Trust), Infrastructure Revamp (DevOps/CI-CD).

        Write a comprehensive, authoritative how-to guide targeting this keyword:
        PRIMARY KEYWORD: "{keyword}"
        CATEGORY: {category}

        REQUIREMENTS:
        - 1,500–2,500 words
        - Genuinely useful — real commands, real configurations, real pitfalls
        - Written for IT managers and sysadmins at small/medium businesses globally
        - 5–8 numbered steps (each step is a concrete action, not vague advice)
        - Include actual CLI commands, PowerShell, or config snippets where relevant (in <pre><code> blocks)
        - Cite at least one real standard, tool, or vendor (Microsoft docs, NIST, CIS, etc.)
        - End with a "When to bring in a consultant" section (soft CTA — honest, not salesy)
        - Tone: expert peer helping a colleague, not a vendor pitch

        STRUCTURE the HTML with:
        - <div class="post-meta">DATE · READTIME · CATEGORY</div>
        - <h1>TITLE</h1>
        - <div class="article-hero"><img src="HERO_IMAGE_PLACEHOLDER" alt="HERO_ALT_PLACEHOLDER" loading="eager" fetchpriority="high"></div>
        - <div class="howto-intro"><p>intro paragraph with keyword</p></div>
        - <div class="howto-prereqs"><h2>Prerequisites</h2><ul>...</ul></div>
        - Steps as <h2>Step N: [Action verb + what]</h2> followed by <p> and <pre><code> blocks
        - <div class="howto-consultant-cta"><h2>When to bring in a consultant</h2><p>...</p><a href="../contact.html" class="btn btn-primary">Book a free consultation</a></div>

        Return ONLY valid JSON (no markdown fences) with these exact fields:
        {{
          "slug": "seo-url-slug-4-6-words",
          "title": "Full compelling title (include primary keyword naturally)",
          "metaDescription": "145-155 char meta description with keyword",
          "date": "{today}",
          "readTime": "X min read",
          "category": "{category}",
          "difficulty": "Beginner|Intermediate|Advanced",
          "timeEstimate": "e.g. 45 minutes or 2-3 hours",
          "keyword": "{keyword}",
          "excerpt": "2-sentence excerpt under 160 chars",
          "imageQuery": "3-4 word Pexels search query relevant to topic",
          "imageAlt": "Descriptive alt text under 125 chars with keyword",
          "prerequisites": ["item 1", "item 2", "item 3"],
          "steps": [
            {{"name": "Step name", "text": "One sentence describing what this step accomplishes"}}
          ],
          "htmlContent": "Full article HTML as described above. Replace HERO_IMAGE_PLACEHOLDER and HERO_ALT_PLACEHOLDER."
        }}
    """).strip()

    for attempt in range(1, 4):
        try:
            response = CLIENT.models.generate_content(model=GEMINI_MODEL, contents=prompt)
            raw = response.text.strip()
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
            match = re.search(r"\{[\s\S]*\}", raw)
            if match:
                raw = match.group(0)
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"   Attempt {attempt} failed: {e}")
            if attempt == 3:
                raise RuntimeError(f"Gemini returned invalid JSON after 3 attempts: {e}")
            prompt += "\n\nCRITICAL: JSON parse error. Escape ALL double quotes inside strings as \\\" — especially in htmlContent."


def build_html(article: dict, hero_url: str) -> str:
    image_alt = article.get("imageAlt", article.get("imageQuery", "IT infrastructure"))
    content = (
        article["htmlContent"]
        .replace("HERO_IMAGE_PLACEHOLDER", hero_url)
        .replace("HERO_ALT_PLACEHOLDER", image_alt)
    )
    thumb_url     = hero_url.replace("w=1400", "w=1200").replace("h=600", "h=630")
    canonical_url = f"https://skycoresolutions.com/how-to/{article['slug']}.html"

    # Build HowTo schema JSON-LD
    steps_schema = json.dumps([
        {"@type": "HowToStep", "name": s["name"], "text": s["text"]}
        for s in article.get("steps", [])
    ], indent=4)

    prereqs_schema = ", ".join(article.get("prerequisites", []))

    howto_schema = f"""{{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "{article['title'].replace('"', '\\"')}",
  "description": "{article['metaDescription'].replace('"', '\\"')}",
  "totalTime": "PT1H",
  "supply": [{{"@type": "HowToSupply", "name": "{prereqs_schema}"}}],
  "step": {steps_schema}
}}"""

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{article['title']} — SkyCore Solutions</title>
  <meta name="description" content="{article['metaDescription']}" />
  <meta name="theme-color" content="#000000" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../assets/css/style.css" />
  <link rel="stylesheet" href="https://asset-tidycal.b-cdn.net/css/embed.css" />
  <!-- SEO: Open Graph + Canonical -->
  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="SkyCore Solutions" />
  <meta property="og:title" content="{article['title']} — SkyCore Solutions" />
  <meta property="og:description" content="{article['metaDescription']}" />
  <meta property="og:url" content="{canonical_url}" />
  <meta property="og:image" content="{thumb_url}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{article['title']} — SkyCore Solutions" />
  <meta name="twitter:description" content="{article['metaDescription']}" />
  <meta name="twitter:image" content="{thumb_url}" />
  <link rel="canonical" href="{canonical_url}" />
  <meta property="article:published_time" content="{article['date']}" />
  <!-- HowTo Schema — enables Google rich snippets with numbered steps -->
  <script type="application/ld+json">
  {howto_schema}
  </script>
</head>
<body>
  <header class="nav">
    <div class="nav-inner">
      <a href="../" class="logo"><img class="logo-svg" src="../assets/images/logo.png" alt="SkyCore logo" /><span><span class="sky">SKY</span><span class="core">CORE</span> <span class="inc">SOLUTIONS</span></span></a>
      <nav class="nav-links">
        <a href="../">Home</a>
        <a href="../services.html">Services</a>
        <a href="../about.html">About</a>
        <a href="../blog/">Blog</a>
        <a href="./">Resources</a>
        <a href="../contact.html">Contact</a>
        <a href="#" class="btn btn-primary" style="padding:10px 18px;" data-tidycal-popup="mnkpzxm/30-minute-meeting">Free Consultation</a>
      </nav>
      <button class="nav-burger" aria-label="Menu"><span></span><span></span><span></span></button>
    </div>
  </header>

  <article class="article howto-article">
    {content}
  </article>

  <footer class="footer">
    <div class="container">
      <div class="footer-grid">
        <div><a href="../" class="logo"><img class="logo-svg" src="../assets/images/logo.png" alt="SkyCore logo" /><span><span class="sky">SKY</span><span class="core">CORE</span> <span class="inc">SOLUTIONS</span></span></a><p style="margin-top:14px;max-width:320px;">Transforming IT infrastructure with innovation and expertise.</p><p style="margin-top:8px;color:var(--text-3);font-size:0.9rem;">Montreal, Quebec, Canada</p></div>
        <div><h4>Services</h4><ul><li><a href="../services.html#cloud">Cloud Migration</a></li><li><a href="../services.html#security">Security Hardening</a></li><li><a href="../services.html#infra">Infrastructure Revamp</a></li></ul></div>
        <div><h4>Resources</h4><ul><li><a href="../blog/">Blog</a></li><li><a href="./">How-To Guides</a></li><li><a href="../contact.html">Contact</a></li></ul></div>
        <div><h4>Contact</h4><ul><li><a href="mailto:info@skycoresolutions.com">info@skycoresolutions.com</a></li><li><a href="tel:+15145009562">(514) 500-9562</a></li><li style="color:var(--text-3);font-size:0.9rem;">Mon–Fri: 9AM–6PM EST</li><li style="color:var(--text-3);font-size:0.9rem;">24/7 Emergency Support</li></ul></div>
      </div>
      <div class="footer-bottom"><span>&copy; <span id="year">2026</span> SkyCore Solutions Inc. All rights reserved.</span><span>SkyCore Solutions Inc. is a registered trademark.</span></div>
    </div>
  </footer>
  <script>document.getElementById("year").textContent = new Date().getFullYear();</script>
  <script src="../assets/js/main.js"></script>
  <script src="https://asset-tidycal.b-cdn.net/js/embed.js"></script>
</body>
</html>"""


def prepend_to_posts_js(article: dict, thumb_url: str):
    posts_path = "how-to/posts.js"
    with open(posts_path, "r", encoding="utf-8") as f:
        content = f.read()

    title   = article["title"].replace("\\", "\\\\").replace('"', '\\"')
    excerpt = article["excerpt"].replace("\\", "\\\\").replace('"', '\\"')
    keyword = article["keyword"].replace('"', '\\"')

    new_entry = (
        f'  {{\n'
        f'    slug: "{article["slug"]}",\n'
        f'    title: "{title}",\n'
        f'    date: "{article["date"]}",\n'
        f'    readTime: "{article["readTime"]}",\n'
        f'    category: "{article["category"]}",\n'
        f'    difficulty: "{article.get("difficulty", "Intermediate")}",\n'
        f'    timeEstimate: "{article.get("timeEstimate", "45 min")}",\n'
        f'    keyword: "{keyword}",\n'
        f'    excerpt: "{excerpt}",\n'
        f'    image: "{thumb_url}"\n'
        f'  }},\n'
    )

    content = content.replace(
        "window.SKYCORE_HOWTO = [\n",
        f"window.SKYCORE_HOWTO = [\n{new_entry}"
    )

    with open(posts_path, "w", encoding="utf-8") as f:
        f.write(content)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    kw_item = pick_next_keyword()
    if not kw_item:
        print("✓ All keywords in the queue have been written. Add more to KEYWORD_QUEUE.")
        return

    print(f"── Next keyword: \"{kw_item['keyword']}\" (volume: {kw_item['volume']:,}/mo) ──")
    print(f"   Category: {kw_item['category']}")

    print("── Generating article via Gemini 2.5 Flash ──")
    article = generate_article(kw_item)
    print(f"   Slug:       {article['slug']}")
    print(f"   Title:      {article['title']}")
    print(f"   Difficulty: {article.get('difficulty')} | Time: {article.get('timeEstimate')}")
    print(f"   Steps:      {len(article.get('steps', []))}")

    hero_url, thumb_url = pick_photo(article.get("imageQuery", kw_item["keyword"]), kw_item["category"])
    print(f"   Image:      {hero_url[:80]}...")

    html_path = f"how-to/{article['slug']}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(build_html(article, hero_url))
    print(f"── Written: {html_path} ──")

    prepend_to_posts_js(article, thumb_url)
    print("── how-to/posts.js updated ──")

    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from update_sitemap import regenerate as regen_sitemap
    regen_sitemap()

    print("Done ✓")


if __name__ == "__main__":
    main()
