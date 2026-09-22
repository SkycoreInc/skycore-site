"""
SkyCore Solutions — Microsoft How-To Generator (Generator 2)
Generates one deep, SEO-optimized Microsoft product guide per run.

Covers all major Azure / Microsoft 365 surface areas in rotation,
alternating between Cloud Migration and Infrastructure Revamp categories
so no two consecutive guides cover the same pillar.

Reads keyword volumes from scripts/ms_keyword_queue.json if available
(refreshed monthly by keyword-refresh.yml). Falls back to hardcoded list.

Requires env vars:
  GEMINI_API_KEY
  PEXELS_API_KEY   (optional — falls back to Unsplash)

Run:
  python scripts/generate_ms_howto.py
"""

import os
import re
import json
import time
import textwrap
import requests
from google import genai
from datetime import date

# ── Config ────────────────────────────────────────────────────────────────────

CLIENT         = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
GEMINI_MODEL   = "gemini-2.5-flash"
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

# ── MS topic queue ────────────────────────────────────────────────────────────
# Ordered: Cloud Migration and Infrastructure Revamp alternate naturally
# when the alternating-category logic is applied.
# Each covers a distinct Azure/MS365 product — no overlap with Generator 1.

MS_TOPIC_QUEUE = [
    # Hottest current Microsoft topics — one published per month
    {"keyword": "Microsoft 365 Copilot setup guide SMB",              "category": "Cloud Migration",      "volume": 9900},
    {"keyword": "Microsoft Defender XDR setup guide SMB",             "category": "Security Hardening",   "volume": 6600},
    {"keyword": "Azure OpenAI Service setup guide SMB",               "category": "Infrastructure Revamp","volume": 5400},
    {"keyword": "Microsoft Entra External ID setup guide",            "category": "Security Hardening",   "volume": 4800},
    {"keyword": "Microsoft Security Copilot setup guide",             "category": "Security Hardening",   "volume": 4400},
    {"keyword": "Microsoft Copilot Studio setup guide SMB",           "category": "Infrastructure Revamp","volume": 3900},
    {"keyword": "Azure AI Foundry setup guide small business",        "category": "Infrastructure Revamp","volume": 3500},
    {"keyword": "Microsoft Fabric analytics setup SMB",               "category": "Cloud Migration",      "volume": 3200},
    {"keyword": "Windows 11 24H2 migration guide SMB",                "category": "Infrastructure Revamp","volume": 2900},
    {"keyword": "GitHub Copilot Business setup guide",                "category": "Infrastructure Revamp","volume": 2600},
    {"keyword": "Microsoft Intune Suite setup guide SMB",             "category": "Security Hardening",   "volume": 2300},
    {"keyword": "Azure AI Document Intelligence setup guide",         "category": "Cloud Migration",      "volume": 2000},
]

# ── Authoritative doc sources per keyword ────────────────────────────────────

