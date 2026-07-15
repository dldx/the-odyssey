"""Detect ALL seats in the seat map using contour-based circle detection, regardless of color."""

import cv2
import json
import numpy as np

# Use the image with most available seats
img = cv2.imread("seat-maps/2026-08-10_12-00.png")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
h, w = gray.shape
print(f"Image: {w}x{h}")

# The seat map area is roughly y=290-610, x=100-670
# Seats are small circles ~9px diameter

# Try threshold-based segmentation: seats are lighter than background
# Use adaptive thresholding to find all seat-like blobs
_, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)

# Find contours
contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

# Filter contours by area and circularity
seats = []
for cnt in contours:
    area = cv2.contourArea(cnt)
    if 30 < area < 200:  # seat circle area range
        (cx, cy), radius = cv2.minEnclosingCircle(cnt)
        # Check circularity
        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0:
            continue
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        if circularity > 0.4:  # reasonably circular
            # Only keep seats in the seat map area
            if 280 < cy < 620 and 90 < cx < 680:
                seats.append({"x": int(cx), "y": int(cy), "area": area})

print(f"Detected {len(seats)} seats")

# Sort by y then x
seats.sort(key=lambda s: (s["y"], s["x"]))

# Analyze y-distribution for rows
ys = [s["y"] for s in seats]
print(f"Y range: {min(ys)} - {max(ys)}")

# Save for further analysis
with open("all-grid-seats.json", "w") as f:
    json.dump(seats, f, indent=2)

# Cluster by Y
y_vals = sorted(set(ys), reverse=True)
rows = []
for y in y_vals:
    if not rows or abs(y - np.mean(rows[-1])) > 10:
        rows.append([y])
    else:
        rows[-1].append(y)

print(f"\nRow clusters (10px threshold): {len(rows)}")
for i, row in enumerate(rows):
    y_avg = np.mean(row)
    row_seats = [s for s in seats if abs(s["y"] - y_avg) <= 6]
    xs = sorted([s["x"] for s in row_seats])
    print(f"  row {i}: y={y_avg:.0f}, seats={len(row_seats)}, x={min(xs)}-{max(xs)}")

# Draw on image
annotated = img.copy()
for s in seats:
    cv2.circle(annotated, (s["x"], s["y"]), 5, (0, 255, 0), 1)
cv2.imwrite("all-grid-annotated.png", annotated)
print("\nSaved all-grid-annotated.png")
