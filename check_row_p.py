"""Check the top-most seats in the left block to see if Row P exists."""

import json
import numpy as np

with open("analyzed-seats.json") as f:
    data = json.load(f)

unique_seats = data["unique_seats"]
left_seats = [s for s in unique_seats if s["x"] < 250]

# Compute projections with correct slope -0.327
for s in left_seats:
    s["proj"] = s["y"] - (-0.327) * s["x"]

# Sort by proj descending
left_seats.sort(key=lambda s: s["proj"], reverse=True)

print("Top 15 seats (lowest projections, i.e., top of left block):")
for s in left_seats[-15:]:
    print(f"  x={s['x']:.1f}, y={s['y']:.1f}, proj={s['proj']:.1f}")
