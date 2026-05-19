"""
SkyCore Solutions — Keyword Research Script
Uses DataForSEO Google Ads API to validate search volume and competition
for the IT how-to article hub.

Requirements:
  DATAFORSEO_LOGIN    env var (your DataForSEO email)
  DATAFORSEO_PASSWORD env var (your DataForSEO API password)

Run:
  python scripts/keyword_research.py
"""

import os
import json
import base64
import urllib.request
import urllib.error
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────

LOGIN    = os.environ["DATAFORSEO_LOGIN"]
PASSWORD = os.environ["DATAFORSEO_PASSWORD"]
CREDS    = base64.b64encode(f"{LOGIN}:{PASSWORD}".encode()).decode()

# Target keywords — grouped by service pillar
KEYWORDS = {
    "Cloud Migration": [
        "how to migrate SQL Server to Azure",
        "SQL Server to Azure migration guide",
        "migrate on-premise server to Azure",
        "Azure AD Connect setup small business",
        "how to move Exchange to Microsoft 365",
        "migrate Exchange on-premise to Office 365",
        "Azure Virtual Machine migration guide",
        "Azure backup setup small business",
        "Azure cost optimization small business",
        "hybrid cloud setup small business",
        "cloud migration checklist SMB",
        "Microsoft 365 migration guide",
    ],
    "Security Hardening": [
        "how to set up Active Directory tiering",
        "Active Directory tier 0 tier 1 tier 2",
        "how to configure DMARC DKIM SPF",
        "DMARC setup step by step",
        "Microsoft 365 MFA setup small business",
        "how to enable MFA Office 365",
        "zero trust security small business",
        "how to implement zero trust network",
        "Windows Server hardening checklist",
        "how to harden Windows Server 2022",
        "ransomware protection small business",
        "endpoint security small business",
        "cybersecurity checklist SMB",
        "how to set up conditional access Azure AD",
        "PIPEDA compliance IT checklist Canada",
    ],
    "Infrastructure Revamp": [
        "how to set up CI CD pipeline small team",
        "CI CD pipeline setup guide",
        "how to containerize legacy application",
        "Docker containerization guide",
        "how to migrate physical server to virtual machine",
        "VMware to Azure migration guide",
        "disaster recovery plan small business",
        "how to build disaster recovery plan IT",
        "remote work IT infrastructure setup",
        "how to set up VPN for small business",
        "IT infrastructure modernization guide",
        "DevOps implementation small business",
    ],
    "Local SEO": [
        "IT support Montreal",
        "managed IT services Montreal",
        "IT consulting Montreal",
        "cybersecurity services Montreal",
        "cloud migration services Montreal",
        "IT support small business Montreal",
        "IT infrastructure Montreal",
        "Azure consultant Montreal",
        "Microsoft 365 support Montreal",
        "network security audit Montreal",
    ],
}

# ── API call ──────────────────────────────────────────────────────────────────

