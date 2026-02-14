"""
Extract distinctive qualifications from job-description bullets.

Produces normalized tokens: degrees, fields, technologies, soft skills.
"""

import re
from typing import Sequence

# Reuse tech lexicons from skills_extractor for consistency
from skills_extractor import (
    LANGUAGES,
    TOOLS,
    PROTOCOLS,
    VENDORS_PLATFORMS,
)

# ---------------------------------------------------------------------------
# Qualification-specific lexicons
# ---------------------------------------------------------------------------

DEGREES = {
    "Bachelor's", "Bachelors", "Bachelor", "BS", "B.S.", "BA", "B.A.",
    "Master's", "Masters", "Master", "MS", "M.S.", "MA", "M.A.", "MSc", "MSc.",
    "PhD", "Ph.D.", "Doctorate", "MBA", "M.B.A.",
}

FIELDS = {
    "Computer Science", "Engineering", "Electrical Engineering", "EE",
    "Computer Engineering", "Mathematics", "Physics", "Related field",
    "STEM", "Statistics", "Data Science",
}

SOFT_SKILLS = {
    "communication", "written communication", "verbal communication",
    "multitasking", "time management", "work independently", "collaborate",
    "collaboration", "teamwork", "problem solving", "analytical",
    "attention to detail", "leadership", "self-starter", "motivated",
    "organizational skills", "prioritization", "stakeholder",
    "technical writing", "documentation", "explain", "mentoring",
}

# Technologies that often appear in qualifications (add to skills lexicons)
QUALIFICATION_TECH = {
    "Lustre", "CI/CD", "Jira", "Linux", "kernel", "Python", "C++", "C",
}

LIST_PATTERNS = [
    re.compile(r"\b(?:degree|in)\s+([^.]+?)(?:\.|$)", re.I),
    re.compile(r"\(([^)]+)\)"),
    re.compile(r"\b(?:experience with|working with|experience in)\s+([^.]+?)(?:\.|$)", re.I),
    re.compile(r"\bsuch as\s+([^.]+?)(?:\.|$)", re.I),
]


def _normalize(s: str) -> str:
    return s.strip()


def _split_list_phrase(phrase: str) -> list[str]:
    phrase = phrase.strip()
    phrase = re.sub(r"\s+and\s+", ", ", phrase, flags=re.I)
    phrase = re.sub(r"\s+or\s+", ", ", phrase, flags=re.I)
    parts = [p.strip() for p in re.split(r",", phrase) if p.strip()]
    return parts


def _category_qualification(token: str) -> str:
    t_lower = token.lower()
    if t_lower in {d.lower() for d in DEGREES} or re.match(r"^B\.?S\.?$|^M\.?S\.?$|^Ph\.?D\.?$", token, re.I):
        return "degree"
    if t_lower in {f.lower() for f in FIELDS} or "engineering" in t_lower or "computer science" in t_lower:
        return "field"
    if t_lower in {s.lower() for s in SOFT_SKILLS} or any(ss in t_lower for ss in SOFT_SKILLS):
        return "soft_skill"
    if t_lower in {x.lower() for x in LANGUAGES} | {x.lower() for x in TOOLS} | {x.lower() for x in QUALIFICATION_TECH}:
        return "technology"
    if t_lower in {x.lower() for x in PROTOCOLS} | {x.lower() for x in VENDORS_PLATFORMS}:
        return "technology"
    if re.search(r"experience|years?|working with", t_lower) and len(token) < 50:
        return "experience"
    return "other"


def extract_qualifications_from_bullets(bullets: Sequence[str]) -> list[dict]:
    """
    From a list of qualification bullets, extract distinctive tokens.
    Returns list of {"qualification": str, "category": str}.
    Drops salary/benefits lines.
    """
    seen = set()
    result: list[dict] = []

    def add(s: str):
        s = _normalize(s)
        if not s or len(s) > 100:
            return
        if "base salary" in s.lower() or "benefits" in s.lower() or "vacation" in s.lower():
            return
        # Drop list-artifact fragments
        if s.lower().startswith("in ") or s.lower() in ("a related field", "or a related field"):
            return
        key = s.lower()
        if key in seen:
            return
        seen.add(key)
        result.append({"qualification": s, "category": _category_qualification(s)})

    for bullet in bullets:
        if not bullet:
            continue
        text = bullet
        if "estimated base salary" in text.lower() or "benefits package" in text.lower():
            continue

        # 1) Degrees
        for d in DEGREES:
            if re.search(rf"\b{re.escape(d)}\b", text, re.I):
                add(d)

        # 2) Fields (degree in X, Y, or Z)
        for f in FIELDS:
            if re.search(rf"\b{re.escape(f)}\b", text, re.I):
                add(f)

        # 3) Soft skills
        for ss in SOFT_SKILLS:
            if ss in text.lower():
                add(ss)

        # 4) Tech from qualifications (LANGUAGES, TOOLS, QUALIFICATION_TECH, etc.)
        all_tech = LANGUAGES | TOOLS | QUALIFICATION_TECH
        for tech in all_tech:
            if re.search(rf"\b{re.escape(tech)}\b", text, re.I):
                add(tech)

        # 5) "Experience working with X or Y" / "degree in X, Y, or Z"
        for pat in LIST_PATTERNS:
            for m in pat.finditer(text):
                phrase = m.group(1).strip()
                phrase = re.split(r"\s+is\s+|\s+to\s+|\s+for\s+", phrase, maxsplit=1)[0].strip()
                for token in _split_list_phrase(phrase):
                    if len(token) < 2 or len(token) > 60:
                        continue
                    if token.lower() in ("e.g", "etc", "and", "or", "such as", "related"):
                        continue
                    add(token)

    return result
