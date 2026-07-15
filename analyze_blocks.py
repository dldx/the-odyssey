"""Build row/block structure from 288 unique seat positions with detailed x-analysis."""

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

# Use 10px threshold for rows
y_vals = sorted(set(unique_seats[:, 1].astype(int)), reverse=True)
rows = []
for y in y_vals:
    if not rows or abs(y - np.mean(rows[-1])) > 10:
        rows.append([y])
    else:
        rows[-1].append(y)

print(f"Row clusters: {len(rows)}")

for i, row in enumerate(rows):
    y_avg = np.mean(row)
    mask = np.abs(unique_seats[:, 1] - y_avg) <= 6
    row_seats = unique_seats[mask]
    row_seats = row_seats[row_seats[:, 0].argsort()]

    print(f"\n=== Row {i} (y={y_avg:.0f}, {len(row_seats)} seats) ===")
    xs = row_seats[:, 0].astype(int).tolist()

    # Print x positions and gaps
    for j, x in enumerate(xs):
        gap = xs[j] - xs[j-1] if j > 0 else 0
        gap_str = f"  [+{gap}]" if j > 0 else ""
        print(f"  x={x:4d}{gap_str}")

    # Identify blocks by gaps > 25px
    blocks = [[xs[0]]]
    for j in range(1, len(xs)):
        if xs[j] - xs[j-1] > 25:
            blocks.append([xs[j]])
        else:
            blocks[-1].append(xs[j])

    block_names = []
    for b in blocks:
        block_names.append(f"x={b[0]}-{b[-1]} ({len(b)} seats)")
    print(f"  Blocks: {block_names}")
