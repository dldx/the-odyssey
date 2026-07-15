"""Find the optimal slope for the right block without enforcing an exact number of rows."""

import json
import numpy as np

with open("analyzed-seats.json") as f:
    data = json.load(f)

unique_seats = data["unique_seats"]
right_seats = [s for s in unique_seats if s["x"] > 500]

best_m = 0
min_variance = float("inf")
best_num_clusters = 0

# Scan positive slopes (0.25 to 0.35)
for m in np.linspace(0.25, 0.35, 1000):
    projections = [s["y"] - m * s["x"] for s in right_seats]
    projections.sort()
    
    # Cluster with 10px threshold
    clusters = []
    for p in projections:
        if not clusters or p - np.mean(clusters[-1]) > 10:
            clusters.append([p])
        else:
            clusters[-1].append(p)
            
    # Calculate average variance of clusters
    var = np.mean([np.var(c) for c in clusters if len(c) > 1])
    # We want a clean number of rows (between 11 and 13)
    if 11 <= len(clusters) <= 13 and var < min_variance:
        min_variance = var
        best_m = m
        best_num_clusters = len(clusters)

print(f"Optimal slope m for right block: {best_m:.4f} (gave {best_num_clusters} rows, variance={min_variance:.4f})")

# Let's project with this optimal slope and display the rows!
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
row_letters_right = ["B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N", "P"]

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
