"""
Extract distinctive terms from job profile / intro paragraph(s).

Captures role type, technologies, work arrangement (hybrid, remote).
"""

import re
from typing import Sequence

# ---------------------------------------------------------------------------
# Profile lexicons
# ---------------------------------------------------------------------------

WORK_ARRANGEMENT = {
    "hybrid", "remote", "flexible", "in-office", "on-site", "distributed",
    "work from home", "WFH", "in-person",
}

ROLE_KEYWORDS = {
    "engineer", "developer", "architect", "analyst", "scientist", "researcher",
    "lead", "manager", "specialist", "administrator", "consultant",
}

# Tech/tools that often appear in intro
PROFILE_TECH = {
    "Lustre", "CI/CD", "Python", "C++", "Linux", "kernel", "Jira",
    "filesystem", "core dump", "packages", "upstream",
}

LIST_LIKE = [
    re.compile(r"\b(?:with|using|including)\s+([^.]+?)(?:\.|$)", re.I),
    re.compile(r"\b(?:experience with|experience in)\s+([^.]+?)(?:\.|$)", re.I),
]


def _normalize(s: str) -> str:
    return s.strip()


def extract_profile_terms(profile_lines: Sequence[str]) -> list[dict]:
    """
    From profile intro text (list of lines or one string), extract terms.
    Returns list of {"term": str, "category": str}.
    Categories: work_arrangement, role, technology, other.
    """
    text = "\n".join(profile_lines) if isinstance(profile_lines, (list, tuple)) else profile_lines
    if not text or not text.strip():
        return []

    seen = set()
    result: list[dict] = []

    def add(s: str, category: str):
        s = _normalize(s)
        if not s or len(s) > 80:
            return
        key = (s.lower(), category)
        if key in seen:
            return
        seen.add(key)
        result.append({"term": s, "category": category})

    # 1) Work arrangement
    for w in WORK_ARRANGEMENT:
        if re.search(rf"\b{re.escape(w)}\b", text, re.I):
            add(w, "work_arrangement")

    # 2) Role-ish phrases (e.g. "Lustre Engineer")
    for r in ROLE_KEYWORDS:
        if re.search(rf"\b\w+\s+{re.escape(r)}\b", text, re.I):
            # Capture "X Engineer" / "Y Architect"
            for m in re.finditer(rf"(\w+\s+{re.escape(r)})", text, re.I):
                add(m.group(1), "role")

    # 3) Tech in profile
    for t in PROFILE_TECH:
        if re.search(rf"\b{re.escape(t)}\b", text, re.I):
            add(t, "technology")

    # 4) Common tech phrases
    if "Lustre" in text or "lustre" in text:
        add("Lustre", "technology")
    if re.search(r"CI/CD", text, re.I):
        add("CI/CD", "technology")
    if re.search(r"core dump", text, re.I):
        add("core dump", "technology")
    if re.search(r"filesystem", text, re.I):
        add("filesystem", "technology")

    return result
