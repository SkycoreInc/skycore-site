# SkyCore Solutions — Project Memory

## Company
- **Name:** SkyCore Solutions Inc.
- **Location:** Montreal, Quebec, Canada
- **Industry:** IT Consulting
- **Services:** Cloud Migration (Azure), Security Hardening (NIST/CIS/Zero Trust), Infrastructure Revamp (DevOps/CI-CD/containerization)
- **Target clients:** Small and medium businesses (SMBs), primarily Montreal and North America
- **Phone:** (514) 500-9562
- **Email:** info@skycoresolutions.com
- **Hours:** Mon–Fri 9AM–6PM EST, 24/7 Emergency Support

## Website
- **URL:** https://skycoresolutions.com
- **Stack:** Pure static HTML/CSS/JS — no build step
- **Hosting:** Netlify (auto-deploys from GitHub on every push)
- **Repo:** https://github.com/SkycoreInc/skycore-site (branch: `main`)
- **Local path:** `C:\Users\ahmad\OneDrive\Documents\SkyCore Inc\Claude\site`
- **Git push auth:** PAT embedded in URL — `https://PAT_REDACTED@github.com/SkycoreInc/skycore-site.git main`

## Site Structure
```
site/
├── index.html          # Homepage
├── services.html       # Services (Cloud, Security, Infrastructure)
├── about.html          # About page
├── contact.html        # Contact + TidyCal inline booking
├── blog/
│   ├── index.html      # Blog listing (renders from posts.js)
│   ├── posts.js        # Blog manifest — add new entries at TOP
│   ├── feed.xml        # RSS feed (auto-updated by generate_blog.py)
│   └── *.html          # Individual blog post pages
├── how-to/
│   ├── index.html      # How-To hub (renders from posts.js with category filters)
│   ├── posts.js        # How-To manifest — add new entries at TOP
│   └── *.html          # Individual how-to article pages (with HowTo JSON-LD schema)
├── assets/
│   ├── css/style.css   # All styles (includes howto-filters, difficulty badges, code blocks)
│   ├── js/main.js      # TidyCal modal + nav logic
│   └── images/logo.png # Logo (black bg, use mix-blend-mode:screen for transparency)
├── scripts/
│   ├── generate_blog.py   # Auto blog generator
│   ├── generate_howto.py  # Auto how-to article generator (30-keyword priority queue)
│   └── keyword_research.py # DataForSEO keyword research tool
└── .github/workflows/
    ├── blog-generator.yml  # Cron: every 2 days at 10AM UTC
    └── howto-generator.yml # Cron: every 3 days at 11AM UTC
```

## Key Integrations
- **TidyCal:** Booking popup via `data-tidycal-popup="mnkpzxm/30-minute-meeting"` — handled by custom iframe modal in main.js (NOT embed.js)
- **Formspree:** Contact form AJAX, formId `xzdorrzo`
- **Zapier:** RSS feed → LinkedIn Company Page auto-post (free tier)
- **LinkedIn Company Page:** Auto-posts within ~15 min of new blog post via Zapier + feed.xml

## Automated Blog System
- **Trigger:** GitHub Actions cron `0 10 */2 * *` (every 2 days, 10AM UTC) + manual `workflow_dispatch`
- **Script:** `scripts/generate_blog.py`
- **AI model:** Gemini 2.5 Flash (free tier) — secret `GEMINI_API_KEY`
- **Images:** Pexels API (keyword search, never repeats) — secret `PEXELS_API_KEY`; falls back to Unsplash pool
- **RSS:** `blog/feed.xml` updated automatically on every new post
- **SEO:** Each post gets OG tags, Twitter Card, canonical link, descriptive alt text
- **Push fix:** Workflow uses retry loop (up to 5x with `git pull --rebase`) to handle remote-ahead rejections

## Design System
- **Fonts:** Orbitron (headings), Inter (body)
- **Colors:** Dark theme — cyan `var(--cyan)`, gradient `var(--gradient)`
- **Logo:** 108×88px in header (`mix-blend-mode: screen` for transparency), 80×65px in footer (same blend mode)
- **Logo gap:** 2px between icon and "SKYCORE SOLUTIONS" text
- **Brand name:** "SKYCORE SOLUTIONS" (not "SKYCORE INC.")

## SEO Status
- All 10 pages have OG + Twitter Card + canonical tags
- Blog hero images have descriptive alt text
- Sitemap: NOT yet created (to-do — would speed up Google indexing)
- Google Search Console: not yet set up (recommended next step)

## How-To Article Hub
- **Hub page:** `/how-to/` with category filters (Cloud Migration, Security Hardening, Infrastructure, IT Strategy)
- **Generator:** `scripts/generate_howto.py` — 30-keyword priority queue ordered by US search volume
- **GitHub Actions:** `howto-generator.yml` — runs every 3 days at 11AM UTC (offset from blog at 10AM)
- **Schema:** HowTo JSON-LD on every article page (enables Google rich snippets)
- **Pexels images:** Same deduplication logic as blog — never repeats images
- **Keyword queue:** disaster-recovery → MFA → AD tiering → DMARC → CI/CD → zero-trust → containerization → etc.
- **Categories:** Cloud Migration, Security Hardening, Infrastructure Revamp, IT Strategy

## Planned Work
- **Sitemap.xml:** Not yet generated
- **Google Search Console:** Not yet connected

## Content Strategy
- Blog posts tied to SkyCore's 3 services
- SEO keywords: "managed IT services Montreal", "cloud migration Azure", "IT infrastructure Montreal", "cybersecurity SMB", "zero trust security", "ransomware protection SMB", "Microsoft 365 security", "cloud cost optimization", "IT consulting Montreal", "infrastructure modernization"
- Posts hook on real news/CVEs from RSS feeds (TheHackersNews, BleepingComputer, Krebs, TechCrunch, ZDNet, Azure blog)
