"""Analyze right block geometry with slope = +0.306."""

import json
import numpy as np

with open("analyzed-seats.json") as f:
    data = json.load(f)

unique_seats = data["unique_seats"]
right_seats = [s for s in unique_seats if s["x"] > 500]

# Try different positive slopes to see which minimizes intra-row variance
best_m = 0
min_variance = float("inf")

for m in np.linspace(0.20, 0.40, 2000):
    projections = [s["y"] - m * s["x"] for s in right_seats]
    # Cluster projections
    projections.sort()
    clusters = []
    for p in projections:
        if not clusters or p - np.mean(clusters[-1]) > 8:
            clusters.append([p])
        else:
            clusters[-1].append(p)
    
    # Calculate average variance of clusters
    var = np.mean([np.var(c) for c in clusters if len(c) > 1])
    if len(clusters) == 12 and var < min_variance: # we expect 12 rows B to N
        min_variance = var
        best_m = m

print(f"Best slope m for right block: {best_m:.4f}")

# Let's run with the best slope we found in this range
for s in right_seats:
    s["proj"] = s["y"] - best_m * s["x"]

right_seats.sort(key=lambda s: s["proj"], reverse=True)

right_rows = []
for s in right_seats:
    if not right_rows or s["proj"] - np.mean([x["proj"] for x in right_rows[-1]]) < -10:
        right_rows.append([s])
    else:
        right_rows[-1].append(s)

print(f"\nFound {len(right_rows)} rows in right block:")
row_letters_right = ["B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N"]

for i, r in enumerate(right_rows):
    letter = row_letters_right[i] if i < len(row_letters_right) else f"Row_{i}"
    r_ys = [s["y"] for s in r]
    r_xs = [s["x"] for s in r]
    proj_avg = np.mean([s['proj'] for s in r])
    print(f"  {letter:3s}: seats={len(r):2d}, x={min(r_xs):5.1f}-{max(r_xs):5.1f}, y={min(r_ys):5.1f}-{max(r_ys):5.1f}, proj_avg={proj_avg:.1f}")

print("\nGaps between rows in right block:")
for i in range(len(right_rows) - 1):
    gap = np.mean([s['proj'] for s in right_rows[i]]) - np.mean([s['proj'] for s in right_rows[i+1]])
    print(f"  {row_letters_right[i]} -> {row_letters_right[i+1]}: {gap:.1f}px")
