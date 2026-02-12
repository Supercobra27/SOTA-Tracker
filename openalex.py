import requests
from bs4 import BeautifulSoup
import json
import math
import pandas as pd
from pydantic import BaseModel
import ddd

def flatten(xss):
    return [x for xs in xss for x in xs]

BASE_URL = "https://api.openalex.org"
WORKS = "/works"
TOPICS = "/topics"
PAGE_QUERY = "&page="
PERPAGE_QUERY = "&per_page="
API_KEY = "&api_key="

keywords = ["Parallel", "Interconnect", "Computing", "Technology", "Optic", "Photonic"]

pattern = r"Parallel|Interconnect|Computing|Technology|Optic|Photonic|Network"
pattern = r"Parallel|Interconnect"

df = pd.read_csv("data/merged_3.csv")
df = df[df["id_topic"].str.contains(pattern, case=False, na=False)]

df2 = dict(zip(df["id_topic"], df["id_name"]))
print(df2)

for id in set(df["id_name"]):
    data = json.loads(requests.get(f"{BASE_URL}/works?filter=primary_topic.id:{id},best_oa_location.source.id:S4306400194,publication_year:%3E2024").content)
    count = data["meta"]["count"]
    print(count)