DOC_SOURCES = {
    "Microsoft 365 Copilot setup guide SMB": [
        "https://learn.microsoft.com/en-us/copilot/microsoft-365/microsoft-365-copilot-overview",
        "https://learn.microsoft.com/en-us/copilot/microsoft-365/microsoft-365-copilot-setup",
        "https://learn.microsoft.com/en-us/copilot/microsoft-365/microsoft-365-copilot-requirements",
        "https://learn.microsoft.com/en-us/copilot/microsoft-365/microsoft-365-copilot-privacy",
    ],
    "Microsoft Defender XDR setup guide SMB": [
        "https://learn.microsoft.com/en-us/defender-xdr/microsoft-365-defender",
        "https://learn.microsoft.com/en-us/defender-xdr/get-started",
        "https://learn.microsoft.com/en-us/defender-xdr/pilot-deploy-overview",
        "https://learn.microsoft.com/en-us/defender-xdr/investigate-incidents",
    ],
    "Azure OpenAI Service setup guide SMB": [
        "https://learn.microsoft.com/en-us/azure/ai-services/openai/overview",
        "https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/create-resource",
        "https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models",
        "https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/content-filter",
        "https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/deploy-models",
    ],
    "Microsoft Entra External ID setup guide": [
        "https://learn.microsoft.com/en-us/entra/external-id/customers/overview-customers-ciam",
        "https://learn.microsoft.com/en-us/entra/external-id/customers/quickstart-trial-setup",
        "https://learn.microsoft.com/en-us/entra/external-id/customers/how-to-user-flow-sign-up-sign-in-customers",
        "https://learn.microsoft.com/en-us/entra/external-id/customers/concept-security-customers",
    ],
    "Microsoft Security Copilot setup guide": [
        "https://learn.microsoft.com/en-us/copilot/security/microsoft-security-copilot",
        "https://learn.microsoft.com/en-us/copilot/security/get-started-security-copilot",
        "https://learn.microsoft.com/en-us/copilot/security/authentication",
        "https://learn.microsoft.com/en-us/copilot/security/plugin-overview",
    ],
    "Microsoft Copilot Studio setup guide SMB": [
        "https://learn.microsoft.com/en-us/microsoft-copilot-studio/fundamentals-what-is-copilot-studio",
        "https://learn.microsoft.com/en-us/microsoft-copilot-studio/fundamentals-get-started",
        "https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-first-bot",
        "https://learn.microsoft.com/en-us/microsoft-copilot-studio/publication-fundamentals-publish-channels",
    ],
    "Azure AI Foundry setup guide small business": [
        "https://learn.microsoft.com/en-us/azure/ai-foundry/what-is-azure-ai-foundry",
        "https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/create-projects",
        "https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/deployments-overview",
        "https://learn.microsoft.com/en-us/azure/ai-foundry/responsible-use-of-ai-overview",
    ],
    "Microsoft Fabric analytics setup SMB": [
        "https://learn.microsoft.com/en-us/fabric/get-started/microsoft-fabric-overview",
        "https://learn.microsoft.com/en-us/fabric/get-started/fabric-trial",
        "https://learn.microsoft.com/en-us/fabric/get-started/create-workspaces",
        "https://learn.microsoft.com/en-us/fabric/security/security-overview",
        "https://learn.microsoft.com/en-us/fabric/get-started/licenses",
    ],
    "Windows 11 24H2 migration guide SMB": [
        "https://learn.microsoft.com/en-us/windows/whats-new/windows-11-version-24h2",
        "https://learn.microsoft.com/en-us/windows/deployment/update/waas-quick-start",
        "https://learn.microsoft.com/en-us/mem/intune/fundamentals/windows-upgrade",
        "https://learn.microsoft.com/en-us/windows/deployment/windows-autopatch/overview/windows-autopatch-overview",
    ],
    "GitHub Copilot Business setup guide": [
        "https://docs.github.com/en/copilot/about-github-copilot/what-is-github-copilot",
        "https://docs.github.com/en/copilot/managing-copilot/managing-github-copilot-in-your-organization/setting-up-github-copilot-for-your-organization",
        "https://docs.github.com/en/copilot/using-github-copilot/using-github-copilot-in-the-command-line",
        "https://docs.github.com/en/copilot/responsible-use-of-github-copilot-features/responsible-use-of-github-copilot-in-your-organization",
    ],
    "Microsoft Intune Suite setup guide SMB": [
        "https://learn.microsoft.com/en-us/mem/intune/fundamentals/what-is-intune",
        "https://learn.microsoft.com/en-us/mem/intune/fundamentals/intune-add-ons",
        "https://learn.microsoft.com/en-us/mem/intune/protect/advanced-threat-protection",
        "https://learn.microsoft.com/en-us/mem/intune/protect/endpoint-security",
        "https://learn.microsoft.com/en-us/mem/intune/fundamentals/remote-help",
    ],
    "Azure AI Document Intelligence setup guide": [
        "https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/overview",
        "https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/how-to-guides/create-document-intelligence-resource",
        "https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/concept-model-overview",
        "https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/how-to-guides/build-a-custom-classifier",
    ],
}

