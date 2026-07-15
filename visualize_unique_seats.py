"""Plot the unique seat positions to visualize the layout and design a robust row/block mapping."""

import cv2
import json
import numpy as np

with open("detected-seats.json") as f:
    data = json.load(f)

# Collect all seat coordinates across all screenings
all_coords = []
for key, info in data.items():
    for s in info["seats"]:
        all_coords.append((s["x"], s["y"]))

all_coords = np.array(all_coords)

# Deduplicate to find unique seat positions (6px threshold)
sorted_idx = np.lexsort((all_coords[:, 0], all_coords[:, 1]))
sorted_coords = all_coords[sorted_idx]

unique_seats = []
for coord in sorted_coords:
    found = False
    for i, us in enumerate(unique_seats):
        if abs(coord[0] - us[0]) <= 6 and abs(coord[1] - us[1]) <= 6:
            # Average coordinates
            unique_seats[i] = ((unique_seats[i][0] + coord[0]) / 2, (unique_seats[i][1] + coord[1]) / 2)
            found = True
            break
    if not found:
        unique_seats.append((coord[0], coord[1]))

unique_seats = np.array(unique_seats)
print(f"Unique seat positions found: {len(unique_seats)}")

# Load a clean seat map image to draw on
img = cv2.imread("seat-maps/2026-08-10_12-00.png")
viz = img.copy()

# Draw unique seats and their index / coordinates
for idx, (x, y) in enumerate(unique_seats):
    cv2.circle(viz, (int(x), int(y)), 4, (0, 0, 255), -1)
    # Put a small index number next to each seat
    cv2.putText(viz, str(idx), (int(x) - 10, int(y) - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 0), 1)

cv2.imwrite("unique_seats_viz.png", viz)
print("Saved unique_seats_viz.png")
