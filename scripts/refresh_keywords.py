"""
SkyCore Solutions — Keyword Queue Refresher
Calls DataForSEO to get real search volumes for both how-to generators.
Writes:
  scripts/keyword_queue.json    — Generator 1 (broad IT topics)
  scripts/ms_keyword_queue.json — Generator 2 (Microsoft product guides)

Run monthly via GitHub Actions (keyword-refresh.yml).
Cost: ~$0.05 per run (one DataForSEO task per queue).

Requires env vars:
  DATAFORSEO_LOGIN
  DATAFORSEO_PASSWORD
"""

import os
import json
import base64
import urllib.request
from datetime import date

LOGIN    = os.environ["DATAFORSEO_LOGIN"]
PASSWORD = os.environ["DATAFORSEO_PASSWORD"]
CREDS    = base64.b64encode(f"{LOGIN}:{PASSWORD}".encode()).decode()
TODAY    = date.today().isoformat()

# ── Generator 1 seed keywords (broad IT / security / infra) ───────────────────

GEN1_SEEDS = [
    # IT Strategy
    {"keyword": "disaster recovery plan for small business",  "category": "IT Strategy"},
    {"keyword": "IT disaster recovery guide",                 "category": "IT Strategy"},
    {"keyword": "business continuity plan SMB",               "category": "IT Strategy"},
    {"keyword": "IT infrastructure assessment guide",         "category": "IT Strategy"},
    # Security Hardening
    {"keyword": "zero trust network access implementation",   "category": "Security Hardening"},
    {"keyword": "ransomware protection for small business",   "category": "Security Hardening"},
    {"keyword": "how to set up MFA for your organization",    "category": "Security Hardening"},
    {"keyword": "how to implement zero trust security",       "category": "Security Hardening"},
    {"keyword": "PIPEDA compliance IT checklist",             "category": "Security Hardening"},
    {"keyword": "DMARC configuration step by step",           "category": "Security Hardening"},
    {"keyword": "Office 365 MFA setup guide",                 "category": "Security Hardening"},
    {"keyword": "Windows Server hardening checklist",         "category": "Security Hardening"},
    {"keyword": "endpoint protection for small business",     "category": "Security Hardening"},
    {"keyword": "server hardening checklist",                 "category": "Security Hardening"},
    {"keyword": "Active Directory tiering best practices",    "category": "Security Hardening"},
    {"keyword": "how to configure DMARC DKIM SPF",            "category": "Security Hardening"},
    {"keyword": "Azure conditional access setup guide",       "category": "Security Hardening"},
    {"keyword": "how to harden Windows Server 2022",          "category": "Security Hardening"},
    {"keyword": "cybersecurity audit checklist SMB",          "category": "Security Hardening"},
    {"keyword": "phishing simulation setup guide",            "category": "Security Hardening"},
    # Cloud Migration
    {"keyword": "cloud migration guide for SMB",              "category": "Cloud Migration"},
    {"keyword": "Exchange to Office 365 migration guide",     "category": "Cloud Migration"},
    {"keyword": "Azure MFA configuration guide",              "category": "Cloud Migration"},
    {"keyword": "on premise to Azure migration guide",        "category": "Cloud Migration"},
    {"keyword": "Office 365 migration step by step",          "category": "Cloud Migration"},
    {"keyword": "Azure AD Connect setup guide",               "category": "Cloud Migration"},
    {"keyword": "SQL Server to Azure migration guide",        "category": "Cloud Migration"},
    {"keyword": "Azure backup setup guide",                   "category": "Cloud Migration"},
    {"keyword": "physical server to Azure VM migration",      "category": "Cloud Migration"},
    {"keyword": "hybrid cloud setup small business",          "category": "Cloud Migration"},
    # Infrastructure Revamp
    {"keyword": "GitHub Actions CI CD pipeline setup",        "category": "Infrastructure Revamp"},
    {"keyword": "Docker containerization tutorial",           "category": "Infrastructure Revamp"},
    {"keyword": "CI CD pipeline setup for small teams",       "category": "Infrastructure Revamp"},
    {"keyword": "DevOps implementation for small business",   "category": "Infrastructure Revamp"},
    {"keyword": "IT infrastructure modernization guide",      "category": "Infrastructure Revamp"},
    {"keyword": "Kubernetes setup guide small business",      "category": "Infrastructure Revamp"},
    {"keyword": "VMware to Hyper-V migration guide",          "category": "Infrastructure Revamp"},
    {"keyword": "network segmentation guide SMB",             "category": "Infrastructure Revamp"},
]

# ── Generator 2 seed keywords (Microsoft product guides) ──────────────────────

