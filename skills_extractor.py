"""
Extract distinctive skills from job-description bullets for storage and analysis.

Takes parsed "skills" bullets (e.g. from jobs.parse_sections) and produces
normalized skill tokens suitable for CSV/DB: technologies, protocols, tools,
languages, clouds, vendors, and high-level categories.
"""

import re
from typing import Sequence

# ---------------------------------------------------------------------------
# Skill lexicons: normalized name -> category (for matching in prose)
# ---------------------------------------------------------------------------

PROTOCOLS = {
    "OSPF", "BGP", "PIM", "IGMP", "RoCEv2", "VXLAN", "TCP", "UDP", "HTTP",
    "HTTPS", "DNS", "SNMP", "LLDP", "LACP", "STP", "RSTP", "MLAG",
}

TOOLS = {
    "tcpdump", "Wireshark", "Ansible", "Salt", "Prometheus", "Grafana",
    "ELK", "GitHub", "Git", "Wireshark", "pcap",
}

LANGUAGES = {
    "Python", "C++", "C", "Rust", "Go", "Java", "JavaScript", "TypeScript",
    "Bash", "Shell", "SQL",
}

CLOUDS = {
    "AWS", "GCP", "Azure", "GCP", "Google Cloud", "Azure",
}

VENDORS_PLATFORMS = {
    "Arista", "EOS", "Cisco", "NX-OS", "Nvidia", "Cumulus", "SONiC",
    "Juniper", "Linux", "Unix",
}

# Combined set for "mentioned in text" lookup (lowercase for matching)
ALL_KNOWN_SKILLS = (
    {s.lower() for s in PROTOCOLS}
    | {s.lower() for s in TOOLS}
    | {s.lower() for s in LANGUAGES}
    | {s.lower() for s in CLOUDS}
    | {s.lower() for s in VENDORS_PLATFORMS}
)


def _normalize(s: str) -> str:
    return s.strip()


def _category(s: str) -> str:
    s_lower = s.lower()
    if s_lower in {x.lower() for x in PROTOCOLS}:
        return "protocol"
    if s_lower in {x.lower() for x in TOOLS}:
        return "tool"
    if s_lower in {x.lower() for x in LANGUAGES}:
        return "language"
    if s_lower in {x.lower() for x in CLOUDS}:
        return "cloud"
    if s_lower in {x.lower() for x in VENDORS_PLATFORMS}:
        return "vendor_platform"
    return "other"


# Patterns to pull listed items out of prose
LIST_PATTERNS = [
    # "such as X, Y, and Z" or "such as X, Y, Z"
    re.compile(r"\bsuch as\s+([^.]+?)(?:\.|$)", re.I),
    # "X, Y, and Z" in parentheses
    re.compile(r"\(([^)]+)\)"),
    # "e.g. X, Y, Z"
    re.compile(r"\be\.g\.\s*([^.]+?)(?:\.|$)", re.I),
    # "including X, Y, Z"
    re.compile(r"\bincluding\s+([^.]+?)(?:\.|$)", re.I),
]


def _split_list_phrase(phrase: str) -> list[str]:
    """Split a phrase like 'X, Y, and Z' or 'X, Y or Z' into tokens."""
    phrase = phrase.strip()
    # Normalize " and " / " or " to comma for split
    phrase = re.sub(r"\s+and\s+", ", ", phrase, flags=re.I)
    phrase = re.sub(r"\s+or\s+", ", ", phrase, flags=re.I)
    parts = [p.strip() for p in re.split(r",", phrase) if p.strip()]
    return parts


