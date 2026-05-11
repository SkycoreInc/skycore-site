"""
SkyCore Solutions — Automated Blog Generator
Runs via GitHub Actions every 2 days.
Requires: GEMINI_API_KEY environment variable (free at aistudio.google.com).
"""

import os
import re
import json
import textwrap
import feedparser
from google import genai
from datetime import date

# ── Config ────────────────────────────────────────────────────────────────────

CLIENT = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
GEMINI_MODEL = "gemini-2.5-flash"   # free-tier model

RSS_FEEDS = [
    "https://feeds.feedburner.com/TheHackersNews",
    "https://www.bleepingcomputer.com/feed/",
    "https://krebsonsecurity.com/feed/",
    "https://techcrunch.com/feed/",
    "https://www.zdnet.com/news/rss.xml",
    "https://azure.microsoft.com/en-us/blog/feed/",
]

# Curated Unsplash photo IDs by topic keyword
PHOTO_MAP = {
    "ransomware":        "1526374965328-7f61d4dc18c5",
    "phishing":          "1526374965328-7f61d4dc18c5",
    "malware":           "1526374965328-7f61d4dc18c5",
    "security":          "1550751827-4bd374c3f58b",
    "zero trust":        "1550751827-4bd374c3f58b",
    "hardening":         "1563986768609-322da13575f3",
    "vulnerability":     "1563986768609-322da13575f3",
    "breach":            "1504384308090-c894fdcc538d",
    "compliance":        "1504384308090-c894fdcc538d",
    "endpoint":          "1550751827-4bd374c3f58b",
    "cloud":             "1451187580459-43490279c0fa",
    "azure":             "1451187580459-43490279c0fa",
    "cost":              "1451187580459-43490279c0fa",
    "migration":         "1451187580459-43490279c0fa",
    "backup":            "1544197150-b99a580bb7a8",
    "data":              "1544197150-b99a580bb7a8",
    "microsoft 365":     "1544197150-b99a580bb7a8",
    "server":            "1558494949-ef010cbdcc31",
    "infrastructure":    "1558494949-ef010cbdcc31",
    "technical debt":    "1558494949-ef010cbdcc31",
    "network":           "1558618666-fcd25c85cd64",
    "firewall":          "1558618666-fcd25c85cd64",
    "devops":            "1461749280684-dccba630e2f6",
    "code":              "1461749280684-dccba630e2f6",
    "modernization":     "1461749280684-dccba630e2f6",
}
DEFAULT_PHOTO = "1558494949-ef010cbdcc31"

# ── Helpers ───────────────────────────────────────────────────────────────────

def fetch_news() -> list[str]:
    articles = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:4]:
                title   = entry.get("title", "").strip()
                summary = re.sub(r"<[^>]+>", "", entry.get("summary", ""))[:280].strip()
                source  = feed.feed.get("title", url)
                if title:
                    articles.append(f"[{source}] {title}: {summary}")
        except Exception as e:
            print(f"Feed error ({url}): {e}")
    return articles[:20]


def pick_photo(image_query: str) -> tuple[str, str]:
    q = image_query.lower()
    photo_id = DEFAULT_PHOTO
    for keyword, pid in PHOTO_MAP.items():
        if keyword in q:
            photo_id = pid
            break
    hero  = f"https://images.unsplash.com/photo-{photo_id}?w=1400&auto=format&fit=crop&q=80"
    thumb = f"https://images.unsplash.com/photo-{photo_id}?w=800&auto=format&fit=crop&q=80"
    return hero, thumb


