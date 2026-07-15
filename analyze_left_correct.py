"""Analyze the left block geometry using the correct slope -0.327 derived from Row B."""

import json
import numpy as np

with open("analyzed-seats.json") as f:
    data = json.load(f)

unique_seats = data["unique_seats"]
left_seats = [s for s in unique_seats if s["x"] < 250]

# Correct slope from bottom-most row of left block
slope = -0.327

# Project each seat
for s in left_seats:
    s["proj"] = s["y"] - slope * s["x"]

left_seats.sort(key=lambda s: s["proj"], reverse=True)

# Cluster into rows using projection values
left_rows = []
for s in left_seats:
    if not left_rows or s["proj"] - np.mean([x["proj"] for x in left_rows[-1]]) < -10:
        left_rows.append([s])
    else:
        left_rows[-1].append(s)

print(f"Using slope {slope}: found {len(left_rows)} rows:")
row_letters_left = ["B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N", "P"]

for i, r in enumerate(left_rows):
    letter = row_letters_left[i] if i < len(row_letters_left) else f"Row_{i}"
    r_ys = [s["y"] for s in r]
    r_xs = [s["x"] for s in r]
    proj_avg = np.mean([s['proj'] for s in r])
    print(f"  {letter:3s}: seats={len(r):2d}, x={min(r_xs):5.1f}-{max(r_xs):5.1f}, y={min(r_ys):5.1f}-{max(r_ys):5.1f}, proj_avg={proj_avg:.1f}")

# Let's print adjacent row projection gaps
print("\nGaps between rows:")
for i in range(len(left_rows) - 1):
    gap = np.mean([s['proj'] for s in left_rows[i]]) - np.mean([s['proj'] for s in left_rows[i+1]])
    print(f"  {row_letters_left[i]} -> {row_letters_left[i+1]}: {gap:.1f}px")
