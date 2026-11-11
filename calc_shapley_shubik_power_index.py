# Ref: Shapley, L. S., & Shubik, M. (1954). A Method for Evaluating the Distribution of Power in a Committee System.
#      American Political Science Review, 48(3), 787–792.
import math

import numpy as np
import pandas as pd

# %% Read data.
seats = pd.read_csv(
    "results/parliament_seats_preliminary.csv", index_col="party_id"
)

# %% Set zero seat parties aside.
active_parties = seats[seats["parliament_seats"] > 0]
dummy_parties = seats[seats["parliament_seats"] == 0]

# %% Define constants of Shapley Shubik power index.
q = math.ceil(active_parties["parliament_seats"].sum() / 2)
n = active_parties.shape[0]
weights = active_parties["parliament_seats"].to_numpy()
# Precompute permutation weighting factors: k! * (n - 1 - k)!
perm_weights = np.array([math.factorial(k) * math.factorial(n - 1 - k) for k in range(n)])
n_fact = math.factorial(n)
s = np.zeros(n, dtype=np.float64)

# %% Dynamic programming for each party.
for i in range(n):
    other_weights = np.delete(weights, i)
    # dp[coalition_size, weight] holds subset counts
    # Size: (n rows: 0 to n-1) x (q columns: 0 to q-1)
    dp = np.zeros((n, q))
    dp[0, 0] = 1  # Base case: empty coalition has size 0, weight 0

    # Vectorized DP knapsack update over other parties
    for w in other_weights:
        for k in reversed(range(n - 1)):
            # Shift and add counts across weights in [w, q - 1]
            dp[k+1, w:q] += dp[k, :q-w]

    # Vectorized swing accumulation across all coalition sizes k
    swings_by_k = dp[:, max(0, q - weights[i]) : q].sum(axis=1)
    total_pivotal_perms = np.sum(swings_by_k * perm_weights)
    s[i] = total_pivotal_perms / n_fact

# %% Merge results of zero seat parties.
active_parties["shapley_index"] = s
dummy_parties["shapley_index"] = 0

results = pd.concat([active_parties, dummy_parties], axis=0)
results = results[["party_name", "shapley_index"]].sort_values(
    by="shapley_index", ascending=False)

# %% Export.
results.to_csv("results/shapley_shubik_power_index.csv",)
