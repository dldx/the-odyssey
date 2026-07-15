import cv2
import numpy as np

img = cv2.imread("seat-maps/2026-07-30_13-00.png")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Let's find the most common non-white, non-black, non-gray colors
# Specifically looking for the blue seats.
# Blue seats are typically very saturated blue.
# Let's filter for H in [100, 130], S > 150, V > 150
lower_blue = np.array([100, 150, 150])
upper_blue = np.array([130, 255, 255])
mask = cv2.inRange(hsv, lower_blue, upper_blue)

# Find non-zero pixel coordinates
y_indices, x_coordinates = np.where(mask > 0)
if len(x_coordinates) > 0:
    print(f"Found {len(x_coordinates)} blue pixels with tight mask")
    # Sample some actual BGR values
    sampled_bgr = []
    for i in range(min(10, len(x_coordinates))):
        x, y = x_coordinates[i], y_indices[i]
        sampled_bgr.append(img[y, x].tolist())
    print("Sample BGR values of blue pixels:", sampled_bgr)
else:
    print("No blue pixels found with tight mask, trying broader mask")
    # Try broader blue mask
    lower_blue = np.array([90, 100, 100])
    upper_blue = np.array([135, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    y_indices, x_coordinates = np.where(mask > 0)
    print(f"Found {len(x_coordinates)} blue pixels with broader mask")
    sampled_bgr = []
    for i in range(min(10, len(x_coordinates))):
        x, y = x_coordinates[i], y_indices[i]
        sampled_bgr.append(img[y, x].tolist())
    print("Sample BGR values of blue pixels:", sampled_bgr)
