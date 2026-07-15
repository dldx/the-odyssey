"""Find the center of concentric circles (x0, y0) for the curvy middle block rows."""

import json
import numpy as np

# Load unique seats
with open("analyzed-seats.json") as f:
    data = json.load(f)

unique_seats = data["unique_seats"]

# Filter to center block (250 <= x <= 500)
center_seats = [s for s in unique_seats if 250 <= s["x"] <= 500]
print(f"Total seats in center block: {len(center_seats)}")

# Assume x0 is around the center of the seat map (x=385.5)
# Scan y0 from 800 to 5000 (below the image)
# We want to find y0 that minimizes the radius variance within clustered rows
best_y0 = 0
best_x0 = 0
min_variance = float("inf")
best_num_clusters = 0

for x0 in np.linspace(380, 390, 11):
    for y0 in np.linspace(800, 3000, 220):
        # Calculate radius for each seat
        radii = [np.sqrt((s["x"] - x0)**2 + (s["y"] - y0)**2) for s in center_seats]
        radii.sort()
        
        # Cluster radii (row spacing is ~25px, so use 12px threshold)
        clusters = []
        for r in radii:
            if not clusters or r - np.mean(clusters[-1]) > 12:
                clusters.append([r])
            else:
                clusters[-1].append(r)
                
        # Calculate average variance of clusters
        var = np.mean([np.var(c) for c in clusters if len(c) > 1])
        # We expect several rows in the center block (e.g. 5 to 10 rows detected)
        if 5 <= len(clusters) <= 10 and var < min_variance:
            min_variance = var
            best_x0 = x0
            best_y0 = y0
            best_num_clusters = len(clusters)

print(f"Optimal concentric circle center: ({best_x0:.1f}, {best_y0:.1f})")
print(f"  Gave {best_num_clusters} row clusters, average radius variance={min_variance:.4f}")

# Let's project and print the row details
x0, y0 = best_x0, best_y0
for s in center_seats:
    s["radius"] = np.sqrt((s["x"] - x0)**2 + (s["y"] - y0)**2)

center_seats.sort(key=lambda s: s["radius"]) # sort by radius ascending (from back to front, or front to back?
# Let's check:
# Center y0 is below the screen (e.g. y0 = 1500).
# Front row (Row A) is closest to the screen (y around 600).
# Back row (Row Q) is furthest from the screen (y around 300).
# So for y0 = 1500, a front row seat (y=600) has distance 1500 - 600 = 900.
# A back row seat (y=300) has distance 1500 - 300 = 1200.
# So radius is SMALLER for front rows, and LARGER for back rows!
# Let's sort by radius ascending: this means front to back (Row A to Row Q).

center_rows = []
for s in center_seats:
    if not center_rows or s["radius"] - np.mean([x["radius"] for x in center_rows[-1]]) > 12:
        center_rows.append([s])
    else:
        center_rows[-1].append(s)

print(f"\nFound {len(center_rows)} rows in center block:")
# Center block can have rows: A, B, C, D, E, F, G, H, J, K, L, M, N, P, Q
row_letters_center = ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N", "P", "Q"]

for i, r in enumerate(center_rows):
    letter = row_letters_center[i] if i < len(row_letters_center) else f"Row_{i}"
    r_ys = [s["y"] for s in r]
    r_xs = [s["x"] for s in r]
    rad_avg = np.mean([s['radius'] for s in r])
    print(f"  {letter:3s}: seats={len(r):2d}, x={min(r_xs):5.1f}-{max(r_xs):5.1f}, y={min(r_ys):5.1f}-{max(r_ys):5.1f}, radius_avg={rad_avg:.1f}")

print("\nGaps between rows in center block (radii gaps):")
for i in range(len(center_rows) - 1):
    gap = np.mean([s['radius'] for s in center_rows[i+1]]) - np.mean([s['radius'] for s in center_rows[i]])
    print(f"  {row_letters_center[i]} -> {row_letters_center[i+1]}: {gap:.1f}px")
