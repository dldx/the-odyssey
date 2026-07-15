"""Aggregate and deduplicate all detected blue seats across all screenings to build the complete seat grid."""

import json
import numpy as np

with open("detected-seats.json") as f:
    data = json.load(f)

# Collect all seat coordinates
all_coords = []
for key, info in data.items():
    for seat in info["seats"]:
        all_coords.append((seat["x"], seat["y"]))

all_coords = np.array(all_coords)
print(f"Total seat detections (with duplicates): {len(all_coords)}")

# Deduplicate: cluster nearby points (within 6px = same seat)
# Sort by y, then x
sorted_idx = np.lexsort((all_coords[:, 0], all_coords[:, 1]))
sorted_coords = all_coords[sorted_idx]

unique_seats = []
for coord in sorted_coords:
    found = False
    for i, us in enumerate(unique_seats):
        if abs(coord[0] - us[0]) <= 6 and abs(coord[1] - us[1]) <= 6:
            # Average with existing
            unique_seats[i] = (
                (unique_seats[i][0] + coord[0]) / 2,
                (unique_seats[i][1] + coord[1]) / 2,
            )
            found = True
            break
    if not found:
        unique_seats.append((coord[0], coord[1]))

unique_seats = np.array(unique_seats)
print(f"Unique seat positions: {len(unique_seats)}")
print(f"X range: {unique_seats[:, 0].min()} - {unique_seats[:, 0].max()}")
print(f"Y range: {unique_seats[:, 1].min()} - {unique_seats[:, 1].max()}")

# Cluster by Y (rows) - sort by y descending (bottom = front = row A)
# The curve means y varies within a row. Use adaptive threshold.
ys = sorted(unique_seats[:, 1], reverse=True)  # bottom to top

# Try different thresholds to find natural row breaks
print("\n--- Y gaps analysis (bottom to top) ---")
y_sorted = sorted(set(unique_seats[:, 1]), reverse=True)
gaps = []
for i in range(1, len(y_sorted)):
    gap = y_sorted[i - 1] - y_sorted[i]
    if gap > 8:
        gaps.append((gap, y_sorted[i - 1], y_sorted[i]))
        print(f"  gap={gap}px between y={y_sorted[i-1]} and y={y_sorted[i]}")

print(f"\nTotal gaps > 8px: {len(gaps)}")

# Cluster rows using 14px threshold
rows = []
for y in y_sorted:
    if not rows or abs(y - np.mean(rows[-1])) > 14:
        rows.append([y])
    else:
        rows[-1].append(y)

print(f"\nRow clusters (14px threshold): {len(rows)}")
for i, row in enumerate(rows):
    y_avg = np.mean(row)
    # Find seats in this row band
    mask = np.abs(unique_seats[:, 1] - y_avg) <= 8
    seats_in_row = unique_seats[mask]
    xs = sorted(seats_in_row[:, 0])
    print(f"  row {i}: y={y_avg:.0f}, seats={len(seats_in_row)}, x={min(xs)}-{max(xs)}")

    # Show x-gaps within the row (to identify blocks)
    if len(xs) > 2:
        x_gaps = [xs[j + 1] - xs[j] for j in range(len(xs) - 1)]
        big_gaps = [(g, xs[j], xs[j + 1]) for j, g in enumerate(x_gaps) if g > 25]
        if big_gaps:
            print(f"    x-gaps > 25px: {big_gaps}")