def extract_skills_from_bullets(bullets: Sequence[str]) -> list[dict]:
    """
    From a list of skill bullets (long prose strings), extract distinctive
    skill tokens with category. Returns list of {"skill": str, "category": str}.
    """
    seen = set()
    result: list[dict] = []

    def add(s: str):
        s = _normalize(s)
        if not s or len(s) > 80:
            return
        key = s.lower()
        if key in seen:
            return
        seen.add(key)
        result.append({"skill": s, "category": _category(s)})

    for bullet in bullets:
        if not bullet or "base salary" in bullet.lower():
            continue
        text = bullet

        # 1) Mentioned known skills (whole-word)
        for skill in PROTOCOLS | TOOLS | LANGUAGES | CLOUDS | VENDORS_PLATFORMS:
            if skill in {"GCP", "Google Cloud"} and "Google Cloud" in text and "GCP" not in text:
                add("GCP")
                continue
            # Prefer whole-word or immediately after punctuation
            if re.search(rf"\b{re.escape(skill)}\b", text, re.I):
                add(skill)

        # 2) Listed items from patterns
        for pat in LIST_PATTERNS:
            for m in pat.finditer(text):
                phrase = m.group(1).strip()
                # Trim trailing sentence (e.g. "Ansible or Salt is desirable...")
                phrase = re.split(r"\s+is\s+|\s+to\s+support\s+|\s+for\s+", phrase, maxsplit=1)[0].strip()
                for token in _split_list_phrase(phrase):
                    # Filter to likely skills: not pure sentence fragments
                    if any(c.isdigit() for c in token) and len(token) < 4:
                        continue
                    if token.lower() in ("e.g", "etc", "and", "or", "such as"):
                        continue
                    if re.search(r"\b(is|to|for|with|in|and|or)\b", token, re.I) and len(token) > 25:
                        continue
                    add(token)

    return result


def extract_skill_tokens_only(bullets: Sequence[str]) -> list[str]:
    """Convenience: return just the skill strings (no category)."""
    return [x["skill"] for x in extract_skills_from_bullets(bullets)]


# ---------------------------------------------------------------------------
# Helpers (job–skill correlation is done in jobs.write_jobs_and_skills)
# ---------------------------------------------------------------------------

def enrich_job_with_skills(
    job: dict,
    bullets_key: str = "skills_bullets",
    skills_key: str = "skills",
    categories_key: str = "skill_categories",
) -> dict:
    """
    Given a job dict that has bullets_key (list of skill bullets), add
    skills_key (list of tokens) and optionally categories_key (skill -> category).
    """
    bullets = job.get(bullets_key) or job.get("skills_raw") or []
    if isinstance(bullets, str):
        bullets = [b.strip() for b in bullets.split("\n") if b.strip()]
    extracted = extract_skills_from_bullets(bullets)
    job = dict(job)
    job[skills_key] = [e["skill"] for e in extracted]
    job[categories_key] = {e["skill"]: e["category"] for e in extracted}
    return job


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    example_bullets = [
        "Excellent oral and written communication skills: able to distill complicated issues into clear and concise terms",
        "Able to create and maintain clear and effective technical documentation",
        "In depth understanding of common layer 2 and layer 3 network protocols (OSPF, BGP, PIM, IGMP, RoCEv2, spine-leaf architecture, and VXLAN) and best practices for them",
        "Proven ability to select and work with vendors to engineer switches for next-generation computing environments",
        "Experience managing Arista (EOS), Cisco (NX-OS), Nvidia (Cumulus) and SONiC-based switches, as well as an interest in exploring new platforms",
        "Strong design skills in computing and grid networks, with expertise in capacity planning, and full lifecycle project management",
        "Experience with packet decoding and analysis tools such as tcpdump and Wireshark",
        "Experience with public cloud networks, such as AWS, GCP, Azure",
        "Familiarity with configuration management tools, such as Ansible or Salt is desirable to support zero-touch network management",
        "Familiarity with Python, Prometheus, Grafana, ELK, GitHub is desirable",
        "Understanding of basic power consumption and cooling issues in a data center environment",
        "Knowledge of fiber optics technology and cabling standards ranging from 1 to 800 Gbps. Ability to sort through specs and make recommendations on appropriate purchases.",
        "Skilled in Unix/Linux command line utilities and networking stack",
        "Experience with AI style network designs and workloads is preferred",
    ]

    extracted = extract_skills_from_bullets(example_bullets)
    print("Extracted skills (skill, category):")
    for e in extracted:
        print(f"  {e['skill']!r} -> {e['category']}")

    tokens = extract_skill_tokens_only(example_bullets)
    print("\nTokens only:", tokens)
