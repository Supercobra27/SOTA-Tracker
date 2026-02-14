"""
I have no idea what cursor was smoking
"""

import csv
import json
import re
import requests
from bs4 import BeautifulSoup

from company import Company
from skills_extractor import extract_skills_from_bullets
from qualifications_extractor import extract_qualifications_from_bullets
from profile_extractor import extract_profile_terms


# ---------------------------------------------------------------------------
# Section parsing (shared by HRT and others that use Responsibilities/Profile/Skills)
# ---------------------------------------------------------------------------

def parse_sections(text: str) -> dict[str, list[str]]:
    sections = {
        "intro": [],
        "responsibilities": [],
        "profile": [],
        "skills": [],
        "qualifications": [],
    }
    text = text.replace("\r", "")
    pattern = r"(Responsibilities|Profile|Skills|Qualifications)"
    parts = re.split(pattern, text, flags=re.I)
    # First segment (before any section header) is intro/profile text
    if parts and parts[0].strip():
        intro_lines = [
            line.strip("•- \n\t")
            for line in parts[0].split("\n")
            if line.strip()
        ]
        sections["intro"] = intro_lines
    for i in range(1, len(parts), 2):
        header = parts[i].strip().lower()
        block = parts[i + 1] if i + 1 < len(parts) else ""
        lines = [
            line.strip("•- \n\t")
            for line in block.split("\n")
            if line.strip()
        ]
        if header == "responsibilities":
            sections["responsibilities"] = lines
        elif header == "profile":
            sections["profile"] = lines
        elif header == "skills":
            sections["skills"] = lines
        elif header == "qualifications":
            sections["qualifications"] = lines
    # If we have intro but no explicit Profile section, use intro as profile content
    if sections["intro"] and not sections["profile"]:
        sections["profile"] = sections["intro"]
    return sections


# ---------------------------------------------------------------------------
# Hudson River Trading
# ---------------------------------------------------------------------------

HRT_AJAX_URL = "https://www.hudsonrivertrading.com/wp-admin/admin-ajax.php"

HRT_SETTING = {
    "meta_data": [
        {"icon": "", "term": "locations"},
        {"icon": "", "term": "job-category"},
        {"icon": "", "term": "job-type"},
    ],
    "settings": {"hide_job_id": True},
}

HRT_PAYLOAD = {
    "action": "get_hrt_jobs_handler",
    "data[search]": "",
    "setting": json.dumps(HRT_SETTING),
}

HRT_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.hudsonrivertrading.com/careers/",
    "X-Requested-With": "XMLHttpRequest",
}


class HRTCompany(Company):
    def __init__(self):
        super().__init__(name="Hudson River Trading", slug="hrt")

    def fetch_raw_jobs(self):
        r = requests.post(HRT_AJAX_URL, data=HRT_PAYLOAD, headers=HRT_HEADERS, timeout=30)
        r.raise_for_status()
        return r.json()

    def parse_job(self, raw: dict) -> dict:
        soup = BeautifulSoup(raw["content"], "html.parser")
        title_el = soup.select_one(".hrt-card-title")
        title = title_el.get_text(strip=True).replace("–", "-")
        url = title_el["href"]
        meta = [m.get_text(strip=True) for m in soup.select(".hrt-card-info-item span")]
        meta_str = " | ".join(meta)

        description = parse_sections(raw["description"])
        bullets = description["skills"]
        for i, item in enumerate(bullets):
            if "The estimated base salary range" in item:
                bullets = bullets[:i]
                break

        qual_bullets = description["qualifications"]
        for i, item in enumerate(qual_bullets):
            if "The estimated base salary range" in item or "benefits package" in item:
                qual_bullets = qual_bullets[:i]
                break

        # Profile: explicit section or intro paragraph
        profile_lines = description["profile"] or description["intro"]

        return {
            "title": title,
            "url": url,
            "meta": meta_str,
            "skill_bullets": bullets,
            "qualification_bullets": qual_bullets,
            "profile_lines": profile_lines,
        }


# ---------------------------------------------------------------------------
# Storage: jobs.csv (id, company, title, url, meta) + job_skills.csv (job_id, skill, category)
# ---------------------------------------------------------------------------

def write_jobs_and_skills(
    jobs: list[dict],
    jobs_path: str = "data/jobs.csv",
    job_skills_path: str = "data/job_skills.csv",
    job_qualifications_path: str = "data/job_qualifications.csv",
    job_profile_path: str = "data/job_profile.csv",
) -> None:
    """
    Assign each job an id, write jobs and correlation CSVs.
    Jobs must have: company, title, url, meta, skill_bullets, qualification_bullets, profile_lines.
    """
    job_rows = []
    skill_rows = []
    qualification_rows = []
    profile_rows = []

    for job_id, job in enumerate(jobs, start=1):
        job_rows.append({
            "id": job_id,
            "company": job["company"],
            "title": job["title"],
            "url": job["url"],
            "meta": job["meta"],
        })
        for e in extract_skills_from_bullets(job.get("skill_bullets") or []):
            skill_rows.append({"job_id": job_id, "skill": e["skill"], "category": e["category"]})
        for e in extract_qualifications_from_bullets(job.get("qualification_bullets") or []):
            qualification_rows.append({
                "job_id": job_id,
                "qualification": e["qualification"],
                "category": e["category"],
            })
        for e in extract_profile_terms(job.get("profile_lines") or []):
            profile_rows.append({
                "job_id": job_id,
                "term": e["term"],
                "category": e["category"],
            })

    with open(jobs_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "company", "title", "url", "meta"])
        writer.writeheader()
        writer.writerows(job_rows)

    with open(job_skills_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["job_id", "skill", "category"])
        writer.writeheader()
        writer.writerows(skill_rows)

    with open(job_qualifications_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["job_id", "qualification", "category"])
        writer.writeheader()
        writer.writerows(qualification_rows)

    with open(job_profile_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["job_id", "term", "category"])
        writer.writeheader()
        writer.writerows(profile_rows)

    print(
        f"Wrote {len(job_rows)} jobs to {jobs_path}; "
        f"{len(skill_rows)} skills, {len(qualification_rows)} qualifications, {len(profile_rows)} profile terms"
    )


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    companies = [HRTCompany()]
    all_jobs = []
    for company in companies:
        jobs = company.get_jobs()
        all_jobs.extend(jobs)
        print(f"[{company.slug}] {len(jobs)} jobs")

    write_jobs_and_skills(all_jobs)
