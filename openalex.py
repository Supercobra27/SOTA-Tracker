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