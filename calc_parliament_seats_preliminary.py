import sqlite3

import numpy as np
import pandas as pd

# %% Read data.
with open("sqls/party_votes.sql") as f:
    sql_party_votes = f.read()
with open("sqls/party_electorate_seats.sql") as f:
    sql_electorate_seats = f.read()
with open("sqls/party_names.sql") as f:
    sql_party_names = f.read()
with sqlite3.connect("main.sqlite") as c:
    party_votes = pd.read_sql(sql_party_votes, c)
    electorate_seats = pd.read_sql(sql_electorate_seats, c)
    party_names = pd.read_sql(sql_party_names, c, index_col="party_id")

# %% Calc seats pool.
ind_mask = electorate_seats["party_id"].isna()
ind_seats = electorate_seats.loc[ind_mask, "electorate_seats"].sum()
party_electorate_seats = electorate_seats.loc[~ind_mask, :].set_index("party_id")
party_seats = 120 - ind_seats
n_electorate = electorate_seats["electorate_seats"].sum()
assert n_electorate <= party_seats, \
    ("New Zealand 2026 parliament seats allocation algorithm cannot be migrated to "
     "a case where number of electorates larger than number of parliament seats.")

# %% Calc eligible parties.
sum_votes = party_votes["votes"].sum()
eligible_parties_id_votes = set(
    party_votes.loc[20 * party_votes["votes"] >= sum_votes, "party_id"])
eligible_parties_id_electorates = set(party_electorate_seats.index)
eligible_parties_id = eligible_parties_id_electorates | eligible_parties_id_votes

# %% Calc list seats.
eligible_parties_votes = party_votes.loc[
    party_votes["party_id"].isin(eligible_parties_id)]

# Sainte-Laguë method
v = eligible_parties_votes["votes"].values[np.newaxis, :]
s = 1 / (2 * np.arange(party_seats)[:, np.newaxis] + 1)
# Only suitable when float64 sv * s < 49152 (CPU L1 cache 384KB), O(rows * cols).
top_k_idx = np.argpartition(-(v * s).ravel(), party_seats - 1)[:party_seats]
n_parties = len(eligible_parties_id)
top_k_col_idx = top_k_idx % n_parties
t = np.bincount(top_k_col_idx, minlength=n_parties)

party_prop_seats = pd.DataFrame(
    {"proportional_seats": t},
    index=eligible_parties_votes["party_id"],
)

# %% Calc parliament seats.
party_seats = pd.merge(
    # .astype("Int64") is nullable integer type, to prevent outer join from introducing
    # np.float64(nan)
    party_prop_seats.astype("Int64"), party_electorate_seats.astype("Int64"),
    left_index=True, right_index=True, how="outer"
)
party_seats["parliament_seats"] = party_seats.max(axis=1)

# %% Display results.
party_seats_ = party_seats.join(party_names).sort_values(
    "parliament_seats", ascending=False)[["party_name", "parliament_seats"]]

with pd.option_context(
    "display.max_rows", None,
    "display.max_columns", None,
    "display.max_colwidth", None,
    "display.width", 1000
):
    print(party_seats_)
total_parliament_seats = party_seats_["parliament_seats"].sum() + ind_seats
print("Total parliament seats:", total_parliament_seats)