GEN2_SEEDS = [
    # Cloud Migration — MS products
    {"keyword": "migrate file server to Azure Files guide",      "category": "Cloud Migration"},
    {"keyword": "Azure Virtual Desktop setup guide",             "category": "Cloud Migration"},
    {"keyword": "VMware migration to Azure guide",               "category": "Cloud Migration"},
    {"keyword": "Microsoft 365 tenant to tenant migration",      "category": "Cloud Migration"},
    {"keyword": "migrate SharePoint to SharePoint Online",       "category": "Cloud Migration"},
    {"keyword": "Azure cost management optimization SMB",        "category": "Cloud Migration"},
    {"keyword": "Microsoft Entra ID setup guide SMB",            "category": "Cloud Migration"},
    {"keyword": "Hyper-V migration to Azure guide",              "category": "Cloud Migration"},
    {"keyword": "Microsoft Teams Phone setup small business",    "category": "Cloud Migration"},
    {"keyword": "Azure SQL Managed Instance migration guide",    "category": "Cloud Migration"},
    {"keyword": "Microsoft 365 Business Premium setup guide",    "category": "Cloud Migration"},
    {"keyword": "Azure Migrate assessment guide SMB",            "category": "Cloud Migration"},
    # Infrastructure Revamp — MS products
    {"keyword": "Azure Functions serverless deployment guide",   "category": "Infrastructure Revamp"},
    {"keyword": "Azure Kubernetes Service setup guide",          "category": "Infrastructure Revamp"},
    {"keyword": "Azure DevOps CI CD pipeline setup guide",       "category": "Infrastructure Revamp"},
    {"keyword": "Microsoft Intune MDM setup SMB",                "category": "Infrastructure Revamp"},
    {"keyword": "Azure Monitor Log Analytics setup guide",       "category": "Infrastructure Revamp"},
    {"keyword": "Microsoft Sentinel SIEM setup SMB",             "category": "Infrastructure Revamp"},
    {"keyword": "Azure Arc hybrid cloud management guide",       "category": "Infrastructure Revamp"},
    {"keyword": "Azure Container Apps deployment guide",         "category": "Infrastructure Revamp"},
    {"keyword": "Microsoft Defender for Business setup guide",   "category": "Infrastructure Revamp"},
    {"keyword": "Azure API Management setup guide",              "category": "Infrastructure Revamp"},
    {"keyword": "Azure Virtual Network setup guide SMB",         "category": "Infrastructure Revamp"},
    {"keyword": "Microsoft Purview compliance setup guide",      "category": "Infrastructure Revamp"},
    {"keyword": "Azure Logic Apps workflow automation guide",    "category": "Infrastructure Revamp"},
    {"keyword": "Azure Firewall setup and configuration guide",  "category": "Infrastructure Revamp"},
    {"keyword": "Azure DevTest Labs setup guide",                "category": "Infrastructure Revamp"},
    {"keyword": "Microsoft Entra Privileged Identity Management","category": "Infrastructure Revamp"},
]

# ── DataForSEO helper ─────────────────────────────────────────────────────────

def fetch_volumes(keywords: list[str]) -> dict[str, dict]:
    """Return {keyword: {volume, competition}} from DataForSEO."""
    payload = json.dumps([{
        "keywords":      keywords,
        "language_name": "English",
        "location_name": "United States",
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
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DataForSEO HTTP {e.code}: {e.reason}\nResponse body: {body}\n\nCheck that DATAFORSEO_LOGIN is your account email and DATAFORSEO_PASSWORD is the API password from app.dataforseo.com → API Access.")
    if data.get("status_code") != 20000:
        raise RuntimeError(f"DataForSEO API error {data.get('status_code')}: {data.get('status_message')}")
    result = data["tasks"][0].get("result") or []
    return {r["keyword"]: r for r in result}


COMPETITION_SCORE = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, None: 2}

def opportunity_score(volume: int, competition: str) -> float:
    vol  = min(volume or 0, 10000)
    comp = COMPETITION_SCORE.get(competition, 2)
    return round((vol + 1) / comp, 1)


def build_queue(seeds: list[dict], volume_map: dict) -> list[dict]:
    rows = []
    for item in seeds:
        kw   = item["keyword"]
        data = volume_map.get(kw, {})
        vol  = data.get("search_volume") or 0
        comp = data.get("competition_level")
        rows.append({
            "keyword":     kw,
            "category":    item["category"],
            "volume":      vol,
            "competition": comp or "N/A",
            "score":       opportunity_score(vol, comp),
            "refreshed":   TODAY,
        })
    # Sort highest opportunity first within each category block,
    # then globally by score so generators pick best overall
    rows.sort(key=lambda r: r["score"], reverse=True)
    return rows


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    scripts_dir = os.path.dirname(os.path.abspath(__file__))

    # ── Generator 1 queue ─────────────────────────────────────────────────────
    print(f"Fetching volumes for {len(GEN1_SEEDS)} Gen-1 keywords...")
    kw1 = [s["keyword"] for s in GEN1_SEEDS]
    vol1 = fetch_volumes(kw1)
    queue1 = build_queue(GEN1_SEEDS, vol1)
    path1 = os.path.join(scripts_dir, "keyword_queue.json")
    with open(path1, "w", encoding="utf-8") as f:
        json.dump(queue1, f, indent=2)
    print(f"  Saved {len(queue1)} keywords -> {path1}")

    # ── Generator 2 queue ─────────────────────────────────────────────────────
    print(f"Fetching volumes for {len(GEN2_SEEDS)} Gen-2 MS keywords...")
    kw2 = [s["keyword"] for s in GEN2_SEEDS]
    vol2 = fetch_volumes(kw2)
    queue2 = build_queue(GEN2_SEEDS, vol2)
    path2 = os.path.join(scripts_dir, "ms_keyword_queue.json")
    with open(path2, "w", encoding="utf-8") as f:
        json.dump(queue2, f, indent=2)
    print(f"  Saved {len(queue2)} keywords -> {path2}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\nTop 5 Gen-1 opportunities:")
    for r in queue1[:5]:
        print(f"  [{r['category']}] {r['keyword']} — vol {r['volume']:,} | {r['competition']} | score {r['score']}")
    print("\nTop 5 Gen-2 MS opportunities:")
    for r in queue2[:5]:
        print(f"  [{r['category']}] {r['keyword']} — vol {r['volume']:,} | {r['competition']} | score {r['score']}")
    print(f"\nDone. Volumes are global (US market baseline). Next refresh: ~30 days ({TODAY})")


if __name__ == "__main__":
    main()
