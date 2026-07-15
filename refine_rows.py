"""Refine row clustering by analyzing y-gap distribution to find natural row breaks."""

import json
import numpy as np

with open("detected-seats.json") as f:
    data = json.load(f)

# Aggregate and deduplicate
all_coords = []
for key, info in data.items():
    for seat in info["seats"]:
        all_coords.append((seat["x"], seat["y"]))

all_coords = np.array(all_coords)

# Deduplicate with 6px threshold
sorted_idx = np.lexsort((all_coords[:, 0], all_coords[:, 1]))
sorted_coords = all_coords[sorted_idx]

unique_seats = []
for coord in sorted_coords:
    found = False
    for i, us in enumerate(unique_seats):
        if abs(coord[0] - us[0]) <= 6 and abs(coord[1] - us[1]) <= 6:
            unique_seats[i] = ((unique_seats[i][0] + coord[0]) / 2, (unique_seats[i][1] + coord[1]) / 2)
            found = True
            break
    if not found:
        unique_seats.append((coord[0], coord[1]))

unique_seats = np.array(unique_seats)

# Sort unique y values bottom to top (high y = front = row A)
y_vals = sorted(set(unique_seats[:, 1].astype(int)), reverse=True)
print(f"Unique y values ({len(y_vals)}): {y_vals}")

# Show consecutive gaps
print("\nConsecutive y-gaps:")
for i in range(len(y_vals) - 1):
    gap = y_vals[i] - y_vals[i + 1]
    marker = " <<<<" if gap > 10 else ""
    print(f"  y={y_vals[i]:4d} -> y={y_vals[i+1]:4d}  gap={gap:2d}{marker}")

# Try different thresholds
for threshold in [8, 10, 11, 12]:
    rows = []
    for y in y_vals:
        if not rows or abs(y - np.mean(rows[-1])) > threshold:
            rows.append([y])
        else:
            rows[-1].append(y)
    print(f"\nThreshold {threshold}px: {len(rows)} rows")
    for i, row in enumerate(rows):
        y_avg = np.mean(row)
        mask = np.abs(unique_seats[:, 1] - y_avg) <= threshold / 2 + 4
        count = np.sum(mask)
        print(f"  row {i}: y={y_avg:.0f}, seats={count}")
