"""Inspect exact row assignments and projections for the left block."""

import json
import numpy as np

# Load unique seats
with open("analyzed-seats.json") as f:
    data = json.load(f)

unique_seats = data["unique_seats"]
left_seats = [s for s in unique_seats if s["x"] < 250]

# Compute projections
LEFT_SLOPE = -0.327
for s in left_seats:
    s["proj"] = s["y"] - LEFT_SLOPE * s["x"]

left_seats.sort(key=lambda s: s["proj"], reverse=True)

# Let's cluster into rows using 12px threshold on projection
left_rows = []
for s in left_seats:
    if not left_rows or s["proj"] - np.mean([x["proj"] for x in left_rows[-1]]) < -12:
        left_rows.append([s])
    else:
        left_rows[-1].append(s)

print(f"Clustered into {len(left_rows)} rows:")
for i, r in enumerate(left_rows):
    ys = [s["y"] for s in r]
    xs = [s["x"] for s in r]
    projs = [s["proj"] for s in r]
    print(f"  row {i:2d}: seats={len(r):2d}, proj={np.mean(projs):.1f} (min={min(projs):.1f}, max={max(projs):.1f}), x={min(xs):.1f}-{max(xs):.1f}, y={min(ys):.1f}-{max(ys):.1f}")
