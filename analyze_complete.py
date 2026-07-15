"""
Analyze the near-complete seat map (2026-08-24_14-00, 276 seats) to determine
the correct row count and structure. Use a smarter approach: detect rows by
looking at the y-gap distribution and fitting the expected number of rows.
"""

import json
import numpy as np
from collections import defaultdict

with open("detected-seats.json") as f:
    data = json.load(f)

seats = data["2026-08-24_14-00"]["seats"]
coords = np.array([(s["x"], s["y"]) for s in seats])
print(f"Total seats: {len(coords)}")

# Sort by y descending (bottom to top)
order = np.argsort(-coords[:, 1])
coords = coords[order]

# Print all y values and gaps
ys = coords[:, 1].astype(int)
print(f"\nY range: {ys.min()}-{ys.max()}, span={ys.max()-ys.min()}px")

# If BFI IMAX has 17 rows (A-Q), expected spacing = 297/16 ≈ 18.6px
# If 16 rows, spacing = 297/15 ≈ 19.8px
# If 15 rows, spacing = 297/14 ≈ 21.2px

# Let's try different thresholds and see which gives the most stable row structure
for threshold in [14, 15, 16, 17, 18, 19, 20]:
    y_vals = sorted(set(ys), reverse=True)
    rows = []
    for y in y_vals:
        if not rows or abs(y - np.mean(rows[-1])) > threshold:
            rows.append([y])
        else:
            rows[-1].append(y)

    row_centers = [np.mean(r) for r in rows]
    gaps = [row_centers[i] - row_centers[i+1] for i in range(len(row_centers)-1)]
    counts = []
    for rc in row_centers:
        n = np.sum(np.abs(coords[:, 1] - rc) <= threshold / 2)
        counts.append(n)

    # Stability = std of gaps (lower = more uniform = more likely correct)
    if len(gaps) > 1:
        gap_std = np.std(gaps)
        gap_mean = np.mean(gaps)
    else:
        gap_std = 0
        gap_mean = 0

    print(f"  threshold={threshold}: {len(rows)} rows, gap_mean={gap_mean:.1f}, gap_std={gap_std:.1f}, "
          f"seats_per_row={counts}")

# Try threshold=17 which should give ~17 rows
print("\n=== Detailed analysis with threshold=17 ===")
y_vals = sorted(set(ys), reverse=True)
rows = []
for y in y_vals:
    if not rows or abs(y - np.mean(rows[-1])) > 17:
        rows.append([y])
    else:
        rows[-1].append(y)

print(f"Rows: {len(rows)}")
for i, r in enumerate(rows):
    ya = np.mean(r)
    mask = np.abs(coords[:, 1] - ya) <= 9
    row_seats = coords[mask]
    row_seats = row_seats[row_seats[:, 0].argsort()]
    xs = row_seats[:, 0].astype(int)

    # Detect blocks (gaps > 25px)
    blocks = [[xs[0]]] if len(xs) > 0 else []
    for j in range(1, len(xs)):
        if xs[j] - xs[j-1] > 25:
            blocks.append([xs[j]])
        else:
            blocks[-1].append(xs[j])

    block_strs = [f"{b[0]}-{b[-1]}({len(b)})" for b in blocks]
    print(f"  row {i}: y={ya:.0f}, n={len(xs)}, blocks: {block_strs}")

# Also try threshold=15
print("\n=== Detailed analysis with threshold=15 ===")
rows = []
for y in y_vals:
    if not rows or abs(y - np.mean(rows[-1])) > 15:
        rows.append([y])
    else:
        rows[-1].append(y)

print(f"Rows: {len(rows)}")
for i, r in enumerate(rows):
    ya = np.mean(r)
    mask = np.abs(coords[:, 1] - ya) <= 8
    row_seats = coords[mask]
    row_seats = row_seats[row_seats[:, 0].argsort()]
    xs = row_seats[:, 0].astype(int)

    blocks = [[xs[0]]] if len(xs) > 0 else []
    for j in range(1, len(xs)):
        if xs[j] - xs[j-1] > 25:
            blocks.append([xs[j]])
        else:
            blocks[-1].append(xs[j])

    block_strs = [f"{b[0]}-{b[-1]}({len(b)})" for b in blocks]
    print(f"  row {i}: y={ya:.0f}, n={len(xs)}, blocks: {block_strs}")
