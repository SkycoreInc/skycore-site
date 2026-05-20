"""
SkyCore Solutions — How-To Article Generator
Generates one SEO-optimized, schema-marked how-to article per run.

Improvements v2:
  - Fetches current official documentation before writing (accuracy, no stale UI refs)
  - CLI-first: PowerShell / Azure CLI / bash lead every step; GUI is secondary
  - Picks next unwritten keyword from the priority queue (highest volume first)

Requires env vars:
  GEMINI_API_KEY   — free at aistudio.google.com
  PEXELS_API_KEY   — free at pexels.com/api

Run:
  python scripts/generate_howto.py
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

# ── Keyword queue (ordered by opportunity score: volume / competition) ─────────

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
    {"keyword": "DMARC configuration step by step",           "category": "Security Hardening",   "volume": 140},
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

# ── Official doc sources per keyword ──────────────────────────────────────────
# Each entry lists 1-3 authoritative URLs to fetch for current accuracy.
# Prefer Microsoft Learn, NIST, CISA, GitHub Docs — stable, well-structured.

DOC_SOURCES = {
    "disaster recovery plan for small business": [
        "https://learn.microsoft.com/en-us/azure/site-recovery/site-recovery-overview",
        "https://learn.microsoft.com/en-us/azure/backup/backup-overview",
        "https://www.ready.gov/business-continuity-planning",
        "https://www.cisa.gov/resources-tools/resources/ransomware-guide",
        "https://csrc.nist.gov/publications/detail/sp/800-34/rev-1/final",
    ],
    "IT disaster recovery guide": [
        "https://learn.microsoft.com/en-us/azure/site-recovery/site-recovery-overview",
        "https://learn.microsoft.com/en-us/azure/backup/backup-overview",
        "https://www.ready.gov/business-continuity-planning",
        "https://csrc.nist.gov/publications/detail/sp/800-34/rev-1/final",
        "https://www.cisa.gov/resources-tools/resources/ransomware-guide",
    ],
    "zero trust network access implementation": [
        "https://learn.microsoft.com/en-us/security/zero-trust/zero-trust-overview",
        "https://learn.microsoft.com/en-us/entra/identity/conditional-access/overview",
        "https://csrc.nist.gov/publications/detail/sp/800-207/final",
        "https://www.cisa.gov/zero-trust-maturity-model",
        "https://www.cloudflare.com/learning/security/glossary/what-is-zero-trust/",
    ],
    "ransomware protection for small business": [
        "https://learn.microsoft.com/en-us/security/ransomware/human-operated-ransomware",
        "https://www.cisa.gov/resources-tools/resources/ransomware-guide",
        "https://www.cisa.gov/stopransomware",
        "https://www.cyber.gc.ca/en/guidance/ransomware-playbook-itsm00099",
        "https://www.ncsc.gov.uk/guidance/mitigating-malware-and-ransomware-attacks",
    ],
    "GitHub Actions CI CD pipeline setup": [
        "https://docs.github.com/en/actions/writing-workflows/quickstart",
        "https://docs.github.com/en/actions/about-github-actions/understanding-github-actions",
        "https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions",
        "https://learn.microsoft.com/en-us/azure/devops/pipelines/get-started/what-is-azure-pipelines",
        "https://www.redhat.com/en/topics/devops/what-is-ci-cd",
    ],
    "how to set up MFA for your organization": [
        "https://learn.microsoft.com/en-us/entra/identity/authentication/concept-mfa-howitworks",
        "https://learn.microsoft.com/en-us/entra/identity/authentication/howto-mfa-getstarted",
        "https://learn.microsoft.com/en-us/microsoft-365/admin/security-and-compliance/set-up-multi-factor-authentication",
        "https://www.cisa.gov/mfa",
        "https://pages.nist.gov/800-63-3/sp800-63b.html",
    ],
    "how to implement zero trust security": [
        "https://learn.microsoft.com/en-us/security/zero-trust/zero-trust-overview",
        "https://learn.microsoft.com/en-us/entra/identity/conditional-access/overview",
        "https://csrc.nist.gov/publications/detail/sp/800-207/final",
        "https://www.cisa.gov/zero-trust-maturity-model",
        "https://www.cloudflare.com/learning/security/glossary/what-is-zero-trust/",
    ],
    "PIPEDA compliance IT checklist": [
        "https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/",
        "https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/pipeda-compliance-help/",
        "https://learn.microsoft.com/en-us/compliance/regulatory/offering-pipeda",
        "https://www.cippic.ca/en/PIPEDA",
    ],
    "IT infrastructure modernization guide": [
        "https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/overview",
        "https://learn.microsoft.com/en-us/azure/architecture/framework/",
        "https://www.redhat.com/en/topics/cloud-native-apps/what-is-infrastructure-modernization",
        "https://aws.amazon.com/solutions/cloud-migration/",
        "https://cloud.google.com/solutions/migration-to-gcp-getting-started",
    ],
    "DMARC configuration step by step": [
        "https://learn.microsoft.com/en-us/defender-office-365/email-authentication-dmarc-configure",
        "https://learn.microsoft.com/en-us/defender-office-365/email-authentication-spf-configure",
        "https://learn.microsoft.com/en-us/defender-office-365/email-authentication-dkim-configure",
        "https://dmarc.org/overview/",
        "https://www.cloudflare.com/learning/email-security/dmarc-dkim-spf/",
    ],
    "Office 365 MFA setup guide": [
        "https://learn.microsoft.com/en-us/microsoft-365/admin/security-and-compliance/set-up-multi-factor-authentication",
        "https://learn.microsoft.com/en-us/entra/identity/authentication/howto-mfa-getstarted",
        "https://learn.microsoft.com/en-us/entra/identity/conditional-access/howto-conditional-access-policy-all-users-mfa",
        "https://www.cisa.gov/mfa",
        "https://pages.nist.gov/800-63-3/sp800-63b.html",
    ],
    "Windows Server hardening checklist": [
        "https://learn.microsoft.com/en-us/windows-server/security/security-and-assurance",
        "https://learn.microsoft.com/en-us/windows-server/security/windows-defender/windows-defender-overview-windows-server",
        "https://www.cisecurity.org/benchmark/microsoft_windows_server",
        "https://www.nsa.gov/Press-Room/News-Highlights/Article/Article/2959325/nsa-releases-guidance-on-hardening-microsoft-windows/",
        "https://www.cyber.gc.ca/en/guidance/network-security-configuration-windows-based-systems-itsb-89",
    ],
    "Azure MFA configuration guide": [
        "https://learn.microsoft.com/en-us/entra/identity/authentication/howto-mfa-getstarted",
        "https://learn.microsoft.com/en-us/entra/identity/conditional-access/howto-conditional-access-policy-all-users-mfa",
        "https://learn.microsoft.com/en-us/entra/identity/authentication/concept-mfa-howitworks",
        "https://www.cisa.gov/mfa",
        "https://pages.nist.gov/800-63-3/sp800-63b.html",
    ],
    "endpoint protection for small business": [
        "https://learn.microsoft.com/en-us/defender-endpoint/microsoft-defender-endpoint",
        "https://learn.microsoft.com/en-us/microsoft-365-business-premium/m365bp-set-up-unmanaged-devices",
        "https://www.cisa.gov/resources-tools/resources/endpoint-security-guide",
        "https://www.cyber.gc.ca/en/guidance/endpoint-security-guide",
        "https://www.ncsc.gov.uk/guidance/end-user-device-security",
    ],
    "cloud migration guide for SMB": [
        "https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/migrate/azure-migration-guide/",
        "https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/migrate/",
        "https://learn.microsoft.com/en-us/azure/migrate/migrate-services-overview",
        "https://aws.amazon.com/solutions/cloud-migration/",
        "https://cloud.google.com/solutions/migration-to-gcp-getting-started",
    ],
    "Exchange to Office 365 migration guide": [
        "https://learn.microsoft.com/en-us/exchange/mailbox-migration/mailbox-migration",
        "https://learn.microsoft.com/en-us/exchange/mailbox-migration/cutover-migration-to-office-365",
        "https://learn.microsoft.com/en-us/microsoft-365/admin/misc/set-up-dns-records-vsb",
        "https://learn.microsoft.com/en-us/exchange/mailbox-migration/migrate-mailboxes-across-tenants",
    ],
    "server hardening checklist": [
        "https://learn.microsoft.com/en-us/windows-server/security/security-and-assurance",
        "https://learn.microsoft.com/en-us/azure/security/fundamentals/network-best-practices",
        "https://www.cisecurity.org/benchmark/microsoft_windows_server",
        "https://www.nsa.gov/Press-Room/News-Highlights/Article/Article/2959325/nsa-releases-guidance-on-hardening-microsoft-windows/",
        "https://www.cyber.gc.ca/en/guidance/network-security-configuration-windows-based-systems-itsb-89",
    ],
    "Docker containerization tutorial": [
        "https://docs.docker.com/get-started/introduction/build-and-push-first-image/",
        "https://docs.docker.com/compose/gettingstarted/",
        "https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/",
        "https://kubernetes.io/docs/concepts/overview/",
        "https://www.redhat.com/en/topics/containers/what-is-docker",
    ],
    "Active Directory tiering best practices": [
        "https://learn.microsoft.com/en-us/security/privileged-access-workstations/privileged-access-access-model",
        "https://learn.microsoft.com/en-us/defender-for-identity/security-assessment-unsecure-account-attributes",
        "https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/plan/security-best-practices/best-practices-for-securing-active-directory",
        "https://www.cisa.gov/resources-tools/resources/active-directory-security",
        "https://www.cisecurity.org/benchmark/microsoft_windows_server",
    ],
    "how to configure DMARC DKIM SPF": [
        "https://learn.microsoft.com/en-us/defender-office-365/email-authentication-dmarc-configure",
        "https://learn.microsoft.com/en-us/defender-office-365/email-authentication-dkim-configure",
        "https://learn.microsoft.com/en-us/defender-office-365/email-authentication-spf-configure",
        "https://dmarc.org/overview/",
        "https://www.cloudflare.com/learning/email-security/dmarc-dkim-spf/",
    ],
    "on premise to Azure migration guide": [
        "https://learn.microsoft.com/en-us/azure/site-recovery/migrate-tutorial-on-premises-azure",
        "https://learn.microsoft.com/en-us/azure/migrate/migrate-services-overview",
        "https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/migrate/",
        "https://learn.microsoft.com/en-us/azure/virtual-machines/disks-migrate-windows-virtual-machine",
    ],
    "Office 365 migration step by step": [
        "https://learn.microsoft.com/en-us/exchange/mailbox-migration/mailbox-migration",
        "https://learn.microsoft.com/en-us/exchange/mailbox-migration/cutover-migration-to-office-365",
        "https://learn.microsoft.com/en-us/microsoft-365/admin/misc/set-up-dns-records-vsb",
        "https://learn.microsoft.com/en-us/microsoft-365/enterprise/migrate-data-to-office-365",
    ],
    "Azure AD Connect setup guide": [
        "https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/whatis-azure-ad-connect",
        "https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/how-to-connect-install-express",
        "https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/reference-connect-version-history",
        "https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/how-to-connect-sync-whatis",
    ],
    "CI CD pipeline setup for small teams": [
        "https://docs.github.com/en/actions/writing-workflows/quickstart",
        "https://learn.microsoft.com/en-us/azure/devops/pipelines/get-started/what-is-azure-pipelines",
        "https://docs.gitlab.com/ee/ci/introduction/",
        "https://www.redhat.com/en/topics/devops/what-is-ci-cd",
        "https://martinfowler.com/articles/continuousIntegration.html",
    ],
    "DevOps implementation for small business": [
        "https://learn.microsoft.com/en-us/azure/devops/pipelines/get-started/what-is-azure-pipelines",
        "https://docs.github.com/en/actions/about-github-actions/understanding-github-actions",
        "https://www.redhat.com/en/topics/devops/what-is-devops",
        "https://martinfowler.com/bliki/DevOpsCulture.html",
        "https://cloud.google.com/devops",
    ],
    "SQL Server to Azure migration guide": [
        "https://learn.microsoft.com/en-us/data-migration/",
        "https://learn.microsoft.com/en-us/azure/dms/dms-overview",
        "https://learn.microsoft.com/en-us/azure/azure-sql/migration-guides/database/sql-server-to-sql-database-overview",
        "https://learn.microsoft.com/en-us/sql/sql-server/migrate/guides/sql-server-to-sql-managed-instance-guide",
    ],
    "Azure backup setup guide": [
        "https://learn.microsoft.com/en-us/azure/backup/backup-overview",
        "https://learn.microsoft.com/en-us/azure/backup/quick-backup-vm-portal",
        "https://learn.microsoft.com/en-us/azure/backup/backup-azure-vms-introduction",
        "https://learn.microsoft.com/en-us/azure/backup/guidance-best-practices",
        "https://www.cisa.gov/resources-tools/resources/ransomware-guide",
    ],
    "physical server to Azure VM migration": [
        "https://learn.microsoft.com/en-us/azure/migrate/migrate-services-overview",
        "https://learn.microsoft.com/en-us/azure/site-recovery/migrate-tutorial-on-premises-azure",
        "https://learn.microsoft.com/en-us/azure/migrate/tutorial-assess-physical",
        "https://learn.microsoft.com/en-us/azure/migrate/tutorial-migrate-physical-virtual-machines",
    ],
    "how to harden Windows Server 2022": [
        "https://learn.microsoft.com/en-us/windows-server/security/security-and-assurance",
        "https://learn.microsoft.com/en-us/windows-server/security/windows-defender/windows-defender-overview-windows-server",
        "https://www.cisecurity.org/benchmark/microsoft_windows_server",
        "https://www.nsa.gov/Press-Room/News-Highlights/Article/Article/2959325/nsa-releases-guidance-on-hardening-microsoft-windows/",
        "https://www.cyber.gc.ca/en/guidance/network-security-configuration-windows-based-systems-itsb-89",
    ],
    "Azure conditional access setup guide": [
        "https://learn.microsoft.com/en-us/entra/identity/conditional-access/overview",
        "https://learn.microsoft.com/en-us/entra/identity/conditional-access/howto-conditional-access-policy-all-users-mfa",
        "https://learn.microsoft.com/en-us/entra/identity/conditional-access/concept-conditional-access-policy-common",
        "https://www.cisa.gov/mfa",
        "https://pages.nist.gov/800-63-3/sp800-63b.html",
    ],
}

# ── Fallback Unsplash photos by category ──────────────────────────────────────

FALLBACK_PHOTOS = {
    "Security Hardening":    "1550751827-4bd374c3f58b",
    "Cloud Migration":       "1451187580459-43490279c0fa",
    "Infrastructure Revamp": "1461749280684-dccba630e2f6",
    "IT Strategy":           "1558494949-ef010cbdcc31",
}

# ── Doc fetching ──────────────────────────────────────────────────────────────

def strip_html(html: str) -> str:
    """Remove HTML tags, collapse whitespace, return plain text."""
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
    """Fetch a documentation URL and return cleaned plain text, truncated."""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; SkyCore-Bot/1.0; research)",
        "Accept": "text/html,application/xhtml+xml",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        text = strip_html(resp.text)
        # Trim to max_chars at a sentence boundary
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
    """Fetch all doc sources for the keyword.
    Returns (combined_text, list_of_successfully_fetched_urls).
    """
    urls = DOC_SOURCES.get(keyword, [])
    if not urls:
        print("   No doc sources defined for this keyword — using Gemini training only")
        return "", []

    sections      = []
    fetched_urls  = []
    for url in urls:
        print(f"   Fetching: {url}")
        content = fetch_doc(url)
        if content:
            sections.append(f"SOURCE: {url}\n{content}")
            fetched_urls.append(url)
        time.sleep(1)  # polite crawling

    combined = "\n\n---\n\n".join(sections)
    print(f"   Fetched {len(fetched_urls)}/{len(urls)} docs, {len(combined):,} chars of reference material")
    return combined, fetched_urls


# ── Keyword / image helpers ───────────────────────────────────────────────────

def get_written_keywords() -> set:
    try:
        with open("how-to/posts.js", "r", encoding="utf-8") as f:
            content = f.read()
        return set(re.findall(r'keyword:\s*"([^"]+)"', content))
    except Exception:
        return set()


def get_used_image_urls() -> set:
    try:
        with open("how-to/posts.js", "r", encoding="utf-8") as f:
            content = f.read()
        return set(re.findall(r'image:\s*"([^"]+)"', content))
    except Exception:
        return set()


def pick_next_keyword() -> dict | None:
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
    pid   = FALLBACK_PHOTOS.get(category, "1558494949-ef010cbdcc31")
    hero  = f"https://images.unsplash.com/photo-{pid}?w=1400&auto=format&fit=crop&q=80"
    thumb = f"https://images.unsplash.com/photo-{pid}?w=800&auto=format&fit=crop&q=80"
    print(f"   Unsplash fallback: {pid}")
    return hero, thumb


# ── Article generation ────────────────────────────────────────────────────────

def generate_article(kw_item: dict, ref_docs: str, source_urls: list[str]) -> dict:
    keyword  = kw_item["keyword"]
    category = kw_item["category"]
    today    = date.today().isoformat()

    doc_section = ""
    if ref_docs:
        source_list = "\n".join(f"  - {u}" for u in source_urls)
        doc_section = f"""
