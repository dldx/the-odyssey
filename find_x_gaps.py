"""Analyze x-coordinate distributions to find perfect block boundaries."""

import json
import numpy as np

# Load unique seats from analyzed-seats.json
with open("analyzed-seats.json") as f:
    data = json.load(f)

unique_seats = data["unique_seats"]

# Let's print the sorted x-coordinates of all unique seats
xs = sorted([s["x"] for s in unique_seats])
print(f"Total unique seats: {len(xs)}")
print(f"Sorted unique x values (min to max):")
print(f"  Min x: {xs[0]}")
print(f"  Max x: {xs[-1]}")

# Let's find large gaps in the x-coordinate distribution overall
gaps = []
for i in range(1, len(xs)):
    gap = xs[i] - xs[i-1]
    if gap > 10:
        gaps.append((gap, xs[i-1], xs[i]))

gaps.sort(reverse=True)
print("\nTop 10 largest x gaps overall:")
for gap, x1, x2 in gaps[:10]:
    print(f"  gap={gap:.1f}px between x={x1:.1f} and x={x2:.1f}")
