import json
import re
import sqlite3

import pandas as pd
from bs4 import BeautifulSoup
from requests import Session

# %% Initialize.
session = Session()

# %% Get electorate list.
electorates_response = session.get(
    "https://www.rnz.co.nz/news/election-2026-results/electorates")
electorates_response.raise_for_status()
electorates_page = BeautifulSoup(electorates_response.text, "html.parser")

# %% Parse electorates table.
all_electorates_script = electorates_page.find(
    "script", string=re.compile(r"\\\"id\\\":\\\"all-electorates\\\""))
all_electorates_pushed = \
    all_electorates_script.text.lstrip("self.__next_f.push(").rstrip(")")
all_electorates_pushed = json.loads(all_electorates_pushed)
match = re.match(r"\d+:(.*)", all_electorates_pushed[1])
if match is None:
    raise Exception("Fail to parse electorates list.")
all_electorates_json = match.group(1)
if all_electorates_json is None:
    raise Exception("Fail to parse electorates list.")
all_electorates_json = json.loads(all_electorates_json)
all_electorates = all_electorates_json[3]["children"][3]["electorates"]
all_electorates = pd.DataFrame(all_electorates)
all_electorates = all_electorates[["slug", "name", "isMaori"]]
all_electorates = all_electorates.drop_duplicates(subset=["slug"], ignore_index=True)

# %% Export.
with sqlite3.connect("main.sqlite") as c:
    all_electorates.to_sql(
        "electorates_rnz_preliminary", c, if_exists="replace", index=False)
