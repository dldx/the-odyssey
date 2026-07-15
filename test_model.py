"""Test the geometric row/block classification model on all 288 unique seats."""

import json
import numpy as np
from collections import defaultdict

# Define model parameters
LEFT_SLOPE = -0.327
RIGHT_SLOPE = 0.3001
CENTER_X0, CENTER_Y0 = 380.0, 860.3

# Reference projection centers and radii
LEFT_ROW_PROJS = {
    "B": 642.4, "C": 616.9, "D": 592.0, "E": 566.5, "F": 540.9,
    "G": 514.6, "H": 489.1, "J": 464.0, "K": 438.5, "L": 413.1,
    "M": 387.5, "N": 362.0, "P": 336.5,
}

RIGHT_ROW_PROJS = {
    "B": 407.9, "C": 383.5, "D": 357.7, "E": 334.2, "F": 308.8,
    "G": 283.3, "H": 257.7, "J": 232.0, "K": 205.4, "L": 179.8,
    "M": 154.4, "N": 128.9, "P": 103.4,
}

CENTER_ROW_RADII = {
    "A": 297.3, "B": 321.6, "C": 346.5, "D": 373.4, "E": 398.5,
    "F": 423.4, "G": 448.2, "H": 473.3, "J": 498.4, "K": 523.5,
    "L": 548.6, "M": 573.7, "N": 598.8, "P": 623.9, "Q": 649.0,
}

# Load unique seats
with open("analyzed-seats.json") as f:
    data = json.load(f)

unique_seats = data["unique_seats"]

# Stats
classified_seats = []
counts = defaultdict(lambda: defaultdict(int))

for s in unique_seats:
    x, y = s["x"], s["y"]
    
    # Classify block
    if x <= 250:
        block = "left"
        proj = y - LEFT_SLOPE * x
        # Find nearest row
        row = min(LEFT_ROW_PROJS.keys(), key=lambda r: abs(proj - LEFT_ROW_PROJS[r]))
        error = abs(proj - LEFT_ROW_PROJS[row])
    elif x >= 500:
        block = "right"
        proj = y - RIGHT_SLOPE * x
        row = min(RIGHT_ROW_PROJS.keys(), key=lambda r: abs(proj - RIGHT_ROW_PROJS[r]))
        error = abs(proj - RIGHT_ROW_PROJS[row])
    else:
        block = "center"
        rad = np.sqrt((x - CENTER_X0)**2 + (y - CENTER_Y0)**2)
        row = min(CENTER_ROW_RADII.keys(), key=lambda r: abs(rad - CENTER_ROW_RADII[r]))
        error = abs(rad - CENTER_ROW_RADII[row])
        
    classified_seats.append({
        "x": x, "y": y, "block": block, "row": row, "error": round(error, 2)
    })
    counts[row][block] += 1
    counts[row]["total"] += 1

print("=== Classification seat count per row and block ===")
all_letters = ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N", "P", "Q"]
for r in all_letters:
    bc = counts[r]
    print(f"  Row {r:1s}: Left={bc['left']:2d} Center={bc['center']:2d} Right={bc['right']:2d} Total={bc['total']:2d}")

# Show high-error seats (potential anomalies or misclassifications)
high_errors = [s for s in classified_seats if s["error"] > 5.0]
print(f"\nSeats with fitting error > 5px: {len(high_errors)}")
for s in high_errors[:15]:
    print(f"  x={s['x']:.1f}, y={s['y']:.1f}, block={s['block']:6s}, row={s['row']}, error={s['error']:.1f}")
