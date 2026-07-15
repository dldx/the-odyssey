"""Analyze seat layout: detect ALL seats (not just blue/available) to build the complete grid."""

import cv2
import json
import numpy as np

# Use the screening with the most available seats as reference
img = cv2.imread("seat-maps/2026-08-10_12-00.png")
print(f"Image shape: {img.shape}")

# Convert to grayscale to detect all circular seats
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Detect ALL circles (seats) regardless of color
# Seats are ~10px diameter, so radius ~5
circles = cv2.HoughCircles(
    gray,
    cv2.HOUGH_GRADIENT,
    dp=1,
    minDist=11,
    param1=50,
    param2=15,
    minRadius=3,
    maxRadius=8,
)

if circles is not None:
    circles = np.round(circles[0]).astype(int)
    print(f"Total circles detected: {len(circles)}")

    # Save all detected seats
    all_seats = [{"x": int(c[0]), "y": int(c[1]), "r": int(c[2])} for c in circles]

    with open("all-detected-seats.json", "w") as f:
        json.dump(all_seats, f, indent=2)

    # Analyze y-distribution for row clustering
    ys = sorted(circles[:, 1])
    print(f"\nY range: {min(ys)} - {max(ys)}")
    print(f"Total unique Y values: {len(set(ys))}")

    # Cluster by Y (rows) - use larger threshold for curved rows
    rows = []
    for y in sorted(set(ys)):
        if not rows or abs(y - rows[-1][0]) > 15:
            rows.append([y])
        else:
            rows[-1].append(y)

    print(f"\nRow clusters (15px threshold): {len(rows)}")
    for i, row in enumerate(rows):
        y_avg = np.mean(row)
        # Count seats in this row band
        count = np.sum((circles[:, 1] >= y_avg - 8) & (circles[:, 1] <= y_avg + 8))
        xs_in_row = circles[(circles[:, 1] >= y_avg - 8) & (circles[:, 1] <= y_avg + 8), 0]
        x_min, x_max = min(xs_in_row), max(xs_in_row)
        print(f"  row {i}: y={y_avg:.0f}, count={count}, x={x_min}-{x_max}")

    # Draw all detected circles on the image for verification
    annotated = img.copy()
    for c in circles:
        cv2.circle(annotated, (c[0], c[1]), c[2], (0, 255, 0), 1)
        cv2.circle(annotated, (c[0], c[1]), 1, (0, 0, 255), -1)

    cv2.imwrite("all-seats-annotated.png", annotated)
    print("\nSaved all-seats-annotated.png")
else:
    print("No circles detected!")
