"""Probe: find the exact blue color range and circle dimensions in seat plan images."""
import cv2
import numpy as np
from pathlib import Path

img_path = "seat-maps/2026-07-30_13-00.png"
img = cv2.imread(img_path)
h, w = img.shape[:2]
print(f"Image: {w}x{h}")

# Sample some pixels that should be blue seats (from the visible seat plan)
# We'll look at the histogram of blue-ish pixels
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Look at a region that should have blue seats (middle of the image)
mid_region = hsv[300:500, 200:600]
# Average H, S, V of the brightest blue-ish pixels
mask_blue = (mid_region[:, :, 0] > 100) & (mid_region[:, :, 0] < 140) & (mid_region[:, :, 1] > 100) & (mid_region[:, :, 2] > 100)
blue_pixels = mid_region[mask_blue]
if len(blue_pixels) > 0:
    print(f"Blue pixel sample (count={len(blue_pixels)}):")
    print(f"  H: min={blue_pixels[:,0].min()}, max={blue_pixels[:,0].max()}, mean={blue_pixels[:,0].mean():.0f}")
    print(f"  S: min={blue_pixels[:,1].min()}, max={blue_pixels[:,1].max()}, mean={blue_pixels[:,1].mean():.0f}")
    print(f"  V: min={blue_pixels[:,2].min()}, max={blue_pixels[:,2].max()}, mean={blue_pixels[:,2].mean():.0f}")

# Also check the lighter blue dots (upper rows)
upper_region = hsv[100:250, 250:550]
mask_light = (upper_region[:, :, 0] > 100) & (upper_region[:, :, 0] < 160) & (upper_region[:, :, 1] > 30) & (upper_region[:, :, 2] > 150)
light_pixels = upper_region[mask_light]
if len(light_pixels) > 0:
    print(f"\nLight blue/purple pixel sample (count={len(light_pixels)}):")
    print(f"  H: min={light_pixels[:,0].min()}, max={light_pixels[:,0].max()}, mean={light_pixels[:,0].mean():.0f}")
    print(f"  S: min={light_pixels[:,1].min()}, max={light_pixels[:,1].max()}, mean={light_pixels[:,1].mean():.0f}")
    print(f"  V: min={light_pixels[:,2].min()}, max={light_pixels[:,2].max()}, mean={light_pixels[:,2].mean():.0f}")

# Try detecting circles with HoughCircles
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# Detect circles - typical seat dot is ~8px diameter, so minRadius=3, maxRadius=8
circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1, minDist=15,
                            param1=50, param2=15, minRadius=3, maxRadius=8)
if circles is not None:
    circles = np.uint16(np.around(circles))
    print(f"\nHoughCircles detected: {len(circles[0])}")
    # Sample a few
    for c in circles[0][:5]:
        print(f"  ({c[0]}, {c[1]}) r={c[2]}")
else:
    print("\nHoughCircles: no circles found")

# Also try contour-based approach with a specific blue mask
lower = np.array([100, 100, 100])
upper = np.array([140, 255, 255])
mask = cv2.inRange(hsv, lower, upper)
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
print(f"\nContours with H=[100,140] S,V>100: {len(contours)}")
# Show area distribution
areas = [cv2.contourArea(c) for c in contours]
if areas:
    print(f"  Area range: {min(areas):.0f} - {max(areas):.0f}, mean={np.mean(areas):.0f}")
    # Count contours with area in a reasonable range for seat dots
    seat_like = [a for a in areas if 20 < a < 200]
    print(f"  Contours with area 20-200: {len(seat_like)}")