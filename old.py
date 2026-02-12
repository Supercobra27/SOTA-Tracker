import requests
from bs4 import BeautifulSoup
import json
import math
import pandas as pd

def flatten(xss):
    return [x for xs in xss for x in xs]

BASE_URL = "https://api.openalex.org"
WORKS = "/works"
TOPICS = "/topics"
PAGE_QUERY = "&page="
PERPAGE_QUERY = "&per_page="
API_KEY = "&api_key="
TEST_URL = "https://api.openalex.org/works/https://doi.org/10.48550/arXiv.2408.14090"

url = f"{BASE_URL}/works?filter=primary_topic.id:T10054,best_oa_location.source.id:S4306400194,publication_year:%3E2024"

curr_dom = 2

meta = json.loads(requests.get(f"{BASE_URL}{TOPICS}?filter=domain.id:{curr_dom}").content)["meta"]
per_page_url = int(math.ceil(float(int(meta["count"]) / 10)))
print(per_page_url)

big_data = []
big_names = []
for i in range(1, 11):
    url = f"{BASE_URL}{TOPICS}?filter=domain.id:{curr_dom}{PAGE_QUERY}{i}{PERPAGE_QUERY}{per_page_url}{API_KEY}"
    print(url)
    req = requests.get(url).content
    data = json.loads(req)["results"]
    data_ids = [d["id"].replace("https://openalex.org/", "") for d in data]
    data_names = [d["display_name"] for d in data]
    big_data.append(data_ids)
    big_names.append(data_names)

big_data = flatten(big_data) 
big_names = flatten(big_names)
big_data = pd.DataFrame(big_data)
big_data.columns = ["id"]
big_names = pd.DataFrame(big_names)
big_names.columns = ["id"]
big_data.to_csv(f"topics{curr_dom}.csv")
big_names.to_csv(f"topics_display_names{curr_dom}.csv")

topics = pd.read_csv(f"topics{curr_dom}.csv")
topics_dn = pd.read_csv(f"topics_display_names{curr_dom}.csv")
merged = topics.merge(topics_dn, on="", suffixes=("_name", "_topic"))

merged.to_csv(f"merged_{curr_dom}.csv", index=False)
