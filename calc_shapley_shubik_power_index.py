# Ref: Shapley, L. S., & Shubik, M. (1954). A Method for Evaluating the Distribution of Power in a Committee System.
#      American Political Science Review, 48(3), 787–792.
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
q = active_parties["parliament_seats"].sum() // 2 + 1
n = active_parties.shape[0]
weights = active_parties["parliament_seats"].to_numpy()
s = np.zeros(n, dtype=np.float64)
# k! * (n - 1 - k)! / n!
factor = np.cumprod(
    np.r_[1 / n, np.arange(1, n) / np.arange(n - 1, 0, -1)]
)

# %% Build the shared DP using all parties.
dp = np.zeros((n + 1, q), dtype=np.int64)
dp[0, 0] = 1
for i, w in enumerate(weights):
    if w >= q:
        continue
    dp[1:i + 2, w:q] += dp[:i + 1, :q - w]

# %% Recover excluded-party counts using reusable buffers.
previous = np.zeros(q, dtype=np.int64)
current = np.zeros(q, dtype=np.int64)
swings_by_k = np.zeros(n, dtype=np.int64)
for i, w in enumerate(weights):
    if w >= q:
        s[i] = 1
        continue
    previous[:] = dp[0]
    swings_by_k[0] = np.sum(previous[q - w:])
    for k in range(1, n):
        current[:w] = dp[k, :w]
        np.subtract(dp[k, w:], previous[:q - w], out=current[w:])
        swings_by_k[k] = np.sum(current[q - w:])
        previous, current = current, previous
    s[i] = np.dot(swings_by_k, factor)

# %% Merge results of zero seat parties.
active_parties["shapley_index"] = s
dummy_parties["shapley_index"] = 0

results = pd.concat([active_parties, dummy_parties], axis=0)
results = results[["party_name", "shapley_index"]].sort_values(
    by="shapley_index", ascending=False)

# %% Export.
results.to_csv("results/shapley_shubik_power_index.csv")