# ── Fallback Unsplash photos by category ──────────────────────────────────────

FALLBACK_PHOTOS = {
    "Cloud Migration":       "1451187580459-43490279c0fa",
    "Infrastructure Revamp": "1461749280684-dccba630e2f6",
}

# ── Queue loader ──────────────────────────────────────────────────────────────

def load_ms_queue() -> list:
    """Load from DataForSEO-refreshed JSON if available, else use hardcoded fallback."""
    json_path = os.path.join(os.path.dirname(__file__), "ms_keyword_queue.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                queue = json.load(f)
            print(f"   Loaded {len(queue)} MS topics from ms_keyword_queue.json (refreshed {queue[0].get('refreshed','?')})")
            return queue
        except Exception as e:
            print(f"   ms_keyword_queue.json load failed ({e}), using hardcoded fallback")
    return MS_TOPIC_QUEUE

# ── Keyword/image helpers ─────────────────────────────────────────────────────

def get_written_keywords() -> set:
    try:
        with open("how-to/posts.js", "r", encoding="utf-8") as f:
            content = f.read()
        return set(re.findall(r'keyword:\s*"([^"]+)"', content))
    except Exception:
        return set()


def get_last_category() -> str | None:
    """Return the category of the most recently published how-to article."""
    try:
        with open("how-to/posts.js", "r", encoding="utf-8") as f:
            content = f.read()
        match = re.search(r'category:\s*"([^"]+)"', content)
        return match.group(1) if match else None
    except Exception:
        return None


def get_used_image_urls() -> set:
    try:
        with open("how-to/posts.js", "r", encoding="utf-8") as f:
            content = f.read()
        return set(re.findall(r'image:\s*"([^"]+)"', content))
    except Exception:
        return set()


def pick_next_topic(queue: list) -> dict | None:
    """Pick next unwritten topic, avoiding the same category as the last article."""
    written  = get_written_keywords()
    last_cat = get_last_category()
    available = [item for item in queue if item["keyword"] not in written]

    if not available:
        return None

    if last_cat:
        different = [item for item in available if item["category"] != last_cat]
        if different:
            print(f"   Last category was '{last_cat}' — alternating to a different category")
            return different[0]
        print(f"   All remaining topics are '{last_cat}' — using next highest-volume anyway")

    return available[0]

# ── Doc fetching ──────────────────────────────────────────────────────────────

def strip_html(html: str) -> str:
    text = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_doc(url: str, max_chars: int = 6000) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; SkyCore-Bot/1.0; research)",
        "Accept": "text/html,application/xhtml+xml",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        text = strip_html(resp.text)
        if len(text) > max_chars:
            text = text[:max_chars]
            cut = text.rfind(". ")
            if cut > max_chars * 0.7:
                text = text[:cut + 1]
        return text
    except Exception as e:
        print(f"   [doc fetch failed] {url}: {e}")
        return ""


def gather_reference_docs(keyword: str) -> tuple[str, list[str]]:
    urls = DOC_SOURCES.get(keyword, [])
    if not urls:
        print("   No doc sources for this topic — using Gemini training only")
        return "", []
    sections, fetched_urls = [], []
    for url in urls:
        print(f"   Fetching: {url}")
        content = fetch_doc(url)
        if content:
            sections.append(f"SOURCE: {url}\n{content}")
            fetched_urls.append(url)
        time.sleep(1)
    combined = "\n\n---\n\n".join(sections)
    print(f"   Fetched {len(fetched_urls)}/{len(urls)} docs, {len(combined):,} chars of reference material")
    return combined, fetched_urls

# ── Image helpers ─────────────────────────────────────────────────────────────

def pick_photo_pexels(query: str, used_urls: set) -> tuple[str, str] | tuple[None, None]:
    if not PEXELS_API_KEY:
        return None, None
    queries = [query, query.split()[0] + " technology", "Microsoft Azure cloud"]
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
                    print(f"   Pexels photo #{photo['id']} selected")
                    return hero, thumb
        except Exception as e:
            print(f"   Pexels error: {e}")
    return None, None


