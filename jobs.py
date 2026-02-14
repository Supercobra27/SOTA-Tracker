import requests
import json
from bs4 import BeautifulSoup
import csv
import re

# should expand this to OUTSIDE of quant

class JobBoardURL():
    def __init__(self):
        pass

urls = ['https://www.hudsonrivertrading.com/wp-admin/admin-ajax.php',
        'https://www.jumptrading.com/hr/experienced-candidates',
        'https://www.jumptrading.com/hr/students-new-grads',
        'https://www.janestreet.com/join-jane-street/open-roles/?type=experienced-candidates&location=all-locations',
        'https://www.janestreet.com/join-jane-street/open-roles/?type=students-and-new-grads&location=all-locations&department=all-departments',
        'https://www.realtimerisksystems.com/']

setting = {
    "meta_data": [
        {"icon": "", "term": "locations"},
        {"icon": "", "term": "job-category"},
        {"icon": "", "term": "job-type"}
    ],
    "settings": {"hide_job_id": True}
}

payload = {
    "action": "get_hrt_jobs_handler",
    "data[search]": "",
    "setting": json.dumps(setting)
}

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.hudsonrivertrading.com/careers/",
    "X-Requested-With": "XMLHttpRequest"
}

r = requests.post(urls[0], data=payload, headers=headers)

jobs_json = r.json()

rows = []

def parse_sections(text):
    sections = {
        "responsibilities": [],
        "profile": [],
        "skills": []
    }

    text = text.replace("\r", "")
    
    pattern = r"(Responsibilities|Profile|Skills)"
    parts = re.split(pattern, text)

    for i in range(1, len(parts), 2):
        header = parts[i].lower()
        block = parts[i+1]

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

    return sections

def get_hrt_job():
    for job in jobs_json:
        soup = BeautifulSoup(job["content"], "html.parser")

        title = soup.select_one(".hrt-card-title").get_text(strip=True)
        url = soup.select_one(".hrt-card-title")["href"]

        meta = [m.get_text(strip=True)
                for m in soup.select(".hrt-card-info-item span")]
        
        description = parse_sections(job["description"])
        
        for i, item in enumerate(description["skills"]):
            if 'The estimated base salary range' in item:
                description["skills"] = description["skills"][:i]
        
        print(description["skills"])
        exit()

        rows.append({
            "title": title.replace('–', '-'),
            "url": url,
            "meta": " | ".join(meta)
        })


    # export to CSV
    with open("hrt_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "url", "meta"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"saved {len(rows)} jobs to hrt_jobs.csv")
    
get_hrt_job()
    
# print(requests.get('https://www.hudsonrivertrading.com/hrt-job/hpc-network-engineer-4/').text)