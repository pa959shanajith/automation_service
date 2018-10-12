import requests
from pprint import pprint
r = requests.get("http://localhost:1990/")
r.json()