def pick_photo(image_query: str, category: str) -> tuple[str, str]:
    used = get_used_image_urls()
    hero, thumb = pick_photo_pexels(image_query, used)
    if hero:
        return hero, thumb
    pid   = FALLBACK_PHOTOS.get(category, "1451187580459-43490279c0fa")
    hero  = f"https://images.unsplash.com/photo-{pid}?w=1400&auto=format&fit=crop&q=80"
    thumb = f"https://images.unsplash.com/photo-{pid}?w=800&auto=format&fit=crop&q=80"
    print(f"   Unsplash fallback: {pid}")
    return hero, thumb

# ── Article generation ────────────────────────────────────────────────────────

def generate_article(topic: dict, ref_docs: str, source_urls: list[str]) -> dict:
    keyword  = topic["keyword"]
    category = topic["category"]
    today    = date.today().isoformat()

    doc_section = ""
    if ref_docs:
        source_list = "\n".join(f"  - {u}" for u in source_urls)
        doc_section = f"""
REFERENCE DOCUMENTATION (fetched today from official Microsoft Learn and related sources):
{source_list}

Instructions for using this material:
- Synthesize across ALL sources into one cohesive guide
- Use exact CLI commands, parameter names, and flag values from the docs
- Where docs offer multiple options, recommend the best one for SMBs and say why
- Do NOT copy-paste — extract the facts and write in SkyCore's voice
- CLI and PowerShell commands always come first; portal steps are secondary
---
{ref_docs[:14000]}
---
"""

    prompt = textwrap.dedent(f"""
        You are a senior Azure architect and IT consultant at SkyCore Solutions,
        a Montreal-based IT consulting firm specializing in Cloud Migration (Azure),
        Security Hardening, and Infrastructure Revamp for SMBs.

        Write a comprehensive, authoritative Microsoft implementation guide for:
        PRIMARY KEYWORD: "{keyword}"
        CATEGORY: {category}
        DATE: {today}
        {doc_section}

        CONTENT PHILOSOPHY:
        - MICROSOFT-FIRST: This is a deep implementation guide for a specific Microsoft
          product or Azure service. Every step uses the real Microsoft toolchain:
          Azure CLI, PowerShell (Az module), Microsoft 365 admin center, or Azure Portal.
        - CLI-FIRST: Lead every step with the Azure CLI (`az`) or PowerShell (`Az` module)
          command. GUI portal steps follow in a <p class="gui-note"> block.
        - SEO-OPTIMIZED: Naturally integrate the primary keyword in the title, intro,
          at least two h2 headings, and the conclusion. Write for humans first.
        - ACCURATE: Use exact command syntax from the Microsoft Learn docs above.
          Include real resource names, SKUs, flags, and region codes.
        - SMB-FOCUSED: Assume the reader is an IT admin or owner of a 10-200 person
          company. No enterprise-scale complexity unless it directly applies.
        - HONEST: Call out licensing requirements (e.g. "requires Microsoft 365 Business
          Premium"), cost implications, and real gotchas.
        - OPINIONATED: Give concrete recommendations. "Use Standard_D2s_v5 for most
          SMB workloads" beats "choose an appropriate size."
        - LENGTH: 1,800–2,500 words of real, actionable substance.

        STRUCTURE (use these exact HTML elements):
        1. <div class="post-meta">{today} · READTIME · {category}</div>
        2. <h1>TITLE — include the primary keyword naturally</h1>
        3. <div class="article-hero"><img src="HERO_IMAGE_PLACEHOLDER" alt="HERO_ALT_PLACEHOLDER" loading="eager" fetchpriority="high"></div>
        4. <div class="howto-intro"><p>Hook: state the business problem, why this Microsoft product solves it, what the reader will have working by the end. Include the primary keyword.</p></div>
        5. <div class="howto-prereqs"><h4>Prerequisites</h4><ul>List licenses, roles, tools (Azure CLI version, PowerShell module), and estimated cost</ul></div>
        6. Steps: <h2>Step N: [Strong action verb + exactly what happens]</h2>
           - 1 paragraph context explaining why this step matters
           - Command in <pre><code class="language-azurecli"> or <code class="language-powershell">
           - After each command: bullet list explaining key flags/parameters
           - GUI alternative in <p class="gui-note"><strong>Portal alternative:</strong> ...</p>
           - Confirmation: "Run this to verify:" + a check command
        7. Sprinkle 2-3 callout boxes throughout:
           <div class="howto-callout howto-callout--warning"><strong>Common pitfall:</strong> ...</div>
           <div class="howto-callout howto-callout--tip"><strong>Pro tip:</strong> ...</div>
        8. <div class="howto-consultant-cta"><h3>When to bring in a consultant</h3>
           <p>Be specific about when this setup needs professional help (e.g. hybrid AD, complex licensing, production migration). Soft CTA — not a sales pitch.</p>
           <a href="../contact.html" class="btn btn-primary">Book a free consultation</a></div>

        Return ONLY valid JSON (no markdown fences) with these exact fields:
        {{
          "slug": "seo-url-slug-4-6-words-with-keyword",
          "title": "Full compelling title including primary keyword naturally",
          "metaDescription": "145-155 char meta description with keyword and benefit",
          "readTime": "X min read",
          "category": "{category}",
          "difficulty": "Beginner|Intermediate|Advanced",
          "timeEstimate": "e.g. 45 minutes or 2-3 hours",
          "keyword": "{keyword}",
          "excerpt": "2-sentence excerpt under 160 chars with primary keyword",
          "imageQuery": "3-4 word Pexels search query relevant to the MS product",
          "imageAlt": "Descriptive alt text under 125 chars with keyword",
          "prerequisites": ["item 1", "item 2", "item 3"],
          "steps": [
            {{"name": "Step name", "text": "One sentence describing what this step accomplishes"}}
          ],
          "htmlContent": "Full article HTML as described above."
        }}
    """).strip()

    current_prompt = prompt
    api_attempts   = 0   # counts 503/429 retries independently
    json_attempts  = 0   # counts JSON parse failures independently
    MAX_API        = 6
    MAX_JSON       = 3

    while True:
        try:
            api_attempts += 1
            response = CLIENT.models.generate_content(model=GEMINI_MODEL, contents=current_prompt)
            raw = response.text.strip()
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
            match = re.search(r"\{[\s\S]*\}", raw)
            if match:
                raw = match.group(0)
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError) as e:
            json_attempts += 1
            print(f"   JSON parse failed (attempt {json_attempts}/{MAX_JSON}): {e}")
            if json_attempts >= MAX_JSON:
                raise RuntimeError(f"Gemini returned invalid JSON after {MAX_JSON} parse attempts: {e}")
            current_prompt += "\n\nCRITICAL: JSON parse error. Escape ALL double quotes inside strings with \\\" — especially inside htmlContent."
        except Exception as e:
            err_str = str(e)
            is_retryable = (
                "503" in err_str or "UNAVAILABLE" in err_str or
                "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or
                "500" in err_str
            )
            if is_retryable and api_attempts < MAX_API:
                wait = min(15 * (2 ** (api_attempts - 1)), 120)  # cap at 120s
                print(f"   Gemini API error (attempt {api_attempts}/{MAX_API}): {err_str[:120]}")
                print(f"   Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise

# ── Sources footer ────────────────────────────────────────────────────────────

def build_sources_html(source_urls: list[str]) -> str:
    if not source_urls:
        return ""
    items = []
    for url in source_urls:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        path   = parsed.path.rstrip("/").split("/")[-1].replace("-", " ")
        label  = f"{domain}" + (f" — {path}" if path else "")
        items.append(f'    <li><a href="{url}" target="_blank" rel="noopener noreferrer">{label}</a></li>')
    rows = "\n".join(items)
    return f"""
<div class="howto-sources">
  <h4>References</h4>
  <ul>
{rows}
  </ul>
</div>"""

# ── HTML builder ──────────────────────────────────────────────────────────────

def build_html(article: dict, hero_url: str, source_urls: list[str] | None = None) -> str:
    # Guarantee all fields used in the f-string exist — Gemini sometimes omits them
    article = {
        "date":            date.today().isoformat(),
        "readTime":        "10 min read",
        "metaDescription": "",
        "imageAlt":        "Microsoft Azure guide",
        "imageQuery":      "Microsoft Azure",
        "prerequisites":   [],
        "steps":           [],
        **article,  # real values override defaults
    }
    image_alt = article.get("imageAlt", article.get("imageQuery", "Microsoft Azure guide"))
    content = (
        article["htmlContent"]
        .replace("HERO_IMAGE_PLACEHOLDER", hero_url)
        .replace("HERO_ALT_PLACEHOLDER", image_alt)
    )
    sources_html = build_sources_html(source_urls or [])
    if sources_html:
        content = content + sources_html

    pub_date      = article.get("date") or date.today().isoformat()
    thumb_url     = hero_url.replace("w=1400", "w=1200").replace("h=600", "h=630")
    canonical_url = f"https://skycoresolutions.com/how-to/{article['slug']}.html"

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
  <meta property="article:published_time" content="{pub_date}" />
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
        <div><h4>Contact</h4><ul><li><a href="mailto:info@skycoresolutions.com">info@skycoresolutions.com</a></li><li style="color:var(--text-3);font-size:0.9rem;">Mon-Fri: 9AM-6PM EST</li><li style="color:var(--text-3);font-size:0.9rem;">24/7 Emergency Support</li></ul></div>
      </div>
      <div class="footer-bottom"><span>&copy; <span id="year">2026</span> SkyCore Solutions Inc. All rights reserved.</span><span>SkyCore Solutions Inc. is a registered trademark.</span></div>
    </div>
  </footer>
  <script>document.getElementById("year").textContent = new Date().getFullYear();</script>
  <script src="../assets/js/main.js"></script>
  <script src="https://asset-tidycal.b-cdn.net/js/embed.js"></script>
</body>
</html>"""

# ── posts.js writer ───────────────────────────────────────────────────────────

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
        f'    timeEstimate: "{article.get("timeEstimate", "1-2 hours")}",\n'
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
    queue = load_ms_queue()
    topic = pick_next_topic(queue)
    if not topic:
        print("All MS topics written. Keyword queue will refresh next month via keyword-refresh.yml.")
        return

    print(f"-- Next MS topic: \"{topic['keyword']}\" ({topic.get('volume', 0):,}/mo) --")
    print(f"   Category: {topic['category']}")

    print("-- Fetching reference documentation --")
    ref_docs, source_urls = gather_reference_docs(topic["keyword"])

    print("-- Generating article via Gemini 2.5 Flash --")
    article = generate_article(topic, ref_docs, source_urls)
    article['date'] = date.today().isoformat()  # always set authoritatively
    print(f"   Slug:       {article['slug']}")
    print(f"   Title:      {article['title']}")
    print(f"   Difficulty: {article.get('difficulty')} | Time: {article.get('timeEstimate')}")
    print(f"   Steps:      {len(article.get('steps', []))}")

    hero_url, thumb_url = pick_photo(article.get("imageQuery", topic["keyword"]), topic["category"])
    print(f"   Image:      {hero_url[:80]}...")

    html_path = f"how-to/{article['slug']}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(build_html(article, hero_url, source_urls))
    print(f"-- Written: {html_path} --")

    prepend_to_posts_js(article, thumb_url)
    print("-- how-to/posts.js updated --")

    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from update_sitemap import regenerate as regen_sitemap
    regen_sitemap()

    print("Done")


if __name__ == "__main__":
    main()
