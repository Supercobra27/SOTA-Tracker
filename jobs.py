import requests
import json
from bs4 import BeautifulSoup
import csv
import re

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


def get_hrt_job(jobs_json):
    for job in jobs_json:
        soup = BeautifulSoup(job["content"], "html.parser")

        title = soup.select_one(".hrt-card-title").get_text(strip=True)
        url = soup.select_one(".hrt-card-title")["href"]
        meta = [m.get_text(strip=True)
                for m in soup.select(".hrt-card-info-item span")]
        
        headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Referer": "https://www.hudsonrivertrading.com/",
        }
        
        job_desc = requests.get('https://job-boards.greenhouse.io/embed/job_app?for=wehrtyou&token=7584240', headers=headers)
        job_soup = BeautifulSoup(job_desc.content, "html.parser").get_text()
        job_soup = re.split(r'Responsibilities|Qualifications|The estimated base salary range', job_soup)[1:-1]
        job_soup = [j.replace('\n', ' ').strip() for j in job_soup]
        print(job_soup)
        exit()

get_hrt_job(jobs_json)