"""
Final seat analysis: cluster unique seats into rows and blocks,
assign row letters, and map each screening's available seats to row/block.
"""

import cv2
import json
import numpy as np
from collections import defaultdict

with open("detected-seats.json") as f:
    data = json.load(f)

# --- Step 1: Aggregate and deduplicate all seat positions ---
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
            unique_seats[i] = ((unique_seats[i][0] + coord[0]) / 2,
                              (unique_seats[i][1] + coord[1]) / 2)
            found = True
            break
    if not found:
        unique_seats.append((coord[0], coord[1]))

unique_seats = np.array(unique_seats)
print(f"Unique seat positions: {len(unique_seats)}")

# --- Step 2: Cluster into rows (10px threshold, bottom to top) ---
y_vals = sorted(set(unique_seats[:, 1].astype(int)), reverse=True)
row_clusters = []
for y in y_vals:
    if not row_clusters or abs(y - np.mean(row_clusters[-1])) > 10:
        row_clusters.append([y])
    else:
        row_clusters[-1].append(y)

# BFI IMAX has rows A-Q (17 rows). We have 15 clusters.
# The two largest gaps likely indicate missing rows.
# Compute gaps between consecutive row centers
row_centers = [np.mean(r) for r in row_clusters]
gaps = [row_centers[i] - row_centers[i + 1] for i in range(len(row_centers) - 1)]
avg_gap = np.mean(gaps)
print(f"\nRow centers: {[f'{c:.0f}' for c in row_centers]}")
print(f"Gaps: {[f'{g:.0f}' for g in gaps]}")
print(f"Average gap: {avg_gap:.1f}px")

# Identify rows to insert (where gap > avg_gap * 1.25)
rows_with_inserts = list(row_centers)
insert_positions = []
for i, gap in enumerate(gaps):
    if gap > avg_gap * 1.25:
        insert_y = row_centers[i] - avg_gap
        insert_positions.append((i + 1, insert_y))
        rows_with_inserts.insert(i + 1 + len(insert_positions) - 1, insert_y)
        print(f"  Inserting virtual row at y={insert_y:.0f} (gap was {gap:.0f}px)")

print(f"\nTotal rows (with inserts): {len(rows_with_inserts)}")

# Assign row letters A=bottom to Q=top
row_letters = [chr(ord('A') + i) for i in range(len(rows_with_inserts))]
row_map = {}  # y_center -> row_letter
for i, (y_center, letter) in enumerate(zip(rows_with_inserts, row_letters)):
    row_map[y_center] = letter

print("\nRow mapping:")
for y_center, letter in zip(rows_with_inserts, row_letters):
    print(f"  Row {letter}: y={y_center:.0f}")

# --- Step 3: Classify blocks (left/center/right) ---
# Based on x-gap analysis, block boundaries are approximately:
# Left/Center boundary: ~270 (varies slightly by row due to curvature)
# Center/Right boundary: ~500

# Use a row-dependent boundary that accounts for the curve.
# The center block narrows toward the back. Fit the boundaries from the data.
# For simplicity, use fixed thresholds derived from the data.
LEFT_CENTER = 270
CENTER_RIGHT = 500

def classify_block(x):
    if x < LEFT_CENTER:
        return "left"
    elif x < CENTER_RIGHT:
        return "center"
    else:
        return "right"

# --- Step 4: Assign each unique seat to row + block ---
unique_seat_data = []
for x, y in unique_seats:
    # Find nearest row
    nearest_idx = min(range(len(rows_with_inserts)),
                      key=lambda i: abs(y - rows_with_inserts[i]))
    row_letter = row_letters[nearest_idx]
    block = classify_block(x)
    unique_seat_data.append({
        "x": round(x, 1),
        "y": round(y, 1),
        "row": row_letter,
        "block": block,
    })

print(f"\n--- Seat count by row ---")
row_counts = defaultdict(lambda: defaultdict(int))
for s in unique_seat_data:
    row_counts[s["row"]][s["block"]] += 1
    row_counts[s["row"]]["total"] += 1

for letter in row_letters:
    counts = row_counts[letter]
    print(f"  Row {letter}: L={counts['left']:2d} C={counts['center']:2d} R={counts['right']:2d} total={counts['total']:2d}")

# --- Step 5: Map each screening's available seats to row/block ---
screening_results = {}
for key, info in data.items():
    screening_seats = []
    for seat in info["seats"]:
        x, y = seat["x"], seat["y"]
        nearest_idx = min(range(len(rows_with_inserts)),
                          key=lambda i: abs(y - rows_with_inserts[i]))
        row_letter = row_letters[nearest_idx]
        block = classify_block(x)
        screening_seats.append({
            "x": x,
            "y": y,
            "row": row_letter,
            "block": block,
        })

    # Group by row
    by_row = defaultdict(list)
    for s in screening_seats:
        by_row[s["row"]].append(s)

    screening_results[key] = {
        "datetime": info["datetime"],
        "total_available": info["count"],
        "by_row": {
            row: {
                "count": len(seats),
                "blocks": sorted(set(s["block"] for s in seats)),
                "seats": seats,
            }
            for row, seats in sorted(by_row.items())
        },
    }

# --- Step 6: Save results ---
output = {
    "row_mapping": {
        letter: {"y_center": round(rows_with_inserts[i], 1)}
        for i, letter in enumerate(row_letters)
    },
    "block_boundaries": {
        "left_center": LEFT_CENTER,
        "center_right": CENTER_RIGHT,
    },
    "unique_seats": unique_seat_data,
    "screenings": screening_results,
}

with open("analyzed-seats.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"\nSaved analyzed-seats.json")
print(f"  {len(screening_results)} screenings analyzed")
print(f"  {len(unique_seat_data)} unique seat positions mapped")

# --- Step 7: Summary of best screenings (most available seats) ---
print("\n--- Top 10 screenings by available seats ---")
sorted_screenings = sorted(screening_results.items(),
                           key=lambda x: x[1]["total_available"], reverse=True)
for key, info in sorted_screenings[:10]:
    rows_with_seats = [r for r in info["by_row"] if info["by_row"][r]["count"] > 0]
    rows_str = ", ".join(f"{r}({info['by_row'][r]['count']})" for r in rows_with_seats)
    print(f"  {info['datetime']}: {info['total_available']} seats in rows: {rows_str}")
