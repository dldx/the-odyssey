"""Probe the detected seat coordinates to understand row/block structure."""

import json
from collections import defaultdict

import numpy as np

with open("detected-seats.json") as f:
    data = json.load(f)

# Aggregate all seat coordinates across all screenings
all_seats = []
for screening_key, info in data.items():
    for seat in info["seats"]:
        all_seats.append((seat["x"], seat["y"]))

all_seats = np.array(all_seats)
print(f"Total detected seat instances across all screenings: {len(all_seats)}")

# Cluster by Y coordinate (rows)
# Sort by y descending (bottom of image = lower rows)
y_values = sorted(set(all_seats[:, 1]), reverse=True)
print(f"\nUnique y-values (first 50, bottom to top): {y_values[:50]}")
print(f"Total unique y-values: {len(y_values)}")

# Simple row clustering using 12px threshold
rows = []
for y in y_values:
    if not rows or abs(y - rows[-1][0]) > 12:
        rows.append([y])
    else:
        rows[-1].append(y)

print(f"\nNumber of y-clusters (rows) found: {len(rows)}")
for i, row in enumerate(rows[:20]):
    print(f"  row cluster {i}: y={np.mean(row):.1f}, count={len(row)}")

# Look at x distribution overall
x_values = sorted(all_seats[:, 0])
print(f"\nX range: {min(x_values)} - {max(x_values)}")
print(f"X quartiles: {np.percentile(x_values, [0, 25, 50, 75, 100])}")