REFERENCE DOCUMENTATION (fetched today from these authoritative sources):
{source_list}

Instructions for using this material:
- Synthesize across ALL sources — do not favour one vendor or one perspective
- Use exact command syntax, flag names, and parameter values from the docs
- Where sources differ, note it (e.g. "Microsoft recommends X; NIST SP 800-34 recommends Y")
- Do NOT copy-paste — extract the facts and write in SkyCore's voice
- Prefer commands over GUI steps wherever docs provide them
---
{ref_docs[:14000]}
---
"""

    prompt = textwrap.dedent(f"""
        You are a senior IT consultant at SkyCore Solutions, a global IT consulting firm
        specializing in Cloud Migration (Azure), Security Hardening, and Infrastructure Revamp.

        Write a comprehensive, authoritative how-to guide for this keyword:
        PRIMARY KEYWORD: "{keyword}"
        CATEGORY: {category}
        DATE: {today}
        {doc_section}

        CONTENT PHILOSOPHY:
        - CLI-FIRST: Every step leads with the PowerShell, Azure CLI, or bash command.
          GUI instructions are secondary, mentioned only as "or in the portal: ..." after
          the command. Readers are IT admins who prefer copy-paste over clicking.
        - ACCURATE: Use exact command syntax from the reference docs above (if provided).
          Include real flags and parameters, not just the bare minimum.
        - DIRECT: No fluff. No "in today's digital landscape." Get to the commands fast.
        - HONEST: Include real-world gotchas, common errors, and what to watch out for.
          If something is complex or risky in production, say so.
        - OPINIONATED: Tell readers what you actually recommend, not just what's possible.
        - LENGTH: 1,800-2,500 words of real substance.

        STRUCTURE (use these exact HTML elements):
        1. <div class="post-meta">{today} · READTIME · {category}</div>
        2. <h1>TITLE</h1>
        3. <div class="article-hero"><img src="HERO_IMAGE_PLACEHOLDER" alt="HERO_ALT_PLACEHOLDER" loading="eager" fetchpriority="high"></div>
        4. <div class="howto-intro"><p>Hook paragraph — state the problem, why this matters, what the reader will have working by the end. Include the primary keyword naturally.</p></div>
        5. <div class="howto-prereqs"><h4>Prerequisites</h4><ul>...</ul></div>
        6. Steps: use <h2>Step N: [Strong action verb + what exactly happens]</h2>
           - Each step: 1 paragraph context, then the command(s) in <pre><code class="language-powershell"> or <code class="language-bash"> or <code class="language-azurecli">
           - After commands: explain what each flag does (1 line each)
           - If there's a GUI alternative: <p class="gui-note"><strong>Portal alternative:</strong> ...</p>
           - End of step: expected output or how to confirm it worked
        7. <div class="howto-callout howto-callout--warning"><strong>Common pitfall:</strong> ...</div> — add 2-3 of these throughout
        8. <div class="howto-consultant-cta"><h3>When to bring in a consultant</h3><p>Be honest about when DIY becomes risky. This is a soft CTA, not a sales pitch.</p><a href="../contact.html" class="btn btn-primary">Book a free consultation</a></div>

        Return ONLY valid JSON (no markdown fences) with these exact fields:
        {{
          "slug": "seo-url-slug-4-6-words",
          "title": "Full compelling title including primary keyword",
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
          "htmlContent": "Full article HTML as described above."
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
            print(f"   Attempt {attempt} JSON parse failed: {e}")
            if attempt == 3:
                raise RuntimeError(f"Gemini returned invalid JSON after 3 attempts: {e}")
            prompt += "\n\nCRITICAL: JSON parse error. Escape ALL double quotes inside strings with \\\" — especially inside htmlContent."


# ── HTML builder ──────────────────────────────────────────────────────────────

def build_sources_html(source_urls: list[str]) -> str:
    """Build a small references section for the bottom of the article."""
    if not source_urls:
        return ""
    items = []
    for url in source_urls:
        # Derive a readable label from the URL domain + path
        domain = re.sub(r"^www\.", "", url.split("/")[2])
        path   = "/".join(url.split("/")[3:6]).strip("/")
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


def build_html(article: dict, hero_url: str, source_urls: list[str] | None = None) -> str:
    image_alt = article.get("imageAlt", article.get("imageQuery", "IT infrastructure guide"))
    content = (
        article["htmlContent"]
        .replace("HERO_IMAGE_PLACEHOLDER", hero_url)
        .replace("HERO_ALT_PLACEHOLDER", image_alt)
    )
    # Append sources section before closing article tag
    sources_html = build_sources_html(source_urls or [])
    if sources_html:
        content = content + sources_html
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
  <meta property="article:published_time" content="{article['date']}" />
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
        <div><h4>Contact</h4><ul><li><a href="mailto:info@skycoresolutions.com">info@skycoresolutions.com</a></li><li><a href="tel:+15145009562">(514) 500-9562</a></li><li style="color:var(--text-3);font-size:0.9rem;">Mon-Fri: 9AM-6PM EST</li><li style="color:var(--text-3);font-size:0.9rem;">24/7 Emergency Support</li></ul></div>
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
        print("All keywords written. Add more to KEYWORD_QUEUE.")
        return

    print(f"-- Next keyword: \"{kw_item['keyword']}\" ({kw_item['volume']:,}/mo) --")
    print(f"   Category: {kw_item['category']}")

    print("-- Fetching reference documentation --")
    ref_docs, source_urls = gather_reference_docs(kw_item["keyword"])

    print("-- Generating article via Gemini 2.5 Flash --")
    article = generate_article(kw_item, ref_docs, source_urls)
    print(f"   Slug:       {article['slug']}")
    print(f"   Title:      {article['title']}")
    print(f"   Difficulty: {article.get('difficulty')} | Time: {article.get('timeEstimate')}")
    print(f"   Steps:      {len(article.get('steps', []))}")

    hero_url, thumb_url = pick_photo(article.get("imageQuery", kw_item["keyword"]), kw_item["category"])
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
