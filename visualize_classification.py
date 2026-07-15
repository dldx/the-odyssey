"""Draw classified seats with their row letters and block names onto the clean seat map."""

import cv2
import json
import numpy as np

# Load unique seats and parameters
LEFT_SLOPE = -0.327
RIGHT_SLOPE = 0.3001
CENTER_X0, CENTER_Y0 = 380.0, 860.3

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

# Define a color palette for each row to visually distinguish them
row_colors = {
    "A": (255, 0, 0),     # Red
    "B": (255, 127, 0),   # Orange
    "C": (255, 255, 0),   # Yellow
    "D": (0, 255, 0),     # Green
    "E": (0, 0, 255),     # Blue
    "F": (75, 0, 130),    # Indigo
    "G": (143, 0, 255),   # Violet
    "H": (255, 0, 127),   # Pink
    "J": (0, 255, 255),   # Cyan
    "K": (127, 255, 212), # Aquamarine
    "L": (218, 112, 214), # Orchid
    "M": (255, 215, 0),   # Gold
    "N": (127, 127, 127), # Grey
    "P": (0, 0, 0),       # Black
    "Q": (255, 255, 255)  # White
}

# Load clean seat map image
img = cv2.imread("seat-maps/2026-08-10_12-00.png")
annotated = img.copy()

# Load unique seats from analyzed-seats.json
with open("analyzed-seats.json") as f:
    data = json.load(f)

unique_seats = data["unique_seats"]

for s in unique_seats:
    x, y = s["x"], s["y"]
    
    # Classify row and block using our geometric model
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
        
    color = row_colors.get(row, (128, 128, 128))
    
    # Draw circle for classified seat
    cv2.circle(annotated, (int(x), int(y)), 5, color, -1)
    # Add text overlay showing Row + Block (e.g. "B-L" for row B left block)
    cv2.putText(annotated, f"{row}", (int(x) - 4, int(y) + 3), cv2.FONT_HERSHEY_SIMPLEX, 0.25, (0, 0, 0), 1)

# Draw block boundaries
cv2.line(annotated, (250, 0), (250, 786), (0, 0, 0), 1)
cv2.line(annotated, (500, 0), (500, 786), (0, 0, 0), 1)

cv2.imwrite("classified_seats_overlay.png", annotated)
print("Saved classified_seats_overlay.png")
