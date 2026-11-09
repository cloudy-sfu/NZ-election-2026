import json
import logging
import re
import sqlite3
import sys

import pandas as pd
from bs4 import BeautifulSoup
from requests import Session
from tqdm import tqdm
import time
import random

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
with sqlite3.connect("main.sqlite") as c:
    electorates_id = pd.read_sql("select slug from electorates_rnz_preliminary", c)
electorates_id = electorates_id["slug"]


# Ref: https://react.dev/reference/rsc/server-components
def find_key_in_tree(node, target_key):
    if isinstance(node, dict):
        if target_key in node and isinstance(node[target_key], list):
            return node[target_key]
        for value in node.values():
            result = find_key_in_tree(value, target_key)
            if result is not None:
                return result
    elif isinstance(node, list):
        for item in node:
            result = find_key_in_tree(item, target_key)
            if result is not None:
                return result
    return None


session = Session()
party_ = []
for electorate_id in tqdm(electorates_id):
    electorate_response = session.get(
        f"https://www.rnz.co.nz/news/election-2026-results/electorate/{electorate_id}")
    if electorate_response.status_code != 200:
        logging.warning(f"Fail to fetch electorate {electorate_id}.")
        continue
    vote_page = BeautifulSoup(electorate_response.text, "html.parser")

    party_vote_script = vote_page.find("script", string=re.compile(r"\\\"parties\\\""))
    party_vote_pushed = party_vote_script.text.lstrip("self.__next_f.push(").rstrip(")")
    party_vote_pushed = json.loads(party_vote_pushed)
    match = re.match(r"\d+:(.*)", party_vote_pushed[1])
    if match is None:
        logging.warning(f"Fail to parse party votes results of {electorate_id}.")
        continue
    party_vote_json = match.group(1)
    if party_vote_json is None:
        logging.warning(f"Fail to parse party votes results of {electorate_id}.")
        continue
    party_vote_json = json.loads(party_vote_json)
    party_vote = find_key_in_tree(party_vote_json, "parties")
    if not isinstance(party_vote, list):
        logging.warning(f"Fail to parse party votes results of {electorate_id}.")
        continue
    party_vote = pd.json_normalize(party_vote, sep="_")

    party = party_vote[["partyId", "party_displayName", "party_shortDisplayName",
                        "party_colour"]]
    party_.append(party)
    time.sleep(round(random.uniform(0.7, 1.3), 1))

party_ = pd.concat(party_, axis=0)
party_ = party_.drop_duplicates(subset=["partyId"], ignore_index=True)

with sqlite3.connect("main.sqlite") as c:
    party_.to_sql("parties_rnz", c, if_exists="replace", index=False)
