"""Analyze the geometry of the left block to find row spacing, slope, and column spacing."""

import json
import numpy as np

# Load unique seats
with open("analyzed-seats.json") as f:
    data = json.load(f)

unique_seats = data["unique_seats"]

# Filter to left block
left_seats = [s for s in unique_seats if s["x"] < 250]
print(f"Total seats in left block: {len(left_seats)}")

# We can group left seats into row clusters using y-coordinates first,
# but since the rows are slanted, a simple horizontal band won't be perfect.
# Let's project each seat along a slant line.
# If the row line has equation y = m * x + c, then c = y - m * x.
# For a given slope m, the value (y - m * x) should be constant for all seats in the same row.
# Let's find the optimal slope m that minimizes the variance within row clusters of (y - m * x)!

best_m = 0
min_variance = float("inf")

# Try slopes from -0.5 to 0.5
for m in np.linspace(-0.5, 0.5, 1000):
    projections = [s["y"] - m * s["x"] for s in left_seats]
    # Cluster projections
    projections.sort()
    gaps = [projections[i] - projections[i-1] for i in range(1, len(projections))]
    # Simple clustering with a threshold
    clusters = []
    for p in projections:
        if not clusters or p - np.mean(clusters[-1]) > 8:
            clusters.append([p])
        else:
            clusters[-1].append(p)
    
    # Calculate average variance of clusters
    var = np.mean([np.var(c) for c in clusters if len(c) > 1])
    if len(clusters) == 13 and var < min_variance: # we expect 13 rows B to P
        min_variance = var
        best_m = m

print(f"Best slope m for left block: {best_m:.4f}")

# Plot projections with the best slope
projections = [s["y"] - best_m * s["x"] for s in left_seats]
# Attach projection to seat
for s, p in zip(left_seats, projections):
    s["proj"] = p

# Sort left seats by projection descending (since larger y_proj = closer to bottom = Row B)
left_seats.sort(key=lambda s: s["proj"], reverse=True)

# Cluster them into 13 rows
left_rows = []
for s in left_seats:
    if not left_rows or s["proj"] - np.mean([x["proj"] for x in left_rows[-1]]) < -8:
        left_rows.append([s])
    else:
        left_rows[-1].append(s)

print(f"\nFound {len(left_rows)} rows in left block:")
row_letters_left = ["B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N", "P"]

for i, r in enumerate(left_rows):
    letter = row_letters_left[i] if i < len(row_letters_left) else f"Row_{i}"
    r_ys = [s["y"] for s in r]
    r_xs = [s["x"] for s in r]
    print(f"  {letter}: seats={len(r)}, x={min(r_xs):.1f}-{max(r_xs):.1f}, y={min(r_ys):.1f}-{max(r_ys):.1f}, proj_avg={np.mean([s['proj'] for s in r]):.1f}")