def get_search_volumes(keywords: list[str]) -> list[dict]:
    """Fetch search volume + competition for up to 1000 keywords in one task."""
    payload = json.dumps([{
        "keywords":  keywords,
        "language_name": "English",
        "location_name": "Canada",
    }]).encode()

    req = urllib.request.Request(
        "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live",
        data=payload,
        headers={
            "Authorization": f"Basic {CREDS}",
            "Content-Type":  "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    if data.get("status_code") != 20000:
        raise RuntimeError(f"API error: {data.get('status_message')}")

    return data["tasks"][0].get("result") or []


def get_keyword_ideas(seed_keywords: list[str]) -> list[dict]:
    """Fetch related keyword ideas from a seed list."""
    payload = json.dumps([{
        "keywords":      seed_keywords,
        "language_name": "English",
        "location_name": "Canada",
        "limit":         50,
    }]).encode()

    req = urllib.request.Request(
        "https://api.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/live",
        data=payload,
        headers={
            "Authorization": f"Basic {CREDS}",
            "Content-Type":  "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    if data.get("status_code") != 20000:
        raise RuntimeError(f"API error: {data.get('status_message')}")

    return data["tasks"][0].get("result") or []


# ── Scoring ───────────────────────────────────────────────────────────────────

COMPETITION_SCORE = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, None: 2}

def opportunity_score(volume: int, competition: str) -> float:
    """Higher volume + lower competition = better score."""
    vol   = min(volume or 0, 10000)
    comp  = COMPETITION_SCORE.get(competition, 2)
    return round((vol + 1) / comp, 1)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    all_keywords = [kw for group in KEYWORDS.values() for kw in group]
    print(f"── Fetching search volumes for {len(all_keywords)} keywords ──")

    results_raw = get_search_volumes(all_keywords)
    volume_map  = {r["keyword"]: r for r in results_raw}

    # Build scored rows
    rows = []
    for pillar, keywords in KEYWORDS.items():
        for kw in keywords:
            data   = volume_map.get(kw, {})
            volume = data.get("search_volume") or 0
            comp   = data.get("competition_level")
            score  = opportunity_score(volume, comp)
            rows.append({
                "pillar":      pillar,
                "keyword":     kw,
                "volume":      volume,
                "competition": comp or "N/A",
                "score":       score,
            })

    rows.sort(key=lambda r: r["score"], reverse=True)

    # ── Print report ──────────────────────────────────────────────────────────
    print(f"\n{'='*80}")
    print(f"  SKYCORE SOLUTIONS — KEYWORD OPPORTUNITY REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Location: Canada | Language: English")
    print(f"{'='*80}\n")

    current_pillar = None
    for r in rows:
        if r["pillar"] != current_pillar:
            current_pillar = r["pillar"]
            print(f"\n── {current_pillar} ──")
            print(f"  {'Keyword':<50} {'Volume':>8}  {'Competition':<12}  {'Score':>6}")
            print(f"  {'-'*50} {'-'*8}  {'-'*12}  {'-'*6}")
        print(f"  {r['keyword']:<50} {r['volume']:>8,}  {r['competition']:<12}  {r['score']:>6}")

    # ── Top 10 overall ────────────────────────────────────────────────────────
    print(f"\n{'='*80}")
    print("  TOP 10 OPPORTUNITIES (write these first)")
    print(f"{'='*80}")
    for i, r in enumerate(rows[:10], 1):
        print(f"  {i:2}. [{r['pillar']}]")
        print(f"      {r['keyword']}")
        print(f"      Volume: {r['volume']:,} | Competition: {r['competition']} | Score: {r['score']}")

    # ── Save to JSON ──────────────────────────────────────────────────────────
    out_path = "scripts/keyword_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    print(f"\n── Full report saved to {out_path} ──")
    print(f"── Total API cost: ~$0.05 (1 task) ──")

    # ── Fetch keyword ideas from top seeds ────────────────────────────────────
    print("\n── Fetching keyword ideas from top seeds ──")
    seeds = [r["keyword"] for r in rows[:5]]
    ideas = get_keyword_ideas(seeds)
    ideas.sort(key=lambda x: x.get("search_volume") or 0, reverse=True)

    print(f"\n  TOP 20 RELATED KEYWORDS TO CONSIDER:")
    print(f"  {'Keyword':<50} {'Volume':>8}  {'Competition'}")
    print(f"  {'-'*50} {'-'*8}  {'-'*11}")
    for idea in ideas[:20]:
        kw   = idea.get("keyword", "")
        vol  = idea.get("search_volume") or 0
        comp = idea.get("competition_level") or "N/A"
        print(f"  {kw:<50} {vol:>8,}  {comp}")

    ideas_path = "scripts/keyword_ideas.json"
    with open(ideas_path, "w", encoding="utf-8") as f:
        json.dump(ideas[:50], f, indent=2)
    print(f"\n── Keyword ideas saved to {ideas_path} ──")
    print("\nDone ✓")


if __name__ == "__main__":
    main()