def generate_post(news_items: list[str]) -> dict:
    news_block = "\n".join(f"• {item}" for item in news_items)
    today = date.today().isoformat()

    prompt = textwrap.dedent(f"""
        You are the content writer for SkyCore Solutions, a Montreal-based IT consulting firm.
        Services offered:
          1. Cloud Migration — Azure and hybrid architectures
          2. Security Hardening — NIST, CIS Controls, zero-trust, compliance
          3. Infrastructure Revamp — DevOps, CI/CD, containerization, legacy modernization

        RECENT IT NEWS (use at least one real event as the article hook):
        {news_block}

        TOP SEO KEYWORDS TO WEAVE IN NATURALLY (pick 4-6 most relevant):
        "managed IT services Montreal", "cloud migration Azure", "IT infrastructure Montreal",
        "cybersecurity SMB", "zero trust security", "ransomware protection SMB",
        "Microsoft 365 security", "cloud cost optimization", "IT consulting Montreal",
        "infrastructure modernization", "DevOps implementation", "hybrid cloud strategy",
        "IT compliance Canada", "network security audit", "business continuity IT",
        "endpoint security", "patch management", "disaster recovery plan"

        Write a 750-900 word authoritative blog post that:
        - Opens with a compelling real stat or news hook from the headlines above
        - Provides specific, actionable technical advice (not vague generalities)
        - Ties directly to ONE of SkyCore's three services
        - Naturally incorporates 4-6 of the SEO keywords above
        - Uses clear H2 and H3 subheadings
        - Cites at least one real source (report, vendor, CVE, research firm)
        - Ends with an article-cta block

        Return ONLY valid JSON (no markdown code fences, no extra text) with these exact fields:
        {{
          "slug": "seo-url-slug-4-6-words",
          "title": "Full compelling title with primary keyword",
          "metaDescription": "145-155 char meta description with keyword",
          "date": "{today}",
          "readTime": "X min read",
          "category": "Security Hardening|Cloud Migration|Infrastructure Revamp|IT Strategy",
          "excerpt": "2-sentence blog card excerpt under 160 chars",
          "imageQuery": "3-word topic for photo (e.g. ransomware attack, azure cloud, server infrastructure)",
          "imageAlt": "Descriptive alt text for the hero image (under 125 chars, includes primary keyword)",
          "htmlContent": "Full article body HTML. Start with: <div class=\\"post-meta\\">DATE · READTIME · CATEGORY</div><h1>TITLE</h1><div class=\\"article-hero\\"><img src=\\"HERO_IMAGE_PLACEHOLDER\\" alt=\\"HERO_ALT_PLACEHOLDER\\" loading=\\"eager\\" fetchpriority=\\"high\\"></div> then article paragraphs/headings using <p> <h2> <h3> <ul> <li> <strong> <a>. End with: <div class=\\"article-cta\\"><h3 style=\\"margin-bottom:10px;\\">CTA_HEADING</h3><p style=\\"margin-bottom:20px;\\">CTA_TEXT</p><a href=\\"../contact.html\\" class=\\"btn btn-primary\\">Book a free consultation</a></div>"
        }}
    """).strip()

    for attempt in range(1, 4):
        try:
            response = CLIENT.models.generate_content(model=GEMINI_MODEL, contents=prompt)
            raw = response.text.strip()

            # Strip accidental markdown fences
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)

            # Extract the outermost JSON object in case there's leading/trailing text
            match = re.search(r"\{[\s\S]*\}", raw)
            if match:
                raw = match.group(0)

            return json.loads(raw)

        except (json.JSONDecodeError, ValueError) as e:
            print(f"   Attempt {attempt} failed: {e}")
            if attempt == 3:
                raise RuntimeError(f"Gemini returned invalid JSON after 3 attempts. Last error: {e}\n\nRaw response:\n{raw[:500]}")
            print("   Retrying with stricter prompt...")
            prompt += "\n\nCRITICAL: Your previous response had a JSON parse error. Ensure ALL double quotes inside string values are escaped as \\\" and there are NO unescaped special characters in htmlContent."


def build_html(post: dict, hero_url: str) -> str:
    image_alt = post.get("imageAlt", post.get("imageQuery", "IT infrastructure"))
    content = post["htmlContent"].replace("HERO_IMAGE_PLACEHOLDER", hero_url).replace("HERO_ALT_PLACEHOLDER", image_alt)
    thumb_url = hero_url.replace("w=1400", "w=1200")
    canonical_url = f"https://skycoresolutions.com/blog/{post['slug']}.html"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{post['title']} — SkyCore Solutions</title>
  <meta name="description" content="{post['metaDescription']}" />
  <meta name="theme-color" content="#000000" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../assets/css/style.css" />
  <link rel="stylesheet" href="https://asset-tidycal.b-cdn.net/css/embed.css" />
  <!-- SEO: Open Graph + Canonical -->
  <meta property="og:type" content="article" />
  <meta property="og:site_name" content="SkyCore Solutions" />
  <meta property="og:title" content="{post['title']} — SkyCore Solutions" />
  <meta property="og:description" content="{post['metaDescription']}" />
  <meta property="og:url" content="{canonical_url}" />
  <meta property="og:image" content="{thumb_url}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{post['title']} — SkyCore Solutions" />
  <meta name="twitter:description" content="{post['metaDescription']}" />
  <meta name="twitter:image" content="{thumb_url}" />
  <link rel="canonical" href="{canonical_url}" />
  <meta property="article:published_time" content="{post['date']}" />
