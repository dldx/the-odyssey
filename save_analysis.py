"""
Save the final robust geometric mapping results to analyzed-seats.json,
and compile a summary of seat availability for the user.
"""

import json
import numpy as np
from collections import defaultdict

# Load original detected seats
with open("detected-seats.json") as f:
    data = json.load(f)

# Define robust model parameters
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

# Process each screening
screening_results = {}
for key, info in data.items():
    screening_seats = []
    for seat in info["seats"]:
        x, y = seat["x"], seat["y"]
        
        # Classify block and row
        if x <= 250:
            block = "left"
            proj = y - LEFT_SLOPE * x
            row = min(LEFT_ROW_PROJS.keys(), key=lambda r: abs(proj - LEFT_ROW_PROJS[r]))
        elif x >= 500:
            block = "right"
            proj = y - RIGHT_SLOPE * x
            row = min(RIGHT_ROW_PROJS.keys(), key=lambda r: abs(proj - RIGHT_ROW_PROJS[r]))
        else:
            block = "center"
            rad = np.sqrt((x - CENTER_X0)**2 + (y - CENTER_Y0)**2)
            row = min(CENTER_ROW_RADII.keys(), key=lambda r: abs(rad - CENTER_ROW_RADII[r]))
            
        screening_seats.append({
            "x": x,
            "y": y,
            "row": row,
            "block": block,
        })
        
    # Group available seats by row
    by_row = defaultdict(list)
    for s in screening_seats:
        by_row[s["row"]].append(s)
        
    # Build clean structure
    screening_results[key] = {
        "datetime": info["datetime"],
        "total_available": info["count"],
        "by_row": {
            row: {
                "count": len(seats),
                "blocks": sorted(set(s["block"] for s in seats)),
                "seats": [
                    {"x": s["x"], "y": s["y"], "block": s["block"]}
                    for s in sorted(seats, key=lambda s: s["x"])
                ]
            }
            for row, seats in sorted(by_row.items())
        }
    }

# Export to analyzed-seats.json
output_data = {
    "model_parameters": {
        "left_slope": LEFT_SLOPE,
        "right_slope": RIGHT_SLOPE,
        "center_point": [CENTER_X0, CENTER_Y0]
    },
    "screenings": screening_results
}

with open("analyzed-seats.json", "w") as f:
    json.dump(output_data, f, indent=2)

print("Saved analyzed-seats.json successfully!")