</head>
<body>
  <header class="nav">
    <div class="nav-inner">
      <a href="../" class="logo"><img class="logo-svg" src="../assets/images/logo.png" alt="SkyCore logo" /><span><span class="sky">SKY</span><span class="core">CORE</span> <span class="inc">SOLUTIONS</span></span></a>
      <nav class="nav-links">
        <a href="../">Home</a>
        <a href="../services.html">Services</a>
        <a href="../about.html">About</a>
        <a href="./">Blog</a>
        <a href="../contact.html">Contact</a>
        <a href="#" class="btn btn-primary" style="padding:10px 18px;" data-tidycal-popup="mnkpzxm/30-minute-meeting">Free Consultation</a>
      </nav>
      <button class="nav-burger" aria-label="Menu"><span></span><span></span><span></span></button>
    </div>
  </header>

  <article class="article">
    {content}
  </article>

  <footer class="footer">
    <div class="container">
      <div class="footer-grid">
        <div><a href="../" class="logo"><img class="logo-svg" src="../assets/images/logo.png" alt="SkyCore logo" /><span><span class="sky">SKY</span><span class="core">CORE</span> <span class="inc">SOLUTIONS</span></span></a><p style="margin-top:14px;max-width:320px;">Transforming IT infrastructure with innovation and expertise.</p><p style="margin-top:8px;color:var(--text-3);font-size:0.9rem;">Montreal, Quebec, Canada</p></div>
        <div><h4>Services</h4><ul><li><a href="../services.html#cloud">Cloud Migration</a></li><li><a href="../services.html#security">Security Hardening</a></li><li><a href="../services.html#infra">Infrastructure Revamp</a></li></ul></div>
        <div><h4>Company</h4><ul><li><a href="../about.html">About</a></li><li><a href="./">Blog</a></li><li><a href="../contact.html">Contact</a></li></ul></div>
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


def prepend_to_feed_xml(post: dict, thumb_url: str):
    from email.utils import formatdate
    from datetime import datetime
    feed_path = "blog/feed.xml"
    with open(feed_path, "r", encoding="utf-8") as f:
        content = f.read()

    title   = post["title"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    excerpt = post["excerpt"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    slug    = post["slug"]
    url     = f"https://skycoresolutions.com/blog/{slug}.html"
    img     = thumb_url.replace("&", "&amp;")
    cat     = post["category"].replace("&", "&amp;")
    dt      = datetime.strptime(post["date"], "%Y-%m-%d")
    pub     = formatdate(dt.timestamp(), usegmt=True)

    new_item = (
        f"\n    <item>\n"
        f"      <title>{title}</title>\n"
        f"      <link>{url}</link>\n"
        f"      <guid isPermaLink=\"true\">{url}</guid>\n"
        f"      <pubDate>{pub}</pubDate>\n"
        f"      <description>{excerpt}</description>\n"
        f"      <category>{cat}</category>\n"
        f"      <media:content url=\"{img}\" medium=\"image\"/>\n"
        f"    </item>\n"
    )

    content = content.replace("\n    <item>", new_item + "\n    <item>", 1)

    with open(feed_path, "w", encoding="utf-8") as f:
        f.write(content)


def prepend_to_posts_js(post: dict, thumb_url: str):
    posts_path = "blog/posts.js"
    with open(posts_path, "r", encoding="utf-8") as f:
        content = f.read()

    title   = post["title"].replace("\\", "\\\\").replace('"', '\\"')
    excerpt = post["excerpt"].replace("\\", "\\\\").replace('"', '\\"')

    new_entry = (
        f'  {{\n'
        f'    slug: "{post["slug"]}",\n'
        f'    title: "{title}",\n'
        f'    date: "{post["date"]}",\n'
        f'    readTime: "{post["readTime"]}",\n'
        f'    category: "{post["category"]}",\n'
        f'    excerpt: "{excerpt}",\n'
        f'    tint: "from-sky to-cyan",\n'
        f'    image: "{thumb_url}"\n'
        f'  }},\n'
    )

    content = content.replace(
        "window.SKYCORE_POSTS = [\n",
        f"window.SKYCORE_POSTS = [\n{new_entry}"
    )

    with open(posts_path, "w", encoding="utf-8") as f:
        f.write(content)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("── Fetching news feeds ──")
    news = fetch_news()
    print(f"   {len(news)} headlines collected")

    print("── Generating post via Gemini 2.5 Flash ──")
    post = generate_post(news)
    print(f"   Slug : {post['slug']}")
    print(f"   Title: {post['title']}")

    hero_url, thumb_url = pick_photo(post.get("imageQuery", "server infrastructure"))
    print(f"   Image: {hero_url}")

    html_path = f"blog/{post['slug']}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(build_html(post, hero_url))
    print(f"── Written: {html_path} ──")

    prepend_to_posts_js(post, thumb_url)
    print("── posts.js updated ──")

    prepend_to_feed_xml(post, thumb_url)
    print("── feed.xml updated ──")
    print("Done ✓")


if __name__ == "__main__":
    main()


